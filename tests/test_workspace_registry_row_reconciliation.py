"""The aggregate registry row for STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001 is its canonical record.

The record, the task vector and the vector index carried COSV 10500000110000 (B=0, owner decisions at
.github#2796 comment 6094254732) while the aggregate row still held 10500000114000 (B=4); this pins the
reconciliation and that it admits nothing.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001"


class WorkspaceRegistryRowReconciliationTests(unittest.TestCase):
    def setUp(self):
        registry = json.loads((ROOT / "data/canonical-task-registry.json").read_text(encoding="utf-8"))
        rows = [row for row in registry["tasks"] if row.get("task_id") == TASK]
        self.assertEqual(len(rows), 1)
        self.row = rows[0]
        self.record = json.loads((ROOT / "data/canonical-task-records" / f"{TASK}.json").read_text(encoding="utf-8"))
        self.vector = json.loads((ROOT / "control/task-vectors" / f"{TASK}.json").read_text(encoding="utf-8"))
        index = json.loads((ROOT / "control/task-vector-index.json").read_text(encoding="utf-8"))
        self.indexed = [entry for entry in index["tasks"] if entry.get("task_id") == TASK]

    def test_aggregate_row_is_the_canonical_record(self):
        self.assertEqual(self.row, self.record)

    def test_every_projection_carries_the_same_cosv(self):
        self.assertEqual(self.row["cosv_task_vector"], "10500000110000")
        self.assertEqual(self.vector["vector"], self.row["cosv_task_vector"])
        self.assertEqual([entry["vector"] for entry in self.indexed], [self.row["cosv_task_vector"]])

    def test_reconciliation_admits_nothing(self):
        self.assertEqual(self.row["coordination_state"], "PROPOSED")
        self.assertEqual(self.row["checkout_state"], "UNCLAIMED")
        self.assertEqual(self.row["worker_claim"], {"authority": "WORKERCOORDINATOR", "claim_ref": None, "fence_ref": None, "projection_only": True})
        self.assertEqual(self.row["owner_decisions"]["admission"], "NOT_INVOKED")
        self.assertFalse(self.row["completion"]["runtime_observed"])


if __name__ == "__main__":
    unittest.main()
