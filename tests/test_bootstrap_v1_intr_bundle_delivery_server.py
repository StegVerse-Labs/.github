from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "bootstrap_intr_server",
    ROOT / "scripts/serve_bootstrap_v1_intr_bundle_delivery.py",
)
server = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(server)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def bundle_fixture() -> dict:
    body = {
        "schema": "stegverse.bootstrap.bundle/v1",
        "bundle_version": "1.0.0-rc.1",
        "state": "BUILT",
        "release_candidate": {},
        "source_catalog": {},
        "packages": [{}, {}, {}, {}],
        "component_order": [
            "stegverse.sdk", "stegverse.stegcore",
            "stegverse.core-lite", "stegverse.master-records",
        ],
        "component_count": 4,
        "source_identity_scheme": "sha256-content-manifest",
        "device_materialization_contract": {},
        "github_platform_required": False,
        "specific_external_platform_required": False,
        "network_locator_required": False,
        "transport_implementation_required": False,
        "credential_required": False,
        "bundle_integrity_confers_execution_authority": False,
        "release_activated": False,
        "publication_performed": False,
        "execution_authority": "NONE",
        "authority_effect": "NONE_BUNDLE_BUILD_ONLY",
    }
    return {**body, "bundle_identity": "sha256:" + server.digest(body)}


def build_receipt(bundle: dict) -> dict:
    return {
        "schema": "stegverse.bootstrap.distributable-bundle-build-receipt/v1",
        "state": "COMPLETE",
        "transition_id": "BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_BUILT",
        "bundle_version": "1.0.0-rc.1",
        "bundle_identity": bundle["bundle_identity"],
        "component_count": 4,
        "github_platform_required": False,
        "network_access_performed": False,
        "credential_used": False,
        "repository_writeback_performed": False,
        "release_activated": False,
        "publication_performed": False,
        "execution_authority": "NONE",
    }


class BootstrapV1InTrDeliveryServerTests(unittest.TestCase):
    def test_bundle_state_requires_exact_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = bundle_fixture()
            write_json(root / "bundle/bootstrap-v1-1.0.0-rc.1.bundle.json", bundle)
            write_json(root / "receipts/latest.json", build_receipt(bundle))
            observed, receipt = server.validate_bundle_state(root)
            self.assertEqual(observed["bundle_identity"], bundle["bundle_identity"])
            self.assertEqual(receipt["transition_id"], "BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_BUILT")

    def test_request_remains_zero_authority(self) -> None:
        value = {
            "schema": "stegverse.bootstrap.bundle-delivery-request/v1",
            "request_id": "REQ-1",
            "node_id": "stegnode-existing",
            "device_continuity_id": "stegdevice-existing",
            "bundle_version": "1.0.0-rc.1",
            "request_nonce": "nonce-1",
            "request_grants_execution_authority": False,
            "credential_required": False,
            "github_platform_required": False,
            "authority_effect": "NONE",
        }
        self.assertEqual(server.validate_request(value)["request_id"], "REQ-1")
        value["request_grants_execution_authority"] = True
        with self.assertRaisesRegex(server.BundleDeliveryError, "request_mismatch"):
            server.validate_request(value)

    def test_hosted_environment_fails_closed(self) -> None:
        with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}, clear=True):
            with self.assertRaisesRegex(server.BundleDeliveryError, "hosted_runtime_forbidden"):
                server.reject_hosted_or_credentials()


if __name__ == "__main__":
    unittest.main()
