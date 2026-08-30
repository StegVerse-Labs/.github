from __future__ import annotations

import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workers import bootstrap_v1_distributable_bundle_worker as worker


def package(component: str, payload: bytes) -> dict:
    row = {
        "path": "runtime.txt",
        "sha256": worker.bytes_digest(payload),
        "size": len(payload),
    }
    source_bundle_sha256 = worker.digest([row])
    return {
        "schema": "stegverse.source-package/v1",
        "package_version": "1.0.0",
        "component_id": component,
        "source_identity": "sha256:" + source_bundle_sha256,
        "credential_material_included": False,
        "manifest": {
            "file_count": 1,
            "source_bundle_sha256": source_bundle_sha256,
            "files": [row],
        },
        "files": [
            {
                **row,
                "content_base64": base64.b64encode(payload).decode("ascii"),
            }
        ],
        "authority_effect": "NONE_SOURCE_TRANSPORT_ONLY",
    }


def fixtures() -> tuple[dict, dict, dict[str, dict]]:
    packages = {
        component: package(component, (component + "\n").encode("utf-8"))
        for component in worker.COMPONENTS
    }
    components = [
        {"component_id": component, "source_identity": packages[component]["source_identity"]}
        for component in worker.COMPONENTS
    ]
    catalog = {
        "schema": "stegverse.bootstrap.source-catalog/v1",
        "catalog_version": "1.0.0",
        "state": "FROZEN",
        "source_identity_scheme": "sha256-content-manifest",
        "component_count": 4,
        "components": components,
        "source_identity_set_sha256": worker.digest(components),
        "upstream_source_prep_receipt_sha256": "a" * 64,
        "source_package_contract": {"schema": "stegverse.source-package/v1", "version": "1.0.0"},
        "github_platform_required": False,
        "specific_external_platform_required": False,
        "network_locator_required": False,
        "package_integrity_confers_execution_authority": False,
        "execution_authority": "NONE",
        "authority_effect": "NONE_IDENTITY_FREEZE_ONLY",
    }
    body = {
        "schema": "stegverse.bootstrap.release-candidate/v1",
        "candidate_version": "1.0.0-rc.1",
        "state": "FROZEN",
        "source_identity_scheme": "sha256-content-manifest",
        "source_catalog": {
            "schema": "stegverse.bootstrap.source-catalog/v1",
            "version": "1.0.0",
            "sha256": worker.digest(catalog),
            "source_identity_set_sha256": catalog["source_identity_set_sha256"],
        },
        "source_package_contract": {"schema": "stegverse.source-package/v1", "version": "1.0.0"},
        "device_materialization_contract": {
            "evidence_schema": "stegverse.device-node-source-package-bootstrap-evidence/v1",
            "required_state": "MATERIALIZED_UNADMITTED",
            "execution_authority_before_admission": "NONE",
        },
        "source_freeze_receipt_sha256": "b" * 64,
        "github_platform_required": False,
        "specific_external_platform_required": False,
        "network_locator_required": False,
        "transport_implementation_required": False,
        "credential_required": False,
        "package_integrity_confers_execution_authority": False,
        "release_activated": False,
        "publication_performed": False,
        "execution_authority": "NONE",
        "authority_effect": "NONE_RELEASE_CANDIDATE_FREEZE_ONLY",
    }
    candidate = {**body, "candidate_identity": "sha256:" + worker.digest(body)}
    return candidate, catalog, packages


def invocation() -> dict:
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "task": {
            "task_id": worker.TASK_ID,
            "worker_id": worker.WORKER_ID,
            "claim_id": "claim-bootstrap-bundle",
            "heartbeat_timing": {"fencing_token": 23},
        },
    }


