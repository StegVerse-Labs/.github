#!/usr/bin/env python3
"""Backward-compatible HIL profile over the shared Universal InTr ingress.

The historic HIL profile schema remains stable for existing probes. POST
/intr/materialization is now handled by the shared profiled ingress, which
preserves the HIL admission path byte-for-byte and additionally admits the
SV002 public-observation event-materialization profile.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from workers import universal_intr_profiled_ingress as shared

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
        "supported_origins": [shared.hil.ORIGIN_NODE, shared.hil.ORIGIN_RELAY],
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
        "additional_materialization_profiles": ["SV002:PublicObservation"],
        "authority_effect": PROFILE_AUTHORITY_EFFECT,
    }


class ProfiledIngressHandler(shared.Handler):
    server: "ProfiledIngressServer"

    def do_GET(self) -> None:  # noqa: N802
        if self.path != PROFILE_PATH:
            self.send_json(404, {"state": "NOT_FOUND", "authority_effect": PROFILE_AUTHORITY_EFFECT})
            return
        self.send_json(200, build_profile(tls_enabled=self.server.tls_enabled))


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
        "additional_materialization_profiles": ["SV002:PublicObservation"],
        "authority_effect": PROFILE_AUTHORITY_EFFECT,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
