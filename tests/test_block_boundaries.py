from __future__ import annotations

import json
import unittest

from heartbeat_runtime import HeartbeatRuntime
from tests.test_heartbeat_runtime import RuntimeFixture, write


class BlockBoundaryTests(unittest.TestCase):
    def test_completed_registry_dependency_releases_machine_block(self):
        fx = RuntimeFixture()
        try:
            dependency = fx.task('TASK-DEP', state='COMPLETED')
            dependency['archive_eligible'] = True
            blocked = fx.task('TASK-BLOCKED', state='BLOCKED', authorized=False)
            handoff_path = fx.root / blocked['handoff_ref']
            handoff = json.loads(handoff_path.read_text())
            handoff['state'] = 'BLOCKED'
            handoff['block'] = {
                'block_reason': 'WAIT_FOR_DEPENDENCY',
                'dependency': 'TASK-DEP',
                'observer': 'worker-registry',
                'recheck_trigger': 'each heartbeat',
                'next_check': None,
                'escalation_condition': None,
                'block_expires_at': None,
            }
            write(handoff_path, handoff)
            blocked['block_ref'] = f"{blocked['handoff_ref']}#block"
            blocked['archive_reason_codes'] = ['BLOCKED_DEPENDENCY']
            fx.registry([dependency, blocked])

            result = HeartbeatRuntime(fx.root, adapters={}).cycle()
            released = next(event for event in result['events'] if event.get('event_type') == 'block_released')
            self.assertEqual(released['task_id'], 'TASK-BLOCKED')
            state = json.loads((fx.root / 'control/worker-registry.json').read_text())
            child = next(item for item in state['tasks'] if item['task_id'] == 'TASK-BLOCKED')
            self.assertEqual(child['state'], 'HANDOFF_READY')
            self.assertIsNone(child['block_ref'])
            updated_handoff = json.loads(handoff_path.read_text())
            self.assertEqual(updated_handoff['state'], 'HANDOFF_READY')
            self.assertIsNone(updated_handoff['block'])
        finally:
            fx.close()

    def test_unresolved_machine_block_is_rechecked_but_not_released(self):
        fx = RuntimeFixture()
        try:
            dependency = fx.task('TASK-DEP', state='BLOCKED')
            blocked = fx.task('TASK-BLOCKED', state='BLOCKED', authorized=False)
            handoff_path = fx.root / blocked['handoff_ref']
            handoff = json.loads(handoff_path.read_text())
            handoff['state'] = 'BLOCKED'
            handoff['block'] = {
                'block_reason': 'WAIT_FOR_DEPENDENCY',
                'dependency': 'TASK-DEP',
                'observer': 'worker-registry',
                'recheck_trigger': 'each heartbeat',
                'next_check': None,
                'escalation_condition': None,
                'block_expires_at': None,
            }
            write(handoff_path, handoff)
            blocked['block_ref'] = f"{blocked['handoff_ref']}#block"
            fx.registry([dependency, blocked])

            result = HeartbeatRuntime(fx.root, adapters={}).cycle()
            check = next(event for event in result['events'] if event.get('event_type') == 'block_rechecked' and event.get('task_id') == 'TASK-BLOCKED')
            self.assertFalse(check['released'])
            state = json.loads((fx.root / 'control/worker-registry.json').read_text())
            child = next(item for item in state['tasks'] if item['task_id'] == 'TASK-BLOCKED')
            self.assertEqual(child['state'], 'BLOCKED')
        finally:
            fx.close()

    def test_human_authority_required_is_terminal_for_automation(self):
        fx = RuntimeFixture()
        try:
            task = fx.task('TASK-HUMAN', state='HUMAN_AUTHORITY_REQUIRED')
            boundary_ref = 'boundaries/TASK-HUMAN.json'
            write(fx.root / boundary_ref, {
                'schema': 'stegverse.human-authority-boundary/v0.1',
                'boundary_id': 'BOUNDARY-TASK-HUMAN',
                'task_id': 'TASK-HUMAN',
                'requested_decision': 'Approve or reject the consequential action.',
                'authority_source': 'named-human-authority',
                'evidence_refs': ['evidence/candidate.json'],
                'resume_trigger': 'A separately admitted resolution and authorization are durable.',
                'status': 'PENDING',
                'resolution_ref': None,
                'automation_terminal': True,
            })
            task['block_ref'] = boundary_ref
            fx.registry([task])

            result = HeartbeatRuntime(fx.root, adapters={'fixture': lambda *_: (_ for _ in ()).throw(AssertionError('must not execute'))}).cycle()
            boundary = next(event for event in result['events'] if event.get('event_type') == 'human_authority_required')
            self.assertTrue(boundary['boundary_valid'])
            self.assertTrue(boundary['automation_terminal'])
            self.assertFalse(result['activated'])
            state = json.loads((fx.root / 'control/worker-registry.json').read_text())
            human = state['tasks'][0]
            self.assertEqual(human['state'], 'HUMAN_AUTHORITY_REQUIRED')
            self.assertIsNone(human['claim_id'])
            self.assertIn('AUTOMATION_TERMINAL_UNTIL_HUMAN_DECISION', human['archive_reason_codes'])
        finally:
            fx.close()


if __name__ == '__main__':
    unittest.main()
