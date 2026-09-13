import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "control/portable-workercoordinator-packages/device-kv-intr-observation.json"


class DeviceKVPortableWorkerCoordinatorPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pkg = json.loads(PACKAGE.read_text())

    def test_reuses_canonical_portable_workercoordinator(self):
        pkg = self.pkg
        self.assertEqual(pkg["schema"], "stegverse.workercoordinator-portable-checkout-package/v1")
        self.assertEqual(pkg["portable_authority_epoch"], "WC-PORTABLE-IPHONE-20260902")
        self.assertEqual(pkg["canonical_authority_owner"], "StegVerse-Labs/.github WorkerCoordinator")
        self.assertEqual(pkg["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertEqual(pkg["execution_surface"], "CURRENT_USER_IPHONE")
        self.assertEqual(pkg["credential_authority"], "TV/TVC")
        self.assertEqual(pkg["github_token_runtime_authority"], "NONE")
        self.assertFalse(pkg["heartbeat_grants_execution_authority"])
        self.assertFalse(pkg["parallel_workercoordinator_claim_issuance_allowed"])
        self.assertTrue(pkg["governed_transfer_required_before_other_surface_claims"])

    def test_binds_existing_device_kv_owner_without_new_authority(self):
        pkg = self.pkg
        self.assertEqual(pkg["task"]["task_id"], "SHWP-DEVICE-KV-INTR-OBSERVATION-001")
        self.assertEqual(pkg["task"]["state"], "HANDOFF_READY")
        self.assertEqual(pkg["task"]["admission"]["claim_state"], "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM")
        self.assertEqual(pkg["worker"]["worker_id"], "device-kv-intr-observation-worker")
        self.assertEqual(pkg["worker"]["status"], "AVAILABLE")
        self.assertTrue(set(pkg["required_capabilities"]).issubset(set(pkg["worker"]["capabilities"])))
        self.assertFalse(pkg["event_materialization_binding"]["request_grants_authority"])
        self.assertFalse(pkg["event_materialization_binding"]["consumer_mints_claim_or_fence"])
        self.assertEqual(pkg["event_materialization_binding"]["authority_effect"], "NONE_BINDING_ONLY")

    def test_exact_source_bindings_match_current_files(self):
        expected = {
            "task_fragment_git_blob_sha": "dd26b804a043e99eedb40ce379fdd83064617dd9",
            "handoff_git_blob_sha": "e6ac959c354b3d4036630861caf1ee8d9e6f59a9",
            "state_vector_git_blob_sha": "3dcc04abacb571f19676e34da0db6abfee51e23b",
            "portable_checkout_git_blob_sha": "e8f8e0720e6829edbfec3f89910e271da8aec172",
        }
        self.assertEqual(self.pkg["source_binding"], expected)

    def test_single_device_noncompletion_boundary(self):
        pkg = self.pkg
        self.assertFalse(pkg["external_non_stegverse_machine_required"])
        self.assertFalse(pkg["event_materialization_binding"]["second_user_device_required"])
        self.assertFalse(pkg["event_materialization_binding"]["always_on_receiver_required"])
        self.assertTrue(pkg["single_checkout_per_task_package"])
        self.assertFalse(pkg["terminal_reexecution_allowed"])
        self.assertFalse(pkg["runtime_execution_observed"])
        self.assertFalse(pkg["activation_effect"])


if __name__ == "__main__":
    unittest.main()
