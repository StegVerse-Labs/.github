from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path: sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("serve_hil_intr_materialization_ingress", SCRIPTS / "serve_hil_intr_materialization_ingress.py")
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)
consumer = sys.modules.get("consume_hil_intr_materialization_request")
if consumer is None:
    import consume_hil_intr_materialization_request as consumer


def request(materialization_id: str = "INTR-MAT-" + "c" * 24) -> dict:
    body = {
        "schema": "stegverse.universal-intr-materialization-request/v1", "materialization_id": materialization_id,
        "state": "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION", "transport_schema": "stegverse.universal-intr-transport/v1", "transport_protocol": "InTr",
        "transport_intent_hash": "sha256:" + "1" * 64, "operation_id": "HIL-UPLOAD-INGRESS-001", "packet_id": "INTR-" + "d" * 24,
        "payload_hash": "sha256:" + "2" * 64, "payload_ref": "opaque://hil/HIL-UPLOAD-INGRESS-001",
        "destination": {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "HIL:Ingress"}, "boundary_path": ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"],
        "downstream_owner_ref": "StegVerse-Labs/.github#246", "event_triggered": True, "always_on_receiver_required": False, "second_user_device_required": False,
        "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION", "exact_packet_transport_retry_allowed": True,
        "blind_consequence_retry_allowed": False, "interlock_required": True, "request_grants_execution_authority": False, "claim_or_fence_minted": False,
        "transport_grants_execution_authority": False, "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE",
        "authority_transfer": False, "authority_effect": "NONE_REQUEST_ONLY",
    }
    return {**body, "request_hash": consumer.digest_uri(body)}


