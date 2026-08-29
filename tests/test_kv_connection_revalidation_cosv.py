from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "KV-CONNECTION-REVALIDATION-WORKER-001"
VECTOR = "50000000102000"
BLOCKERS = {
    "SOVEREIGN_RUNTIME_NOT_YET_LIVE_PROVEN",
    "AUTHENTIC_CONFORMANCE_AND_PRIVATE_KV_READBACK_PROOFS_NOT_YET_OBSERVED",
}


class KVConnectionRevalidationCOSVTests(unittest.TestCase):
    def setUp(self):
        self.vector = json.loads((ROOT / f"control/task-vectors/{TASK_ID}.json").read_text(encoding="utf-8"))
        self.index = json.loads((ROOT / "control/task-vector-index.json").read_text(encoding="utf-8"))
        self.coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))
        self.registry = json.loads((ROOT / "control/worker-registry.d/kv-connection-revalidation-worker-001.json").read_text(encoding="utf-8"))

    def test_vector_preserves_two_runtime_blockers_without_activation(self):
        self.assertEqual(self.vector["identity"], f"StegVerse-Labs/.github:task:{TASK_ID}")
        self.assertEqual(self.vector["profile"], "task.v1")
        self.assertEqual(self.vector["vector"], VECTOR)
        self.assertEqual(self.vector["authority_effect"], "NONE")
        metrics = self.vector["exact_metrics"]
        self.assertEqual(metrics["blocker_count"], 2)
        self.assertFalse(metrics["evidence_complete"])
        self.assertFalse(metrics["activated"])
        self.assertFalse(metrics["propagated"])
        blocker_text = self.vector["metric_evidence"]["blocker_count"]
        for blocker in BLOCKERS:
            self.assertIn(blocker, blocker_text)

    def test_index_contains_exactly_one_matching_projection(self):
        matches = [x for x in self.index["tasks"] if x.get("task_id") == TASK_ID]
        self.assertEqual(len(matches), 1)
        entry = matches[0]
        self.assertEqual(entry["registry_ref"], "control/worker-registry.d/kv-connection-revalidation-worker-001.json")
        self.assertEqual(entry["source_state_vector_ref"], f"control/task-vectors/{TASK_ID}.json")
        self.assertEqual(entry["vector"], VECTOR)
        self.assertEqual(entry["authority_effect"], "NONE")
        self.assertEqual(self.index["coverage"]["indexed_vectorized_tasks"], len(self.index["tasks"]))
        self.assertEqual(self.index["coverage"]["local_cosv_record_tasks"], len(self.index["tasks"]))

    def test_coverage_moves_task_from_gap_to_index_without_denominator_change(self):
        summary = self.coverage["worker_registry_summary"]
        total = summary["unique_task_ids_global_plus_fragments"]
        indexed_count = summary["canonically_indexed_task_ids"]
        active_gap = summary["active_unvectorized_unique_task_ids"]
        completed = summary["completed_only_historical_unvectorized_task_ids"]
        superseded = summary["superseded_historical_unvectorized_task_ids"]
        self.assertGreaterEqual(total, 57)
        self.assertGreaterEqual(indexed_count, 35)
        self.assertEqual(total, indexed_count + active_gap + completed + superseded)
        self.assertEqual(active_gap, len(self.coverage["active_worker_task_ids_missing_canonical_cosv"]))
        self.assertNotIn(TASK_ID, self.coverage["active_worker_task_ids_missing_canonical_cosv"])
        indexed = [x for x in self.coverage["indexed_vectors"] if x.get("task_id") == TASK_ID]
        self.assertEqual(indexed, [{"task_id": TASK_ID, "vector": VECTOR}])
        self.assertEqual(self.coverage["total_active_unvectorized_unique_task_ids"], 29)

    def test_registry_and_projection_do_not_promote_provider_or_credential_authority(self):
        task = self.registry["tasks"][0]
        self.assertEqual(task["task_id"], TASK_ID)
        self.assertFalse(task["archive_eligible"])
        self.assertEqual(task["admissible_existence"]["phase"], "ADMISSIBLE")
        self.assertEqual(task["admissible_existence"]["target_phase"], "ACTIVATED")
        self.assertIsNone(task["admissible_existence"]["activation_proof_ref"])
        self.assertEqual(task["admissible_existence"]["credential_authority"], "TV/TVC")
        self.assertFalse(task["admissible_existence"]["github_token_runtime_authority"])
        projection = self.coverage["kv_connection_revalidation_cosv_projection"]
        self.assertEqual(set(projection["blockers"]), BLOCKERS)
        self.assertFalse(projection["activation_proof_observed"])
        self.assertFalse(projection["evidence_complete"])
        self.assertEqual(projection["provider_operation_authority"], "NONE")
        self.assertEqual(projection["credential_authority"], "TV/TVC")
        self.assertEqual(projection["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
