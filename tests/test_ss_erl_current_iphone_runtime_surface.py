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

    def test_current_iphone_is_canonical_execution_surface(self):
        self.assertEqual(self.record["runtime_requirements"]["environment"], "CURRENT_USER_IPHONE_STEGOS_PLUS_KV")
        self.assertEqual(self.profile["runtime_surface"]["execution_surface"], "CURRENT_USER_IPHONE")
        self.assertIn("CURRENT_USER_IPHONE", self.record["runtime_resolution"]["current_executor"])
        self.assertIn("CURRENT_USER_IPHONE", self.handoff)

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
        self.assertEqual(authority["github_runtime_authority"], "NONE")

    def test_runtime_evidence_is_not_upgraded_by_surface_rebind(self):
        self.assertFalse(self.record["completion"]["claimed"])
        self.assertFalse(self.record["completion"]["validated"])
        self.assertFalse(self.record["completion"]["activation_proof_complete"])
        self.assertEqual(
            self.record["runtime_resolution"]["unresolved_classification"],
            "TASK_BOUND_NATIVE_IPHONE_EXECUTION_EVIDENCE_NOT_OBSERVED",
        )
        self.assertIn("TASK_BOUND_NATIVE_IPHONE_EXECUTION_EVIDENCE_NOT_OBSERVED", self.handoff)
        self.assertIn("MASTER_RECORDS_CUSTODY_RECONSTRUCTION_OBSERVED", self.record["expected_evidence_predicates"])


if __name__ == "__main__":
    unittest.main()
