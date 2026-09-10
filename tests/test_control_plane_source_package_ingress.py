from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workers import control_plane_source_package as controlpkg
from workers import hil_intr_profiled_ingress as ingress


def package(rel: str = "workers/example.py", raw: bytes = b"print('ok')\n") -> dict:
    row = {"path": rel, "sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw)}
    manifest_digest = controlpkg.digest([row])
    return {
        "schema": controlpkg.PACKAGE_SCHEMA,
        "package_version": controlpkg.PACKAGE_VERSION,
        "component_id": controlpkg.COMPONENT_ID,
        "source_identity": "sha256:" + manifest_digest,
        "credential_material_included": False,
        "manifest": {"file_count": 1, "source_bundle_sha256": manifest_digest, "files": [row]},
        "files": [{**row, "content_base64": base64.b64encode(raw).decode("ascii")}],
        "provenance": {"source_identity_scheme": "sha256-content-manifest", "external_platform_required": False},
        "authority_effect": controlpkg.AUTHORITY_EFFECT,
    }


def headers(body: bytes) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": ingress.shared.hil.ORIGIN_RELAY,
        "X-StegVerse-Authorization-Id": "AUTH-CONTROL-PLANE-1",
        "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest(),
    }


class ControlPlaneSourcePackageIngressTests(unittest.TestCase):
    def test_valid_package_materializes_declared_source_and_retains_write_once(self) -> None:
        value = package()
        body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            runtime = base / "runtime"; runtime.mkdir()
            source = base / "source"; source.mkdir()
            store = base / "packages"
            with mock.patch.dict(os.environ, {
                "STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(source),
                "STEGVERSE_SOURCE_PACKAGE_ROOT": str(store),
            }, clear=False):
                receipt = ingress.admit_control_plane_source_package(runtime_root=runtime, body=body, headers=headers(body))
            self.assertEqual(receipt["state"], "SOURCE_MATERIALIZED_VERIFIED")
            self.assertEqual(receipt["credential_authority"], "TV/TVC")
            self.assertFalse(receipt["canonical_transition_committed"])
            self.assertEqual((source / "workers/example.py").read_bytes(), b"print('ok')\n")
            retained = Path(receipt["package_ref"])
            self.assertTrue(retained.is_file())
            self.assertEqual(json.loads(retained.read_text()), value)
            receipt_file = runtime / ingress.SOURCE_PACKAGE_RECEIPT_DIR / f"{value['source_identity'][7:]}.json"
            self.assertTrue(receipt_file.is_file())

    def test_exact_retry_is_idempotent(self) -> None:
        value = package()
        body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); runtime = base / "runtime"; runtime.mkdir(); source = base / "source"; source.mkdir(); store = base / "packages"
            env = {"STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(source), "STEGVERSE_SOURCE_PACKAGE_ROOT": str(store)}
            with mock.patch.dict(os.environ, env, clear=False):
                first = ingress.admit_control_plane_source_package(runtime_root=runtime, body=body, headers=headers(body))
                second = ingress.admit_control_plane_source_package(runtime_root=runtime, body=body, headers=headers(body))
            self.assertEqual(first, second)

    def test_mutable_runtime_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(controlpkg.ControlPlaneSourcePackageError, "mutable/forbidden"):
            controlpkg.validate_package(package("receipts/evil.json"))

    def test_git_metadata_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(controlpkg.ControlPlaneSourcePackageError, "mutable/forbidden"):
            controlpkg.validate_package(package(".git/config"))

    def test_non_tvc_relay_origin_is_rejected(self) -> None:
        value = package(); body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode(); bad = headers(body)
        bad["X-StegVerse-Transport-Origin"] = ingress.shared.hil.ORIGIN_NODE
        with tempfile.TemporaryDirectory() as td, self.assertRaisesRegex(ValueError, "requires_tvc_relay"):
            ingress.admit_control_plane_source_package(runtime_root=Path(td), body=body, headers=bad)

    def test_missing_authorization_is_rejected(self) -> None:
        value = package(); body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode(); bad = headers(body)
        bad["X-StegVerse-Authorization-Id"] = ""
        with tempfile.TemporaryDirectory() as td, self.assertRaisesRegex(ValueError, "authorization_id_header_required"):
            ingress.admit_control_plane_source_package(runtime_root=Path(td), body=body, headers=bad)

    def test_profile_advertises_non_authorizing_source_package_path(self) -> None:
        profile = ingress.build_profile(tls_enabled=False)
        self.assertEqual(profile["control_plane_source_package_path"], "/intr/source-package")
        self.assertEqual(profile["control_plane_source_package_component"], "stegverse.control-plane")
        self.assertEqual(profile["control_plane_source_package_execution_authority"], "NONE")
        self.assertEqual(profile["credential_authority"], "TV/TVC")


if __name__ == "__main__":
    unittest.main()
