from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_tvc_recipient_admission_sign_intr_request as builder
from scripts import install_tvc_recipient_admission_sign_universal_intr_route as installer
from workers import tvc_recipient_admission_sign_intr_ingress as ingress

ROOT = Path(__file__).resolve().parents[1]


def platform_request():
    return {
        "schema": "stegverse.vault.agent.platform-recipient-admission-sign-request.v1",
        "purpose": "TVC_RECIPIENT_CAPABILITY_ADMISSION",
        "credentialAuthority": "TV/TVC",
        "transitionAuthority": "Interlock/InTr",
        "authorityKeyID": "tvc://authority-key/p256/0123456789abcdef01234567",
        "authorityPublicJWKSHA256": "sha256:" + "1" * 64,
        "authorityApplicationTag": "org.stegverse.stegos.tvc.recipient-admission-authority.p256",
        "platformKeyClass": "TVC_RECIPIENT_ADMISSION_AUTHORITY_P256",
        "signatureAlgorithm": "ECDSA_P256_SHA256_X962_DER",
        "messageBase64URL": "YWJj",
        "messageSHA256": "sha256:" + "2" * 64,
        "requestNonce": "0123456789abcdef0123456789abcdef",
        "privateKeyMaterialRequested": False,
        "recipientKeyReuseAllowed": False,
        "publicInvocationAllowed": False,
    }


class TVCRecipientAdmissionSignInTrRouteTests(unittest.TestCase):
    def test_builder_binds_exact_platform_request_without_authority(self):
        source = platform_request()
        payload, request = builder.build(source)
        self.assertEqual(payload["platform_request_sha256"], builder.sha_uri(source))
        self.assertEqual(payload["requested_transition"], "INGRESS_ADMITTED")
        self.assertEqual(payload["user_verification_authority"], "KV/SKAP Vault")
        self.assertFalse(payload["user_verification_performed_here"])
        self.assertFalse(payload["credential_material_present"])
        self.assertFalse(request["request_grants_execution_authority"])
        self.assertFalse(request["transport_grants_execution_authority"])
        self.assertEqual(request["authority_effect"], "NONE_REQUEST_ONLY")

    def test_ingress_emits_write_once_exact_bound_intr_admission(self):
        payload, request = builder.build(platform_request())
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            payload_path = runtime / "intr-payloads" / "tvc-recipient-admission-sign" / f"{request['materialization_id']}.json"
            payload_path.parent.mkdir(parents=True, exist_ok=True)
            payload_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            original = ingress.transport_boundary.validate_transport_headers
            ingress.transport_boundary.validate_transport_headers = lambda headers, body: {
                "origin": "TVC_RELAY_EGRESS",
                "authorization_id": "auth-001",
                "payload_sha256": "sha256:" + "3" * 64,
            }
            try:
                raw = json.dumps(request, sort_keys=True).encode("utf-8")
                receipt = ingress.admit(runtime_root=runtime, body=raw, headers={})
                again = ingress.admit(runtime_root=runtime, body=raw, headers={})
            finally:
                ingress.transport_boundary.validate_transport_headers = original
            self.assertEqual(receipt, again)
            self.assertEqual(receipt["state"], "INGRESS_ADMITTED")
            self.assertEqual(receipt["admission_state"], "ADMITTED")
            self.assertEqual(receipt["transition_authority"], "Interlock/InTr")
            self.assertEqual(receipt["authority_effect"], "INGRESS_TRANSITION_ONLY")
            self.assertEqual(receipt["platform_request_sha256"], payload["platform_request_sha256"])
            self.assertEqual(receipt["authority_key_id"], payload["authority_key_id"])
            self.assertEqual(receipt["message_sha256"], payload["message_sha256"])
            self.assertFalse(receipt["runtime_execution_attempted"])
            self.assertFalse(receipt["user_verification_performed_here"])
            body = dict(receipt)
            claimed = body.pop("admission_sha256")
            self.assertEqual(claimed, ingress._admission_sha256(body))

    def test_invalid_or_drifted_payload_fails_closed(self):
        payload, request = builder.build(platform_request())
        payload["message_sha256"] = "sha256:" + "f" * 64
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            path = runtime / "intr-payloads" / "tvc-recipient-admission-sign" / f"{request['materialization_id']}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload), encoding="utf-8")
            original = ingress.transport_boundary.validate_transport_headers
            ingress.transport_boundary.validate_transport_headers = lambda headers, body: {
                "origin": "TVC_RELAY_EGRESS", "authorization_id": "auth-001", "payload_sha256": "sha256:" + "3" * 64,
            }
            try:
                with self.assertRaisesRegex(ValueError, "payload_hash_mismatch"):
                    ingress.admit(runtime_root=runtime, body=json.dumps(request).encode(), headers={})
            finally:
                ingress.transport_boundary.validate_transport_headers = original

    def test_builder_rejects_device_pin_secret_request_and_public_invocation(self):
        cases = [
            ("requiredNodeID", "iphone-a"),
            ("pinnedDeviceID", "iphone-a"),
            ("privateKeyMaterialRequested", True),
            ("recipientKeyReuseAllowed", True),
            ("publicInvocationAllowed", True),
        ]
        for field, value in cases:
            source = platform_request()
            source[field] = value
            with self.assertRaises(ValueError):
                builder.build(source)

    def test_route_installer_is_idempotent_and_reuses_shared_listener(self):
        source = (ROOT / "workers" / "universal_intr_profiled_ingress.py").read_text(encoding="utf-8")
        installed = installer.transform(source)
        self.assertIn('"TVC:RecipientAdmissionAuthoritySign"', installed)
        self.assertIn("is_tvc_recipient_admission_sign(payload)", installed)
        self.assertIn("ThreadingHTTPServer", installed)
        self.assertEqual(installer.transform(installed), installed)
        self.assertEqual(installed.count("ThreadingHTTPServer"), source.count("ThreadingHTTPServer"))


if __name__ == "__main__":
    unittest.main()
