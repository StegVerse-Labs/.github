#!/usr/bin/env python3
"""StegSocials bounded-publication adapter for the shared Universal InTr ingress.

This module owns no listener and grants no publication/provider authority. It
validates one organization-owned Universal InTr request plus its exact local
payload, persists the request write-once, and emits the authentic ingress receipt
only when invoked by the existing sovereign Universal InTr listener.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

PROFILE = "StegSocials:BoundedSocialIngress"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": PROFILE}
DOWNSTREAM_OWNER = "SS-KV-SKAP-SOCIAL-RELEASE-001"
OPERATION_ID = "BOUNDED_SOCIAL_INTR_INGRESS"
REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
PAYLOAD_SCHEMA = "stegverse.stegsocials-bounded-intr-payload/v1"
WORK_SCHEMA = "stegverse.universal-work-interlock/v1"
INTENT_SCHEMA = "stegsocials.bounded-group-intr-execution-intent.v1"
RECEIPT_SCHEMA = "stegverse.stegsocials-bounded-intr-materialization-ingress/v1"
RECEIPT_DIR = Path("receipts/sovereign-network/stegsocials-bounded-intr-ingress")
LATEST = Path("receipts/sovereign-network/stegsocials-bounded-intr-ingress.latest.json")
REQUEST_DIR = Path("intr-materialization")
PAYLOAD_DIR = Path("intr-payloads/stegsocials-bounded-social")
AUTHORITY_EFFECT = "INGRESS_TRANSITION_ONLY"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object_required:{path}")
    return value


def is_stegsocials_bounded(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    request = payload
    entry = payload.get("node_outbox_entry")
    if isinstance(entry, dict) and isinstance(entry.get("materialization_request"), dict):
        request = entry["materialization_request"]
    return (
        request.get("operation_id") == OPERATION_ID
        and request.get("destination") == DESTINATION
        and request.get("downstream_owner_ref") == DOWNSTREAM_OWNER
    )


def validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema": REQUEST_SCHEMA,
        "state": REQUEST_STATE,
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "operation_id": OPERATION_ID,
        "destination": DESTINATION,
        "boundary_path": ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"],
        "downstream_owner_ref": DOWNSTREAM_OWNER,
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "exact_packet_transport_retry_allowed": True,
        "blind_consequence_retry_allowed": False,
        "interlock_required": True,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "transport_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_transfer": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        require(request.get(key) == wanted, f"stegsocials_{key}_mismatch")
    materialization_id = request.get("materialization_id")
    require(isinstance(materialization_id, str) and materialization_id.startswith("INTR-MAT-") and len(materialization_id) == 33, "materialization_id_invalid")
    require(all(ch in "0123456789abcdef" for ch in materialization_id[9:]), "materialization_id_invalid")
    packet_id = request.get("packet_id")
    require(isinstance(packet_id, str) and packet_id.startswith("SS-INTR-") and len(packet_id) == 32, "packet_id_invalid")
    for key in ("transport_intent_hash", "payload_hash", "request_hash"):
        value = request.get(key)
        require(isinstance(value, str) and value.startswith("sha256:") and len(value) == 71, f"{key}_invalid")
    payload_ref = request.get("payload_ref")
    expected_ref = f"runtime://intr-payloads/stegsocials-bounded-social/{materialization_id}.json"
    require(payload_ref == expected_ref, "payload_ref_invalid")
    body = dict(request)
    claimed = body.pop("request_hash")
    require(claimed == sha_uri(body), "request_hash_mismatch")


def validate_payload(payload: Mapping[str, Any], request: Mapping[str, Any]) -> dict[str, Any]:
    require(payload.get("schema") == PAYLOAD_SCHEMA, "payload_schema_invalid")
    require(payload.get("goal_task_id") == DOWNSTREAM_OWNER, "payload_task_mismatch")
    require(payload.get("runtime_admission_observed") is False and payload.get("admission_receipt_ref") is None, "payload_pre_admission_boundary_invalid")
    require(payload.get("credential_material_present") is False and payload.get("provider_operation_authorized") is False, "payload_credential_provider_boundary_invalid")
    require(payload.get("request_grants_execution_authority") is False, "payload_execution_authority_forbidden")
    require(payload.get("authority_effect") == "NONE_PAYLOAD_ONLY", "payload_authority_effect_invalid")
    require(sha_uri(payload) == request.get("payload_hash"), "payload_hash_mismatch")
    record = payload.get("universal_work_interlock_received")
    require(isinstance(record, dict) and record.get("schema") == WORK_SCHEMA, "work_record_invalid")
    require(record.get("direction") == "INGRESS" and record.get("state") == "RECEIVED", "work_record_not_received")
    require(record.get("next_owner") == "INTERLOCK_INTR", "work_record_next_owner_invalid")
    require(record.get("admission_receipt_ref") is None and record.get("runtime_admission_observed") is False, "work_record_synthetic_admission_forbidden")
    authority = record.get("authority")
    require(isinstance(authority, dict), "work_authority_required")
    require(authority.get("credential_authority") == "TV/TVC" and authority.get("github_token_runtime_authority") == "NONE", "work_authority_drift")
    require(authority.get("heartbeat_granted_authority") is False and authority.get("interlock_self_grants_authority") is False and authority.get("intr_self_grants_authority") is False, "work_self_authority_drift")
    intent = record.get("bounded_social_intent")
    require(isinstance(intent, dict) and intent.get("schema") == INTENT_SCHEMA, "bounded_intent_invalid")
    require(intent.get("task_id") == DOWNSTREAM_OWNER, "bounded_intent_task_mismatch")
    require(intent.get("stable_work_id") == payload.get("work_id") == record.get("work_id"), "work_id_binding_mismatch")
    require(intent.get("correlation_id") == payload.get("correlation_id") == record.get("correlation_id"), "correlation_binding_mismatch")
    require(intent.get("group_id") == payload.get("group_id") and intent.get("use_index") == payload.get("use_index"), "group_use_binding_mismatch")
    require(intent.get("participant_approval_receipt_ref") == payload.get("participant_approval_receipt_ref"), "approval_binding_mismatch")
    require(intent.get("state_ref") == payload.get("state_ref"), "state_ref_binding_mismatch")
    require(intent.get("content_ref") == payload.get("content_ref") and intent.get("content_hash") == payload.get("content_hash"), "content_binding_mismatch")
    require(intent.get("platform") == payload.get("platform") and intent.get("account_ref") == payload.get("account_ref"), "target_binding_mismatch")
    require(intent.get("intr_admission_receipt_ref") is None and intent.get("tv_tvc_skap_session_receipt_ref") is None, "synthetic_runtime_receipt_forbidden")
    require(intent.get("request_grants_execution_authority") is False and intent.get("provider_operation_authorized") is False, "bounded_intent_authority_forbidden")
    require(intent.get("secret_material_present") is False and intent.get("raw_credential_material") is None, "bounded_intent_secret_forbidden")
    return dict(intent)


def _write_once(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == raw, "write_once_collision")
        return
    path.write_bytes(raw)


def admit(*, runtime_root: Path, body: bytes, headers: Mapping[str, str], transport_validator) -> dict[str, Any]:
    transport = transport_validator(headers, body)
    try:
        incoming = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError("request_json_invalid") from exc
    require(isinstance(incoming, dict), "request_object_required")
    request: Mapping[str, Any] = incoming
    source: dict[str, Any] = {"node_id": None, "interlock_id": None, "outbox_entry_hash": None}
    if isinstance(incoming.get("node_outbox_entry"), dict):
        entry = incoming["node_outbox_entry"]
        require(isinstance(entry.get("materialization_request"), dict), "node_outbox_materialization_request_required")
        request = entry["materialization_request"]
        source = {
            "node_id": entry.get("node_id"),
            "interlock_id": entry.get("interlock_id"),
            "outbox_entry_hash": entry.get("outbox_entry_hash"),
        }
    validate_request(request)
    runtime = runtime_root.expanduser().resolve()
    payload_path = runtime / PAYLOAD_DIR / f"{request['materialization_id']}.json"
    require(payload_path.is_file(), "payload_not_materialized")
    payload = load_object(payload_path)
    intent = validate_payload(payload, request)

    materialization_id = str(request["materialization_id"])
    request_path = runtime / REQUEST_DIR / f"{materialization_id}.json"
    request_raw = json.dumps(dict(request), sort_keys=True, indent=2).encode("utf-8") + b"\n"
    _write_once(request_path, request_raw)
    receipt_path = runtime / RECEIPT_DIR / f"{materialization_id}.json"
    if receipt_path.exists():
        existing = load_object(receipt_path)
        require(existing.get("request_hash") == request.get("request_hash") and existing.get("state") == "INGRESS_ADMITTED", "write_once_collision")
        return existing

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "operation_id": OPERATION_ID,
        "packet_id": request["packet_id"],
        "work_id": payload["work_id"],
        "correlation_id": payload["correlation_id"],
        "group_id": payload["group_id"],
        "use_index": payload["use_index"],
        "platform": payload["platform"],
        "account_ref": payload["account_ref"],
        "content_hash": payload["content_hash"],
        "participant_approval_receipt_ref": payload["participant_approval_receipt_ref"],
        "state_ref": payload["state_ref"],
        "transport_origin": transport.get("origin"),
        "transport_authorization_id": transport.get("authorization_id"),
        "transport_payload_sha256": transport.get("payload_sha256"),
        "node_id": source.get("node_id"),
        "interlock_id": source.get("interlock_id"),
        "outbox_entry_hash": source.get("outbox_entry_hash"),
        "queue_ref": str(request_path),
        "payload_ref": str(payload_path),
        "exact_request_validated": True,
        "exact_payload_validated": True,
        "write_once_persisted": True,
        "event_ephemeral_execution": True,
        "persistent_runtime_required": False,
        "always_on_receiver_required": False,
        "runtime_execution_attempted": False,
        "provider_operation_authorized": False,
        "credential_material_present": False,
        "claim_or_fence_minted": False,
        "heartbeat_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "admission_grants_publication_authority": False,
        "next_owner": "TV/TVC_SKAP_SESSION_MATERIALIZATION",
        "authority_effect": AUTHORITY_EFFECT,
        "admitted_at": now(),
    }
    receipt["receipt_hash"] = sha_uri(receipt)
    raw = json.dumps(receipt, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    _write_once(receipt_path, raw)
    latest = runtime / LATEST
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_bytes(raw)
    return receipt


__all__ = ["PROFILE", "DESTINATION", "DOWNSTREAM_OWNER", "RECEIPT_SCHEMA", "is_stegsocials_bounded", "validate_request", "validate_payload", "admit"]
