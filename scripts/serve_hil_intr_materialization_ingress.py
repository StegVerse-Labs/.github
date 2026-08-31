#!/usr/bin/env python3
"""Bounded far-side ingress for HIL Universal InTr materialization requests.

Two transport origins are supported and kept semantically distinct:
- STEGOS_NODE_OUTBOX: a registered browser Node sends a non-authorizing local
  outbox trigger envelope. The complete outbox entry is hash-verified here.
- TVC_RELAY_EGRESS: a governed sovereign relay sends the exact materialization
  request after its separate TVC EGRESS authorization path.

Either origin proves only exact queue admission. Neither grants HIL execution,
claim/fence, custody, review, publication, or canonical-state authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

from consume_hil_intr_materialization_request import validate_request
from heartbeat_runtime.intr_carrier_profile import validate_carrier_binding

MAX_REQUEST_BYTES = 512 * 1024
INGRESS_PATH = "/intr/materialization"
REQUEST_DIR_REL = Path("intr-materialization")
RECEIPT_DIR_REL = Path("receipts/sovereign-network/hil-intr-ingress")
LATEST_REL = Path("receipts/sovereign-network/hil-intr-ingress.latest.json")
RECEIPT_SCHEMA = "stegverse.hil-intr-materialization-ingress/v1"
NODE_TRIGGER_SCHEMA = "stegos.node_intr_materialization_trigger.v1"
NODE_OUTBOX_SCHEMA = "stegos.node_intr_outbox_entry.v1"
CREDENTIAL_AUTHORITY = "TV/TVC"
AUTHORITY_EFFECT = "NONE_INGRESS_ONLY"
ORIGIN_NODE = "STEGOS_NODE_OUTBOX"
ORIGIN_RELAY = "TVC_RELAY_EGRESS"


class HILInTrIngressError(ValueError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise HILInTrIngressError(reason)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else _canonical(value)
    return "sha256:" + _sha256(raw)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_id(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in value)[:160]
    _require(bool(safe), "materialization_id_invalid")
    return safe


def _carrier_binding_evidence(request: Mapping[str, Any]) -> dict[str, Any]:
    binding = request.get("carrier_binding")
    if binding is None:
        return {
            "carrier_binding_present": False,
            "carrier_binding_validated": False,
            "carrier_profile": "stegverse.intr.hb-derived-carrier-profile/v1",
            "heartbeat_reference_epoch": None,
            "heartbeat_reference_id": None,
            "carrier_channel_id": None,
            "carrier_binding_sha256": None,
            "carrier_binding_grants_authority": False,
        }
    validated = validate_carrier_binding(
        binding,
        packet_id=str(request.get("packet_id") or ""),
        payload_hash=str(request.get("payload_hash") or ""),
    )
    reference = validated["heartbeat_reference"]
    channel = validated["channel"]
    return {
        "carrier_binding_present": True,
        "carrier_binding_validated": True,
        "carrier_profile": validated["carrier_profile"],
        "heartbeat_reference_epoch": reference["heartbeat_epoch"],
        "heartbeat_reference_id": reference["heartbeat_id"],
        "carrier_channel_id": channel["channel_id"],
        "carrier_binding_sha256": validated["binding_sha256"],
        "carrier_binding_grants_authority": False,
    }


def validate_transport_headers(headers: Mapping[str, str], body: bytes) -> dict[str, str | None]:
    _require(len(body) <= MAX_REQUEST_BYTES, "request_body_too_large")
    transport = str(headers.get("X-StegVerse-Transport", ""))
    origin = str(headers.get("X-StegVerse-Transport-Origin", ""))
    authorization_id = str(headers.get("X-StegVerse-Authorization-Id", "")) or None
    supplied_hash = str(headers.get("X-StegVerse-Payload-SHA256", "")).lower()
    content_type = str(headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
    _require(transport == "InTr", "transport_header_mismatch")
    _require(origin in {ORIGIN_NODE, ORIGIN_RELAY}, "transport_origin_header_invalid")
    _require(content_type in {"application/octet-stream", "application/json"}, "content_type_not_supported")
    _require(len(supplied_hash) == 64 and all(ch in "0123456789abcdef" for ch in supplied_hash), "payload_sha256_header_invalid")
    _require(supplied_hash == _sha256(body), "payload_sha256_header_mismatch")
    if origin == ORIGIN_RELAY:
        _require(bool(authorization_id), "authorization_id_header_required_for_relay")
    else:
        _require(authorization_id is None, "node_outbox_cannot_claim_tvc_authorization")
    return {"transport": transport, "origin": origin, "authorization_id": authorization_id, "payload_sha256": supplied_hash}


def _validate_node_outbox_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    _require(entry.get("schema") == NODE_OUTBOX_SCHEMA, "node_outbox_schema_invalid")
    _require(entry.get("state") == "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY", "node_outbox_state_invalid")
    _require(re.fullmatch(r"SV-NODE-[a-f0-9]{24}", str(entry.get("node_id", ""))) is not None, "node_id_invalid")
    _require(re.fullmatch(r"SV-IL-[a-f0-9]{24}", str(entry.get("interlock_id", ""))) is not None, "interlock_id_invalid")
    _require(entry.get("network_delivery_observed") is False, "node_outbox_already_delivered")
    _require(entry.get("runtime_materialization_observed") is False, "node_outbox_runtime_already_observed")
    _require(entry.get("receiver_receipt_observed") is False, "node_outbox_receiver_already_observed")
    _require(entry.get("tvc_receipt_observed") is False, "node_outbox_tvc_already_observed")
    _require(entry.get("request_grants_execution_authority") is False, "node_outbox_execution_authority_forbidden")
    _require(entry.get("claim_or_fence_minted") is False, "node_outbox_claim_or_fence_forbidden")
    _require(entry.get("credential_authority") == CREDENTIAL_AUTHORITY, "node_outbox_credential_authority_invalid")
    _require(entry.get("github_token_runtime_authority") == "NONE", "node_outbox_github_runtime_authority_forbidden")
    _require(entry.get("authority_effect") == "NONE_LOCAL_CONTINUITY_ONLY", "node_outbox_authority_effect_invalid")
    claimed = entry.get("outbox_entry_hash")
    body = dict(entry); body.pop("outbox_entry_hash", None)
    _require(claimed == _sha256_uri(body), "node_outbox_entry_hash_mismatch")
    request = entry.get("materialization_request")
    _require(isinstance(request, dict), "node_outbox_materialization_request_required")
    validate_request(request)
    _require(entry.get("materialization_id") == request.get("materialization_id"), "node_outbox_materialization_id_mismatch")
    _require(entry.get("request_hash") == request.get("request_hash"), "node_outbox_request_hash_mismatch")
    _require(entry.get("transport_intent_hash") == request.get("transport_intent_hash"), "node_outbox_transport_intent_hash_mismatch")
    _require(entry.get("payload_hash") == request.get("payload_hash"), "node_outbox_payload_hash_mismatch")
    _require(entry.get("destination") == request.get("destination"), "node_outbox_destination_mismatch")
    _require(entry.get("downstream_owner_ref") == request.get("downstream_owner_ref"), "node_outbox_owner_mismatch")
    return request


def extract_materialization(payload: Any, transport: Mapping[str, str | None]) -> tuple[dict[str, Any], dict[str, Any]]:
    origin = transport["origin"]
    if origin == ORIGIN_RELAY:
        _require(isinstance(payload, dict), "request_object_required")
        validate_request(payload)
        return payload, {"transport_origin": ORIGIN_RELAY, "transport_authorization_id": transport["authorization_id"], "node_id": None, "interlock_id": None, "outbox_entry_hash": None}
    _require(isinstance(payload, dict) and payload.get("schema") == NODE_TRIGGER_SCHEMA, "node_trigger_schema_invalid")
    _require(payload.get("transport_origin") == ORIGIN_NODE, "node_trigger_origin_invalid")
    _require(payload.get("authority_effect") == "NONE_TRIGGER_ONLY", "node_trigger_authority_effect_invalid")
    _require(payload.get("request_grants_execution_authority") is False, "node_trigger_execution_authority_forbidden")
    _require(payload.get("claim_or_fence_minted") is False, "node_trigger_claim_or_fence_forbidden")
    entry = payload.get("node_outbox_entry")
    _require(isinstance(entry, dict), "node_outbox_entry_required")
    request = _validate_node_outbox_entry(entry)
    _require(payload.get("node_id") == entry.get("node_id"), "node_trigger_node_id_mismatch")
    _require(payload.get("interlock_id") == entry.get("interlock_id"), "node_trigger_interlock_id_mismatch")
    _require(payload.get("outbox_entry_hash") == entry.get("outbox_entry_hash"), "node_trigger_outbox_hash_mismatch")
    trigger_body = dict(payload); claimed_trigger = trigger_body.pop("trigger_sha256", None)
    _require(claimed_trigger == _sha256_uri(trigger_body), "node_trigger_hash_mismatch")
    return request, {"transport_origin": ORIGIN_NODE, "transport_authorization_id": None, "node_id": entry["node_id"], "interlock_id": entry["interlock_id"], "outbox_entry_hash": entry["outbox_entry_hash"]}


def _write_once(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _require(path.read_bytes() == raw, "write_once_collision")
        return
    path.write_bytes(raw)
    _require(path.read_bytes() == raw, "persistence_verification_failed")


def _receipt_binding_matches(receipt: Mapping[str, Any], request: Mapping[str, Any], source: Mapping[str, Any]) -> bool:
    return all((
        receipt.get("state") == "INGRESS_ADMITTED",
        receipt.get("materialization_id") == request.get("materialization_id"),
        receipt.get("request_hash") == request.get("request_hash"),
        receipt.get("transport_origin") == source.get("transport_origin"),
        receipt.get("transport_authorization_id") == source.get("transport_authorization_id"),
        receipt.get("node_id") == source.get("node_id"),
        receipt.get("interlock_id") == source.get("interlock_id"),
        receipt.get("outbox_entry_hash") == source.get("outbox_entry_hash"),
    ))


def admit_materialization(*, runtime_root: Path, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
    transport = validate_transport_headers(headers, body)
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HILInTrIngressError("request_json_invalid") from exc
    request, source = extract_materialization(payload, transport)
    carrier = _carrier_binding_evidence(request)
    materialization_id = str(request["materialization_id"]); safe_id = _safe_id(materialization_id)
    request_path = runtime_root / REQUEST_DIR_REL / f"{safe_id}.json"
    canonical_request = json.dumps(request, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    _write_once(request_path, canonical_request)

    receipt_path = runtime_root / RECEIPT_DIR_REL / f"{safe_id}.json"
    if receipt_path.exists():
        try: existing = json.loads(receipt_path.read_text(encoding="utf-8"))
        except Exception as exc: raise HILInTrIngressError("existing_ingress_receipt_invalid") from exc
        _require(_receipt_binding_matches(existing, request, source), "write_once_collision")
        return dict(existing)

    receipt = {
        "schema": RECEIPT_SCHEMA, "state": "INGRESS_ADMITTED", "materialization_id": materialization_id,
        "request_hash": request["request_hash"], "transport_intent_hash": request["transport_intent_hash"], "payload_hash": request["payload_hash"],
        "operation_id": request["operation_id"], "packet_id": request["packet_id"], "transport_origin": source["transport_origin"],
        "transport_authorization_id": source["transport_authorization_id"], "node_id": source["node_id"], "interlock_id": source["interlock_id"], "outbox_entry_hash": source["outbox_entry_hash"],
        "transport_payload_sha256": transport["payload_sha256"], "queue_ref": str(request_path), "exact_request_validated": True, "write_once_persisted": True,
        "runtime_execution_attempted": False, "receiver_readiness_claimed": False, "hil_custody_claimed": False, "claim_or_fence_minted": False, "g18_required": False,
        "credential_authority": CREDENTIAL_AUTHORITY, "github_token_runtime_authority": "NONE", **carrier, "authority_effect": AUTHORITY_EFFECT, "admitted_at": _utc_now(),
    }
    receipt_raw = json.dumps(receipt, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    _write_once(receipt_path, receipt_raw)
    latest = runtime_root / LATEST_REL; latest.parent.mkdir(parents=True, exist_ok=True); latest.write_bytes(receipt_raw)
    return receipt


class IngressServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], runtime_root: Path, max_requests: int):
        super().__init__(address, IngressHandler); self.runtime_root = runtime_root; self.max_requests = max_requests; self.handled_requests = 0


class IngressHandler(BaseHTTPRequestHandler):
    server: IngressServer
    def log_message(self, _format: str, *_args: object) -> None: return
    def _json(self, status: int, value: Mapping[str, Any]) -> None:
        raw = json.dumps(dict(value), sort_keys=True).encode("utf-8") + b"\n"; self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_POST(self) -> None:  # noqa: N802
        if self.path != INGRESS_PATH: self._json(404, {"state": "NOT_FOUND", "authority_effect": AUTHORITY_EFFECT}); return
        try: length = int(self.headers.get("Content-Length", ""))
        except ValueError: self._json(411, {"state": "REJECTED", "reason": "content_length_invalid", "authority_effect": AUTHORITY_EFFECT}); return
        if length < 0 or length > MAX_REQUEST_BYTES: self._json(413, {"state": "REJECTED", "reason": "request_body_too_large", "authority_effect": AUTHORITY_EFFECT}); return
        body = self.rfile.read(length)
        try: receipt = admit_materialization(runtime_root=self.server.runtime_root, body=body, headers=self.headers)
        except Exception as exc: self._json(400, {"state": "REJECTED", "reason": str(exc), "authority_effect": AUTHORITY_EFFECT}); return
        self.server.handled_requests += 1; self._json(202, receipt)
        if self.server.max_requests and self.server.handled_requests >= self.server.max_requests: self.close_connection = True


def serve(*, runtime_root: Path, bind_host: str, bind_port: int, max_requests: int, tls_cert: Path | None = None, tls_key: Path | None = None) -> tuple[str, int]:
    runtime = runtime_root.expanduser().resolve(); runtime.mkdir(parents=True, exist_ok=True); server = IngressServer((bind_host, bind_port), runtime, max_requests)
    if tls_cert or tls_key:
        _require(tls_cert is not None and tls_key is not None, "tls_cert_and_key_required_together"); context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); context.load_cert_chain(str(tls_cert), str(tls_key)); server.socket = context.wrap_socket(server.socket, server_side=True)
    elif bind_host not in {"127.0.0.1", "::1", "localhost"}:
        server.server_close(); raise HILInTrIngressError("non_loopback_ingress_requires_tls")
    bound = server.server_address
    try:
        while not max_requests or server.handled_requests < max_requests: server.handle_request()
    finally: server.server_close()
    return str(bound[0]), int(bound[1])


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve bounded HIL Universal InTr materialization ingress."); parser.add_argument("--runtime-root", type=Path, required=True); parser.add_argument("--bind-host", default="127.0.0.1"); parser.add_argument("--bind-port", type=int, default=0); parser.add_argument("--max-requests", type=int, default=1); parser.add_argument("--tls-cert", type=Path); parser.add_argument("--tls-key", type=Path); args = parser.parse_args()
    if args.max_requests < 0: raise SystemExit("max_requests_must_be_nonnegative")
    host, port = serve(runtime_root=args.runtime_root, bind_host=args.bind_host, bind_port=args.bind_port, max_requests=args.max_requests, tls_cert=args.tls_cert, tls_key=args.tls_key)
    print(json.dumps({"schema": "stegverse.hil-intr-materialization-ingress-listener/v1", "state": "STOPPED_AFTER_BOUND", "bound_host": host, "bound_port": port, "credential_authority": CREDENTIAL_AUTHORITY, "github_token_runtime_authority": "NONE", "authority_effect": AUTHORITY_EFFECT}, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
