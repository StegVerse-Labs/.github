from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data/goal-task-component-profiles/GADI-001.json"
EVALUATION = ROOT / "data/reusable-task-component-evaluations/GADI-001.json"
MODEL = ROOT / "data/reusable-task-component-model.json"
TRANSPORT = ROOT / "data/reusable-transport-component-contract.json"
CLOSURE = ROOT / "data/canonical-task-records/GADI-RUNTIME-CLOSURE-001.json"


class GADIReusableTaskComponentProfileTests(unittest.TestCase):
    def load(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_identity_and_mandatory_componentization_are_preserved(self) -> None:
        profile = self.load(PROFILE)
        evaluation = self.load(EVALUATION)
        self.assertEqual(profile["task_id"], "GADI-001")
        self.assertEqual(profile["cosv_task_vector"], "10100000100000")
        self.assertEqual(evaluation["task_id"], "GADI-001")
        self.assertEqual(evaluation["score"], 22)
        self.assertTrue(evaluation["componentization_required"])
        self.assertTrue(evaluation["must_stop_scope_growth"])
        self.assertEqual(evaluation["authority_effect"], "NONE_COORDINATION_ONLY")

    def test_prompt_count_successor_is_not_independent_goal(self) -> None:
        closure = self.load(CLOSURE)
        self.assertEqual(closure["task_id"], "GADI-RUNTIME-CLOSURE-001")
        self.assertEqual(closure["parent_task_id"], "GADI-001")
        self.assertEqual(closure["root_correlation_id"], "GADI-001")
        self.assertEqual(closure["coordination_state"], "SUPERSEDED")
        self.assertFalse(closure["completion"]["claimed"])
        self.assertEqual(closure["allowed_next_transitions"], [])
        self.assertIn("data/goal-task-component-profiles/GADI-001.json", closure["source_refs"])

    def test_selected_reusable_transport_components_exist(self) -> None:
        profile = self.load(PROFILE)
        contract = self.load(TRANSPORT)
        known = {component["id"] for component in contract["components"]}
        selected = {component["component_id"] for component in profile["required_components"]}
        self.assertIn("RTC-GOVERNED-PROCESSING-002", selected)
        self.assertIn("RTC-INTERLOCK-INTR-TRANSPORT-008", selected)
        self.assertIn("RTC-EVIDENCE-CUSTODY-004", selected)
        self.assertTrue({"RTC-GOVERNED-PROCESSING-002", "RTC-INTERLOCK-INTR-TRANSPORT-008", "RTC-EVIDENCE-CUSTODY-004"} <= known)

    def test_maximal_transport_chain_is_not_forced(self) -> None:
        profile = self.load(PROFILE)
        not_required = set(profile["not_required_components"])
        self.assertTrue({"RTC-PUBLISHER-005", "RTC-SDK-RETURN-006", "RTC-STEGVERSE-EGRESS-007", "RTC-FARSIDE-FINAL-009"} <= not_required)

    def test_authority_separation_and_no_device_verification(self) -> None:
        profile = self.load(PROFILE)
        invariants = profile["authority_invariants"]
        self.assertEqual(invariants["task_registry"], "COORDINATION_ONLY")
        self.assertEqual(invariants["worker_claim_fence"], "WorkerCoordinator")
        self.assertEqual(invariants["governed_transition"], "Interlock/InTr")
        self.assertEqual(invariants["credential_provider_release"], "TV/TVC")
        self.assertEqual(invariants["observed_reality_custody_reconstruction"], "Master Records")
        self.assertEqual(invariants["github_runtime_authority"], "NONE")
        self.assertIn("NOT_USER_VERIFIER", invariants["device_role"])
        self.assertIn("KV/SKAP Vault", invariants["user_verification"])

    def test_runtime_observation_component_forbids_second_device_path(self) -> None:
        profile = self.load(PROFILE)
        runtime = next(component for component in profile["required_components"] if component["component_id"] == "GADI-RUNTIME-OBSERVATION-REUSE")
        self.assertIn("no second device requirement", runtime["preconditions"])
        self.assertIn("another GADI runtime-discovery listener", " ".join(profile["superseded_task_specific_orchestration"]))

    def test_model_remains_non_authorizing(self) -> None:
        model = self.load(MODEL)
        self.assertFalse(model["goal_task_contract"]["component_reuse_mints_authority"])
        self.assertEqual(model["composition_invariants"]["github_runtime_authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
