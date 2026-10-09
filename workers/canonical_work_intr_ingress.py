#!/usr/bin/env python3
"""Reusable Canonical Work admission adapter for the existing Universal InTr ingress.

This module does not start a server. The existing Universal InTr ingress owns the
network listener. This adapter validates one CanonicalWork request, persists its
write-once ingress receipt, and dispatches the non-authorizing coordination
consumer. HB32 carrier data is validated as reference/transport evidence only.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, NoReturn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import serve_hil_intr_materialization_ingress as transport_boundary  # noqa: E402
from consume_canonical_work_intr_materialization_request import (  # noqa: E402
    DESTINATION,
    DOWNSTREAM_OWNER,
    validate_request,
)

INGRESS_SCHEMA = "stegverse.canonical-work-intr-materialization-ingress/v1"
RECEIPT_DIR_REL = Path("receipts/sovereign-network/canonical-work-intr-ingress")
LATEST_REL = Path("receipts/sovereign-network/canonical-work-intr-ingress.latest.json")
REQUEST_DIR_REL = Path("intr-materialization")
RELAY_AUTHORIZATION_UNVERIFIABLE = "relay_tvc_authorization_unverifiable:a4_tv_tvc_verifier_absent"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_canonical_work_request(value: Any) -> bool:
    return isinstance(value, dict) and value.get("destination") == DESTINATION and value.get("downstream_owner_ref") == DOWNSTREAM_OWNER


def _envelope_request(payload: Any) -> Any:
    entry = payload.get("node_outbox_entry") if isinstance(payload, dict) else None
    return entry.get("materialization_request") if isinstance(entry, dict) else None


def is_canonical_work(payload: Any) -> bool:
    """Route predicate: an exact CanonicalWork request or a node envelope carrying one."""
    return _is_canonical_work_request(payload) or _is_canonical_work_request(_envelope_request(payload))


def scrubbed_env() -> dict[str, str]:
    import os
    child = dict(os.environ)
    for key in ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS", "GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
        child.pop(key, None)
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    child["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return child


def require_relay_authorization_binding(*, authorization_id: str | None, request_sha256: str) -> NoReturn:
    """Bind a TVC relay authorization id to the exact request digest, or fail closed.

    Binding requires the A4/TV-TVC verification surface. This repository has none
    (org-boundary/runtime/origin_attestation.py is absent; TV_EXPORT_HMAC_VERIFY is
    owned by StegVerse-Labs/tvc), so a supplied id is never self-certified here and
    the relay origin stays unreachable rather than admitted on an unverified claim.
    """
    require(bool(authorization_id), "authorization_id_header_required_for_relay")
    require(len(request_sha256) == 64, "relay_exact_request_digest_invalid")
    raise ValueError(RELAY_AUTHORIZATION_UNVERIFIABLE)


def bound_request(payload: Any, transport: Mapping[str, str | None]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply the origin-specific checks that must hold before ALLOW.

    Node origin: the payload must be a node-trigger/outbox envelope that passes the
    HIL ingress's own envelope validator. Relay origin: the exact request digest
    plus a verified TVC authorization id binding. A carrier binding is never origin.
    """
    origin = transport.get("origin")
    if origin == transport_boundary.ORIGIN_NODE:
        require(_is_canonical_work_request(_envelope_request(payload)), "node_outbox_canonical_work_envelope_required")
        return transport_boundary.extract_materialization(payload, transport, request_validator=validate_request)
    require(origin == transport_boundary.ORIGIN_RELAY, "transport_origin_header_invalid")
    require(isinstance(payload, dict), "request_object_required")
    require(_is_canonical_work_request(payload), "canonical_work_destination_mismatch")
    validate_request(payload)
    require_relay_authorization_binding(authorization_id=transport.get("authorization_id"), request_sha256=str(transport.get("payload_sha256") or ""))


def admit(*, runtime_root: Path, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
    transport = transport_boundary.validate_transport_headers(headers, body)
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError("request_json_invalid") from exc
    request, source = bound_request(payload, transport)

    materialization_id = str(request["materialization_id"])
    request_path = runtime_root / REQUEST_DIR_REL / f"{materialization_id}.json"
    request_raw = json.dumps(request, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    transport_boundary._write_once(request_path, request_raw)

    receipt_path = runtime_root / RECEIPT_DIR_REL / f"{materialization_id}.json"
    if receipt_path.exists():
        existing = json.loads(receipt_path.read_text(encoding="utf-8"))
        require(existing.get("request_hash") == request.get("request_hash") and existing.get("state") == "INGRESS_ADMITTED"
                and existing.get("transport_origin") == source["transport_origin"] and existing.get("outbox_entry_hash") == source["outbox_entry_hash"], "write_once_collision")
        return existing

    receipt = {
        "schema": INGRESS_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "disposition": "ALLOW",
        "disposition_authority": "INTERLOCK_INTR",
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
        "transport_payload_sha256": transport.get("payload_sha256"),
        "queue_ref": str(request_path),
        "exact_request_validated": True,
        "write_once_persisted": True,
        "carrier_binding_present": request.get("carrier_binding") is not None,
        "carrier_binding_grants_authority": False,
        "runtime_execution_attempted": False,
        "claim_or_fence_minted": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "INGRESS_TRANSITION_ONLY",
        "admitted_at": now()
    }
    raw = json.dumps(receipt, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    transport_boundary._write_once(receipt_path, raw)
    latest = runtime_root / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_bytes(raw)

    process = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "scripts" / "consume_canonical_work_intr_materialization_request.py"),
            "--runtime-root",
            str(runtime_root),
            "--materialization-id",
            materialization_id,
        ],
        cwd=str(ROOT),
        env=scrubbed_env(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    return {
        **receipt,
        "dispatch": {
            "consumer_dispatch_attempted": True,
            "consumer_pid": process.pid,
            "consumer_execution_authority": False,
            "consumer_claim_or_fence_minted_by_ingress": False,
            "authority_effect": "NONE_DISPATCH_ONLY"
        }
    }


__all__ = ["DESTINATION", "DOWNSTREAM_OWNER", "INGRESS_SCHEMA", "RELAY_AUTHORIZATION_UNVERIFIABLE", "is_canonical_work", "bound_request", "admit"]
