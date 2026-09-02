from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = {
    "SHWP-ALL-ORG-FEDERATION-001": ("60000000104000", "BLOCKED", 4, "control/worker-registry.json"),
    "SHWP-STEGNUTRITION-CONTINUATION-001": ("50000000107000", "MACHINE_OWNED", 7, "control/worker-registry.d/stegnutrition-continuation-001.json"),
    "SV-DN1-REPOSITORY-PERSISTENCE-PACKAGE-001": ("50000000101000", "MACHINE_OWNED", 1, "control/worker-registry.d/sv-dn1-repository-persistence-package-001.json"),
}
spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)

class WorkerDenominatorClosureCOSVTests(unittest.TestCase):
    def test_final_worker_vectors_recompute_and_bind(self):
        index = json.loads((ROOT / "control/task-vector-index.json").read_text())
        coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text())
        indexed = {x["task_id"]: x for x in index["tasks"]}
        for task_id, (expected, lifecycle, blockers, regpath) in TASKS.items():
            record = json.loads((ROOT / f"control/task-vectors/{task_id}.json").read_text())
            registry = json.loads((ROOT / regpath).read_text())
            task = next(x for x in registry["tasks"] if x["task_id"] == task_id)
            self.assertTrue(cosv.validate_record(record), task_id)
            self.assertEqual(cosv.encode_task(record["exact_metrics"]), expected, task_id)
            self.assertEqual(record["vector"], expected, task_id)
            self.assertEqual(record["exact_metrics"]["lifecycle"], lifecycle, task_id)
            self.assertEqual(record["exact_metrics"]["blocker_count"], blockers, task_id)
            self.assertFalse(record["exact_metrics"]["evidence_complete"], task_id)
            self.assertFalse(record["exact_metrics"]["activated"], task_id)
            self.assertFalse(record["exact_metrics"]["propagated"], task_id)
            self.assertEqual(record["authority_effect"], "NONE", task_id)
            self.assertEqual(task["source_state_vector_ref"], f"control/task-vectors/{task_id}.json")
            self.assertEqual(task["machine_readable_state"]["cosv"]["vector"], expected)
            self.assertEqual(indexed[task_id]["vector"], expected)

    def test_active_worker_denominator_is_closed(self):
        coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text())
        self.assertEqual(coverage["worker_registry_summary"]["canonically_indexed_task_ids"], 69)
        self.assertEqual(coverage["worker_registry_summary"]["active_unvectorized_unique_task_ids"], 0)
        self.assertEqual(coverage["active_worker_task_ids_missing_canonical_cosv"], [])
        self.assertEqual(
            coverage["total_active_unvectorized_unique_task_ids"],
            coverage["organization_registry_summary"]["active_unvectorized_task_ids"],
        )
        self.assertEqual(coverage["worker_denominator_closure"]["active_worker_tasks_vectorized"], 68)
        self.assertEqual(coverage["worker_denominator_closure"]["active_worker_tasks_unvectorized"], 0)

if __name__ == "__main__":
    unittest.main()
