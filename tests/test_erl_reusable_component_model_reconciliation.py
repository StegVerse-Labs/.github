from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001"
COSV = "40000100100000"


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def load_evaluator():
    path = ROOT / "scripts/evaluate_reusable_task_componentization.py"
    spec = importlib.util.spec_from_file_location("reusable_component_eval", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ERLReusableComponentModelTests(unittest.TestCase):
    def test_decomposition_result_recomputes_exactly(self):
        source = load_json(f"data/reusable-task-componentization-inputs/{TASK_ID}.json")
        recorded = load_json(f"data/reusable-task-componentization-evaluations/{TASK_ID}.json")
        actual = load_evaluator().evaluate(source)
        self.assertEqual(actual, recorded)
        self.assertEqual(actual["score"], 28)
        self.assertTrue(actual["must_stop_scope_growth"])

    def test_transport_profile_selects_only_required_components(self):
        profile = load_json(f"data/goal-task-transport-profiles/{TASK_ID}.json")
        self.assertEqual(profile["task_id"], TASK_ID)
        self.assertEqual(profile["cosv_task_vector"], COSV)
        self.assertEqual(
            profile["selected_components"],
            ["RTC-MANIFEST-001", "RTC-EVIDENCE-CUSTODY-004", "RTC-INTERLOCK-INTR-TRANSPORT-008", "RTC-FARSIDE-FINAL-009"],
        )
        self.assertFalse(profile["transport_requirements"]["governed_processing"])
        self.assertEqual(profile["transport_requirements"]["required_round_trips"], [])
        self.assertFalse(profile["transport_requirements"]["publisher_projection"])
        self.assertFalse(profile["transport_requirements"]["sdk_return_assembly"])
        self.assertFalse(profile["transport_requirements"]["stegverse_final_egress_transition"])
        transports = [x for x in profile["component_instances"] if x["component_id"] == "RTC-INTERLOCK-INTR-TRANSPORT-008"]
        self.assertEqual(len(transports), 3)
        self.assertEqual(
            [x["instance_id"] for x in transports],
            ["ERL-HOP-1-EXTERNAL-TO-STEGOS", "ERL-HOP-2-STEGOS-TO-DEVICE", "ERL-HOP-3-DEVICE-TO-KV"],
        )

    def test_component_profile_preserves_authority_separation(self):
        profile = load_json(f"data/goal-task-component-profiles/{TASK_ID}.json")
        auth = profile["authority_invariants"]
        self.assertEqual(auth["task_registry"], "COORDINATION_ONLY")
        self.assertEqual(auth["worker_claim_fence"], "WorkerCoordinator")
        self.assertEqual(auth["governed_transition"], "Interlock/InTr")
        self.assertEqual(auth["credential_provider_release"], "TV/TVC")
        self.assertEqual(auth["user_verification"], "KV/SKAP Vault")
        self.assertEqual(auth["device_user_verification_authority"], "NONE")
        self.assertEqual(auth["master_records"], "OBSERVED_REALITY_CUSTODY_AND_RECONSTRUCTION")
        self.assertEqual(auth["github_runtime_authority"], "NONE")
        self.assertFalse(profile["componentization_mints_authority"])
        self.assertFalse(profile["new_goal_task_required"])

    def test_task_record_binds_component_profiles_without_claiming_completion(self):
        record = load_json(f"data/canonical-task-records/{TASK_ID}.json")
        self.assertEqual(record["task_id"], TASK_ID)
        self.assertEqual(record["cosv_task_vector"], COSV)
        self.assertEqual(record["coordination_state"], "ACTIVE")
        projection = record["component_model_projection"]
        self.assertTrue(projection["goal_identity_preserved"])
        self.assertTrue(projection["cosv_identity_preserved"])
        self.assertEqual(projection["decomposition_score"], 28)
        self.assertFalse(projection["componentization_mints_authority"])
        self.assertFalse(projection["runtime_predicates_completed_by_source_reuse"])
        self.assertFalse(record["completion"]["claimed"])
        self.assertFalse(record["completion"]["validated"])
        self.assertFalse(record["completion"]["activation_proof_complete"])
        self.assertIn("MASTER_RECORDS_CUSTODY_RECONSTRUCTION_OBSERVED", record["expected_evidence_predicates"])
        self.assertEqual(record["authority_model"]["device_user_verification_authority"], "NONE")
        self.assertTrue(record["authority_model"]["kv_skap_remains_sole_user_verification_authority"])

    def test_bespoke_surfaces_are_reclassified_not_new_owners(self):
        profile = load_json(f"data/goal-task-component-profiles/{TASK_ID}.json")
        reclassified = {item["path"]: item for item in profile["superseded_as_orchestration_owners"]}
        self.assertIn("scripts/submit_erl_active_research_intr_binding_local.py", reclassified)
        self.assertIn("workers/erl_device_kv_terminal.py", reclassified)
        self.assertIn("scripts/install_erl_device_kv_prior_lineage.py", reclassified)
        self.assertTrue(all(item["delete_now"] is False for item in reclassified.values()))
        self.assertIn("credential_session", profile["not_applicable_families"])
        self.assertIn("No provider execution occurs", profile["not_applicable_families"]["framework_provider_adapter"])


if __name__ == "__main__":
    unittest.main()
