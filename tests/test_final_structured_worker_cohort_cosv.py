from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = {
    "SHWP-FORMALISM-MANIFOLD-RECONCILIATION-001": ("50000000101000", 1, "control/worker-registry.d/formalism-manifold-orchestration-001.json"),
    "SHWP-FORMALISM-OWNER-MUTATION-EXECUTOR-001": ("50000000101000", 1, "control/worker-registry.d/formalism-owner-mutation-executor-001.json"),
    "SHWP-FORMALISM-MANIFOLD-IMPLEMENTATION-ADMISSION-001": ("50000000101000", 1, "control/worker-registry.d/formalism-manifold-implementation-admission-001.json"),
    "SHWP-FORMALISM-TVC-REPOSITORY-TRANSPORT-CONSUMERS-001": ("50000000101000", 1, "control/worker-registry.d/formalism-tvc-repository-transport-consumers-001.json"),
    "STEGVERSE-TEST-LANES-AUTOLAUNCH-001": ("50000000101000", 1, "control/worker-registry.d/test-lanes-autolaunch.json"),
    "SHWP-SV002-SELF-CHARACTERIZATION-001": ("50000000100000", 0, "control/worker-registry.d/sv002-self-characterization-001.json"),
    "SV-DN1-PUBLIC-PROMOTION-001": ("50000000101000", 1, "control/worker-registry.d/sv-dn1-public-promotion-001.json"),
}

spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)

class FinalStructuredWorkerCohortCOSVTests(unittest.TestCase):
    def test_vectors_recompute_and_bind_without_promotion(self):
        index = json.loads((ROOT / "control/task-vector-index.json").read_text())
        coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text())
        indexed = {x["task_id"]: x for x in index["tasks"]}
        for task_id, (expected, blockers, regpath) in TASKS.items():
            rec = json.loads((ROOT / f"control/task-vectors/{task_id}.json").read_text())
            reg = json.loads((ROOT / regpath).read_text())
            task = next(x for x in reg["tasks"] if x["task_id"] == task_id)
            self.assertTrue(cosv.validate_record(rec), task_id)
            self.assertEqual(cosv.encode_task(rec["exact_metrics"]), expected, task_id)
            self.assertEqual(rec["exact_metrics"]["blocker_count"], blockers, task_id)
            self.assertFalse(rec["exact_metrics"]["evidence_complete"], task_id)
            self.assertFalse(rec["exact_metrics"]["activated"], task_id)
            self.assertFalse(rec["exact_metrics"]["propagated"], task_id)
            self.assertEqual(rec["authority_effect"], "NONE", task_id)
            self.assertEqual(task["source_state_vector_ref"], f"control/task-vectors/{task_id}.json")
            self.assertEqual(task["machine_readable_state"]["cosv"]["vector"], expected)
            self.assertEqual(indexed[task_id]["vector"], expected)
            self.assertNotIn(task_id, coverage["active_worker_task_ids_missing_canonical_cosv"])
        self.assertGreaterEqual(index["coverage"]["indexed_vectorized_tasks"], len(TASKS))
        self.assertEqual(
            coverage["total_active_unvectorized_unique_task_ids"],
            coverage["worker_registry_summary"]["active_unvectorized_unique_task_ids"]
            + coverage["organization_registry_summary"]["active_unvectorized_task_ids"],
        )

if __name__ == "__main__":
    unittest.main()
