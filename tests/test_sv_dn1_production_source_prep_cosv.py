from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SV-DN1-PRODUCTION-SOURCE-PREP-001"
VECTOR = "50000000103000"
BLOCKERS = {
    "TVC_REPOSITORY_BROKER_PR_92_GOVERNED_VALIDATION_AND_ADMISSION_PENDING",
    "PRIVATE_CANONICAL_SOURCE_MATERIALIZATION_RECEIPTS_NOT_YET_OBSERVED",
    "SV_DN1_PRODUCTION_SOURCE_PREP_RECEIPT_NOT_YET_OBSERVED",
}


class SVDN1ProductionSourcePrepCOSVTests(unittest.TestCase):
    def setUp(self):
        self.vector = json.loads((ROOT / f"control/task-vectors/{TASK_ID}.json").read_text(encoding="utf-8"))
        self.index = json.loads((ROOT / "control/task-vector-index.json").read_text(encoding="utf-8"))
        self.coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))
        self.registry = json.loads((ROOT / "control/worker-registry.d/sv-dn1-production-source-prep-001.json").read_text(encoding="utf-8"))
        self.handoff = json.loads((ROOT / "handoffs/SV-DN1-PRODUCTION-SOURCE-PREP-001.json").read_text(encoding="utf-8"))

    def test_vector_recomputes_from_three_exact_blockers(self):
        self.assertEqual(self.vector["identity"], f"StegVerse-Labs/.github:task:{TASK_ID}")
        self.assertEqual(self.vector["vector"], VECTOR)
        self.assertEqual(self.vector["authority_effect"], "NONE")
        metrics = self.vector["exact_metrics"]
        self.assertEqual(metrics["blocker_count"], 3)
        self.assertFalse(metrics["evidence_complete"])
        self.assertFalse(metrics["activated"])
        self.assertFalse(metrics["propagated"])
        for blocker in BLOCKERS:
            self.assertIn(blocker, self.vector["metric_evidence"]["blocker_count"])

    def test_registry_handoff_and_projection_have_exact_blocker_parity(self):
        task = self.registry["tasks"][0]
        self.assertEqual(set(task["admissible_existence"]["blockers"]), BLOCKERS)
        self.assertEqual(set(self.handoff["admissible_existence"]["blockers"]), BLOCKERS)
        projection = self.coverage["sv_dn1_production_source_prep_projection"]
        self.assertEqual(set(projection["blockers"]), BLOCKERS)
        self.assertEqual(projection["tvc_broker_pr"], 92)
        self.assertEqual(projection["tvc_broker_head"], "b5288f9910ada26c6ab2e9bca3f7701afaae2cef")

    def test_index_and_coverage_move_exactly_one_existing_task(self):
        rows = [row for row in self.index["tasks"] if row.get("task_id") == TASK_ID]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["registry_ref"], "control/worker-registry.d/sv-dn1-production-source-prep-001.json")
        self.assertEqual(rows[0]["source_state_vector_ref"], f"control/task-vectors/{TASK_ID}.json")
        self.assertEqual(rows[0]["vector"], VECTOR)
        self.assertNotIn(TASK_ID, self.coverage["active_worker_task_ids_missing_canonical_cosv"])
        indexed = [row for row in self.coverage["indexed_vectors"] if row.get("task_id") == TASK_ID]
        self.assertEqual(indexed, [{"task_id": TASK_ID, "vector": VECTOR}])
        summary = self.coverage["worker_registry_summary"]
        self.assertEqual(summary["canonically_indexed_task_ids"], len(self.coverage["indexed_vectors"]))
        self.assertEqual(summary["active_unvectorized_unique_task_ids"], 15)
        self.assertEqual(
            summary["unique_task_ids_global_plus_fragments"],
            summary["canonically_indexed_task_ids"]
            + summary["active_unvectorized_unique_task_ids"]
            + summary["completed_only_historical_unvectorized_task_ids"]
            + summary["superseded_historical_unvectorized_task_ids"],
        )
        self.assertEqual(self.coverage["total_active_unvectorized_unique_task_ids"], 29)

    def test_projection_cannot_promote_runtime_or_authority(self):
        projection = self.coverage["sv_dn1_production_source_prep_projection"]
        self.assertFalse(projection["activation_proof_observed"])
        self.assertFalse(projection["evidence_complete"])
        self.assertFalse(projection["private_materialization_receipts_observed"])
        self.assertFalse(projection["production_source_prep_receipt_observed"])
        self.assertEqual(projection["credential_authority"], "TV/TVC")
        self.assertEqual(projection["github_token_runtime_authority"], "NONE")
        self.assertFalse(projection["repository_writeback_authority"])
        self.assertFalse(projection["sdk_admission_authority"])
        self.assertFalse(projection["governance_decision_authority"])
        self.assertFalse(projection["publication_authority"])
        self.assertEqual(projection["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
