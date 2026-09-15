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

    def test_default_package_carries_exact_stegbrowser_native_invocation_chain(self) -> None:
        package = builder.build(ROOT, builder.DEFAULT_PATHS)
        paths = {row["path"] for row in package["manifest"]["files"]}
        required = {
            "control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json",
            "control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py",
            "control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.legacy.py",
            "control/transport-manifests/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json",
            "scripts/run_stegbrowser_manifest_bound_runtime.py",
            "scripts/run_stegbrowser_runtime_consumption_reusable.py",
            "scripts/run_stegbrowser_runtime_consumption_reusable.legacy.py",
            "workers/stegbrowser_manifest_intr_ingress.py",
            "source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json",
            "data/canonical-task-records/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json",
        }
        self.assertTrue(required.issubset(paths), sorted(required - paths))

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
