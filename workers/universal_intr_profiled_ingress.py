#!/usr/bin/env python3
"""Shared profiled Universal InTr materialization ingress.

HIL requests delegate to the already-validated HIL ingress unchanged. SV002
public-observation requests use a distinct validator/receipt namespace and,
after write-once admission, launch a credential-scrubbed non-authorizing
consumer. That consumer may ask the existing WorkerCoordinator to execute only
the already-admitted SV002 observation task under its own claim/fence authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import subprocess
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import serve_hil_intr_materialization_ingress as hil  # noqa: E402
from workers.sv002_intr_materialization_consumer import (  # noqa: E402
    DESTINATION as SV002_DESTINATION,
    DOWNSTREAM_OWNER as SV002_OWNER,
    scrubbed_env as sv002_scrubbed_env,
    validate_request as validate_sv002_request,
)

PROFILE_PATH = "/intr/profile"
INGRESS_PATH = "/intr/materialization"
SV002_RECEIPT_SCHEMA = "stegverse.sv002-intr-materialization-ingress/v1"
SV002_RECEIPT_DIR = Path("receipts/sovereign-network/sv002-intr-ingress")
SV002_LATEST = Path("receipts/sovereign-network/sv002-intr-ingress.latest.json")
AUTHORITY_EFFECT = "NONE_INGRESS_ONLY"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_id(value: str) -> str:
    require(value.startswith("INTR-MAT-") and len(value) == 33 and all(ch in "0123456789abcdef" for ch in value[9:]), "materialization_id_invalid")
    return value


def _sv002_request_from_payload(payload: Any, transport: Mapping[str, str | None]) -> tuple[dict[str, Any], dict[str, Any]]:
    origin = transport["origin"]
    if origin == hil.ORIGIN_RELAY:
        require(isinstance(payload, dict), "request_object_required")
        validate_sv002_request(payload)
        return dict(payload), {
            "transport_origin": origin,
            "transport_authorization_id": transport["authorization_id"],
            "node_id": None,
            "interlock_id": None,
            "outbox_entry_hash": None,
        }
    require(isinstance(payload, dict) and payload.get("schema") == hil.NODE_TRIGGER_SCHEMA, "node_trigger_schema_invalid")
    require(payload.get("transport_origin") == hil.ORIGIN_NODE, "node_trigger_origin_invalid")
    require(payload.get("authority_effect") == "NONE_TRIGGER_ONLY", "node_trigger_authority_effect_invalid")
    require(payload.get("request_grants_execution_authority") is False and payload.get("claim_or_fence_minted") is False, "node_trigger_authority_forbidden")
    entry = payload.get("node_outbox_entry")
    require(isinstance(entry, dict), "node_outbox_entry_required")
    require(entry.get("schema") == hil.NODE_OUTBOX_SCHEMA and entry.get("state") == "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY", "node_outbox_state_invalid")
    require(entry.get("network_delivery_observed") is False and entry.get("runtime_materialization_observed") is False and entry.get("receiver_receipt_observed") is False and entry.get("tvc_receipt_observed") is False, "node_outbox_promoted_evidence_forbidden")
    require(entry.get("request_grants_execution_authority") is False and entry.get("claim_or_fence_minted") is False, "node_outbox_authority_forbidden")
    require(entry.get("credential_authority") == "TV/TVC" and entry.get("github_token_runtime_authority") == "NONE" and entry.get("authority_effect") == "NONE_LOCAL_CONTINUITY_ONLY", "node_outbox_credential_boundary_invalid")
    body = dict(entry)
    claimed = body.pop("outbox_entry_hash", None)
    require(claimed == sha_uri(body), "node_outbox_entry_hash_mismatch")
    request = entry.get("materialization_request")
    require(isinstance(request, dict), "node_outbox_materialization_request_required")
    validate_sv002_request(request)
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "destination", "downstream_owner_ref"):
        require(entry.get(key) == request.get(key), "node_outbox_binding_mismatch:" + key)
    require(payload.get("node_id") == entry.get("node_id") and payload.get("interlock_id") == entry.get("interlock_id") and payload.get("outbox_entry_hash") == entry.get("outbox_entry_hash"), "node_trigger_binding_mismatch")
    trigger = dict(payload)
    trigger_claim = trigger.pop("trigger_sha256", None)
    require(trigger_claim == sha_uri(trigger), "node_trigger_hash_mismatch")
    return dict(request), {
        "transport_origin": origin,
        "transport_authorization_id": None,
        "node_id": entry.get("node_id"),
        "interlock_id": entry.get("interlock_id"),
        "outbox_entry_hash": entry.get("outbox_entry_hash"),
    }


def _is_sv002(payload: Any) -> bool:
    if isinstance(payload, dict) and payload.get("destination") == SV002_DESTINATION and payload.get("downstream_owner_ref") == SV002_OWNER:
        return True
    if isinstance(payload, dict):
        entry = payload.get("node_outbox_entry")
        if isinstance(entry, dict):
            request = entry.get("materialization_request")
            return isinstance(request, dict) and request.get("destination") == SV002_DESTINATION and request.get("downstream_owner_ref") == SV002_OWNER
    return False


def _dispatch_sv002_consumer(*, runtime_root: Path, materialization_id: str) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "workers.sv002_intr_materialization_consumer",
        "--source-root",
        str(ROOT),
        "--runtime-root",
        str(runtime_root),
        "--materialization-id",
        materialization_id,
    ]
    process = subprocess.Popen(
        command,
        cwd=str(ROOT),
        env=sv002_scrubbed_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    return {
        "consumer_dispatch_attempted": True,
        "consumer_pid": process.pid,
        "consumer_execution_authority": False,
        "consumer_claim_or_fence_minted_by_ingress": False,
        "authority_effect": "NONE_DISPATCH_ONLY",
    }


def admit_sv002(*, runtime_root: Path, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
    transport = hil.validate_transport_headers(headers, body)
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError("request_json_invalid") from exc
    request, source = _sv002_request_from_payload(payload, transport)
    materialization_id = safe_id(str(request["materialization_id"]))
    request_path = runtime_root / hil.REQUEST_DIR_REL / f"{materialization_id}.json"
    request_raw = json.dumps(request, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    hil._write_once(request_path, request_raw)
    receipt_path = runtime_root / SV002_RECEIPT_DIR / f"{materialization_id}.json"
    if receipt_path.exists():
        existing = json.loads(receipt_path.read_text(encoding="utf-8"))
        require(existing.get("request_hash") == request.get("request_hash") and existing.get("state") == "INGRESS_ADMITTED", "write_once_collision")
        return existing
    receipt = {
        "schema": SV002_RECEIPT_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "transport_origin": source["transport_origin"],
        "transport_authorization_id": source["transport_authorization_id"],
        "node_id": source["node_id"],
        "interlock_id": source["interlock_id"],
        "outbox_entry_hash": source["outbox_entry_hash"],
        "transport_payload_sha256": transport["payload_sha256"],
        "queue_ref": str(request_path),
        "exact_request_validated": True,
        "write_once_persisted": True,
        "runtime_execution_attempted": False,
        "consumer_dispatch_attempted": False,
        "receiver_readiness_claimed": False,
        "round_trip_claimed": False,
        "observation_round_trip_claimed": False,
        "observer_direct_relation_to_stegverse_002": False,
        "claim_or_fence_minted": False,
        "g18_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": AUTHORITY_EFFECT,
        "admitted_at": now(),
    }
    raw = json.dumps(receipt, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    hil._write_once(receipt_path, raw)
    latest = runtime_root / SV002_LATEST
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_bytes(raw)
    dispatch = _dispatch_sv002_consumer(runtime_root=runtime_root, materialization_id=materialization_id)
    return {**receipt, "dispatch": dispatch}


def profile(tls_enabled: bool) -> dict[str, Any]:
    return {
        "schema": "stegverse.universal-intr-profiled-ingress/v1",
        "state": "ACTIVE_SOVEREIGN_INTR_INGRESS",
        "protocol": "InTr",
        "profile_path": PROFILE_PATH,
        "materialization_path": INGRESS_PATH,
        "profiles": ["HIL:Ingress", "SV002:PublicObservation"],
        "supported_origins": [hil.ORIGIN_NODE, hil.ORIGIN_RELAY],
        "event_triggered": True,
        "always_on_application_receiver_required": False,
        "second_user_device_required": False,
        "g18_required": False,
        "tls_enabled": tls_enabled,
        "public_tls_terminated_by": "STEGVERSE_SHARED_SERVICE_GATEWAY",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "execution_authority": "NONE",
        "authority_effect": "NONE_DISCOVERY_EVIDENCE_ONLY",
    }


class Handler(BaseHTTPRequestHandler):
    server: "Server"

    def log_message(self, _fmt: str, *_args: object) -> None:
        return

    def send_json(self, status: int, value: Mapping[str, Any]) -> None:
        raw = json.dumps(dict(value), sort_keys=True).encode("utf-8") + b"\n"
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path != PROFILE_PATH:
            self.send_json(404, {"state": "NOT_FOUND", "authority_effect": "NONE"})
            return
        self.send_json(200, profile(self.server.tls_enabled))

    def do_POST(self) -> None:  # noqa: N802
        if self.path != INGRESS_PATH:
            self.send_json(404, {"state": "NOT_FOUND", "authority_effect": AUTHORITY_EFFECT})
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.send_json(411, {"state": "REJECTED", "reason": "content_length_invalid", "authority_effect": AUTHORITY_EFFECT})
            return
        if length < 0 or length > hil.MAX_REQUEST_BYTES:
            self.send_json(413, {"state": "REJECTED", "reason": "request_body_too_large", "authority_effect": AUTHORITY_EFFECT})
            return
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
            receipt = admit_sv002(runtime_root=self.server.runtime_root, body=body, headers=self.headers) if _is_sv002(payload) else hil.admit_materialization(runtime_root=self.server.runtime_root, body=body, headers=self.headers)
        except Exception as exc:
            self.send_json(400, {"state": "REJECTED", "reason": str(exc), "authority_effect": AUTHORITY_EFFECT})
            return
        self.server.handled_requests += 1
        self.send_json(202, receipt)


class Server(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], runtime_root: Path, max_requests: int):
        super().__init__(address, Handler)
        self.runtime_root = runtime_root
        self.max_requests = max_requests
        self.handled_requests = 0
        self.tls_enabled = False


def serve(*, runtime_root: Path, bind_host: str, bind_port: int, max_requests: int, tls_cert: Path | None = None, tls_key: Path | None = None) -> tuple[str, int]:
    runtime = runtime_root.expanduser().resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    server = Server((bind_host, bind_port), runtime, max_requests)
    if tls_cert or tls_key:
        require(tls_cert is not None and tls_key is not None, "tls_cert_and_key_required_together")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(tls_cert), str(tls_key))
        server.socket = context.wrap_socket(server.socket, server_side=True)
        server.tls_enabled = True
    elif bind_host not in {"127.0.0.1", "::1", "localhost"}:
        server.server_close()
        raise ValueError("non_loopback_ingress_requires_tls")
    bound = server.server_address
    try:
        while not max_requests or server.handled_requests < max_requests:
            server.handle_request()
    finally:
        server.server_close()
    return str(bound[0]), int(bound[1])


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve shared profiled Universal InTr materialization ingress.")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--bind-host", default="127.0.0.1")
    parser.add_argument("--bind-port", type=int, default=0)
    parser.add_argument("--max-requests", type=int, default=1)
    parser.add_argument("--tls-cert", type=Path)
    parser.add_argument("--tls-key", type=Path)
    args = parser.parse_args()
    host, port = serve(runtime_root=args.runtime_root, bind_host=args.bind_host, bind_port=args.bind_port, max_requests=args.max_requests, tls_cert=args.tls_cert, tls_key=args.tls_key)
    print(json.dumps({
        "schema": "stegverse.universal-intr-profiled-ingress-listener/v1",
        "state": "STOPPED_AFTER_BOUND",
        "bound_host": host,
        "bound_port": port,
        "profile_path": PROFILE_PATH,
        "materialization_path": INGRESS_PATH,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "execution_authority": "NONE",
        "authority_effect": "NONE_DISCOVERY_EVIDENCE_ONLY",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
