import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001"


class ERLCurrentIPhoneRuntimeSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads((ROOT / f"data/canonical-task-records/{TASK_ID}.json").read_text())
        cls.profile = json.loads((ROOT / f"data/goal-task-component-profiles/{TASK_ID}.json").read_text())
        cls.handoff = (ROOT / "docs/SS_ERL_ACTIVE_RESEARCH_INTR_RUNTIME_BINDING_MIRROR_HANDOFF.md").read_text()

    def test_current_iphone_is_informational_surface_label_only(self):
        requirements = self.record["runtime_requirements"]
        surface = self.profile["runtime_surface"]
        self.assertEqual(requirements["environment"], "CANONICAL_PORTABLE_STEGOS_PLUS_KV")
        self.assertEqual(requirements["current_surface_label"], "CURRENT_USER_IPHONE")
        self.assertEqual(
            requirements["current_surface_label_semantics"],
            "INFORMATIONAL_ONLY_NOT_AN_IDENTITY_OR_ADMISSION_PREDICATE",
        )
        self.assertEqual(surface["execution_surface"], "CURRENT_USER_IPHONE")
        self.assertIn("present surface label: CURRENT_USER_IPHONE", self.handoff)
        self.assertIn("surface label semantics: INFORMATIONAL_ONLY", self.handoff)

    def test_device_confirmation_discovery_and_presence_are_prohibited(self):
        projection = self.record["component_model_projection"]
        requirements = self.record["runtime_requirements"]
        surface = self.profile["runtime_surface"]
        authority = self.record["authority_model"]

        self.assertFalse(projection["device_confirmation_required"])
        self.assertFalse(projection["device_discovery_required"])
        self.assertFalse(projection["device_presence_probe_required"])
        self.assertEqual(projection["device_identity_gate"], "PROHIBITED")

        self.assertFalse(requirements["device_confirmation_required"])
        self.assertFalse(requirements["device_discovery_required"])
        self.assertFalse(requirements["device_presence_probe_required"])
        self.assertEqual(requirements["device_identity_gate"], "PROHIBITED")

        self.assertFalse(surface["device_confirmation_required"])
        self.assertFalse(surface["device_discovery_required"])
        self.assertFalse(surface["device_presence_probe_required"])
        self.assertEqual(surface["device_identity_gate"], "PROHIBITED")

        self.assertEqual(authority["device_confirmation_authority"], "NONE")
        self.assertFalse(authority["execution_surface_identity_is_runtime_admission"])
        self.assertIn("device identity gate: PROHIBITED", self.handoff)
        self.assertIn("A continuation session MUST NOT attempt to discover, confirm, authorize, identify, probe, enumerate, poll for, wait for, or require an iPhone", self.handoff)

    def test_remote_device_connector_is_not_a_gate(self):
        projection = self.record["component_model_projection"]
        self.assertFalse(projection["remote_device_connector_required"])
        self.assertEqual(projection["remote_device_connector_classification"], "NOT_APPLICABLE")
        self.assertFalse(self.profile["runtime_surface"]["remote_device_connector_required"])
        self.assertEqual(self.profile["runtime_surface"]["remote_device_connector_classification"], "NOT_APPLICABLE")
        self.assertIn("remote connected-device requirement: NOT_APPLICABLE", self.handoff)
        self.assertIn("Do **not** poll for, wait for, or require any remotely connected resident device.", self.handoff)

    def test_single_device_and_authority_invariants_remain(self):
        requirements = self.record["runtime_requirements"]
        authority = self.record["authority_model"]
        self.assertFalse(requirements["second_user_operated_device_required"])
        self.assertFalse(requirements["always_on_external_host_required"])
        self.assertTrue(authority["workercoordinator_remains_claim_fence_authority"])
        self.assertTrue(authority["interlock_intr_remains_transition_authority"])
        self.assertTrue(authority["kv_skap_remains_sole_user_verification_authority"])
        self.assertEqual(authority["device_user_verification_authority"], "NONE")
        self.assertFalse(authority["runtime_subject_binding_is_user_verification"])
        self.assertFalse(authority["current_user_iphone_identity_is_user_verification"])
        self.assertFalse(authority["execution_surface_identity_is_runtime_admission"])
        self.assertEqual(authority["github_runtime_authority"], "NONE")

    def test_runtime_evidence_is_not_upgraded_by_surface_reconciliation(self):
        self.assertFalse(self.record["completion"]["claimed"])
        self.assertFalse(self.record["completion"]["validated"])
        self.assertFalse(self.record["completion"]["activation_proof_complete"])
        self.assertEqual(
            self.record["runtime_resolution"]["unresolved_classification"],
            "TASK_BOUND_PORTABLE_EXECUTION_EVIDENCE_NOT_OBSERVED",
        )
        self.assertIn("TASK_BOUND_PORTABLE_EXECUTION_EVIDENCE_NOT_OBSERVED", self.handoff)
        self.assertIn("MASTER_RECORDS_CUSTODY_RECONSTRUCTION_OBSERVED", self.record["expected_evidence_predicates"])


if __name__ == "__main__":
    unittest.main()
