#!/usr/bin/env python3
"""Bounded far-side ingress for HIL Universal InTr materialization requests.

This service is an event-ephemeral transport endpoint. It proves only that the
exact validated materialization request was admitted into the deployment-local
``intr-materialization`` queue. It does not execute the HIL task, mint a claim or
fence, grant custody, or create review/publication authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import ssl
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

from consume_hil_intr_materialization_request import validate_request

MAX_REQUEST_BYTES = 512 * 1024
INGRESS_PATH = "/intr/materialization"
REQUEST_DIR_REL = Path("intr-materialization")
RECEIPT_DIR_REL = Path("receipts/sovereign-network/hil-intr-ingress")
LATEST_REL = Path("receipts/sovereign-network/hil-intr-ingress.latest.json")
RECEIPT_SCHEMA = "stegverse.hil-intr-materialization-ingress/v1"
CREDENTIAL_AUTHORITY = "TV/TVC"
AUTHORITY_EFFECT = "NONE_INGRESS_ONLY"


class HILInTrIngressError(ValueError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise HILInTrIngressError(reason)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_id(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in value)[:160]
    _require(bool(safe), "materialization_id_invalid")
    return safe


def validate_transport_headers(headers: Mapping[str, str], body: bytes) -> dict[str, str]:
    _require(len(body) <= MAX_REQUEST_BYTES, "request_body_too_large")
    transport = str(headers.get("X-StegVerse-Transport", ""))
    authorization_id = str(headers.get("X-StegVerse-Authorization-Id", ""))
    supplied_hash = str(headers.get("X-StegVerse-Payload-SHA256", "")).lower()
    content_type = str(headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
    _require(transport == "InTr", "transport_header_mismatch")
    _require(bool(authorization_id), "authorization_id_header_required")
    _require(content_type in {"application/octet-stream", "application/json"}, "content_type_not_supported")
    _require(len(supplied_hash) == 64 and all(ch in "0123456789abcdef" for ch in supplied_hash), "payload_sha256_header_invalid")
    _require(supplied_hash == _sha256(body), "payload_sha256_header_mismatch")
    return {
        "transport": transport,
        "authorization_id": authorization_id,
        "payload_sha256": supplied_hash,
    }


def _write_once(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _require(path.read_bytes() == raw, "write_once_collision")
        return
    path.write_bytes(raw)
    _require(path.read_bytes() == raw, "persistence_verification_failed")


def admit_materialization(
    *, runtime_root: Path, body: bytes, headers: Mapping[str, str]
) -> dict[str, Any]:
    transport = validate_transport_headers(headers, body)
    try:
        request = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HILInTrIngressError("request_json_invalid") from exc
    _require(isinstance(request, dict), "request_object_required")
    validate_request(request)

    materialization_id = str(request["materialization_id"])
    safe_id = _safe_id(materialization_id)
    request_path = runtime_root / REQUEST_DIR_REL / f"{safe_id}.json"
    canonical_request = json.dumps(request, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    _write_once(request_path, canonical_request)

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "transport_authorization_id": transport["authorization_id"],
        "transport_payload_sha256": transport["payload_sha256"],
        "queue_ref": str(request_path),
        "exact_request_validated": True,
        "write_once_persisted": True,
        "runtime_execution_attempted": False,
        "receiver_readiness_claimed": False,
        "hil_custody_claimed": False,
        "claim_or_fence_minted": False,
        "g18_required": False,
        "credential_authority": CREDENTIAL_AUTHORITY,
        "github_token_runtime_authority": "NONE",
        "authority_effect": AUTHORITY_EFFECT,
        "admitted_at": _utc_now(),
    }
    receipt_raw = json.dumps(receipt, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    receipt_path = runtime_root / RECEIPT_DIR_REL / f"{safe_id}.json"
    _write_once(receipt_path, receipt_raw)
    latest = runtime_root / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_bytes(receipt_raw)
    return receipt


class IngressServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], runtime_root: Path, max_requests: int):
        super().__init__(address, IngressHandler)
        self.runtime_root = runtime_root
        self.max_requests = max_requests
        self.handled_requests = 0


class IngressHandler(BaseHTTPRequestHandler):
    server: IngressServer

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _json(self, status: int, value: Mapping[str, Any]) -> None:
        raw = json.dumps(dict(value), sort_keys=True).encode("utf-8") + b"\n"
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != INGRESS_PATH:
            self._json(404, {"state": "NOT_FOUND", "authority_effect": AUTHORITY_EFFECT})
            return
        length_text = self.headers.get("Content-Length", "")
        try:
            length = int(length_text)
        except ValueError:
            self._json(411, {"state": "REJECTED", "reason": "content_length_invalid", "authority_effect": AUTHORITY_EFFECT})
            return
        if length < 0 or length > MAX_REQUEST_BYTES:
            self._json(413, {"state": "REJECTED", "reason": "request_body_too_large", "authority_effect": AUTHORITY_EFFECT})
            return
        body = self.rfile.read(length)
        try:
            receipt = admit_materialization(runtime_root=self.server.runtime_root, body=body, headers=self.headers)
        except Exception as exc:
            self._json(400, {"state": "REJECTED", "reason": str(exc), "authority_effect": AUTHORITY_EFFECT})
            return
        self.server.handled_requests += 1
        self._json(202, receipt)
        if self.server.max_requests and self.server.handled_requests >= self.server.max_requests:
            self.close_connection = True


def serve(
    *, runtime_root: Path, bind_host: str, bind_port: int, max_requests: int,
    tls_cert: Path | None = None, tls_key: Path | None = None,
) -> tuple[str, int]:
    runtime = runtime_root.expanduser().resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    server = IngressServer((bind_host, bind_port), runtime, max_requests)
    if tls_cert or tls_key:
        _require(tls_cert is not None and tls_key is not None, "tls_cert_and_key_required_together")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(tls_cert), str(tls_key))
        server.socket = context.wrap_socket(server.socket, server_side=True)
    elif bind_host not in {"127.0.0.1", "::1", "localhost"}:
        server.server_close()
        raise HILInTrIngressError("non_loopback_ingress_requires_tls")

    bound = server.server_address
    try:
        while not max_requests or server.handled_requests < max_requests:
            server.handle_request()
    finally:
        server.server_close()
    return str(bound[0]), int(bound[1])


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve bounded HIL Universal InTr materialization ingress.")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--bind-host", default="127.0.0.1")
    parser.add_argument("--bind-port", type=int, default=0)
    parser.add_argument("--max-requests", type=int, default=1)
    parser.add_argument("--tls-cert", type=Path)
    parser.add_argument("--tls-key", type=Path)
    args = parser.parse_args()
    if args.max_requests < 0:
        raise SystemExit("max_requests_must_be_nonnegative")
    host, port = serve(
        runtime_root=args.runtime_root,
        bind_host=args.bind_host,
        bind_port=args.bind_port,
        max_requests=args.max_requests,
        tls_cert=args.tls_cert,
        tls_key=args.tls_key,
    )
    print(json.dumps({
        "schema": "stegverse.hil-intr-materialization-ingress-listener/v1",
        "state": "STOPPED_AFTER_BOUND",
        "bound_host": host,
        "bound_port": port,
        "credential_authority": CREDENTIAL_AUTHORITY,
        "github_token_runtime_authority": "NONE",
        "authority_effect": AUTHORITY_EFFECT,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
