#!/usr/bin/env python3
"""Sovereign node-gated StegVerse-002 public observation receiver.

Read-only transport endpoint for the Site /sv002-observe/ surface.
No experiment, activation, approval, custody, or model-output authority is granted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Mapping

HOSTED_ENV = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
CREDENTIAL_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN")
MAX_BODY = 2 * 1024 * 1024

REQUEST_SCHEMA = "stegverse.sv002.public_observation.interlock_request.v1"
RESPONSE_SCHEMA = "stegverse.sv002.public_observation.interlock_response.v1"
REQUEST_CLASS = "SV002_PUBLIC_OBSERVE"
OPERATION = "READ_OBSERVATION"
EXPERIMENT_ID = "STEGVERSE-002-SELF-CHARACTERIZATION-001"
PROJECTION_CLASS = "PUBLIC_READ_ONLY"

class SV002ObservationError(ValueError):
    pass

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def sha256_hex(value: Any) -> str:
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
    elif isinstance(value, str):
        raw = value.encode("utf-8")
    else:
        raw = canonical_json(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def _reject_hosted_or_secret_env() -> None:
    for key in HOSTED_ENV:
        if os.environ.get(key):
            raise SV002ObservationError(f"hosted_runtime_forbidden:{key}")
    for key in CREDENTIAL_ENV:
        if os.environ.get(key):
            raise SV002ObservationError(f"credential_environment_forbidden:{key}")

def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SV002ObservationError(f"{label}_object_required")
    return value

def validate_genesis_receipt(observer: Mapping[str, Any]) -> dict[str, str]:
    node_id = str(observer.get("node_id") or "").strip()
    interlock_id = str(observer.get("interlock_id") or "").strip()
    registered_hash = str(observer.get("registration_receipt_sha256") or "").strip()
    genesis = dict(_require_mapping(observer.get("genesis_receipt"), "genesis_receipt"))
    required = {
        "schema": "stegos.node_handoff_receipt.v1",
        "receipt_number": 1,
        "transition": "NODE_REGISTERED",
        "continuity_parent": "GENESIS",
        "authority_effect": "NONE",
        "credential_authority": "TV/TVC",
    }
    for key, expected in required.items():
        if genesis.get(key) != expected:
            raise SV002ObservationError(f"genesis_receipt_{key}_mismatch")
    if genesis.get("node_id") != node_id or genesis.get("interlock_id") != interlock_id:
        raise SV002ObservationError("genesis_receipt_identity_mismatch")
    claimed = str(genesis.pop("receipt_sha256", "") or "")
    if len(claimed) != 64 or any(ch not in "0123456789abcdef" for ch in claimed):
        raise SV002ObservationError("genesis_receipt_digest_invalid")
    actual = sha256_hex(genesis)
    if actual != claimed or registered_hash != claimed:
        raise SV002ObservationError("genesis_receipt_digest_mismatch")
    return {"node_id": node_id, "interlock_id": interlock_id, "registration_receipt_sha256": claimed}

def validate_request(request: Mapping[str, Any], authorization_id: str) -> dict[str, Any]:
    if request.get("schema_version") != REQUEST_SCHEMA:
        raise SV002ObservationError("request_schema_not_admitted")
    if request.get("request_class") != REQUEST_CLASS:
        raise SV002ObservationError("request_class_not_admitted")
    if request.get("operation") != OPERATION or request.get("transport") != "InTr":
        raise SV002ObservationError("operation_or_transport_not_admitted")
    if request.get("authority_transfer") is not False:
        raise SV002ObservationError("authority_transfer_forbidden")
    if request.get("authority_ref") != authorization_id:
        raise SV002ObservationError("authorization_binding_mismatch")
    bindings = _require_mapping(request.get("bindings"), "bindings")
    if bindings.get("experiment_id") != EXPERIMENT_ID or bindings.get("observation_projection") != PROJECTION_CLASS:
        raise SV002ObservationError("experiment_binding_mismatch")
    observer_binding = validate_genesis_receipt(_require_mapping(request.get("observer"), "observer"))
    claimed_request_hash = str(request.get("request_sha256") or "")
    unhashed = dict(request)
    unhashed.pop("request_sha256", None)
    if claimed_request_hash != sha256_hex(unhashed):
        raise SV002ObservationError("request_sha256_mismatch")
    return {"observer_binding": observer_binding, "bindings": dict(bindings)}

def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def _projection(experiment_root: Path, master_records_projection: Path | None) -> dict[str, Any]:
    root = experiment_root.expanduser().resolve()
    execution_path = root / "EXPERIMENT_EXECUTION_RECEIPT.json"
    formal_path = root / "SELF_CHARACTERIZATION_FORMAL.json"
    chain_path = root / "INTERACTION_RECEIPT_CHAIN.json"
    execution = _load_json(execution_path) if execution_path.is_file() else None
    formal = _load_json(formal_path) if formal_path.is_file() else None
    chain = _load_json(chain_path) if chain_path.is_file() else None

    state = {
        "experiment_id": EXPERIMENT_ID,
        "execution": execution if isinstance(execution, Mapping) else {"state": "NOT_OBSERVED"},
    }
    topology = {
        "observer_edge": "READ_ONLY_PROJECTION_ONLY",
        "observer_direct_interaction_with_subject": False,
        "subject": "StegVerse-002",
    }
    knowledge = formal if isinstance(formal, Mapping) else {
        "state": "NOT_OBSERVED",
        "allowed_evidence_states": ["AVAILABLE", "DISCOVERABLE", "ACCESSED", "REFERENCED", "USED", "DERIVED"],
    }
    if isinstance(chain, list):
        events = chain
    elif isinstance(chain, Mapping) and isinstance(chain.get("events"), list):
        events = chain["events"]
    else:
        events = []

    reconstruction: Any = {"state": "NOT_OBSERVED"}
    if master_records_projection is not None:
        mr = master_records_projection.expanduser().resolve()
        if mr.is_file():
            candidate = _load_json(mr)
            if isinstance(candidate, Mapping):
                reconstruction = candidate

    return {
        "state": state,
        "topology": topology,
        "knowledge": knowledge,
        "events": events,
        "reconstruction": reconstruction,
        "evidence_presence": {
            "execution_receipt": execution_path.is_file(),
            "formal_result": formal_path.is_file(),
            "interaction_receipt_chain": chain_path.is_file(),
            "master_records_projection": bool(master_records_projection and master_records_projection.expanduser().resolve().is_file()),
        },
    }

def _load_stegos(stegos_root: Path):
    root = stegos_root.expanduser().resolve()
    if not (root / "stegos" / "universal_intr_transport.py").is_file():
        raise SV002ObservationError(f"stegos_source_missing:{root}")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from stegos.universal_intr_transport import build_hop_receipt, build_transport_intent, sha256_uri
    return build_hop_receipt, build_transport_intent, sha256_uri

def _write_once(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") == serialized:
            return
        raise SV002ObservationError(f"write_once_collision:{path}")
    path.write_text(serialized, encoding="utf-8")

def process_request(
    request: Mapping[str, Any],
    *,
    authorization_id: str,
    stegos_root: Path,
    experiment_root: Path,
    runtime_root: Path,
    boundary_identity_ref: str,
    master_records_projection: Path | None = None,
) -> dict[str, Any]:
    admitted = validate_request(request, authorization_id)
    build_hop_receipt, build_transport_intent, sha256_uri = _load_stegos(stegos_root)

    ingress_intent = build_transport_intent(
        operation_id=f"SV002_PUBLIC_OBSERVE:{admitted['observer_binding']['node_id']}:INGRESS",
        payload_hash=sha256_uri(dict(request)),
        source_boundary="DEVICE_SYSTEM",
        source_subsystem="Site:SV002PublicObservation",
        destination_boundary="STEGOS_ECOSYSTEM",
        destination_subsystem=".github:SV002PublicObservationRuntime",
    )
    ingress = build_hop_receipt(
        ingress_intent,
        hop_index=1,
        receipt_id="SV002-IN-" + ingress_intent["packet_id"][5:],
        boundary_identity_ref=boundary_identity_ref,
        recorded_at=now_iso(),
        prior_receipt_hash=None,
        transition_state="RECEIVED",
    )

    response: dict[str, Any] = {
        "schema_version": RESPONSE_SCHEMA,
        "operation": OPERATION,
        "decision": "ALLOW_READ_ONLY_OBSERVATION",
        "authority_effect": "NONE",
        "authority_transfer": False,
        "observer_binding": admitted["observer_binding"],
        "bindings": admitted["bindings"],
        "projection": _projection(experiment_root, master_records_projection),
    }

    egress_payload = dict(response)
    egress_intent = build_transport_intent(
        operation_id=f"SV002_PUBLIC_OBSERVE:{admitted['observer_binding']['node_id']}:EGRESS",
        payload_hash=sha256_uri(egress_payload),
        source_boundary="STEGOS_ECOSYSTEM",
        source_subsystem=".github:SV002PublicObservationRuntime",
        destination_boundary="DEVICE_SYSTEM",
        destination_subsystem="Site:SV002PublicObservation",
        prior_transport_receipt_hash=ingress["receipt_hash"],
    )
    egress = build_hop_receipt(
        egress_intent,
        hop_index=1,
        receipt_id="SV002-OUT-" + egress_intent["packet_id"][5:],
        boundary_identity_ref=boundary_identity_ref,
        recorded_at=now_iso(),
        prior_receipt_hash=ingress["receipt_hash"],
        transition_state="FORWARDED",
    )
    response["transport_receipts"] = {"ingress": ingress, "egress": egress}

    bundle = {
        "schema": "stegverse.sv002.public-observation-runtime-receipt-bundle/v1",
        "state": "PUBLIC_OBSERVATION_ROUND_TRIP_FORWARDED",
        "experiment_id": EXPERIMENT_ID,
        "observer_binding": admitted["observer_binding"],
        "authorization_ref": authorization_id,
        "ingress_intent": ingress_intent,
        "ingress_receipt": ingress,
        "egress_intent": egress_intent,
        "egress_receipt": egress,
        "projection_evidence_presence": response["projection"]["evidence_presence"],
        "authority_effect": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "recorded_at": now_iso(),
    }
    receipt_path = runtime_root.expanduser().resolve() / "receipts/sovereign-network/sv002-public-observation" / f"{ingress['receipt_id']}.json"
    _write_once(receipt_path, bundle)
    return response

class BoundedHTTPServer(HTTPServer):
    processed_requests = 0

def make_handler(args):
    class Handler(BaseHTTPRequestHandler):
        server_version = "StegVerseSV002ObserveInTr/1"

        def _cors(self) -> None:
            origin = self.headers.get("Origin")
            if origin == args.allowed_origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")

        def do_GET(self) -> None:
            if self.path != "/intr/sv002-observe/readiness":
                self.send_response(404); self.end_headers(); return
            raw = canonical_json({
                "schema": "stegverse.sv002.public-observation-runtime-readiness/v1",
                "state": "READY",
                "transport": "InTr",
                "host": args.host,
                "port": args.port,
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": "NONE",
                "authority_effect": "NONE",
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_OPTIONS(self) -> None:
            if self.headers.get("Origin") != args.allowed_origin:
                self.send_response(403); self.end_headers(); return
            self.send_response(204)
            self._cors()
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "content-type,x-stegverse-transport,x-stegverse-authorization-id,x-stegverse-payload-sha256")
            self.end_headers()

        def do_POST(self) -> None:
            if self.path != "/intr/sv002-observe":
                self.send_response(404); self.end_headers(); return
            try:
                if self.headers.get("Origin") != args.allowed_origin:
                    raise SV002ObservationError("origin_not_admitted")
                if self.headers.get("X-StegVerse-Transport") != "InTr":
                    raise SV002ObservationError("transport_header_mismatch")
                authorization_id = str(self.headers.get("X-StegVerse-Authorization-Id") or "").strip()
                if not authorization_id:
                    raise SV002ObservationError("authorization_id_required")
                length = int(self.headers.get("Content-Length") or "0")
                if length <= 0 or length > MAX_BODY:
                    raise SV002ObservationError("request_size_invalid")
                body = self.rfile.read(length)
                if str(self.headers.get("X-StegVerse-Payload-SHA256") or "") != sha256_hex(body):
                    raise SV002ObservationError("request_payload_hash_mismatch")
                request = json.loads(body.decode("utf-8"))
                if not isinstance(request, dict):
                    raise SV002ObservationError("request_object_required")
                response = process_request(
                    request,
                    authorization_id=authorization_id,
                    stegos_root=args.stegos_root,
                    experiment_root=args.experiment_root,
                    runtime_root=args.runtime_root,
                    boundary_identity_ref=args.boundary_identity_ref,
                    master_records_projection=args.master_records_projection,
                )
                raw = (canonical_json(response) + "\n").encode("utf-8")
                self.send_response(200); self._cors()
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                self.server.processed_requests += 1
            except Exception as exc:
                raw = canonical_json({
                    "schema": "stegverse.sv002.public-observation-runtime-error/v1",
                    "state": "FAIL_CLOSED",
                    "reason": str(exc),
                    "authority_effect": "NONE",
                }).encode("utf-8")
                self.send_response(400); self._cors()
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        def log_message(self, fmt, *values):
            return
    return Handler

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stegos-root", type=Path, required=True)
    parser.add_argument("--experiment-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--master-records-projection", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8772)
    parser.add_argument("--max-requests", type=int, default=1)
    parser.add_argument("--allowed-origin", default="https://stegverse.org")
    parser.add_argument("--boundary-identity-ref", required=True)
    args = parser.parse_args()

    _reject_hosted_or_secret_env()
    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        raise SV002ObservationError("public_bind_forbidden_use_shared_service_gateway")

    server = BoundedHTTPServer((args.host, args.port), make_handler(args))
    if args.max_requests <= 0:
        server.serve_forever(poll_interval=0.5)
    else:
        while server.processed_requests < args.max_requests:
            server.handle_request()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
