#!/usr/bin/env python3
"""StegBrowser profile adapter for the existing shared Universal InTr ingress."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import serve_hil_intr_materialization_ingress as hil  # noqa: E402
from workers.stegbrowser_intr_materialization_consumer import (  # noqa: E402
    DESTINATION,
    DOWNSTREAM_OWNER,
    scrubbed_env,
    validate_request,
)

RECEIPT_SCHEMA = "stegverse.stegbrowser-intr-materialization-ingress/v1"
RECEIPT_DIR = Path("receipts/sovereign-network/stegbrowser-intr-ingress")
LATEST_REL = Path("receipts/sovereign-network/stegbrowser-intr-ingress.latest.json")
BINDING_DIR_REL = Path("intr-payloads/stegbrowser-manifest-invocation")
AUTHORITY_EFFECT = "NONE_INGRESS_ONLY"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def is_stegbrowser(payload: Any) -> bool:
    if isinstance(payload, dict) and payload.get("destination") == DESTINATION and payload.get("downstream_owner_ref") == DOWNSTREAM_OWNER:
        return True
    if isinstance(payload, dict):
        entry = payload.get("node_outbox_entry")
        if isinstance(entry, dict):
            request = entry.get("materialization_request")
            return isinstance(request, dict) and request.get("destination") == DESTINATION and request.get("downstream_owner_ref") == DOWNSTREAM_OWNER
    return False


def _request_from_node_trigger(payload: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
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
    entry_body = dict(entry)
    claimed_entry = entry_body.pop("outbox_entry_hash", None)
    require(claimed_entry == sha_uri(entry_body), "node_outbox_entry_hash_mismatch")
    request = entry.get("materialization_request")
    require(isinstance(request, dict), "node_outbox_materialization_request_required")
    validate_request(request)
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "destination", "downstream_owner_ref"):
        require(entry.get(key) == request.get(key), "node_outbox_binding_mismatch:" + key)
    require(payload.get("node_id") == entry.get("node_id") and payload.get("interlock_id") == entry.get("interlock_id") and payload.get("outbox_entry_hash") == entry.get("outbox_entry_hash"), "node_trigger_binding_mismatch")
    trigger_body = dict(payload)
    claimed_trigger = trigger_body.pop("trigger_sha256", None)
    require(claimed_trigger == sha_uri(trigger_body), "node_trigger_hash_mismatch")
    binding = entry.get("stegbrowser_invocation")
    if binding is not None:
        require(isinstance(binding, dict), "stegbrowser_invocation_binding_invalid")
        require(request.get("payload_hash") == sha_uri(binding), "stegbrowser_invocation_binding_payload_hash_mismatch")
        opaque_ref = "opaque://stegbrowser-manifest-invocation/" + str(request["payload_hash"])[7:]
        require(request.get("payload_ref") == opaque_ref, "stegbrowser_invocation_binding_payload_ref_mismatch")
    return dict(request), {
        "node_id": entry.get("node_id"),
        "interlock_id": entry.get("interlock_id"),
        "outbox_entry_hash": entry.get("outbox_entry_hash"),
    }, dict(binding) if isinstance(binding, dict) else None


def _dispatch(*, runtime_root: Path, materialization_id: str) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "workers.stegbrowser_intr_materialization_consumer",
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
        env=scrubbed_env(),
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


def admit(*, runtime_root: Path, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
    transport = hil.validate_transport_headers(headers, body)
    require(transport.get("origin") == hil.ORIGIN_NODE, "stegbrowser_requires_direct_node_origin")
    require(transport.get("authorization_id") is None, "stegbrowser_node_origin_cannot_claim_tvc_authorization")
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError("request_json_invalid") from exc
    request, source, binding = _request_from_node_trigger(payload)
    materialization_id = str(request["materialization_id"])
    binding_path = None
    if binding is not None:
        binding_digest = str(request["payload_hash"])[7:]
        binding_path = runtime_root / BINDING_DIR_REL / f"{binding_digest}.json"
        binding_raw = json.dumps(binding, sort_keys=True, indent=2).encode("utf-8") + b"\n"
        hil._write_once(binding_path, binding_raw)
    request_path = runtime_root / hil.REQUEST_DIR_REL / f"{materialization_id}.json"
    request_raw = json.dumps(request, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    hil._write_once(request_path, request_raw)
    receipt_path = runtime_root / RECEIPT_DIR / f"{materialization_id}.json"
    if receipt_path.exists():
        existing = json.loads(receipt_path.read_text(encoding="utf-8"))
        require(existing.get("request_hash") == request.get("request_hash") and existing.get("state") == "INGRESS_ADMITTED", "write_once_collision")
        return existing
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "transport_origin": hil.ORIGIN_NODE,
        "transport_authorization_id": None,
        "node_id": source["node_id"],
        "interlock_id": source["interlock_id"],
        "outbox_entry_hash": source["outbox_entry_hash"],
        "transport_payload_sha256": transport["payload_sha256"],
        "queue_ref": str(request_path),
        "binding_payload_ref": request["payload_ref"] if binding is not None else None,
        "binding_custody_ref": str(binding_path) if binding_path is not None else None,
        "exact_request_validated": True,
        "write_once_persisted": True,
        "runtime_execution_attempted": False,
        "consumer_dispatch_attempted": False,
        "claim_or_fence_minted": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": AUTHORITY_EFFECT,
    }
    raw = json.dumps(receipt, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    hil._write_once(receipt_path, raw)
    latest = runtime_root / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_bytes(raw)
    dispatch = _dispatch(runtime_root=runtime_root, materialization_id=materialization_id)
    return {**receipt, "dispatch": dispatch}


__all__ = ["DESTINATION", "DOWNSTREAM_OWNER", "RECEIPT_SCHEMA", "admit", "is_stegbrowser"]
