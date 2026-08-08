from __future__ import annotations

import json
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


if __name__ == '__main__':
    unittest.main()
