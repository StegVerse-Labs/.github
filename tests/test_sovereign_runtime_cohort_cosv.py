from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = {
    "SHWP-HIL-SOVEREIGN-RECEIVER-001": ("50000000105000", 5, "control/worker-registry.d/hil-sovereign-receiver-001.json"),
    "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001": ("50000000101000", 1, "control/worker-registry.d/stegos-sovereign-relay-materialization-001.json"),
    "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001": ("50000000101000", 1, "control/worker-registry.d/stegos-relay-node-kv-continuity-001.json"),
    "SHWP-DEVICE-KV-INTR-OBSERVATION-001": ("50000000101000", 1, "control/worker-registry.d/device-kv-intr-observation-001.json"),
}
spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)

class SovereignRuntimeCohortCOSVTests(unittest.TestCase):
    def test_vectors_and_registry_parity(self):
        index = json.loads((ROOT / "control/task-vector-index.json").read_text())
        coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text())
        indexed = {x["task_id"]: x for x in index["tasks"]}
        for task_id, (expected, blockers, regpath) in TASKS.items():
            rec = json.loads((ROOT / f"control/task-vectors/{task_id}.json").read_text())
            reg = json.loads((ROOT / regpath).read_text())["tasks"][0]
            self.assertTrue(cosv.validate_record(rec), task_id)
            self.assertEqual(cosv.encode_task(rec["exact_metrics"]), expected, task_id)
            self.assertEqual(rec["exact_metrics"]["blocker_count"], blockers, task_id)
            self.assertEqual(reg["source_state_vector_ref"], f"control/task-vectors/{task_id}.json")
            self.assertEqual(reg["machine_readable_state"]["cosv"]["vector"], expected)
            self.assertFalse(rec["exact_metrics"]["activated"])
            self.assertFalse(rec["exact_metrics"]["evidence_complete"])
            self.assertEqual(rec["authority_effect"], "NONE")
            self.assertNotIn(task_id, coverage["active_worker_task_ids_missing_canonical_cosv"])
            self.assertEqual(indexed[task_id]["vector"], expected)
        self.assertEqual(index["coverage"]["indexed_vectorized_tasks"], 50)
        self.assertEqual(coverage["worker_registry_summary"]["canonically_indexed_task_ids"], 50)
        self.assertEqual(coverage["worker_registry_summary"]["active_unvectorized_unique_task_ids"], 14)
        self.assertEqual(coverage["total_active_unvectorized_unique_task_ids"], 28)

if __name__ == "__main__":
    unittest.main()
