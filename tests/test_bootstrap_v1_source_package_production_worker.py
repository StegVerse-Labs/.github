from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from workers import bootstrap_v1_source_package_production_worker as worker


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


class BootstrapV1SourcePackageProductionTests(unittest.TestCase):
    def make_source(self, root: Path, component: str, files: dict[str, bytes]) -> tuple[str, dict]:
        for rel, raw in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        manifest, _ = worker.manifest_and_files(root)
        return "sha256:" + manifest["source_bundle_sha256"], manifest

    def make_receipt(self, roots: dict[str, Path], identities: dict[str, str]) -> dict:
        return {
            "schema": "stegverse.sv-dn1.production-source-prep-receipt/v2",
            "state": "COMPLETE",
            "transition_id": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
            "source_identity_scheme": "sha256-content-manifest",
            "migration_anchors_verified": True,
            "network_source_fetch_performed": False,
            "github_platform_required": False,
            "credential_used": False,
            "github_token_used": False,
            "repository_writeback_performed": False,
            "sdk_admitted": False,
            "source_roots": {c: str(roots[c]) for c in worker.COMPONENTS},
            "source_identities": dict(identities),
            "source_root_env": {worker.ROOT_ENV[c]: str(roots[c]) for c in worker.COMPONENTS},
        }

    def invocation(self) -> dict:
        return {
            "schema": "stegverse.worker-invocation/v0.1",
            "task": {
                "task_id": worker.TASK_ID,
                "worker_id": worker.WORKER_ID,
                "claim_id": "claim-test",
                "heartbeat_timing": {"fencing_token": 31},
            },
        }

    def test_build_package_matches_source_identity_and_roundtrips(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "sdk"
            identity, manifest = self.make_source(
                root,
                "stegverse.sdk",
                {"stegverse/a.py": b"alpha\n", "README.md": b"hello\n"},
            )
            package = worker.build_package("stegverse.sdk", root, identity)
            worker.validate_package(package, "stegverse.sdk", identity)
            self.assertEqual(package["source_identity"], identity)
            self.assertEqual(package["manifest"]["source_bundle_sha256"], manifest["source_bundle_sha256"])
            self.assertFalse(package["credential_material_included"])
            self.assertEqual(package["authority_effect"], "NONE_SOURCE_TRANSPORT_ONLY")

    def test_upstream_requires_exact_four_root_locator_bindings(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            roots = {}
            identities = {}
            for index, component in enumerate(worker.COMPONENTS):
                root = base / worker.slug(component)
                identity, _ = self.make_source(root, component, {"file.txt": f"{index}\n".encode()})
                roots[component] = root
                identities[component] = identity
            receipt = self.make_receipt(roots, identities)
            ids, observed_roots = worker.validate_upstream(receipt)
            self.assertEqual(ids, identities)
            self.assertEqual(observed_roots, {c: str(roots[c].resolve()) for c in worker.COMPONENTS})
            receipt["source_root_env"][worker.ROOT_ENV["stegverse.sdk"]] = "/wrong"
            with self.assertRaisesRegex(RuntimeError, "disagrees"):
                worker.validate_upstream(receipt)

    def test_execute_produces_four_idempotent_packages_without_authority(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source_prep = base / "source-prep"
            packages = base / "packages"
            bound = base / "bound"
            roots = {}
            identities = {}
            for index, component in enumerate(worker.COMPONENTS):
                root = base / "roots" / worker.slug(component)
                identity, _ = self.make_source(
                    root,
                    component,
                    {
                        "file.txt": f"{component}-{index}\n".encode(),
                        "nested/value.json": json.dumps({"component": component}).encode(),
                    },
                )
                roots[component] = root
                identities[component] = identity
            receipt = self.make_receipt(roots, identities)
            write_json(source_prep / "receipts/latest.json", receipt)

            env = {
                worker.SOURCE_PREP_ENV: str(source_prep),
                worker.PACKAGE_ENV: str(packages),
                worker.BOUND_ENV: str(bound),
            }
            with mock.patch.dict("os.environ", env, clear=True):
                first = worker.execute(self.invocation())
                second = worker.execute(self.invocation())

            self.assertEqual(first["transition_id"], "BOOTSTRAP_V1_SOURCE_PACKAGES_PRODUCED")
            self.assertEqual(first["component_count"], 4)
            self.assertEqual(first, second)
            self.assertFalse(first["network_access_performed"])
            self.assertFalse(first["credential_used"])
            self.assertFalse(first["repository_writeback_performed"])
            self.assertFalse(first["package_execution_performed"])
            self.assertFalse(first["sdk_admitted"])
            self.assertEqual(first["execution_authority"], "NONE")
            for row in first["packages"]:
                package = json.loads(Path(row["package_path"]).read_text())
                worker.validate_package(package, row["component_id"], row["source_identity"])

    def test_source_byte_drift_fails_before_package_write(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source_prep = base / "source-prep"
            packages = base / "packages"
            roots = {}
            identities = {}
            for index, component in enumerate(worker.COMPONENTS):
                root = base / "roots" / worker.slug(component)
                identity, _ = self.make_source(root, component, {"file.txt": f"{index}\n".encode()})
                roots[component] = root
                identities[component] = identity
            receipt = self.make_receipt(roots, identities)
            write_json(source_prep / "receipts/latest.json", receipt)
            (roots["stegverse.sdk"] / "file.txt").write_bytes(b"drift\n")
            with mock.patch.dict("os.environ", {
                worker.SOURCE_PREP_ENV: str(source_prep),
                worker.PACKAGE_ENV: str(packages),
                worker.BOUND_ENV: str(base / "bound"),
            }, clear=True):
                with self.assertRaisesRegex(RuntimeError, "no longer match"):
                    worker.execute(self.invocation())
            self.assertFalse(worker.package_path(packages, "stegverse.sdk").exists())

    def test_existing_package_conflict_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source_prep = base / "source-prep"
            packages = base / "packages"
            roots = {}
            identities = {}
            for index, component in enumerate(worker.COMPONENTS):
                root = base / "roots" / worker.slug(component)
                identity, _ = self.make_source(root, component, {"file.txt": f"{index}\n".encode()})
                roots[component] = root
                identities[component] = identity
            write_json(source_prep / "receipts/latest.json", self.make_receipt(roots, identities))
            conflict_path = worker.package_path(packages, "stegverse.sdk")
            write_json(conflict_path, {"schema": "wrong"})
            with mock.patch.dict("os.environ", {
                worker.SOURCE_PREP_ENV: str(source_prep),
                worker.PACKAGE_ENV: str(packages),
                worker.BOUND_ENV: str(base / "bound"),
            }, clear=True):
                with self.assertRaises(worker.PackageConflict):
                    worker.execute(self.invocation())

    def test_hosted_or_credential_environment_is_rejected(self):
        with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "hosted environment"):
                worker.execute(self.invocation())
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "secret"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "credential-bearing"):
                worker.execute(self.invocation())


if __name__ == "__main__":
    unittest.main()
