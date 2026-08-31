from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SHWP-LOCAL-SOURCE-GENERATION-EXECUTOR-001"
VECTOR_REF = f"control/task-vectors/{TASK_ID}.json"
BLOCKERS = [
    "SOVEREIGN_LOCAL_MODEL_LIVE_ACTIVATION_NOT_YET_OBSERVED",
    "FORMALISM_SOURCE_GENERATION_INTEGRATION_PROOF_NOT_YET_OBSERVED",
    "RESIDENT_SOURCE_GENERATION_AND_RECURSIVE_REOBSERVATION_NOT_YET_PROVEN",
]

spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)


class LocalSourceGenerationCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / VECTOR_REF).read_text(encoding="utf-8"))
        fragment = json.loads((ROOT / "control/worker-registry.d/local-source-generation-executor-001.json").read_text(encoding="utf-8"))
        self.task = next(x for x in fragment["tasks"] if x["task_id"] == TASK_ID)
        self.handoff = json.loads((ROOT / "handoffs/SHWP-LOCAL-SOURCE-GENERATION-EXECUTOR-001.json").read_text(encoding="utf-8"))
        self.task_state = json.loads((ROOT / "data/local-source-generation-executor/task-state.json").read_text(encoding="utf-8"))
        self.claim = json.loads((ROOT / "control/session-implementation-claim-2026-08-14-local-source-generation-executor.json").read_text(encoding="utf-8"))
        retrospective = json.loads((ROOT / "control/admissible-existence-retrospective-conformance.json").read_text(encoding="utf-8"))
        self.ae_entry = next(x for x in retrospective["entries"] if x["task_id"] == TASK_ID)
        self.coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))

    def test_vector_recomputes_from_reconciled_three_blocker_state(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]), "50000000103000")
        self.assertEqual(self.record["vector"], "50000000103000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"], 3)
        self.assertEqual(self.task["admissible_existence"]["blockers"], BLOCKERS)
        self.assertEqual(self.handoff["admissible_existence"]["blockers"], BLOCKERS)
        self.assertEqual(self.task_state["blockers"], BLOCKERS)

    def test_all_structured_lifecycle_surfaces_are_admissible_not_activated(self):
        self.assertEqual(self.task["admissible_existence"]["phase"], "ADMISSIBLE")
        self.assertEqual(self.handoff["admissible_existence"]["phase"], "ADMISSIBLE")
        self.assertEqual(self.task_state["canonical_source_generation_phase"], "ADMISSIBLE")
        self.assertEqual(self.ae_entry["phase"], "ADMISSIBLE")
        self.assertEqual(self.task["admissible_existence"]["target_phase"], "ACTIVATED")
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])
        self.assertEqual(self.task["admissible_existence"]["integration_evidence_refs"], [])
        self.assertFalse(self.record["exact_metrics"]["evidence_complete"])
        self.assertFalse(self.record["exact_metrics"]["activated"])
        self.assertFalse(self.record["exact_metrics"]["propagated"])

    def test_released_source_claim_does_not_grant_runtime_or_repository_authority(self):
        self.assertEqual(self.claim["state"], "COMPLETE_VALIDATED_RELEASED")
        self.assertFalse(self.task_state["manual_execution_allowed"])
        self.assertEqual(self.task_state["manual_allowed_role"], "NONE")
        self.assertFalse(self.handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(self.handoff["authority"]["github_token_required"])
        for marker in (
            "no_admissibility_authority",
            "no_repository_mutation_authority",
            "no_credential_authority",
            "no_provider_or_wallet_authority",
        ):
            self.assertIn(marker, self.handoff["goal"]["authority_ceiling"])
        projection = self.coverage["local_source_generation_executor_reconciliation"]
        self.assertEqual(projection["repository_mutation_authority"], "TV/TVC_ONLY")
        self.assertFalse(projection["activation_proof_observed"])
        self.assertFalse(projection["integration_evidence_observed"])
        self.assertFalse(projection["resident_recursive_reobservation_observed"])

    def test_bindings_and_global_coverage_are_structurally_consistent(self):
        index = json.loads((ROOT / "control/task-vector-index.json").read_text(encoding="utf-8"))
        indexed = {x["task_id"]: x for x in index["tasks"]}
        self.assertEqual(indexed[TASK_ID]["vector"], "50000000103000")
        self.assertEqual(self.task["source_state_vector_ref"], VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"], VECTOR_REF)
        self.assertEqual(self.task_state["source_state_vector_ref"], VECTOR_REF)
        self.assertNotIn(TASK_ID, self.coverage["active_worker_task_ids_missing_canonical_cosv"])
        self.assertEqual(index["coverage"]["indexed_vectorized_tasks"], len(index["tasks"]))
        worker_indexed = [row for row in index["tasks"] if row.get("registry_ref") != "control/organization-task-registry.json"]
        self.assertEqual(self.coverage["worker_registry_summary"]["canonically_indexed_task_ids"], len(worker_indexed))
        self.assertGreaterEqual(len(index["tasks"]), 33)
        worker_gap = self.coverage["worker_registry_summary"]["active_unvectorized_unique_task_ids"]
        self.assertEqual(worker_gap, len(self.coverage["active_worker_task_ids_missing_canonical_cosv"]))
        org_gap = self.coverage["organization_registry_summary"]["active_unvectorized_task_ids"]
        self.assertEqual(self.coverage["total_active_unvectorized_unique_task_ids"], worker_gap + org_gap)


if __name__ == "__main__":
    unittest.main()
