from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SV-DN1-PRODUCTION-SOURCE-PREP-001"
VECTOR = "50000000102000"
BLOCKERS = {
    "CONTENT_ADDRESSED_SOURCE_PACKAGES_OR_ALREADY_LOCAL_ROOTS_REQUIRED_FOR_ANY_MISSING_COMPONENT",
    "SV_DN1_PRODUCTION_SOURCE_PREP_RECEIPT_NOT_YET_OBSERVED",
}


class SVDN1ProductionSourcePrepCOSVTests(unittest.TestCase):
    def setUp(self):
        self.vector = json.loads((ROOT / f"control/task-vectors/{TASK_ID}.json").read_text(encoding="utf-8"))
        self.index = json.loads((ROOT / "control/task-vector-index.json").read_text(encoding="utf-8"))
        self.coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))
        self.registry = json.loads((ROOT / "control/worker-registry.d/sv-dn1-production-source-prep-001.json").read_text(encoding="utf-8"))
        self.handoff = json.loads((ROOT / "handoffs/SV-DN1-PRODUCTION-SOURCE-PREP-001.json").read_text(encoding="utf-8"))

    def test_vector_recomputes_from_two_exact_blockers(self):
        self.assertEqual(self.vector["identity"], f"StegVerse-Labs/.github:task:{TASK_ID}")
        self.assertEqual(self.vector["vector"], VECTOR)
        self.assertEqual(self.vector["authority_effect"], "NONE")
        metrics = self.vector["exact_metrics"]
        self.assertEqual(metrics["blocker_count"], 2)
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
        self.assertEqual(projection["source_identity_scheme"], "sha256-content-manifest")
        self.assertFalse(projection["github_platform_required"])
        self.assertFalse(projection["network_source_fetch_allowed"])

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
        worker_indexed = [row for row in self.index["tasks"] if row.get("registry_ref") != "control/organization-task-registry.json"]
        self.assertEqual(summary["canonically_indexed_task_ids"], len(worker_indexed))
        expected_active_unvectorized = (
            summary["unique_task_ids_global_plus_fragments"]
            - summary["completed_only_historical_unvectorized_task_ids"]
            - summary["superseded_historical_unvectorized_task_ids"]
            - summary["canonically_indexed_task_ids"]
        )
        self.assertEqual(summary["active_unvectorized_unique_task_ids"], expected_active_unvectorized)
        self.assertEqual(
            summary["unique_task_ids_global_plus_fragments"],
            summary["canonically_indexed_task_ids"]
            + summary["active_unvectorized_unique_task_ids"]
            + summary["completed_only_historical_unvectorized_task_ids"]
            + summary["superseded_historical_unvectorized_task_ids"],
        )
        self.assertEqual(
            self.coverage["total_active_unvectorized_unique_task_ids"],
            expected_active_unvectorized + self.coverage["organization_registry_summary"]["active_unvectorized_task_ids"],
        )

    def test_projection_cannot_promote_runtime_or_authority(self):
        projection = self.coverage["sv_dn1_production_source_prep_projection"]
        self.assertFalse(projection["activation_proof_observed"])
        self.assertFalse(projection["evidence_complete"])
        self.assertFalse(projection["content_addressed_source_packages_observed"])
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