class BootstrapV1DistributableBundleTests(unittest.TestCase):
    def test_exact_four_packages_build_transport_neutral_bundle(self):
        candidate, catalog, packages = fixtures()
        identities = worker.validate_catalog(catalog)
        worker.validate_candidate(candidate, catalog)
        for component in worker.COMPONENTS:
            worker.validate_package(packages[component], component, identities[component])
        bundle = worker.build_bundle(candidate, catalog, packages)
        self.assertEqual(bundle["schema"], "stegverse.bootstrap.bundle/v1")
        self.assertEqual(bundle["bundle_version"], "1.0.0-rc.1")
        self.assertEqual(bundle["component_order"], list(worker.COMPONENTS))
        self.assertEqual([p["component_id"] for p in bundle["packages"]], list(worker.COMPONENTS))
        self.assertTrue(bundle["bundle_identity"].startswith("sha256:"))
        self.assertFalse(bundle["github_platform_required"])
        self.assertFalse(bundle["specific_external_platform_required"])
        self.assertFalse(bundle["network_locator_required"])
        self.assertFalse(bundle["transport_implementation_required"])
        self.assertFalse(bundle["credential_required"])
        self.assertFalse(bundle["bundle_integrity_confers_execution_authority"])
        self.assertFalse(bundle["release_activated"])
        self.assertFalse(bundle["publication_performed"])
        self.assertEqual(bundle["execution_authority"], "NONE")

    def test_package_byte_and_identity_drift_fail_closed(self):
        _, catalog, packages = fixtures()
        identities = worker.validate_catalog(catalog)
        bad = json.loads(json.dumps(packages["stegverse.sdk"]))
        bad["files"][0]["content_base64"] = base64.b64encode(b"tampered\n").decode("ascii")
        with self.assertRaisesRegex(RuntimeError, "file integrity mismatch"):
            worker.validate_package(bad, "stegverse.sdk", identities["stegverse.sdk"])
        bad = json.loads(json.dumps(packages["stegverse.sdk"]))
        bad["source_identity"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(RuntimeError, "source identity mismatch"):
            worker.validate_package(bad, "stegverse.sdk", identities["stegverse.sdk"])

    def test_candidate_catalog_binding_mismatch_fails(self):
        candidate, catalog, _ = fixtures()
        candidate["source_catalog"]["sha256"] = "f" * 64
        body = worker.candidate_body(candidate)
        candidate["candidate_identity"] = "sha256:" + worker.digest(body)
        with self.assertRaisesRegex(RuntimeError, "candidate/source catalog binding mismatch"):
            worker.validate_candidate(candidate, catalog)

    def test_execute_is_idempotent_and_bundle_conflict_fails(self):
        candidate, catalog, packages = fixtures()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rc = root / "rc"
            freeze = root / "freeze"
            package_root = root / "packages"
            bound = root / "bound"
            (rc / "candidate").mkdir(parents=True)
            (freeze / "catalog").mkdir(parents=True)
            (rc / "candidate/bootstrap-v1-1.0.0-rc.1.json").write_text(json.dumps(candidate))
            (freeze / "catalog/bootstrap-v1-source-catalog.json").write_text(json.dumps(catalog))
            for component, value in packages.items():
                path = package_root / worker.slug(component)
                path.mkdir(parents=True)
                (path / "package.json").write_text(json.dumps(value))
            env = {
                worker.RC_ENV: str(rc),
                worker.FREEZE_ENV: str(freeze),
                worker.PACKAGE_ENV: str(package_root),
                worker.BOUND_ENV: str(bound),
            }
            with mock.patch.dict("os.environ", env, clear=True):
                first = worker.execute(invocation())
                second = worker.execute(invocation())
                self.assertEqual(first["bundle_identity"], second["bundle_identity"])
                path = bound / "bundle/bootstrap-v1-1.0.0-rc.1.bundle.json"
                frozen = json.loads(path.read_text())
                frozen["release_activated"] = True
                path.write_text(json.dumps(frozen))
                with self.assertRaisesRegex(worker.BundleConflict, "FROZEN_BOOTSTRAP_V1_BUNDLE_CONFLICT"):
                    worker.execute(invocation())

    def test_missing_inputs_return_handoff_ready_without_platform_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            with (
                mock.patch.dict(
                    "os.environ",
                    {
                        worker.RC_ENV: td + "/rc",
                        worker.FREEZE_ENV: td + "/freeze",
                        worker.PACKAGE_ENV: td + "/packages",
                        worker.BOUND_ENV: td + "/bound",
                    },
                    clear=True,
                ),
                mock.patch("sys.stdin", io.StringIO(json.dumps(invocation()) + "\n")),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                self.assertEqual(worker.main(), 0)
                result = json.loads(stdout.getvalue())
            self.assertEqual(result["state"], "HANDOFF_READY")
            self.assertEqual(result["transition_id"], "BOOTSTRAP_V1_BUNDLE_INPUT_PENDING")
            self.assertFalse(result["blocker"]["third_party_runtime_required"])
            self.assertFalse(result["blocker"]["github_platform_required"])
            self.assertFalse(result["blocker"]["human_action_required"])

    def test_control_surfaces_preserve_zero_authority(self):
        root = Path(__file__).resolve().parents[1]
        handoff = json.loads((root / "handoffs/BOOTSTRAP-V1-DISTRIBUTABLE-BUNDLE-001.json").read_text())
        adapter = json.loads((root / "control/process-worker-adapters.d/bootstrap-v1-distributable-bundle-001.json").read_text())
        registry = json.loads((root / "control/worker-registry.d/bootstrap-v1-distributable-bundle-001.json").read_text())
        self.assertFalse(handoff["authority"]["github_platform_required"])
        self.assertFalse(handoff["authority"]["network_access_authority"])
        self.assertFalse(handoff["authority"]["package_execution_authority"])
        self.assertFalse(handoff["authority"]["release_activation_authority"])
        self.assertFalse(handoff["authority"]["repository_writeback_authority"])
        self.assertNotIn("GITHUB_TOKEN", adapter["adapters"][0]["env_allowlist"])
        self.assertEqual(registry["tasks"][0]["state"], "HANDOFF_READY")


if __name__ == "__main__":
    unittest.main()
