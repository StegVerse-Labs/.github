#!/usr/bin/env python3
"""Backward-compatible HIL profile over the shared Universal InTr ingress.

The historic HIL profile schema remains stable for existing probes. POST
/intr/materialization is handled by the shared profiled ingress for HIL/SV002
and additionally admits the SV-DN-1 established-web-bootstrap browser evidence
profile without changing either existing path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from workers import universal_intr_profiled_ingress as shared
from workers import sv_dn1_browser_evidence_intr_ingress as svdn1

PROFILE_PATH = shared.PROFILE_PATH
PROFILE_SCHEMA = "stegverse.hil-intr-materialization-ingress-profile/v1"
PROFILE_AUTHORITY_EFFECT = "NONE_DISCOVERY_EVIDENCE_ONLY"


def build_profile(*, tls_enabled: bool) -> dict[str, Any]:
    return {
        "schema": PROFILE_SCHEMA,
        "state": "ACTIVE_SOVEREIGN_INTR_INGRESS",
        "protocol": "InTr",
        "profile_path": PROFILE_PATH,
        "materialization_path": shared.INGRESS_PATH,
        "supported_origins": [shared.hil.ORIGIN_NODE, shared.hil.ORIGIN_RELAY, svdn1.ORIGIN],
        "direct_node_credential_requirement": "NONE",
        "direct_node_tvc_authorization_required": False,
        "relay_tvc_authorization_required": True,
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "exact_request_validation_required": True,
        "write_once_queue_admission": True,
        "tls_enabled": bool(tls_enabled),
        "public_tls_terminated_by": "STEGVERSE_SHARED_SERVICE_GATEWAY",
        "runtime_execution_attempted": False,
        "hil_receiver_readiness_claimed": False,
        "hil_custody_claimed": False,
        "g18_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "execution_authority": "NONE",
        "additional_materialization_profiles": ["SV002:PublicObservation", svdn1.PROFILE],
        "authority_effect": PROFILE_AUTHORITY_EFFECT,
    }


def _svdn1_transport_headers(headers: Mapping[str, str], body: bytes) -> str:
    if len(body) > shared.hil.MAX_REQUEST_BYTES:
        raise ValueError("request_body_too_large")
    if str(headers.get("X-StegVerse-Transport", "")) != "InTr":
        raise ValueError("transport_header_mismatch")
    if str(headers.get("X-StegVerse-Transport-Origin", "")) != svdn1.ORIGIN:
        raise ValueError("transport_origin_header_invalid")
    if str(headers.get("X-StegVerse-Authorization-Id", "")):
        raise ValueError("web_bootstrap_egress_cannot_claim_tvc_authorization")
    content_type = str(headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        raise ValueError("content_type_not_supported")
    supplied = str(headers.get("X-StegVerse-Payload-SHA256", "")).lower()
    if len(supplied) != 64 or any(ch not in "0123456789abcdef" for ch in supplied):
        raise ValueError("payload_sha256_header_invalid")
    actual = hashlib.sha256(body).hexdigest()
    if supplied != actual:
        raise ValueError("payload_sha256_header_mismatch")
    return actual


class ProfiledIngressHandler(shared.Handler):
    server: "ProfiledIngressServer"

    def do_GET(self) -> None:  # noqa: N802
        if self.path != PROFILE_PATH:
            self.send_json(404, {"state": "NOT_FOUND", "authority_effect": PROFILE_AUTHORITY_EFFECT})
            return
        self.send_json(200, build_profile(tls_enabled=self.server.tls_enabled))

    def do_POST(self) -> None:  # noqa: N802
        if self.path != shared.INGRESS_PATH:
            self.send_json(404, {"state": "NOT_FOUND", "authority_effect": shared.AUTHORITY_EFFECT})
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.send_json(411, {"state": "REJECTED", "reason": "content_length_invalid", "authority_effect": shared.AUTHORITY_EFFECT})
            return
        if length < 0 or length > shared.hil.MAX_REQUEST_BYTES:
            self.send_json(413, {"state": "REJECTED", "reason": "request_body_too_large", "authority_effect": shared.AUTHORITY_EFFECT})
            return
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
            if isinstance(payload, dict) and payload.get("schema") == svdn1.TRANSPORT_SCHEMA:
                transport_sha = _svdn1_transport_headers(self.headers, body)
                receipt = svdn1.admit(runtime_root=self.server.runtime_root, payload=payload, transport_payload_sha256=transport_sha)
            elif shared._is_sv002(payload):
                receipt = shared.admit_sv002(runtime_root=self.server.runtime_root, body=body, headers=self.headers)
            else:
                receipt = shared.hil.admit_materialization(runtime_root=self.server.runtime_root, body=body, headers=self.headers)
        except Exception as exc:
            self.send_json(400, {"state": "REJECTED", "reason": str(exc), "authority_effect": shared.AUTHORITY_EFFECT})
            return
        self.server.handled_requests += 1
        self.send_json(202, receipt)


class ProfiledIngressServer(shared.Server):
    def __init__(self, address: tuple[str, int], runtime_root: Path, max_requests: int):
        super().__init__(address, runtime_root, max_requests)
        self.RequestHandlerClass = ProfiledIngressHandler


def serve(*, runtime_root: Path, bind_host: str, bind_port: int, max_requests: int,
          tls_cert: Path | None = None, tls_key: Path | None = None) -> tuple[str, int]:
    runtime = runtime_root.expanduser().resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    server = ProfiledIngressServer((bind_host, bind_port), runtime, max_requests)
    if tls_cert or tls_key:
        if tls_cert is None or tls_key is None:
            server.server_close()
            raise ValueError("tls_cert_and_key_required_together")
        import ssl
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
    parser = argparse.ArgumentParser(description="Serve profiled sovereign Universal InTr ingress with HIL-compatible discovery.")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--bind-host", default="127.0.0.1")
    parser.add_argument("--bind-port", type=int, default=0)
    parser.add_argument("--max-requests", type=int, default=1)
    parser.add_argument("--tls-cert", type=Path)
    parser.add_argument("--tls-key", type=Path)
    args = parser.parse_args()
    if args.max_requests < 0:
        raise SystemExit("max_requests_must_be_nonnegative")
    host, port = serve(runtime_root=args.runtime_root, bind_host=args.bind_host, bind_port=args.bind_port,
                       max_requests=args.max_requests, tls_cert=args.tls_cert, tls_key=args.tls_key)
    print(json.dumps({
        "schema": "stegverse.hil-intr-profiled-ingress-listener/v1",
        "state": "STOPPED_AFTER_BOUND",
        "bound_host": host,
        "bound_port": port,
        "profile_path": PROFILE_PATH,
        "materialization_path": shared.INGRESS_PATH,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "execution_authority": "NONE",
        "additional_materialization_profiles": ["SV002:PublicObservation", svdn1.PROFILE],
        "authority_effect": PROFILE_AUTHORITY_EFFECT,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
