#!/usr/bin/env python3
"""Serve the exact canonical Bootstrap v1 bundle over Universal Interlock/InTr.

This is a bounded transport surface. It does not fetch source, build packages,
admit execution, activate release state, or transfer authority.
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
from typing import Any, Mapping

POLICY_ID = "STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001"
TRANSPORT_PROFILE = "stegverse.universal-intr.adjacent-hop/v1"
REQUEST_SCHEMA = "stegverse.bootstrap.bundle-delivery-request/v1"
RESPONSE_SCHEMA = "stegverse.bootstrap.bundle-delivery-response/v1"
BUNDLE_SCHEMA = "stegverse.bootstrap.bundle/v1"
BUNDLE_VERSION = "1.0.0-rc.1"
DEFAULT_BUNDLE_STATE = Path.home() / ".stegverse" / "state" / "bootstrap-v1-distributable-bundle"
HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL",
    "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "TVC_EPHEMERAL_GITHUB_TOKEN", "HF_TOKEN", "HUGGINGFACE_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "OAUTH_TOKEN",
)
MAX_REQUEST_BODY = 64 * 1024


class BundleDeliveryError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_uri(value: Any) -> str:
    if isinstance(value, bytes):
        raw = value
    else:
        raw = canonical_bytes(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def reject_hosted_or_credentials() -> None:
    hosted = [name for name in HOSTED_ENV if truthy(os.getenv(name))]
    if hosted:
        raise BundleDeliveryError("hosted_runtime_forbidden:" + ",".join(sorted(hosted)))
    credentials = [name for name in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(name))]
    if credentials:
        raise BundleDeliveryError(
            "credential_environment_forbidden:" + ",".join(sorted(credentials))
        )


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise BundleDeliveryError(f"required_local_object_missing:{path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BundleDeliveryError(f"json_object_required:{path}")
    return value


def bundle_body(bundle: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in bundle.items() if key != "bundle_identity"}


def validate_bundle_state(bundle_state_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    root = bundle_state_root.expanduser().resolve()
    bundle = load_json(root / "bundle" / "bootstrap-v1-1.0.0-rc.1.bundle.json")
    receipt = load_json(root / "receipts" / "latest.json")

    if bundle.get("schema") != BUNDLE_SCHEMA or bundle.get("bundle_version") != BUNDLE_VERSION:
        raise BundleDeliveryError("canonical_bundle_schema_or_version_mismatch")
    if bundle.get("state") != "BUILT" or bundle.get("component_count") != 4:
        raise BundleDeliveryError("canonical_bundle_not_built")
    claimed_identity = bundle.get("bundle_identity")
    actual_identity = "sha256:" + digest(bundle_body(bundle))
    if claimed_identity != actual_identity:
        raise BundleDeliveryError("canonical_bundle_identity_mismatch")
    required_bundle = {
        "github_platform_required": False,
        "specific_external_platform_required": False,
        "network_locator_required": False,
        "transport_implementation_required": False,
        "credential_required": False,
        "bundle_integrity_confers_execution_authority": False,
        "release_activated": False,
        "publication_performed": False,
        "execution_authority": "NONE",
        "authority_effect": "NONE_BUNDLE_BUILD_ONLY",
    }
    for key, wanted in required_bundle.items():
        if bundle.get(key) != wanted:
            raise BundleDeliveryError(f"canonical_bundle_authority_mismatch:{key}")

    required_receipt = {
        "schema": "stegverse.bootstrap.distributable-bundle-build-receipt/v1",
        "state": "COMPLETE",
        "transition_id": "BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_BUILT",
        "bundle_version": BUNDLE_VERSION,
        "bundle_identity": claimed_identity,
        "component_count": 4,
        "github_platform_required": False,
        "network_access_performed": False,
        "credential_used": False,
        "repository_writeback_performed": False,
        "release_activated": False,
        "publication_performed": False,
        "execution_authority": "NONE",
    }
    for key, wanted in required_receipt.items():
        if receipt.get(key) != wanted:
            raise BundleDeliveryError(f"bundle_build_receipt_mismatch:{key}")
    return bundle, receipt


def validate_request(value: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "schema": REQUEST_SCHEMA,
        "bundle_version": BUNDLE_VERSION,
        "request_grants_execution_authority": False,
        "credential_required": False,
        "github_platform_required": False,
        "authority_effect": "NONE",
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise BundleDeliveryError(f"delivery_request_mismatch:{key}")
    for key in ("request_id", "node_id", "device_continuity_id", "request_nonce"):
        item = value.get(key)
        if not isinstance(item, str) or not item.strip():
            raise BundleDeliveryError(f"delivery_request_field_required:{key}")
    if len(value["request_id"]) > 160 or len(value["request_nonce"]) > 160:
        raise BundleDeliveryError("delivery_request_identifier_too_long")
    return dict(value)


def load_intr(stegos_root: Path):
    root = stegos_root.expanduser().resolve()
    module = root / "stegos" / "universal_intr_transport.py"
    if not module.is_file():
        raise BundleDeliveryError(f"universal_intr_source_missing:{root}")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from stegos.universal_intr_transport import (  # type: ignore
        build_hop_receipt,
        build_transport_intent,
        validate_receipt_chain,
        validate_transport_intent,
    )
    return build_transport_intent, build_hop_receipt, validate_transport_intent, validate_receipt_chain


def write_once(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(dict(value), indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") == serialized:
            return
        raise BundleDeliveryError(f"write_once_collision:{path}")
    path.write_text(serialized, encoding="utf-8")


def process_delivery(
    request: Mapping[str, Any],
    *,
    bundle_state_root: Path,
    stegos_root: Path,
    runtime_root: Path,
    boundary_identity_ref: str,
) -> dict[str, Any]:
    request = validate_request(request)
    bundle, build_receipt = validate_bundle_state(bundle_state_root)
    build_transport_intent, build_hop_receipt, validate_transport_intent, validate_receipt_chain = load_intr(stegos_root)

    request_payload_hash = sha256_uri(request)
    request_intent = build_transport_intent(
        operation_id="BOOTSTRAP_V1_BUNDLE_REQUEST:" + request["request_id"],
        payload_hash=request_payload_hash,
        source_boundary="DEVICE_SYSTEM",
        source_subsystem="ESTABLISHED_BROWSER_NODE",
        destination_boundary="STEGOS_ECOSYSTEM",
        destination_subsystem="BOOTSTRAP_V1_BUNDLE_CUSTODY",
        prior_transport_receipt_hash=None,
    )
    validate_transport_intent(request_intent)
    request_ingress = build_hop_receipt(
        request_intent,
        hop_index=1,
        receipt_id="BOOTSTRAP-IN-" + request_intent["packet_id"][5:],
        boundary_identity_ref=boundary_identity_ref,
        recorded_at=now_iso(),
        prior_receipt_hash=None,
        transition_state="RECEIVED",
    )
    validate_receipt_chain(request_intent, [request_ingress])

    bundle_payload_hash = sha256_uri(bundle)
    response_intent = build_transport_intent(
        operation_id="BOOTSTRAP_V1_BUNDLE_RESPONSE:" + request["request_id"],
        payload_hash=bundle_payload_hash,
        source_boundary="STEGOS_ECOSYSTEM",
        source_subsystem="BOOTSTRAP_V1_BUNDLE_CUSTODY",
        destination_boundary="DEVICE_SYSTEM",
        destination_subsystem="ESTABLISHED_BROWSER_NODE",
        prior_transport_receipt_hash=request_ingress["receipt_hash"],
    )
    validate_transport_intent(response_intent)
    response_egress = build_hop_receipt(
        response_intent,
        hop_index=1,
        receipt_id="BOOTSTRAP-OUT-" + response_intent["packet_id"][5:],
        boundary_identity_ref=boundary_identity_ref,
        recorded_at=now_iso(),
        prior_receipt_hash=request_ingress["receipt_hash"],
        transition_state="FORWARDED",
    )
    validate_receipt_chain(response_intent, [response_egress])

    response = {
        "schema": RESPONSE_SCHEMA,
        "state": "DELIVERED_UNADMITTED",
        "request_id": request["request_id"],
        "node_id": request["node_id"],
        "device_continuity_id": request["device_continuity_id"],
        "bundle_version": BUNDLE_VERSION,
        "bundle_identity": bundle["bundle_identity"],
        "bundle": bundle,
        "bundle_build_receipt_sha256": sha256_uri(build_receipt),
        "request_payload_sha256": request_payload_hash,
        "bundle_payload_sha256": bundle_payload_hash,
        "transport_profile": TRANSPORT_PROFILE,
        "universal_intr_policy_id": POLICY_ID,
        "canonical_protocol_adopted": True,
        "interlock_required_per_hop": True,
        "receipt_hash_chain_required": True,
        "request_transport_intent": request_intent,
        "request_ingress_receipt": request_ingress,
        "response_transport_intent": response_intent,
        "response_egress_receipt": response_egress,
        "credential_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "runtime_activation_claimed": False,
        "production_interlock_runtime_activated": False,
        "execution_authority": "NONE",
        "release_activated": False,
        "publication_performed": False,
        "authority_effect": "NONE_BUNDLE_DELIVERY_ONLY",
    }

    durable = {
        "schema": "stegverse.bootstrap.bundle-delivery-runtime-receipt/v1",
        "state": "DELIVERY_FORWARDED",
        "transition_id": "BOOTSTRAP_V1_INTR_BUNDLE_DELIVERY_OBSERVED",
        "request_id": request["request_id"],
        "node_id": request["node_id"],
        "device_continuity_id": request["device_continuity_id"],
        "bundle_identity": bundle["bundle_identity"],
        "request_payload_sha256": request_payload_hash,
        "bundle_payload_sha256": bundle_payload_hash,
        "request_ingress_receipt": request_ingress,
        "response_egress_receipt": response_egress,
        "transport_profile": TRANSPORT_PROFILE,
        "universal_intr_policy_id": POLICY_ID,
        "canonical_protocol_adopted": True,
        "runtime_activation_claimed": False,
        "production_interlock_runtime_activated": False,
        "credential_used": False,
        "github_token_used": False,
        "network_source_fetch_performed": False,
        "repository_writeback_performed": False,
        "package_execution_performed": False,
        "sdk_admitted": False,
        "release_activated": False,
        "publication_performed": False,
        "execution_authority": "NONE",
        "authority_effect": "NONE_BUNDLE_DELIVERY_ONLY",
        "recorded_at": now_iso(),
    }
    safe_id = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in request["request_id"])
    write_once(
        runtime_root.expanduser().resolve()
        / "receipts" / "sovereign-network" / "bootstrap-v1-intr" / f"{safe_id}.json",
        durable,
    )
    return response


def make_handler(args):
    class Handler(BaseHTTPRequestHandler):
        server_version = "StegVerseBootstrapV1InTr/1"

        def _cors(self) -> None:
            origin = self.headers.get("Origin")
            if origin == args.allowed_origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")

        def _write_json(self, status: int, value: Mapping[str, Any]) -> None:
            raw = canonical_bytes(dict(value)) + b"\n"
            self.send_response(status)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            if self.path != "/intr/bootstrap-v1/readiness":
                self.send_response(404)
                self.end_headers()
                return
            try:
                bundle, _ = validate_bundle_state(args.bundle_state_root)
                self._write_json(200, {
                    "schema": "stegverse.bootstrap.bundle-delivery-readiness/v1",
                    "state": "READY",
                    "transport": "InTr",
                    "transport_profile": TRANSPORT_PROFILE,
                    "universal_intr_policy_id": POLICY_ID,
                    "bundle_version": BUNDLE_VERSION,
                    "bundle_identity": bundle["bundle_identity"],
                    "credential_required": False,
                    "credential_authority": "TV/TVC",
                    "github_token_runtime_authority": "NONE",
                    "execution_authority": "NONE",
                    "authority_effect": "NONE_READINESS_ONLY",
                })
            except Exception as exc:
                self._write_json(503, {
                    "schema": "stegverse.bootstrap.bundle-delivery-error/v1",
                    "state": "FAIL_CLOSED",
                    "reason": str(exc),
                    "authority_effect": "NONE",
                })

        def do_OPTIONS(self) -> None:
            if self.headers.get("Origin") != args.allowed_origin:
                self.send_response(403)
                self.end_headers()
                return
            self.send_response(204)
            self._cors()
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header(
                "Access-Control-Allow-Headers",
                "content-type,x-stegverse-transport,x-stegverse-payload-sha256",
            )
            self.end_headers()

        def do_POST(self) -> None:
            if self.path != "/intr/bootstrap-v1/bundle":
                self.send_response(404)
                self.end_headers()
                return
            try:
                if self.headers.get("Origin") != args.allowed_origin:
                    raise BundleDeliveryError("origin_not_admitted")
                if self.headers.get("X-StegVerse-Transport") != "InTr":
                    raise BundleDeliveryError("transport_header_mismatch")
                length = int(self.headers.get("Content-Length") or "0")
                if length <= 0 or length > MAX_REQUEST_BODY:
                    raise BundleDeliveryError("request_size_invalid")
                body = self.rfile.read(length)
                claimed_hash = str(self.headers.get("X-StegVerse-Payload-SHA256") or "")
                if claimed_hash != hashlib.sha256(body).hexdigest():
                    raise BundleDeliveryError("request_payload_hash_mismatch")
                request = json.loads(body.decode("utf-8"))
                if not isinstance(request, dict):
                    raise BundleDeliveryError("request_object_required")
                response = process_delivery(
                    request,
                    bundle_state_root=args.bundle_state_root,
                    stegos_root=args.stegos_root,
                    runtime_root=args.runtime_root,
                    boundary_identity_ref=args.boundary_identity_ref,
                )
                self._write_json(200, response)
                self.server.processed_requests += 1
            except Exception as exc:
                self._write_json(400, {
                    "schema": "stegverse.bootstrap.bundle-delivery-error/v1",
                    "state": "FAIL_CLOSED",
                    "reason": str(exc),
                    "authority_effect": "NONE",
                })

        def log_message(self, fmt, *values):
            return

    return Handler


class BoundedHTTPServer(HTTPServer):
    processed_requests = 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stegos-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--bundle-state-root", type=Path, default=DEFAULT_BUNDLE_STATE)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8781)
    parser.add_argument("--max-requests", type=int, default=1)
    parser.add_argument("--allowed-origin", default="https://stegverse.org")
    parser.add_argument("--boundary-identity-ref", required=True)
    parser.add_argument("--tls-cert", type=Path)
    parser.add_argument("--tls-key", type=Path)
    args = parser.parse_args()

    reject_hosted_or_credentials()
    validate_bundle_state(args.bundle_state_root)
    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        if not args.tls_cert or not args.tls_key:
            raise BundleDeliveryError("non_loopback_requires_tls")
        if not args.tls_cert.is_file() or not args.tls_key.is_file():
            raise BundleDeliveryError("non_loopback_tls_material_missing")

    server = BoundedHTTPServer((args.host, args.port), make_handler(args))
    if args.tls_cert and args.tls_key:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(args.tls_cert, args.tls_key)
        server.socket = context.wrap_socket(server.socket, server_side=True)

    if args.max_requests <= 0:
        server.serve_forever(poll_interval=0.5)
        return 0
    while server.processed_requests < args.max_requests:
        server.handle_request()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
