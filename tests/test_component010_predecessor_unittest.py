import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / 'scripts/evaluate_task_registry_collision_checkin.py'
REGISTRY = ROOT / 'data/canonical-task-registry.json'

class CheckinPredecessorReadbackTest(unittest.TestCase):
    def call_gate_source(self, ledger, task_id, session_id):
        generation = json.loads(REGISTRY.read_text())['generation']
        payload = {
            'task_id': task_id,
            'caller_surface': 'AI_SESSION_GATE',
            'observed_registry_generation': generation,
            'checkin_context': {'session_id': session_id, 'actor_kind': 'CHATGPT_SESSION'},
        }
        env = dict(os.environ, STEGVERSE_TASK_REGISTRY_EVENT_LEDGER=str(ledger))
        result = subprocess.run([sys.executable, str(EVALUATOR)], cwd=ROOT,
                                input=json.dumps(payload), text=True, capture_output=True,
                                check=True, env=env)
        return json.loads(result.stdout)

    def test_existing_ledger_provides_exact_returned_predecessors(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / 'checkin-events.jsonl'
            first = self.call_gate_source(ledger, 'WORKER-TASK-RESOURCE-COST-LINKAGE-001', 'synthetic-first')
            self.assertIn('checkin_event_sha256', first)
            self.assertIsNone(first['checkin_event_predecessor_sha256'])
            second = self.call_gate_source(ledger, 'UNREGISTERED-TEST-IDENTITY', 'synthetic-second')
            rows = [json.loads(line) for line in ledger.read_text().splitlines()]
            self.assertEqual(second['disposition'], 'STOP_NOT_REGISTERED')
            self.assertEqual(rows[-2]['event_type'], 'CHECK_IN')
            self.assertEqual(rows[-1]['event_type'], 'STOPPED')
            self.assertEqual(second['checkin_event_sha256'], rows[-2]['event_sha256'])
            self.assertEqual(second['checkin_event_predecessor_sha256'], rows[-3]['event_sha256'])
            self.assertEqual(second['stopped_event_sha256'], rows[-1]['event_sha256'])
            self.assertEqual(second['stopped_event_predecessor_sha256'], rows[-2]['event_sha256'])
            self.assertEqual(rows[-1]['predecessor_event_sha256'], rows[-2]['event_sha256'])

if __name__ == '__main__':
    unittest.main()
