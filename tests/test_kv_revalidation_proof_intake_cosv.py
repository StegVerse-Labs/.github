from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "KV-REVALIDATION-PROOF-INTAKE-001"
VECTOR = "50000000102000"
BLOCKERS = {
    "SOVEREIGN_RUNTIME_NOT_YET_LIVE_PROVEN",
    "BOUNDED_REVALIDATION_INTAKE_MANIFEST_NOT_YET_OBSERVED",
}


class KVRevalidationProofIntakeCOSVTests(unittest.TestCase):
    def setUp(self):
        self.vector = json.loads((ROOT / f"control/task-vectors/{TASK_ID}.json").read_text(encoding="utf-8"))
        self.index = json.loads((ROOT / "control/task-vector-index.json").read_text(encoding="utf-8"))
        self.coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))
        self.registry = json.loads((ROOT / "control/worker-registry.d/kv-revalidation-proof-intake-001.json").read_text(encoding="utf-8"))

    def test_vector_is_machine_owned_nonactivating_two_blocker_state(self):
        self.assertEqual(self.vector["identity"], f"StegVerse-Labs/.github:task:{TASK_ID}")
        self.assertEqual(self.vector["profile"], "task.v1")
        self.assertEqual(self.vector["vector"], VECTOR)
        self.assertEqual(self.vector["authority_effect"], "NONE")
        metrics = self.vector["exact_metrics"]
        self.assertEqual(metrics["blocker_count"], 2)
        self.assertFalse(metrics["evidence_complete"])
        self.assertFalse(metrics["activated"])
        self.assertFalse(metrics["propagated"])
        for blocker in BLOCKERS:
            self.assertIn(blocker, self.vector["metric_evidence"]["blocker_count"])

    def test_index_and_global_coverage_bind_exactly_once(self):
        rows = [row for row in self.index["tasks"] if row.get("task_id") == TASK_ID]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["registry_ref"], "control/worker-registry.d/kv-revalidation-proof-intake-001.json")
        self.assertEqual(rows[0]["source_state_vector_ref"], f"control/task-vectors/{TASK_ID}.json")
        self.assertEqual(rows[0]["vector"], VECTOR)
        self.assertEqual(self.index["coverage"]["indexed_vectorized_tasks"], len(self.index["tasks"]))
        self.assertEqual(self.index["coverage"]["local_cosv_record_tasks"], len(self.index["tasks"]))

        indexed = [row for row in self.coverage["indexed_vectors"] if row.get("task_id") == TASK_ID]
        self.assertEqual(indexed, [{"task_id": TASK_ID, "vector": VECTOR}])
        self.assertNotIn(TASK_ID, self.coverage["active_worker_task_ids_missing_canonical_cosv"])
        summary = self.coverage["worker_registry_summary"]
        self.assertEqual(summary["unique_task_ids_global_plus_fragments"], 58)
        self.assertEqual(summary["canonically_indexed_task_ids"], 36)
        self.assertEqual(summary["active_unvectorized_unique_task_ids"], 15)
        self.assertEqual(58, 36 + 15 + 6 + 1)

    def test_registry_and_projection_preserve_authority_boundary(self):
        task = self.registry["tasks"][0]
        self.assertEqual(task["task_id"], TASK_ID)
        self.assertEqual(task["source_state_vector_ref"], f"control/task-vectors/{TASK_ID}.json")
        self.assertFalse(task["archive_eligible"])
        self.assertEqual(task["admissible_existence"]["phase"], "ADMISSIBLE")
        self.assertEqual(set(task["admissible_existence"]["blockers"]), BLOCKERS)
        self.assertEqual(task["admissible_existence"]["credential_authority"], "TV/TVC")
        self.assertFalse(task["admissible_existence"]["github_token_runtime_authority"])

        projection = self.coverage["kv_revalidation_proof_intake_projection"]
        self.assertEqual(set(projection["blockers"]), BLOCKERS)
        self.assertFalse(projection["activation_proof_observed"])
        self.assertFalse(projection["evidence_complete"])
        self.assertEqual(projection["provider_operation_authority"], "NONE")
        self.assertEqual(projection["credential_authority"], "TV/TVC")
        self.assertEqual(projection["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
