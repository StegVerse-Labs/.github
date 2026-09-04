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
from typing import Any, Mapping

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


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_canonical_work(payload: Any) -> bool:
    return isinstance(payload, dict) and payload.get("destination") == DESTINATION and payload.get("downstream_owner_ref") == DOWNSTREAM_OWNER


def scrubbed_env() -> dict[str, str]:
    import os
    child = dict(os.environ)
    for key in ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS", "GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
        child.pop(key, None)
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    child["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return child


def admit(*, runtime_root: Path, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
    transport = transport_boundary.validate_transport_headers(headers, body)
    try:
        request = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError("request_json_invalid") from exc
    require(isinstance(request, dict), "request_object_required")
    require(is_canonical_work(request), "canonical_work_destination_mismatch")
    validate_request(request)

    materialization_id = str(request["materialization_id"])
    request_path = runtime_root / REQUEST_DIR_REL / f"{materialization_id}.json"
    request_raw = json.dumps(request, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    transport_boundary._write_once(request_path, request_raw)

    receipt_path = runtime_root / RECEIPT_DIR_REL / f"{materialization_id}.json"
    if receipt_path.exists():
        existing = json.loads(receipt_path.read_text(encoding="utf-8"))
        require(existing.get("request_hash") == request.get("request_hash") and existing.get("state") == "INGRESS_ADMITTED", "write_once_collision")
        return existing

    receipt = {
        "schema": INGRESS_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "transport_origin": transport.get("origin"),
        "transport_authorization_id": transport.get("authorization_id"),
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


__all__ = ["DESTINATION", "DOWNSTREAM_OWNER", "INGRESS_SCHEMA", "is_canonical_work", "admit"]
