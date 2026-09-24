from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest

from workers import hil_intr_profiled_ingress as ingress
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
        self.assertLessEqual(len(rendered), ingress.SOURCE_PACKAGE_MAX_BYTES)
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

    def test_default_package_carries_complete_functional_memory_relay_delta(self) -> None:
        package = builder.build(ROOT, builder.DEFAULT_PATHS)
        rows = {row["path"]: row for row in package["manifest"]["files"]}
        for rel in subject.REQUIRED_FUNCTIONAL_MEMORY_PATHS:
            self.assertIn(rel, rows)
            self.assertRegex(rows[rel]["sha256"], r"^[0-9a-f]{64}$")

    def test_existing_relay_continuation_is_not_attempted_without_existing_inputs(self) -> None:
        package = builder.build(ROOT, builder.DEFAULT_PATHS)
        with tempfile.TemporaryDirectory() as td, mock.patch.dict(os.environ, {
            subject.RELAY_AUTH_ENV: "",
            subject.RELAY_BINDING_ENV: "",
            subject.STEGOS_ROOT_ENV: "",
        }, clear=False):
            result = subject._relay_existing_authorized_package(
                package=package,
                package_path=Path(td) / "package.json",
                runtime_root=Path(td),
            )
        self.assertEqual(result["state"], "EXISTING_RELAY_INPUTS_NOT_CONFIGURED")
        self.assertFalse(result["attempted"])
        self.assertEqual(result["authority_effect"], "NONE_EXISTING_RELAY_NOT_INVOKED")

    def test_existing_relay_continuation_requires_exact_far_side_file_digests(self) -> None:
        package = builder.build(ROOT, builder.DEFAULT_PATHS)
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            package_path = base / "package.json"
            package_path.write_text(json.dumps(package), encoding="utf-8")
            auth = base / "authorization.json"; auth.write_text("{}")
            binding = base / "binding.json"; binding.write_text("{}")
            stegos = base / "StegOS"; (stegos / "scripts").mkdir(parents=True)
            relay_script = stegos / "scripts/execute_control_plane_source_package_relay.py"
            relay_script.write_text("# placeholder\n")
            packaged = {row["path"]: row for row in package["manifest"]["files"]}
            materialized = [
                {"path": rel, "sha256": packaged[rel]["sha256"], "size": packaged[rel]["size"]}
                for rel in subject.REQUIRED_FUNCTIONAL_MEMORY_PATHS
            ]
            output = {
                "state": "SOURCE_MATERIALIZED_VERIFIED",
                "source_package_ingress_verified": True,
                "result": {
                    "source_package_ingress_receipt": {
                        "source_identity": package["source_identity"],
                        "source_materialization": {"files": materialized},
                    }
                },
            }
            completed = mock.Mock(returncode=0, stdout=json.dumps(output) + "\n", stderr="")
            env = {
                subject.RELAY_AUTH_ENV: str(auth),
                subject.RELAY_BINDING_ENV: str(binding),
                subject.STEGOS_ROOT_ENV: str(stegos),
            }
            with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(subject.subprocess, "run", return_value=completed):
                result = subject._relay_existing_authorized_package(
                    package=package,
                    package_path=package_path,
                    runtime_root=base / "runtime",
                )
            self.assertEqual(result["state"], "SOURCE_MATERIALIZED_VERIFIED")
            self.assertTrue(result["far_side_materialization_verified"])
            self.assertFalse(result["new_authorization_issued"])
            self.assertFalse(result["new_binding_created"])
            self.assertFalse(result["new_transport_created"])
            self.assertTrue((base / "runtime" / subject.RELAY_RECEIPT_REL).is_file())

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


def test_org_receipt_dependencies_are_exact_allowlisted():
    source = (ROOT / "workers/control_plane_source_package.py").read_text(encoding="utf-8")
    assert '"resident-runtime/aggregate_repo_transition.py"' in source
    assert '".stegverse/transition-ledger/org-contract.json"' in source
