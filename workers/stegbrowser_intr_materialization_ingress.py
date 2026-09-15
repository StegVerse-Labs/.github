#!/usr/bin/env python3
"""StegBrowser adapter for the existing shared Universal InTr listener.

The adapter reuses the validated StegVerse-002 Node-bound write-once admission
shape. It does not start a listener or mint execution/claim authority.
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
from workers.stegbrowser_intr_materialization_consumer import (  # noqa: E402
    DESTINATION, DOWNSTREAM_OWNER, INGRESS_SCHEMA, scrubbed_env, validate_request,
)

RECEIPT_DIR_REL = Path("receipts/sovereign-network/stegbrowser-intr-ingress")
LATEST_REL = Path("receipts/sovereign-network/stegbrowser-intr-ingress.latest.json")
REQUEST_DIR_REL = Path("intr-materialization")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_stegbrowser(payload: Any) -> bool:
    if isinstance(payload, dict) and payload.get("destination") == DESTINATION and payload.get("downstream_owner_ref") == DOWNSTREAM_OWNER:
        return True
    if isinstance(payload, dict):
        entry = payload.get("node_outbox_entry")
        if isinstance(entry, dict):
            request = entry.get("materialization_request")
            return isinstance(request, dict) and request.get("destination") == DESTINATION and request.get("downstream_owner_ref") == DOWNSTREAM_OWNER
    return False


def _request_from_payload(payload: Any, transport: Mapping[str, str | None]) -> tuple[dict[str, Any], dict[str, Any]]:
    origin = transport["origin"]
    if origin == transport_boundary.ORIGIN_RELAY:
        require(isinstance(payload, dict), "request_object_required")
        validate_request(payload)
        return dict(payload), {
            "transport_origin": origin,
            "transport_authorization_id": transport["authorization_id"],
            "node_id": payload.get("node_id"),
            "interlock_id": payload.get("interlock_id"),
            "outbox_entry_hash": None,
        }

    require(isinstance(payload, dict) and payload.get("schema") == transport_boundary.NODE_TRIGGER_SCHEMA, "node_trigger_schema_invalid")
    require(payload.get("transport_origin") == transport_boundary.ORIGIN_NODE, "node_trigger_origin_invalid")
    require(payload.get("authority_effect") == "NONE_TRIGGER_ONLY", "node_trigger_authority_effect_invalid")
    require(payload.get("request_grants_execution_authority") is False and payload.get("claim_or_fence_minted") is False, "node_trigger_authority_forbidden")
    entry = payload.get("node_outbox_entry")
    require(isinstance(entry, dict), "node_outbox_entry_required")
    require(entry.get("schema") == transport_boundary.NODE_OUTBOX_SCHEMA and entry.get("state") == "LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY", "node_outbox_state_invalid")
    require(entry.get("network_delivery_observed") is False and entry.get("runtime_materialization_observed") is False and entry.get("receiver_receipt_observed") is False and entry.get("tvc_receipt_observed") is False, "node_outbox_promoted_evidence_forbidden")
    require(entry.get("request_grants_execution_authority") is False and entry.get("claim_or_fence_minted") is False, "node_outbox_authority_forbidden")
    require(entry.get("credential_authority") == "TV/TVC" and entry.get("github_token_runtime_authority") == "NONE" and entry.get("authority_effect") == "NONE_LOCAL_CONTINUITY_ONLY", "node_outbox_credential_boundary_invalid")
    body = dict(entry)
    claimed = body.pop("outbox_entry_hash", None)
    require(claimed == transport_boundary._sha256_uri(body), "node_outbox_entry_hash_mismatch")
    request = entry.get("materialization_request")
    require(isinstance(request, dict), "node_outbox_materialization_request_required")
    validate_request(request)
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "destination", "downstream_owner_ref", "node_id", "interlock_id", "registration_receipt_sha256", "manifest_sha256"):
        require(entry.get(key) == request.get(key), "node_outbox_binding_mismatch:" + key)
    require(payload.get("node_id") == entry.get("node_id") and payload.get("interlock_id") == entry.get("interlock_id") and payload.get("outbox_entry_hash") == entry.get("outbox_entry_hash"), "node_trigger_binding_mismatch")
    trigger = dict(payload)
    trigger_claim = trigger.pop("trigger_sha256", None)
    require(trigger_claim == transport_boundary._sha256_uri(trigger), "node_trigger_hash_mismatch")
    return dict(request), {
        "transport_origin": origin,
        "transport_authorization_id": None,
        "node_id": entry.get("node_id"),
        "interlock_id": entry.get("interlock_id"),
        "outbox_entry_hash": entry.get("outbox_entry_hash"),
    }


def admit(*, runtime_root: Path, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
    transport = transport_boundary.validate_transport_headers(headers, body)
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError("request_json_invalid") from exc
    require(is_stegbrowser(payload), "stegbrowser_destination_mismatch")
    request, source = _request_from_payload(payload, transport)
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
        "transport_origin": source["transport_origin"],
        "transport_authorization_id": source["transport_authorization_id"],
        "node_id": source["node_id"],
        "interlock_id": source["interlock_id"],
        "outbox_entry_hash": source["outbox_entry_hash"],
        "registration_receipt_sha256": request["registration_receipt_sha256"],
        "manifest_sha256": request["manifest_sha256"],
        "transport_payload_sha256": transport["payload_sha256"],
        "queue_ref": str(request_path),
        "exact_request_validated": True,
        "write_once_persisted": True,
        "runtime_execution_attempted": False,
        "claim_or_fence_minted": False,
        "round_trip_1_started": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_INGRESS_ONLY",
        "admitted_at": now(),
    }
    raw = json.dumps(receipt, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    transport_boundary._write_once(receipt_path, raw)
    latest = runtime_root / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_bytes(raw)

    process = subprocess.Popen(
        [sys.executable, "-m", "workers.stegbrowser_intr_materialization_consumer", "--source-root", str(ROOT), "--runtime-root", str(runtime_root), "--materialization-id", materialization_id],
        cwd=str(ROOT), env=scrubbed_env(), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True,
    )
    return {**receipt, "dispatch": {
        "consumer_dispatch_attempted": True,
        "consumer_pid": process.pid,
        "consumer_execution_authority": False,
        "consumer_claim_or_fence_minted_by_ingress": False,
        "authority_effect": "NONE_DISPATCH_ONLY",
    }}


__all__ = ["DESTINATION", "DOWNSTREAM_OWNER", "INGRESS_SCHEMA", "is_stegbrowser", "admit"]
