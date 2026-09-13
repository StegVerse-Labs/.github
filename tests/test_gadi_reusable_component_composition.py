import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class GadiReusableComponentCompositionTests(unittest.TestCase):
    def load(self, rel):
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))

    def test_identity_and_authority(self):
        task = self.load("data/canonical-task-records/GADI-RUNTIME-CLOSURE-001.json")
        self.assertEqual(task["task_id"], "GADI-RUNTIME-CLOSURE-001")
        self.assertEqual(task["cosv_task_vector"], "10100000100000")
        self.assertEqual(task["coordination_state"], "ACTIVE")
        self.assertFalse(task["completion"]["claimed"])
        self.assertEqual(task["authority_model"]["worker_claim_authority"], "WORKERCOORDINATOR")
        self.assertEqual(task["authority_model"]["user_verification_authority"], "KV_SKAP_VAULT")
        self.assertEqual(task["authority_model"]["stegos_device_role"], "INTERCHANGEABLE_TRANSPORT_NODE")

    def test_selected_components(self):
        profile = self.load("data/goal-task-transport-profiles/GADI-RUNTIME-CLOSURE-001.json")
        selected = set(profile["selected_components"])
        for item in ("RTC-RESIDENT-RENDEZVOUS-010", "RTC-INTERLOCK-INTR-TRANSPORT-008", "RTC-EVIDENCE-CUSTODY-004"):
            self.assertIn(item, selected)
        for item in ("RTC-MANIFEST-001", "RTC-PUBLISHER-005", "RTC-SDK-RETURN-006"):
            self.assertNotIn(item, selected)

    def test_rendezvous_transport_only(self):
        component = self.load("data/reusable-task-components/RTC-RESIDENT-RENDEZVOUS-010.json")
        self.assertEqual(component["authority_effect"], "NONE")
        self.assertEqual(component["authority_owner"], "NONE_TRANSPORT_ONLY")
        self.assertEqual(component["canonical_authority_dependencies"]["user_verification"], "KV/SKAP Vault")
        self.assertIn("must_not_verify_user_from_device_identity", component["anti_invariants"])

    def test_decomposition_threshold(self):
        evaluation = self.load("data/reusable-task-component-evaluations/GADI-RUNTIME-CLOSURE-001.json")
        self.assertGreaterEqual(evaluation["score"], 13)
        self.assertTrue(evaluation["componentization_required"])
        self.assertTrue(evaluation["must_stop_scope_growth"])

if __name__ == "__main__":
    unittest.main()
