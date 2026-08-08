from __future__ import annotations

import json
import unittest

from heartbeat_runtime import HeartbeatRuntime, WorkerResponse
from tests.test_heartbeat_runtime import RuntimeFixture


class LifecycleAuthorityTests(unittest.TestCase):
    def test_normal_heartbeat_response_does_not_renew_authority(self):
        fx = RuntimeFixture()
        try:
            basis = fx.cost_basis('fixture', beats=4)
            task = fx.task('TASK-A', cost_basis_ref=basis)
            fx.registry([task])

            def adapter(task, handoff, epoch):
                return WorkerResponse(state='ACTIVE', transition_id='WORK', transition_sequence=epoch)

            runtime = HeartbeatRuntime(fx.root, adapters={'fixture': adapter})
            runtime.cycle()
            first = json.loads((fx.root / 'control/worker-registry.json').read_text())['tasks'][0]
            self.assertEqual(first['heartbeat_timing']['expiry_epoch'], 5)
            self.assertEqual(first['heartbeat_timing']['max_missing_response_beats'], 2)
            self.assertEqual(first['heartbeat_timing']['renewal_count'], 0)

            runtime.cycle()
            second = json.loads((fx.root / 'control/worker-registry.json').read_text())['tasks'][0]
            self.assertEqual(second['heartbeat_timing']['expiry_epoch'], 5)
            self.assertEqual(second['heartbeat_timing']['renewal_count'], 0)
        finally:
            fx.close()

    def test_separately_admitted_scope_bound_renewal_extends_expiry(self):
        fx = RuntimeFixture()
        try:
            basis = fx.cost_basis('fixture', beats=4)
            task = fx.task('TASK-A', cost_basis_ref=basis)
            fx.registry([task])

            def adapter(task, handoff, epoch):
                return WorkerResponse(state='ACTIVE', transition_id='WORK', transition_sequence=epoch)

            runtime = HeartbeatRuntime(fx.root, adapters={'fixture': adapter})
            runtime.cycle()
            registry_path = fx.root / 'control/worker-registry.json'
            registry = json.loads(registry_path.read_text())
            active = registry['tasks'][0]
            self.assertEqual(active['heartbeat_timing']['expiry_epoch'], 5)
            handoff = json.loads((fx.root / active['handoff_ref']).read_text())
            renewal_ref = 'renewals/TASK-A-HB2.json'
            renewal = {
                'schema': 'stegverse.worker-renewal-admission/v0.1',
                'renewal_id': 'RENEW-TASK-A-HB2',
                'task_id': 'TASK-A',
                'claim_id': active['claim_id'],
                'fencing_token': active['heartbeat_timing']['fencing_token'],
                'prior_expiry_epoch': 5,
                'additional_beats': 3,
                'scope_sha256': runtime._scope_sha256(handoff),
                'authority_source': handoff['authority']['authority_source'],
                'policy_version': handoff['authority']['policy_version'],
                'status': 'ADMITTED',
                'heartbeat_grants_renewal': False,
            }
            from tests.test_heartbeat_runtime import write
            write(fx.root / renewal_ref, renewal)
            active['renewal_ref'] = renewal_ref
            write(registry_path, registry)

            result = runtime.cycle()
            renewed_event = next(event for event in result['events'] if event.get('event_type') == 'authorization_renewed')
            self.assertFalse(renewed_event['heartbeat_granted_renewal'])
            state = json.loads(registry_path.read_text())['tasks'][0]
            self.assertEqual(state['heartbeat_timing']['expiry_epoch'], 8)
            self.assertEqual(state['heartbeat_timing']['renewal_count'], 1)
            self.assertIsNone(state['renewal_ref'])
            self.assertIn(renewal_ref, state['evidence_refs'])

            runtime.cycle()
            state2 = json.loads(registry_path.read_text())['tasks'][0]
            self.assertEqual(state2['heartbeat_timing']['expiry_epoch'], 8)
            self.assertEqual(state2['heartbeat_timing']['renewal_count'], 1)
        finally:
            fx.close()

    def test_missing_same_hb_responses_degrade_then_orphan_before_authority_expiry(self):
        fx = RuntimeFixture()
        try:
            basis = fx.cost_basis('fixture', beats=4)
            task = fx.task('TASK-A', cost_basis_ref=basis)
            fx.registry([task])

            def adapter(task, handoff, epoch):
                return WorkerResponse(
                    state='ACTIVE',
                    transition_id='WORK',
                    transition_sequence=1,
                    checkpoint_ref='master-records/orchestration:checkpoint-task-a',
                )

            runtime = HeartbeatRuntime(fx.root, adapters={'fixture': adapter})
            runtime.cycle()  # HB1: valid response; response-loss threshold 2, expiry HB5
            runtime.adapters = {}

            hb2 = runtime.cycle()
            self.assertFalse(any(event.get('event_type') == 'worker_orphaned' for event in hb2['events']))
            state2 = json.loads((fx.root / 'control/worker-registry.json').read_text())
            parent2 = next(item for item in state2['tasks'] if item['task_id'] == 'TASK-A')
            worker2 = state2['workers'][0]
            self.assertEqual(parent2['state'], 'ACTIVE')
            self.assertIn('WORKER_RESPONSE_MISSING_OBSERVED', parent2['archive_reason_codes'])
            self.assertEqual(worker2['status'], 'DEGRADED')
            self.assertEqual(parent2['heartbeat_timing']['expiry_epoch'], 5)

            hb3 = runtime.cycle()
            orphan_event = next(event for event in hb3['events'] if event.get('event_type') == 'worker_orphaned')
            self.assertEqual(orphan_event['last_valid_fencing_token'], 1)
            state3 = json.loads((fx.root / 'control/worker-registry.json').read_text())
            parent = next(item for item in state3['tasks'] if item['task_id'] == 'TASK-A')
            recovery = next(item for item in state3['tasks'] if item['task_id'].startswith('RECOVER-TASK-A-ORPHAN-HB3'))
            self.assertEqual(parent['state'], 'BLOCKED')
            self.assertIsNone(parent['claim_id'])
            self.assertIsNone(parent['worker_id'])
            self.assertEqual(parent['last_checkpoint_ref'], 'master-records/orchestration:checkpoint-task-a')
            self.assertEqual(parent['heartbeat_timing']['expiry_epoch'], 5)
            self.assertEqual(parent['heartbeat_timing']['fencing_token'], 1)
            self.assertEqual(recovery['state'], 'HANDOFF_READY')
            self.assertIn('SUCCESSOR_RECONSTRUCTION_REQUIRED', recovery['archive_reason_codes'])
            generated = json.loads((fx.root / recovery['handoff_ref']).read_text())
            self.assertEqual(generated['task']['parent_task_id'], 'TASK-A')
            self.assertEqual(generated['continuity']['checkpoint_ref'], 'master-records/orchestration:checkpoint-task-a')
            self.assertNotIn('reconstruction_ref', generated['continuity'])
            self.assertLess(3, parent['heartbeat_timing']['expiry_epoch'])
        finally:
            fx.close()


if __name__ == '__main__':
    unittest.main()
