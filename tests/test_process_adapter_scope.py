from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from heartbeat_runtime.process_adapter import ProcessWorkerAdapter


WORKER = r'''
import json
from pathlib import Path
import sys
inv = json.load(sys.stdin)
mode = Path('mode.txt').read_text().strip()
if mode == 'allowed':
    p = Path('allowed/result.txt')
else:
    p = Path('outside.txt')
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text('mutation-from-worker\n')
json.dump({
    'schema': 'stegverse.worker-response/v0.1',
    'state': 'COMPLETED',
    'transition_id': 'DONE',
    'transition_sequence': 1,
    'evidence_refs': [],
    'cost_observation': {'external_cost_usd': 0}
}, sys.stdout)
sys.stdout.write('\n')
'''

BOUND_WORKER = r'''
import json
import os
from pathlib import Path
import sys
inv = json.load(sys.stdin)
mode = Path('mode.txt').read_text().strip()
root = Path(os.environ['STEGVERSE_BOUND_STATE_ROOT'])
assert root.is_absolute()
assert str(root).startswith(str(Path.cwd().parent))
assert '.stegverse' not in str(root)
if mode == 'state_allowed':
    target = root / 'outbox/request.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('{"request":true}\n')
elif mode == 'state_denied':
    target = root / 'escape.json'
    target.write_text('{}\n')
elif mode == 'read_inbox':
    value = json.loads((root / 'inbox/receipt.json').read_text())
    target = Path('allowed/result.txt')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value['status'] + '\n')
json.dump({
    'schema': 'stegverse.worker-response/v0.1',
    'state': 'COMPLETED',
    'transition_id': 'DONE',
    'transition_sequence': 1,
    'evidence_refs': [],
    'cost_observation': {'external_cost_usd': 0}
}, sys.stdout)
sys.stdout.write('\n')
'''


class ProcessAdapterScopeTests(unittest.TestCase):
    def setup_workspace(self, mode: str):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        (root / 'worker.py').write_text(WORKER, encoding='utf-8')
        (root / 'mode.txt').write_text(mode, encoding='utf-8')
        task = {
            'task_id': 'TASK-SCOPE',
            'goal_id': 'TASK-SCOPE',
            'claim_id': 'SHWP-TASK-SCOPE-G7',
            'worker_id': 'worker',
            'worker_instance_id': 'worker-HB1-G7',
            'heartbeat_timing': {'fencing_token': 7},
        }
        handoff = {
            'execution': {
                'allowed_paths': ['allowed/**'],
                'required_capabilities': ['fixture_execute'],
                'allowed_services': [],
            }
        }
        adapter = ProcessWorkerAdapter(
            [sys.executable, 'worker.py'],
            cwd=root,
            timeout_seconds=5,
        )
        return tmp, root, task, handoff, adapter

    def test_allowed_sandbox_delta_is_committed_and_receipted(self):
        tmp, root, task, handoff, adapter = self.setup_workspace('allowed')
        try:
            response = adapter(task, handoff, 1)
            self.assertEqual(response.state, 'COMPLETED')
            self.assertEqual((root / 'allowed/result.txt').read_text(), 'mutation-from-worker\n')
            receipts = sorted((root / 'receipts/worker-mutation-scope').glob('*.json'))
            self.assertEqual(len(receipts), 1)
            receipt = json.loads(receipts[0].read_text())
            self.assertEqual(receipt['decision'], 'ALLOW')
            self.assertEqual(receipt['claim_id'], 'SHWP-TASK-SCOPE-G7')
            self.assertEqual(receipt['fencing_token'], 7)
            self.assertEqual(receipt['changed_paths'], ['allowed/result.txt'])
            self.assertFalse(receipt['bound_state_enabled'])
            self.assertIn(receipts[0].relative_to(root).as_posix(), response.evidence_refs)
        finally:
            tmp.cleanup()

    def test_out_of_scope_delta_is_denied_without_authoritative_mutation(self):
        tmp, root, task, handoff, adapter = self.setup_workspace('denied')
        try:
            with self.assertRaisesRegex(RuntimeError, 'mutation denied by claim scope'):
                adapter(task, handoff, 1)
            self.assertFalse((root / 'outside.txt').exists())
            receipts = sorted((root / 'receipts/worker-mutation-scope').glob('*.json'))
            self.assertEqual(len(receipts), 1)
            receipt = json.loads(receipts[0].read_text())
            self.assertEqual(receipt['decision'], 'DENY')
            self.assertEqual(receipt['reason'], 'OUT_OF_SCOPE_MUTATION')
            self.assertEqual(receipt['changed_paths'], ['outside.txt'])
        finally:
            tmp.cleanup()

    def test_claim_fence_mismatch_fails_before_worker_execution(self):
        tmp, root, task, handoff, adapter = self.setup_workspace('allowed')
        try:
            task['claim_id'] = 'SHWP-TASK-SCOPE-G6'
            with self.assertRaisesRegex(RuntimeError, 'claim/fencing generation mismatch'):
                adapter(task, handoff, 1)
            self.assertFalse((root / 'allowed/result.txt').exists())
            self.assertFalse((root / 'receipts/worker-mutation-scope').exists())
        finally:
            tmp.cleanup()


