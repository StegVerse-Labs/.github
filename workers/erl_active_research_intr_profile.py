#!/usr/bin/env python3
"""ERL active-research profile for the existing shared Universal InTr ingress.

This module is not a listener or execution owner. It validates one exact ERL
active-research binding, records the two boundary transitions that are directly
observed by the shared resident ingress path, and projects the terminal
DEVICE_SYSTEM -> KV materialization request onto the existing DEVICE_KV owner.
It never grants authority and never treats generated/fixture receipts as runtime
proof.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

BINDING_SCHEMA = "stegverse.erl.active-research-intr-binding/v1"
ENVELOPE_SCHEMA = "stegverse.erl.active-research-acquisition-envelope/v1"
INTENT_SCHEMA = "stegverse.universal-intr-transport/v1"
REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
RECEIPT_SCHEMA = "stegverse.intr.hop_receipt/v1"
FULL_PATH = ["EXTERNAL_SYSTEM", "STEGOS_ECOSYSTEM", "DEVICE_SYSTEM", "KV"]
TERMINAL_PATH = ["DEVICE_SYSTEM", "KV"]
TERMINAL_DESTINATION = {"boundary": "KV", "subsystem": "KnowledgeVault:Interlock"}
TERMINAL_OWNER = "StegVerse-Labs/continuity-vault-kit#79"
ERL_RECEIPT_DIR = Path("receipts/sovereign-network/erl-active-research-intr")
ERL_LATEST = Path("receipts/sovereign-network/erl-active-research-intr.latest.json")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, (bytes, bytearray)) else canonical(value)
    return "sha256:" + hashlib.sha256(bytes(raw)).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _receipt(*, intent: Mapping[str, Any], hop_index: int, prior: str | None, boundary_identity_ref: str, transition_state: str) -> dict[str, Any]:
    path = list(intent["boundary_path"])
    body = {
        "schema": RECEIPT_SCHEMA,
        "receipt_id": f"ERL-ACTIVE-{intent['packet_id']}-{hop_index}",
        "packet_id": intent["packet_id"],
        "hop_index": hop_index,
        "direction": "FORWARD",
        "from_role": path[hop_index - 1],
        "to_role": path[hop_index],
        "operation_hash": sha_uri({"operation_id": intent["operation_id"], "packet_id": intent["packet_id"], "payload_hash": intent["payload_hash"]}),
        "payload_hash": intent["payload_hash"],
        "prior_receipt_hash": prior,
        "boundary_identity_ref": boundary_identity_ref,
        "boundary_verification": "VERIFIED",
        "transition_state": transition_state,
        "secret_plaintext_present": False,
        "authority_transfer": False,
        "recorded_at": now(),
    }
    return {**body, "receipt_hash": sha_uri(body)}


def is_erl_active_research(payload: Any) -> bool:
    return isinstance(payload, dict) and payload.get("schema") == BINDING_SCHEMA


def validate_binding(binding: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    require(binding.get("schema") == BINDING_SCHEMA, "erl_binding_schema_invalid")
    envelope = binding.get("acquisition_envelope")
    intent = binding.get("transport_intent")
    request = binding.get("materialization_request")
    require(isinstance(envelope, dict) and envelope.get("schema") == ENVELOPE_SCHEMA, "erl_envelope_invalid")
    require(isinstance(intent, dict) and intent.get("schema") == INTENT_SCHEMA and intent.get("protocol") == "InTr", "erl_intent_invalid")
    require(isinstance(request, dict) and request.get("schema") == REQUEST_SCHEMA, "erl_request_invalid")
    envelope_hash = sha_uri(envelope)
    require(binding.get("acquisition_envelope_sha256") == envelope_hash, "erl_envelope_hash_mismatch")
    require(intent.get("payload_hash") == envelope_hash, "erl_intent_payload_hash_mismatch")
    require(intent.get("boundary_path") == FULL_PATH, "erl_boundary_path_invalid")
    require(intent.get("source") == {"boundary": "EXTERNAL_SYSTEM", "subsystem": "ERL:ActiveResearchExternalSource"}, "erl_source_invalid")
    require(intent.get("destination") == {"boundary": "KV", "subsystem": "KnowledgeVault:ERL"}, "erl_destination_invalid")
    require(intent.get("interlock_required") is True, "erl_interlock_required")
    authority = intent.get("authority") or {}
    require(authority.get("authority_transfer") is False and authority.get("transport_grants_execution_authority") is False, "erl_intent_authority_invalid")
    require(authority.get("credential_authority") == "TV/TVC", "erl_credential_authority_invalid")
    for key in ("operation_id", "packet_id", "payload_hash"):
        require(request.get(key) == intent.get(key), "erl_request_binding_mismatch:" + key)
    require(request.get("boundary_path") == FULL_PATH, "erl_request_boundary_path_invalid")
    require(request.get("request_grants_execution_authority") is False, "erl_request_authority_invalid")
    require(request.get("claim_or_fence_minted") is False, "erl_request_claim_invalid")
    require(request.get("authority_transfer") is False, "erl_request_transfer_invalid")
    require(request.get("credential_authority") == "TV/TVC", "erl_request_credential_authority_invalid")
    require(request.get("github_token_runtime_authority") == "NONE", "erl_request_github_authority_invalid")
    require(binding.get("runtime_receipts_present") is False and binding.get("transport_execution_claimed") is False, "erl_source_must_not_claim_runtime")
    return dict(envelope), dict(intent), dict(request)


def _write_once(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(dict(value), indent=2, sort_keys=True) + "\n"
    if path.exists():
        require(path.read_text(encoding="utf-8") == rendered, "erl_write_once_collision")
        return
    path.write_text(rendered, encoding="utf-8")
    require(path.read_text(encoding="utf-8") == rendered, "erl_write_readback_mismatch")


def admit(*, runtime_root: Path, payload: Mapping[str, Any], transport_payload_sha256: str) -> dict[str, Any]:
    envelope, intent, request = validate_binding(payload)
    require(isinstance(transport_payload_sha256, str) and transport_payload_sha256.startswith("sha256:"), "erl_transport_payload_hash_invalid")

    hop1 = _receipt(intent=intent, hop_index=1, prior=intent.get("prior_transport_receipt_hash"), boundary_identity_ref="resident://universal-intr-profiled-ingress", transition_state="FORWARDED")
    hop2 = _receipt(intent=intent, hop_index=2, prior=hop1["receipt_hash"], boundary_identity_ref="resident://device-system-materialization", transition_state="FORWARDED")

    terminal_body = {
        "schema": REQUEST_SCHEMA,
        "materialization_id": request["materialization_id"],
        "state": "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
        "transport_schema": INTENT_SCHEMA,
        "transport_protocol": "InTr",
        "transport_intent_hash": sha_uri(intent),
        "operation_id": intent["operation_id"],
        "packet_id": intent["packet_id"],
        "payload_hash": intent["payload_hash"],
        "payload_ref": request["payload_ref"],
        "destination": TERMINAL_DESTINATION,
        "boundary_path": TERMINAL_PATH,
        "downstream_owner_ref": TERMINAL_OWNER,
        "prior_transport_receipt_hash": hop2["receipt_hash"],
        "erl_full_path": FULL_PATH,
        "erl_upstream_receipt_hashes": [hop1["receipt_hash"], hop2["receipt_hash"]],
        "erl_transport_intent": intent,
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
    terminal = {**terminal_body, "request_hash": sha_uri(terminal_body)}
    evidence = {
        "schema": "stegverse.erl.active-research-intr-profile-admission/v1",
        "state": "PROFILE_ADMITTED_TERMINAL_MATERIALIZATION_PENDING",
        "materialization_id": terminal["materialization_id"],
        "operation_id": intent["operation_id"],
        "packet_id": intent["packet_id"],
        "payload_hash": intent["payload_hash"],
        "transport_payload_sha256": transport_payload_sha256,
        "hop_receipts": [hop1, hop2],
        "terminal_materialization_request": terminal,
        "terminal_runtime_receipt_present": False,
        "provider_operation_reexecution_authorized": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_PROFILE_ADMISSION_ONLY",
    }
    path = runtime_root / ERL_RECEIPT_DIR / f"{terminal['materialization_id']}.json"
    _write_once(path, evidence)
    latest = runtime_root / ERL_LATEST
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence
