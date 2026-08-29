from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "serve_hil_intr_materialization_ingress",
    SCRIPTS / "serve_hil_intr_materialization_ingress.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
consumer = sys.modules.get("consume_hil_intr_materialization_request")
if consumer is None:
    import consume_hil_intr_materialization_request as consumer


def request(materialization_id: str = "INTR-MAT-" + "c" * 24) -> dict:
    body = {
        "schema": "stegverse.universal-intr-materialization-request/v1",
        "materialization_id": materialization_id,
        "state": "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "transport_intent_hash": "sha256:" + "1" * 64,
        "operation_id": "HIL-UPLOAD-INGRESS-001",
        "packet_id": "INTR-" + "d" * 24,
        "payload_hash": "sha256:" + "2" * 64,
        "payload_ref": "opaque://hil/HIL-UPLOAD-INGRESS-001",
        "destination": {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "HIL:Ingress"},
        "boundary_path": ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"],
        "downstream_owner_ref": "StegVerse-Labs/.github#246",
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "exact_packet_transport_retry_allowed": True,
        "blind_consequence_retry_allowed": False,
        "interlock_required": True,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "transport_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_transfer": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    return {**body, "request_hash": consumer.digest_uri(body)}


def encoded(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def headers(body: bytes, authorization_id: str = "RELAY-EGRESS-AUTH-TEST") -> dict[str, str]:
    return {
        "Content-Type": "application/octet-stream",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Authorization-Id": authorization_id,
        "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest(),
    }


class HILInTrMaterializationIngressTests(unittest.TestCase):
    def test_exact_request_is_admitted_write_once_without_execution_authority(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            req = request()
            body = encoded(req)
            receipt = mod.admit_materialization(runtime_root=runtime, body=body, headers=headers(body))
            self.assertEqual(receipt["state"], "INGRESS_ADMITTED")
            self.assertTrue(receipt["exact_request_validated"])
            self.assertTrue(receipt["write_once_persisted"])
            self.assertFalse(receipt["runtime_execution_attempted"])
            self.assertFalse(receipt["claim_or_fence_minted"])
            self.assertFalse(receipt["g18_required"])
            self.assertEqual(receipt["credential_authority"], "TV/TVC")
            self.assertEqual(receipt["github_token_runtime_authority"], "NONE")
            queued = runtime / mod.REQUEST_DIR_REL / f"{req['materialization_id']}.json"
            self.assertTrue(queued.is_file())
            consumer.validate_request(json.loads(queued.read_text(encoding="utf-8")))

    def test_same_exact_request_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            req = request()
            body = encoded(req)
            first = mod.admit_materialization(runtime_root=runtime, body=body, headers=headers(body))
            second = mod.admit_materialization(runtime_root=runtime, body=body, headers=headers(body))
            self.assertEqual(first["materialization_id"], second["materialization_id"])
            self.assertEqual(first["request_hash"], second["request_hash"])

    def test_transport_payload_hash_mismatch_fails_closed_before_queue_write(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            body = encoded(request())
            bad = headers(body)
            bad["X-StegVerse-Payload-SHA256"] = "0" * 64
            with self.assertRaisesRegex(mod.HILInTrIngressError, "payload_sha256_header_mismatch"):
                mod.admit_materialization(runtime_root=runtime, body=body, headers=bad)
            self.assertFalse((runtime / mod.REQUEST_DIR_REL).exists())

    def test_request_hash_or_destination_tamper_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            req = request()
            req["destination"] = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "Other"}
            body = encoded(req)
            with self.assertRaises(consumer.HILInTrMaterializationError):
                mod.admit_materialization(runtime_root=runtime, body=body, headers=headers(body))

    def test_different_authorization_cannot_overwrite_existing_ingress_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            body = encoded(request())
            mod.admit_materialization(runtime_root=runtime, body=body, headers=headers(body, "AUTH-1"))
            with self.assertRaisesRegex(mod.HILInTrIngressError, "write_once_collision"):
                mod.admit_materialization(runtime_root=runtime, body=body, headers=headers(body, "AUTH-2"))


if __name__ == "__main__":
    unittest.main()