def encoded(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def relay_headers(body: bytes, authorization_id: str = "RELAY-EGRESS-AUTH-TEST") -> dict[str, str]:
    return {"Content-Type": "application/octet-stream", "X-StegVerse-Transport": "InTr", "X-StegVerse-Transport-Origin": mod.ORIGIN_RELAY,
            "X-StegVerse-Authorization-Id": authorization_id, "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest()}


def node_entry(req: dict | None = None) -> dict:
    req = request() if req is None else req
    body = {
        "schema": "stegos.node_intr_outbox_entry.v1", "state": "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY",
        "node_id": "SV-NODE-" + "a" * 24, "interlock_id": "SV-IL-" + "b" * 24, "materialization_id": req["materialization_id"],
        "request_hash": req["request_hash"], "transport_intent_hash": req["transport_intent_hash"], "payload_hash": req["payload_hash"],
        "response_sha256": "3" * 64, "provenance_sha256": "sha256:" + "4" * 64, "destination": req["destination"],
        "downstream_owner_ref": req["downstream_owner_ref"], "materialization_request": req, "network_delivery_observed": False,
        "runtime_materialization_observed": False, "receiver_receipt_observed": False, "tvc_receipt_observed": False,
        "request_grants_execution_authority": False, "claim_or_fence_minted": False, "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE", "authority_effect": "NONE_LOCAL_CONTINUITY_ONLY",
    }
    return {**body, "outbox_entry_hash": consumer.digest_uri(body)}


def node_trigger(entry: dict | None = None) -> dict:
    entry = node_entry() if entry is None else entry
    body = {"schema": mod.NODE_TRIGGER_SCHEMA, "transport_origin": mod.ORIGIN_NODE, "node_id": entry["node_id"], "interlock_id": entry["interlock_id"],
            "outbox_entry_hash": entry["outbox_entry_hash"], "node_outbox_entry": entry, "request_grants_execution_authority": False,
            "claim_or_fence_minted": False, "authority_effect": "NONE_TRIGGER_ONLY"}
    return {**body, "trigger_sha256": consumer.digest_uri(body)}


def node_headers(body: bytes) -> dict[str, str]:
    return {"Content-Type": "application/json", "X-StegVerse-Transport": "InTr", "X-StegVerse-Transport-Origin": mod.ORIGIN_NODE,
            "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest()}


class HILInTrMaterializationIngressTests(unittest.TestCase):
    def test_exact_relay_request_is_admitted_without_execution_authority(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td); req = request(); body = encoded(req)
            receipt = mod.admit_materialization(runtime_root=runtime, body=body, headers=relay_headers(body))
            self.assertEqual(receipt["state"], "INGRESS_ADMITTED"); self.assertEqual(receipt["transport_origin"], mod.ORIGIN_RELAY)
            self.assertEqual(receipt["transport_authorization_id"], "RELAY-EGRESS-AUTH-TEST"); self.assertIsNone(receipt["node_id"])
            self.assertFalse(receipt["runtime_execution_attempted"]); self.assertFalse(receipt["claim_or_fence_minted"]); self.assertFalse(receipt["g18_required"])
            queued = runtime / mod.REQUEST_DIR_REL / f"{req['materialization_id']}.json"; self.assertTrue(queued.is_file())
            consumer.validate_request(json.loads(queued.read_text(encoding="utf-8")))

    def test_exact_node_outbox_trigger_is_hash_verified_and_admitted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td); trigger = node_trigger(); body = encoded(trigger)
            receipt = mod.admit_materialization(runtime_root=runtime, body=body, headers=node_headers(body))
            self.assertEqual(receipt["transport_origin"], mod.ORIGIN_NODE); self.assertIsNone(receipt["transport_authorization_id"])
            self.assertEqual(receipt["node_id"], trigger["node_id"]); self.assertEqual(receipt["interlock_id"], trigger["interlock_id"])
            self.assertEqual(receipt["outbox_entry_hash"], trigger["outbox_entry_hash"]); self.assertTrue(receipt["write_once_persisted"])

    def test_node_trigger_cannot_claim_tvc_authorization(self) -> None:
        body = encoded(node_trigger()); bad = node_headers(body); bad["X-StegVerse-Authorization-Id"] = "NOT-A-TVC-GRANT"
        with tempfile.TemporaryDirectory() as td, self.assertRaisesRegex(mod.HILInTrIngressError, "node_outbox_cannot_claim_tvc_authorization"):
            mod.admit_materialization(runtime_root=Path(td), body=body, headers=bad)

    def test_tampered_node_outbox_hash_fails_closed(self) -> None:
        trigger = node_trigger(); trigger["node_outbox_entry"]["response_sha256"] = "f" * 64; body = encoded(trigger)
        with tempfile.TemporaryDirectory() as td, self.assertRaisesRegex(mod.HILInTrIngressError, "node_outbox_entry_hash_mismatch"):
            mod.admit_materialization(runtime_root=Path(td), body=body, headers=node_headers(body))

    def test_same_exact_origin_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td); trigger = node_trigger(); body = encoded(trigger)
            first = mod.admit_materialization(runtime_root=runtime, body=body, headers=node_headers(body))
            second = mod.admit_materialization(runtime_root=runtime, body=body, headers=node_headers(body)); self.assertEqual(first, second)

    def test_different_origin_cannot_overwrite_existing_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td); req = request(); relay_body = encoded(req)
            mod.admit_materialization(runtime_root=runtime, body=relay_body, headers=relay_headers(relay_body))
            trigger = node_trigger(node_entry(req)); node_body = encoded(trigger)
            with self.assertRaisesRegex(mod.HILInTrIngressError, "write_once_collision"):
                mod.admit_materialization(runtime_root=runtime, body=node_body, headers=node_headers(node_body))

    def test_transport_payload_hash_mismatch_fails_before_queue_write(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td); body = encoded(request()); bad = relay_headers(body); bad["X-StegVerse-Payload-SHA256"] = "0" * 64
            with self.assertRaisesRegex(mod.HILInTrIngressError, "payload_sha256_header_mismatch"):
                mod.admit_materialization(runtime_root=runtime, body=body, headers=bad)
            self.assertFalse((runtime / mod.REQUEST_DIR_REL).exists())

    def test_request_hash_or_destination_tamper_fails_closed(self) -> None:
        req = request(); req["destination"] = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "Other"}; body = encoded(req)
        with tempfile.TemporaryDirectory() as td, self.assertRaises(consumer.HILInTrMaterializationError):
            mod.admit_materialization(runtime_root=Path(td), body=body, headers=relay_headers(body))


if __name__ == "__main__": unittest.main()
