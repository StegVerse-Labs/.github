from __future__ import annotations
import json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NEW_TASKS=[
"SHWP-ARA-GRAPH-RUNTIME-086",
"RESOLVE-G18-RESIDENT-REQUEST-CONSUMPTION-001",
"KV-CONNECTION-HEALTH-RECONCILER-001",
"KV-PROVIDER-CHANGE-OBSERVER-001",
"SV-DN1-INTR-RUNTIME-001",
"SV-DN1-RESIDENT-OBSERVER-001",
"SV-DN1-SDK-FIRST-ROUND-001",
"SV-DN1-SOURCE-MATERIALIZATION-001",
"TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001",
"SHWP-CMC028-ROOT-CUSTODY-EVIDENCE-001",
]

class COSVLiveDenominatorReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.coverage=json.loads((ROOT/"control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))
        self.healer=json.loads((ROOT/"control/task-vectors/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json").read_text(encoding="utf-8"))
        self.healer_handoff=json.loads((ROOT/"handoffs/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json").read_text(encoding="utf-8"))

    def test_live_worker_denominator_includes_current_new_tasks(self):
        summary=self.coverage["worker_registry_summary"]
        self.assertEqual(summary["unique_task_ids_global_plus_fragments"],55)
        self.assertEqual(summary["canonically_indexed_task_ids"],17)
        self.assertEqual(summary["active_unvectorized_unique_task_ids"],31)
        self.assertEqual(self.coverage["total_active_unvectorized_unique_task_ids"],45)
        missing=set(self.coverage["active_worker_task_ids_missing_canonical_cosv"])
        for task_id in NEW_TASKS:
            self.assertIn(task_id,missing)

    def test_healer_vector_cardinality_stays_one_with_current_blocker(self):
        dep=self.healer_handoff["completion"]["dependency_state"]
        self.assertEqual(dep["state"],"BLOCKED")
        self.assertEqual(dep["blocker"],"RESIDENT_G18_REQUEST_QUEUED_CONSUMPTION_AND_V13_ACTIVATION_PROOF_NOT_OBSERVED")
        self.assertEqual(self.healer["exact_metrics"]["blocker_count"],1)
        self.assertEqual(self.healer["vector"],"50000000101000")
        self.assertIn(dep["blocker"],self.healer["metric_evidence"]["blocker_count"])

    def test_new_tasks_are_not_silently_vectorized(self):
        for task_id in NEW_TASKS:
            self.assertFalse((ROOT/f"control/task-vectors/{task_id}.json").exists())

if __name__=="__main__":
    unittest.main()
