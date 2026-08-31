from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASKS=[
"SHWP-FORMALISM-INVENTORY-001",
"SHWP-FORMALISM-HANDOFF-NORMALIZATION-001",
"SHWP-FORMALISM-MATHEMATICAL-CROSSWALK-001",
"SHWP-MANIFOLD-GOVERNANCE-MAPPING-001",
]
EXCLUDED="SHWP-FORMALISM-MANIFOLD-RECONCILIATION-001"
spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)
class FormalismCohortCOSVTests(unittest.TestCase):
    def setUp(self):
        self.fragment=json.loads((ROOT/"control/worker-registry.d/formalism-manifold-orchestration-001.json").read_text(encoding="utf-8"))
        self.index=json.loads((ROOT/"control/task-vector-index.json").read_text(encoding="utf-8"))
    def test_all_four_vectors_recompute_and_bind(self):
        for task_id in TASKS:
            record=json.loads((ROOT/f"control/task-vectors/{task_id}.json").read_text(encoding="utf-8"))
            self.assertTrue(cosv.validate_record(record))
            self.assertEqual(cosv.encode_task(record["exact_metrics"]),record["vector"])
            self.assertEqual(record["vector"],"50000000100000")
            task=next(x for x in self.fragment["tasks"] if x["task_id"]==task_id)
            self.assertIsNone(task["block_ref"])
            self.assertFalse(task["archive_eligible"])
            self.assertEqual(task["source_state_vector_ref"],f"control/task-vectors/{task_id}.json")
            hand=json.loads((ROOT/task["handoff_ref"]).read_text(encoding="utf-8"))
            self.assertIsNone(hand["block"])
            self.assertEqual(hand["source_state_vector_ref"],task["source_state_vector_ref"])
    def test_missing_receipt_is_not_promoted(self):
        for task_id in TASKS:
            record=json.loads((ROOT/f"control/task-vectors/{task_id}.json").read_text(encoding="utf-8"))
            m=record["exact_metrics"]
            self.assertEqual(m["blocker_count"],0)
            self.assertFalse(m["evidence_complete"])
            self.assertFalse(m["activated"])
            self.assertFalse(m["propagated"])
    def test_reconciliation_lane_is_vectorized_but_still_blocked(self):
        record=json.loads((ROOT/f"control/task-vectors/{EXCLUDED}.json").read_text(encoding="utf-8"))
        self.assertTrue(cosv.validate_record(record))
        self.assertEqual(cosv.encode_task(record["exact_metrics"]),record["vector"])
        self.assertEqual(record["vector"],"50000000101000")
        self.assertEqual(record["exact_metrics"]["blocker_count"],1)
        self.assertFalse(record["exact_metrics"]["evidence_complete"])
        self.assertFalse(record["exact_metrics"]["activated"])
        self.assertFalse(record["exact_metrics"]["propagated"])
        indexed={x["task_id"] for x in self.index["tasks"]}
        self.assertIn(EXCLUDED,indexed)
if __name__=="__main__": unittest.main()