class BoundStateAdapterTests(unittest.TestCase):
    def setup_bound(self, mode: str):
        tmp = tempfile.TemporaryDirectory()
        outer = Path(tmp.name)
        workspace = outer / 'workspace'
        state_root = outer / 'authoritative-state'
        workspace.mkdir()
        state_root.mkdir()
        (workspace / 'worker.py').write_text(BOUND_WORKER, encoding='utf-8')
        (workspace / 'mode.txt').write_text(mode, encoding='utf-8')
        task = {
            'task_id': 'TASK-BOUND',
            'goal_id': 'TASK-BOUND',
            'claim_id': 'SHWP-TASK-BOUND-G3',
            'worker_id': 'worker',
            'worker_instance_id': 'worker-HB4-G3',
            'heartbeat_timing': {'fencing_token': 3},
        }
        handoff = {
            'execution': {
                'allowed_paths': ['allowed/**'],
                'required_capabilities': ['fixture_execute'],
                'allowed_services': ['local-bound-state'],
            }
        }
        adapter = ProcessWorkerAdapter(
            [sys.executable, 'worker.py'],
            cwd=workspace,
            timeout_seconds=5,
            env_allowlist=(),
            bound_state_root=state_root,
            bound_state_allowed_paths=('outbox/**', 'inbox/**', 'processed/**'),
        )
        return tmp, workspace, state_root, task, handoff, adapter

    def test_bound_state_write_is_projected_after_scope_validation(self):
        tmp, workspace, state_root, task, handoff, adapter = self.setup_bound('state_allowed')
        try:
            response = adapter(task, handoff, 4)
            self.assertEqual(response.state, 'COMPLETED')
            self.assertEqual((state_root / 'outbox/request.json').read_text(), '{"request":true}\n')
            receipts = sorted((workspace / 'receipts/worker-mutation-scope').glob('*.json'))
            receipt = json.loads(receipts[-1].read_text())
            self.assertTrue(receipt['bound_state_enabled'])
            self.assertEqual(receipt['bound_state_changed_paths'], ['outbox/request.json'])
            self.assertFalse(receipt['bound_state_authoritative_path_exposed_to_worker'])
        finally:
            tmp.cleanup()

    def test_bound_state_out_of_scope_write_is_denied(self):
        tmp, workspace, state_root, task, handoff, adapter = self.setup_bound('state_denied')
        try:
            with self.assertRaisesRegex(RuntimeError, 'mutation denied by claim scope'):
                adapter(task, handoff, 4)
            self.assertFalse((state_root / 'escape.json').exists())
            receipts = sorted((workspace / 'receipts/worker-mutation-scope').glob('*.json'))
            receipt = json.loads(receipts[-1].read_text())
            self.assertEqual(receipt['decision'], 'DENY')
            self.assertEqual(receipt['reason'], 'OUT_OF_SCOPE_BOUND_STATE_MUTATION')
        finally:
            tmp.cleanup()

    def test_inbox_state_is_mirrored_into_next_worker_sandbox(self):
        tmp, workspace, state_root, task, handoff, adapter = self.setup_bound('read_inbox')
        try:
            (state_root / 'inbox').mkdir()
            (state_root / 'inbox/receipt.json').write_text('{"status":"READY"}\n')
            adapter(task, handoff, 4)
            self.assertEqual((workspace / 'allowed/result.txt').read_text(), 'READY\n')
            self.assertEqual(json.loads((state_root / 'inbox/receipt.json').read_text())['status'], 'READY')
        finally:
            tmp.cleanup()

    def test_bound_state_root_with_symlink_is_rejected_before_execution(self):
        tmp, workspace, state_root, task, handoff, adapter = self.setup_bound('state_allowed')
        try:
            target = state_root / 'target.txt'
            target.write_text('x')
            try:
                os.symlink(target, state_root / 'link.txt')
            except (OSError, NotImplementedError):
                self.skipTest('symlink unavailable')
            with self.assertRaisesRegex(RuntimeError, 'may not contain symlinks'):
                adapter(task, handoff, 4)
            self.assertFalse((state_root / 'outbox/request.json').exists())
        finally:
            tmp.cleanup()


if __name__ == '__main__':
    unittest.main()
