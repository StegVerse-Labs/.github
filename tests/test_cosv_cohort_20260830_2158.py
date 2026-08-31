from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = {
    "STEGFIN-LIVE-ENTRY-003": ("50000000101000", 1, "control/worker-registry.d/stegfin-live-entry-003.json"),
    "STEGFIN-LIVE-PRETRADE-005": ("50000000101000", 1, "control/worker-registry.d/stegfin-live-pretrade-005.json"),
    "HEALER-FAILURE-MAILBOX-LIVE-SHADOW-001": ("50000000106000", 6, "control/worker-registry.d/healer-failure-mailbox-shadow-001.json"),
    "HEALER-FAILURE-MAILBOX-SOVEREIGN-BENCHMARK-001": ("50000000101000", 1, "control/worker-registry.d/healer-failure-mailbox-benchmark-001.json"),
}

spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)

class CohortCOSVTests(unittest.TestCase):
    def test_vectors_recompute_and_do_not_promote_runtime(self):
        index = json.loads((ROOT / "control/task-vector-index.json").read_text())
        coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text())
        indexed = {x["task_id"]: x for x in index["tasks"]}
        for task_id, (expected, blockers, regpath) in TASKS.items():
            rec = json.loads((ROOT / f"control/task-vectors/{task_id}.json").read_text())
            reg = json.loads((ROOT / regpath).read_text())["tasks"][0]
            self.assertTrue(cosv.validate_record(rec), task_id)
            self.assertEqual(cosv.encode_task(rec["exact_metrics"]), expected, task_id)
            self.assertEqual(rec["exact_metrics"]["blocker_count"], blockers, task_id)
            self.assertFalse(rec["exact_metrics"]["activated"], task_id)
            self.assertFalse(rec["exact_metrics"]["evidence_complete"], task_id)
            self.assertFalse(rec["exact_metrics"]["propagated"], task_id)
            self.assertEqual(rec["authority_effect"], "NONE", task_id)
            self.assertEqual(reg["source_state_vector_ref"], f"control/task-vectors/{task_id}.json")
            self.assertEqual(reg["machine_readable_state"]["cosv"]["vector"], expected)
            self.assertEqual(indexed[task_id]["vector"], expected)
            self.assertNotIn(task_id, coverage["active_worker_task_ids_missing_canonical_cosv"])
        self.assertGreaterEqual(index["coverage"]["indexed_vectorized_tasks"], len(TASKS))
        self.assertGreaterEqual(coverage["worker_registry_summary"]["canonically_indexed_task_ids"], len(TASKS))
        self.assertEqual(
            coverage["total_active_unvectorized_unique_task_ids"],
            coverage["worker_registry_summary"]["active_unvectorized_unique_task_ids"]
            + coverage["organization_registry_summary"]["active_unvectorized_task_ids"],
        )

if __name__ == "__main__":
    unittest.main()
