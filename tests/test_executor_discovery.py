from __future__ import annotations

import json
import unittest

from heartbeat_runtime import HeartbeatRuntime, WorkerResponse
from tests.test_heartbeat_runtime import RuntimeFixture, write


class ExecutorDiscoveryTests(unittest.TestCase):
    def test_two_equivalent_available_workers_are_ambiguous_and_not_selected(self):
        fx = RuntimeFixture()
        calls = []
        try:
            basis = fx.cost_basis('fixture')
            task = fx.task('TASK-A', cost_basis_ref=basis)
            fx.registry([task])
            registry_path = fx.root / 'control/worker-registry.json'
            registry = json.loads(registry_path.read_text())
            registry['workers'].append({
                'worker_id': 'fixture-worker-2',
                'executor_type': 'repository_worker',
                'capabilities': ['fixture_execute'],
                'status': 'AVAILABLE',
                'adapter_ref': 'fixture',
                'authority_source': 'fixture authority',
                'last_seen_at': None,
            })
            write(registry_path, registry)

            def adapter(*args):
                calls.append(args)
                return WorkerResponse(state='COMPLETED', transition_id='DONE', transition_sequence=1)

            result = HeartbeatRuntime(fx.root, adapters={'fixture': adapter}).cycle()
            self.assertFalse(result['activated'])
            self.assertEqual(calls, [])
            state = json.loads(registry_path.read_text())
            self.assertIsNone(state['tasks'][0]['claim_id'])
            self.assertEqual(state['workers'][0]['status'], 'AVAILABLE')
            self.assertEqual(state['workers'][1]['status'], 'AVAILABLE')
            deferred = [event for event in result['events'] if event.get('event_type') == 'activation_deferred']
            self.assertEqual(deferred[-1]['reason'], 'EXECUTOR_NOT_RESOLVED')
        finally:
            fx.close()

    def test_exactly_one_matching_available_worker_is_selected(self):
        fx = RuntimeFixture()
        calls = []
        try:
            basis = fx.cost_basis('fixture')
            task = fx.task('TASK-A', cost_basis_ref=basis)
            fx.registry([task])
            registry_path = fx.root / 'control/worker-registry.json'
            registry = json.loads(registry_path.read_text())
            registry['workers'].append({
                'worker_id': 'nonmatching-worker',
                'executor_type': 'repository_worker',
                'capabilities': ['different_capability'],
                'status': 'AVAILABLE',
                'adapter_ref': 'fixture',
                'authority_source': 'fixture authority',
                'last_seen_at': None,
            })
            write(registry_path, registry)

            def adapter(task, handoff, epoch):
                calls.append((task['task_id'], epoch))
                return WorkerResponse(state='ACTIVE', transition_id='WORK', transition_sequence=1)

            result = HeartbeatRuntime(fx.root, adapters={'fixture': adapter}).cycle()
            self.assertTrue(result['activated'])
            self.assertEqual(calls, [('TASK-A', 1)])
            state = json.loads(registry_path.read_text())
            self.assertEqual(state['tasks'][0]['worker_id'], 'fixture-worker')
            self.assertEqual(state['workers'][1]['status'], 'AVAILABLE')
        finally:
            fx.close()


if __name__ == '__main__':
    unittest.main()
