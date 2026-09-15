import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json"
PROFILE = ROOT / "data/goal-task-transport-profiles/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json"
TASK = ROOT / "source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json"
WRAPPER = ROOT / "scripts/run_stegbrowser_manifest_bound_runtime.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class StegBrowserManifestBoundOwnedMirrorPathTests(unittest.TestCase):
    def test_manifest_binds_goal_cosv_and_owned_route(self):
        manifest = load(MANIFEST)
        self.assertEqual(manifest["task_id"], "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001")
        self.assertEqual(manifest["cosv_task_vector"], "40000100100000")
        self.assertEqual(manifest["path_source"], "MANIFEST")
        self.assertEqual(manifest["route_owner"], "STEGVERSE")
        self.assertIs(manifest["endpoint_discovery_required"], False)
        self.assertIs(manifest["receiver_discovery_required"], False)
        self.assertIs(manifest["undeclared_endpoint_or_receiver_substitution_allowed"], False)
        self.assertEqual(manifest["outbound"]["receiver_role"], "OWNED_MIRROR_REFLECTOR")
        self.assertEqual(manifest["round_trip_1"]["return_target"], "MASTER_RECORDS_RECORDING_SURFACE")
        self.assertEqual(manifest["between_round_trips"]["processing_boundary"], "STEGVERSE_OWNED_MIRROR_BOUNDARY")
        self.assertEqual(manifest["round_trip_2"]["receiver"], "STEGVERSE_ECOSYSTEM")

    def test_profile_points_to_exact_manifest_and_two_declared_round_trips(self):
        profile = load(PROFILE)
        self.assertEqual(profile["manifest_ref"], str(MANIFEST.relative_to(ROOT)))
        contract = profile["manifest_route_contract"]
        self.assertIs(contract["manifest_required_before_ecosystem_egress"], True)
        self.assertIs(contract["manifest_is_transport_path_contract"], True)
        self.assertIs(contract["path_discovery_after_invocation_required"], False)
        self.assertIs(contract["mirror_receiver_discovery_required"], False)
        self.assertEqual(profile["repeatability"]["RTC-ROUNDTRIP-003"], 2)

    def test_reusable_task_invokes_manifest_binding_wrapper(self):
        task = load(TASK)
        self.assertEqual(task["manifest_ref"], str(MANIFEST.relative_to(ROOT)))
        self.assertEqual(task["runner_templates"], ["scripts/run_stegbrowser_manifest_bound_runtime.py"])
        self.assertIn("MANIFEST_BOUND_TO_INVOCATION", task["completion_predicates"])
        self.assertIn("SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED", task["completion_predicates"])
        self.assertIn("SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED", task["completion_predicates"])

    def test_wrapper_fails_closed_on_route_substitution_and_binds_digest_to_invocation(self):
        source = WRAPPER.read_text(encoding="utf-8")
        self.assertIn("manifest_outbound_endpoint_mismatch", source)
        self.assertIn("manifest_owned_mirror_receiver_mismatch", source)
        self.assertIn("manifest_round_trip_2_endpoint_mismatch", source)
        self.assertIn('STEGVERSE_REUSABLE_TASK_INVOCATION_ID', source)
        self.assertIn('MANIFEST-{digest[:24]}', source)
        self.assertIn('MANIFEST_BOUND_TO_INVOCATION', source)


if __name__ == "__main__":
    unittest.main()
