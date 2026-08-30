#!/usr/bin/env python3
"""Sovereign READ_REVIEW Interlock/InTr endpoint for evaluator browser transport.

Bounded first operational lane: exact pre-bound READ_REVIEW only. No review,
approval, freeze, execution, credential, or custody authority is granted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path("data/evaluator-review/cross-framework-current-basis-001.json")
HOSTED_ENV = ("GITHUB_ACTIONS","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
CREDENTIAL_ENV = ("GITHUB_TOKEN","GH_TOKEN","STEGVERSE_GITHUB_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN")
MAX_BODY = 2 * 1024 * 1024

class EvaluatorRuntimeError(ValueError):
    pass

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def raw_sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()

def _reject_hosted_or_secret_env() -> None:
    for key in HOSTED_ENV:
        if os.environ.get(key):
            raise EvaluatorRuntimeError(f"hosted_runtime_forbidden:{key}")
    for key in CREDENTIAL_ENV:
        if os.environ.get(key):
            raise EvaluatorRuntimeError(f"credential_environment_forbidden:{key}")

def _load_stegos(stegos_root: Path):
    root = stegos_root.expanduser().resolve()
    registry = root / "specs" / "universal-intr-connector-profiles.v1.json"
    if not (root / "stegos" / "intr_backbone.py").is_file() or not registry.is_file():
        raise EvaluatorRuntimeError(f"stegos_source_missing:{root}")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from stegos.evaluator_intr_roundtrip import validate_browser_interlock_request
    from stegos.intr_backbone import connector_from_registry
    return connector_from_registry(registry, "evaluator-read-review"), validate_browser_interlock_request

def _load_projection(site_root: Path, source: str) -> dict[str, Any]:
    if source != DEFAULT_SOURCE.as_posix():
        raise EvaluatorRuntimeError("review_source_not_admitted")
    path = site_root.expanduser().resolve() / DEFAULT_SOURCE
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvaluatorRuntimeError("review_projection_object_required")
    return value

def _manifest_hash(review: dict[str, Any]) -> str:
    manifest = review.get("manifest")
    if not isinstance(manifest, dict):
        raise EvaluatorRuntimeError("review_manifest_missing")
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def _validate_projection_binding(request: dict[str, Any], review: dict[str, Any]) -> None:
    bindings = request["bindings"]
    test = review.get("test") or {}
    if bindings.get("test_id") != test.get("id"):
        raise EvaluatorRuntimeError("review_test_binding_mismatch")
    if bindings.get("revision") != test.get("version"):
        raise EvaluatorRuntimeError("review_revision_binding_mismatch")
    if bindings.get("manifest_hash") != _manifest_hash(review):
        raise EvaluatorRuntimeError("review_manifest_hash_binding_mismatch")

def _write_once(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") == serialized:
            return
        raise EvaluatorRuntimeError(f"write_once_collision:{path}")
    path.write_text(serialized, encoding="utf-8")

def process_read_review(request: dict[str, Any], *, site_root: Path, stegos_root: Path, runtime_root: Path, authorization_id: str, boundary_identity_ref: str) -> dict[str, Any]:
    connector, validate_browser_interlock_request = _load_stegos(stegos_root)
    admitted = validate_browser_interlock_request(request)
    if admitted["operation"] != "READ_REVIEW":
        raise EvaluatorRuntimeError("operation_not_available_in_read_only_runtime")
    if request.get("authority_ref") != authorization_id:
        raise EvaluatorRuntimeError("authorization_binding_mismatch")
    payload = request.get("payload") or {}
    source = str(payload.get("source") or DEFAULT_SOURCE.as_posix())
    review = _load_projection(site_root, source)
    _validate_projection_binding(request, review)

    bindings = admitted["bindings"]
    ingress_packet = connector.prepare(
        request,
        payload_schema="stegverse.evaluator_review.interlock_request.v1",
        operation="READ_REVIEW",
        operation_id=f"EVALUATOR:READ_REVIEW:{bindings['test_id']}:v{bindings['revision']}:INGRESS",
    )
    ingress = connector.accept_hop(
        ingress_packet,
        hop_index=1,
        receipt_id="EVAL-IN-" + ingress_packet.intent["packet_id"][5:],
        boundary_identity_ref=boundary_identity_ref,
        recorded_at=now_iso(),
        prior_receipt_hash=None,
        transition_state="RECEIVED",
    )
    ingress_result = connector.validate_complete(ingress_packet, [ingress])

    response: dict[str, Any] = {
        "schema_version": "stegverse.evaluator_review.interlock_response.v1",
        "operation": "READ_REVIEW",
        "decision": "ALLOW_BOUNDED_CONTEXT",
        "authority_effect": "NONE",
        "authority_transfer": False,
        "bindings": dict(request["bindings"]),
        "review": review,
    }
    egress_packet = connector.prepare_response(
        ingress_packet,
        [ingress],
        response,
        payload_schema="stegverse.evaluator_review.interlock_response.v1",
        operation_id=f"EVALUATOR:READ_REVIEW:{bindings['test_id']}:v{bindings['revision']}:EGRESS",
    )
    egress = connector.accept_hop(
        egress_packet,
        hop_index=1,
        receipt_id="EVAL-OUT-" + egress_packet.intent["packet_id"][5:],
        boundary_identity_ref=boundary_identity_ref,
        recorded_at=now_iso(),
        prior_receipt_hash=ingress["receipt_hash"],
        transition_state="FORWARDED",
    )
    egress_result = connector.validate_complete(egress_packet, [egress])
    response["transport_receipts"] = {"ingress": ingress, "egress": egress}

    bundle = {
        "schema": "stegverse.evaluator-read-review-runtime-receipt-bundle/v1",
        "state": "READ_REVIEW_ROUND_TRIP_FORWARDED",
        "request_bindings": dict(request["bindings"]),
        "authorization_ref": authorization_id,
        "connector_profile_id": connector.profile.profile_id,
        "canonical_backbone": "stegos.intr_backbone.CanonicalInTrConnector",
        "ingress_intent": ingress_packet.intent,
        "ingress_receipt": ingress,
        "ingress_backbone_result": ingress_result,
        "egress_intent": egress_packet.intent,
        "egress_receipt": egress,
        "egress_backbone_result": egress_result,
        "authority_effect": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "recorded_at": now_iso(),
    }
    _write_once(runtime_root.expanduser().resolve() / "receipts/sovereign-network/evaluator-intr" / f"{ingress['receipt_id']}.json", bundle)
    return response

def make_handler(args):
    class Handler(BaseHTTPRequestHandler):
        server_version = "StegVerseEvaluatorInTr/1"
        def _cors(self) -> None:
            origin = self.headers.get("Origin")
            if origin == args.allowed_origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
        def do_GET(self) -> None:
            if self.path != "/intr/evaluator/readiness":
                self.send_response(404); self.end_headers(); return
            raw = json.dumps({
                "schema":"stegverse.evaluator-intr-runtime-readiness/v1",
                "state":"READY",
                "transport":"InTr",
                "host":args.host,
                "port":args.port,
                "credential_authority":"TV/TVC",
                "github_token_runtime_authority":"NONE",
                "authority_effect":"NONE",
            }, sort_keys=True, separators=(",", ":")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Cache-Control","no-store")
            self.send_header("Content-Length",str(len(raw)))
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
            if self.path != "/intr/evaluator":
                self.send_response(404); self.end_headers(); return
            try:
                if self.headers.get("Origin") != args.allowed_origin:
                    raise EvaluatorRuntimeError("origin_not_admitted")
                if self.headers.get("X-StegVerse-Transport") != "InTr":
                    raise EvaluatorRuntimeError("transport_header_mismatch")
                authorization_id = str(self.headers.get("X-StegVerse-Authorization-Id") or "").strip()
                if not authorization_id:
                    raise EvaluatorRuntimeError("authorization_id_required")
                length = int(self.headers.get("Content-Length") or "0")
                if length <= 0 or length > MAX_BODY:
                    raise EvaluatorRuntimeError("request_size_invalid")
                body = self.rfile.read(length)
                if str(self.headers.get("X-StegVerse-Payload-SHA256") or "") != raw_sha256(body):
                    raise EvaluatorRuntimeError("request_payload_hash_mismatch")
                request = json.loads(body.decode("utf-8"))
                if not isinstance(request, dict):
                    raise EvaluatorRuntimeError("request_object_required")
                response = process_read_review(
                    request,
                    site_root=args.site_root,
                    stegos_root=args.stegos_root,
                    runtime_root=args.runtime_root,
                    authorization_id=authorization_id,
                    boundary_identity_ref=args.boundary_identity_ref,
                )
                raw = (json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
                self.send_response(200); self._cors()
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers(); self.wfile.write(raw)
                self.server.processed_requests += 1
            except Exception as exc:
                raw = json.dumps({"schema":"stegverse.evaluator-intr-runtime-error/v1","state":"FAIL_CLOSED","reason":str(exc),"authority_effect":"NONE"}).encode("utf-8")
                self.send_response(400); self._cors()
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers(); self.wfile.write(raw)
        def log_message(self, fmt, *values):
            return
    return Handler

class BoundedHTTPServer(HTTPServer):
    processed_requests = 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", type=Path, required=True)
    parser.add_argument("--stegos-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--max-requests", type=int, default=1)
    parser.add_argument("--allowed-origin", default="https://stegverse.org")
    parser.add_argument("--boundary-identity-ref", required=True)
    parser.add_argument("--tls-cert", type=Path)
    parser.add_argument("--tls-key", type=Path)
    args = parser.parse_args()
    _reject_hosted_or_secret_env()
    if args.host not in {"127.0.0.1", "::1", "localhost"} and (not args.tls_cert or not args.tls_key):
        raise EvaluatorRuntimeError("non_loopback_requires_tls")
    server = BoundedHTTPServer((args.host, args.port), make_handler(args))
    if args.tls_cert and args.tls_key:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(args.tls_cert, args.tls_key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    if args.max_requests <= 0:
        server.serve_forever(poll_interval=0.5)
    else:
        while server.processed_requests < args.max_requests:
            server.handle_request()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
