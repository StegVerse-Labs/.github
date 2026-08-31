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
"SV-DN1-PRODUCTION-SOURCE-PREP-001",
"SHWP-CMC028-ROOT-CUSTODY-EVIDENCE-001",
]

def _unique_worker_task_ids():
    ids=set()
    paths=[ROOT/"control/worker-registry.json"]+sorted((ROOT/"control/worker-registry.d").glob("*.json"))
    for path in paths:
        data=json.loads(path.read_text(encoding="utf-8"))
        for task in data.get("tasks",[]):
            task_id=task.get("task_id")
            if isinstance(task_id,str) and task_id:
                ids.add(task_id)
    return ids

class COSVLiveDenominatorReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.coverage=json.loads((ROOT/"control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))
        self.index=json.loads((ROOT/"control/task-vector-index.json").read_text(encoding="utf-8"))
        self.healer=json.loads((ROOT/"control/task-vectors/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json").read_text(encoding="utf-8"))
        self.healer_handoff=json.loads((ROOT/"handoffs/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json").read_text(encoding="utf-8"))

    def test_live_worker_denominator_and_partition_are_consistent(self):
        summary=self.coverage["worker_registry_summary"]
        self.assertEqual(summary["unique_task_ids_global_plus_fragments"],len(_unique_worker_task_ids()))
        worker_indexed=[row for row in self.index["tasks"] if row.get("registry_ref") != "control/organization-task-registry.json"]
        self.assertEqual(summary["canonically_indexed_task_ids"],len(worker_indexed))
        expected_active_unvectorized=summary["unique_task_ids_global_plus_fragments"]-summary["completed_only_historical_unvectorized_task_ids"]-summary["superseded_historical_unvectorized_task_ids"]-summary["canonically_indexed_task_ids"]
        self.assertEqual(summary["active_unvectorized_unique_task_ids"],expected_active_unvectorized)
        self.assertEqual(self.coverage["total_active_unvectorized_unique_task_ids"],expected_active_unvectorized+self.coverage["organization_registry_summary"]["active_unvectorized_task_ids"])

    def test_each_new_task_is_exactly_indexed_or_active_missing(self):
        missing=set(self.coverage["active_worker_task_ids_missing_canonical_cosv"])
        indexed={x["task_id"] for x in self.index["tasks"]}
        for task_id in NEW_TASKS:
            self.assertNotEqual(task_id in indexed, task_id in missing)
            vector_path=ROOT/f"control/task-vectors/{task_id}.json"
            self.assertEqual(vector_path.exists(), task_id in indexed)

    def test_healer_vector_reconciles_after_g18_gate_retirement(self):
        dep=self.healer_handoff["completion"]["dependency_state"]
        self.assertEqual(dep["state"],"RELEASE_COMPLETE_NOT_A_DOWNSTREAM_GATE")
        self.assertIsNone(dep["blocker"])
        self.assertEqual(self.healer["exact_metrics"]["blocker_count"],0)
        self.assertEqual(self.healer["vector"],"50000000100000")
        self.assertIn("retired",self.healer["metric_evidence"]["blocker_count"].lower())

if __name__=="__main__":
    unittest.main()
