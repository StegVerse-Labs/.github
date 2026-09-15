from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_control_plane_source_package_reusable",
    ROOT / "scripts/build_control_plane_source_package_reusable.py",
)
assert SPEC and SPEC.loader
subject = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subject)

BUILDER_SPEC = importlib.util.spec_from_file_location(
    "build_control_plane_source_package",
    ROOT / "scripts/build_control_plane_source_package.py",
)
assert BUILDER_SPEC and BUILDER_SPEC.loader
builder = importlib.util.module_from_spec(BUILDER_SPEC)
BUILDER_SPEC.loader.exec_module(builder)

REQUEST_REL = "control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json"
NONCE = "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001-20260915T142500Z"


class ReusableControlPlaneSourcePackageTests(unittest.TestCase):
    def test_default_package_is_relay_bounded_and_self_carries_reusable_producer(self) -> None:
        package = builder.build(ROOT, builder.DEFAULT_PATHS)
        rendered = (json.dumps(package, indent=2, sort_keys=True) + "\n").encode("utf-8")
        paths = {row["path"] for row in package["manifest"]["files"]}
        self.assertIn("scripts/build_control_plane_source_package_reusable.py", paths)
        self.assertIn("source-bundles/reusable-task-registry.d/RT-CONTROL-PLANE-SOURCE-PACKAGE-001.json", paths)
        self.assertLessEqual(len(rendered), 512 * 1024)
        self.assertFalse(package["credential_material_included"])
        self.assertEqual(package["authority_effect"], "NONE_SOURCE_TRANSPORT_ONLY")

    def test_default_package_carries_exact_unchanged_stegbrowser_one_shot_request(self) -> None:
        package = builder.build(ROOT, builder.DEFAULT_PATHS)
        paths = {row["path"] for row in package["manifest"]["files"]}
        self.assertIn(REQUEST_REL, paths)
        packaged = next(row for row in package["files"] if row["path"] == REQUEST_REL)
        import base64
        request = json.loads(base64.b64decode(packaged["content_base64"]).decode("utf-8"))
        self.assertEqual(request["invocation_request_nonce"], NONCE)
        self.assertEqual(request["requested_invocation_count"], 1)
        self.assertEqual(request["requested_test_scope"], "A0_A4_SINGLE_INVOCATION")
        self.assertEqual(request["requested_goal_task_id"], "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001")
        self.assertEqual(request["authority_effect"], "NONE_REQUEST_ONLY")

    def test_reusable_runner_retains_exact_content_addressed_package(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td) / "runtime"
            receipts = runtime / "receipts/reusable-task"
            receipts.mkdir(parents=True)
            manifest_path = receipts / "manifest.json"
            result_path = receipts / "result.json"
            manifest = {
                "reusable_task_id": subject.REUSABLE_TASK_ID,
                "invocation_id": "rt-control-plane-source-package-20260913T22Z",
                "manifest_hash": "sha256:test-manifest",
                "parameters": {"source_root": str(ROOT), "runtime_root": str(runtime)},
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            env = {
                "STEGVERSE_REUSABLE_TASK_MANIFEST": str(manifest_path),
                "STEGVERSE_REUSABLE_TASK_RESULT_PATH": str(result_path),
                "STEGVERSE_REUSABLE_TASK_COMPLETION_PREDICATES_JSON": json.dumps([
                    "CONTROL_PLANE_SOURCE_PACKAGE_BUILT_VERIFIED",
                    "CONTENT_ADDRESSED_PACKAGE_RETAINED",
                    "NO_NETWORK_SOURCE_FETCH_PERFORMED",
                    "NO_CREDENTIAL_MATERIAL_INCLUDED",
                    "NO_RELAY_OR_TRANSITION_AUTHORITY_MINTED",
                ]),
            }
            with mock.patch.dict(os.environ, env, clear=False):
                result = subject.run()
            package_ref = Path(result["package"]["package_ref"])
            self.assertTrue(package_ref.is_file())
            package = json.loads(package_ref.read_text(encoding="utf-8"))
            self.assertEqual(package["source_identity"], result["package"]["source_identity"])
            self.assertEqual(package_ref.stem, package["source_identity"].removeprefix("sha256:"))
            self.assertFalse(result["package"]["relay_transport_executed"])
            self.assertFalse(result["package"]["tvc_authorization_issued"])
            self.assertEqual(result["authority_effect"], "NONE_SOURCE_PACKAGE_BUILD_ONLY")
            self.assertTrue(result_path.is_file())


if __name__ == "__main__":
    unittest.main()
