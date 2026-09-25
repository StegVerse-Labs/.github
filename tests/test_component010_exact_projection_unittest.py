import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = ('ECOSYSTEM-INGRESS-AI-BOUNDARIES-001', 'TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001', 'TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001')

class ExistingOwnerProjectionTest(unittest.TestCase):
    def test_all_three_exact_existing_shards_projected_once(self):
        registry = json.loads((ROOT / 'data/canonical-task-registry.json').read_text())
        for name in IDS:
            shard = json.loads((ROOT / 'data/canonical-task-records' / (name + '.json')).read_text())
            rows = [row for row in registry['tasks'] if row.get('task_id') == name]
            self.assertEqual(rows, [shard])
            self.assertEqual(shard['checkout_state'], 'CHECKED_OUT')
