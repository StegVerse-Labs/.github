#!/usr/bin/env python3
"""KV AI memory profile for the existing shared Universal InTr ingress.

This module validates one exact Personal-KV memory packet submission and emits a
non-authorizing admission receipt only when invoked by the shared ingress. It
performs no model/provider operation, WorkerCoordinator claim/fence, credential
resolution, KV mutation, or writeback.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

TASK_ID = "SV-KV-AI-PERSISTENCE-001"
SUBMISSION_SCHEMA = "stegverse.kv.ai-memory-intr-submission/v1"
PACKET_SCHEMA = "stegverse.kv.ai-memory-context-packet/v1"
RECEIPT_SCHEMA = "stegverse.kv.ai-memory-intr-admission/v1"
RECEIPT_DIR = Path("receipts/sovereign-network/kv-ai-memory-intr")
LATEST = Path("receipts/sovereign-network/kv-ai-memory-intr.latest.json")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def packet_sha256(packet: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical(dict(packet))).hexdigest()


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, (bytes, bytearray)) else canonical(value)
    return "sha256:" + hashlib.sha256(bytes(raw)).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_kv_ai_memory_submission(payload: Any) -> bool:
    return isinstance(payload, dict) and payload.get("schema") == SUBMISSION_SCHEMA


def validate_packet(packet: Mapping[str, Any]) -> None:
    require(packet.get("schema") == PACKET_SCHEMA, "memory_packet_schema_invalid")
    require(packet.get("kv_class") == "PERSONAL_KV", "memory_packet_kv_class_invalid")
    require(packet.get("authority_domain") == "PERSON", "memory_packet_authority_domain_invalid")
    require(packet.get("consumer_ai_role") == "PERSONAL_ASSISTANT_AI", "memory_packet_consumer_role_invalid")
    require(packet.get("intr_admission_required") is True, "memory_packet_intr_required")
    require(packet.get("secret_material_included") is False, "memory_packet_secret_material_forbidden")
    require(packet.get("cross_authority_content_included") is False, "memory_packet_cross_authority_forbidden")
    require(packet.get("model_is_authority") is False, "memory_packet_model_authority_forbidden")
    require(packet.get("context_transfers_authority") is False, "memory_packet_authority_transfer_forbidden")
    require(packet.get("authority_effect") == "NONE_CONTEXT_ONLY", "memory_packet_authority_effect_invalid")
    packet_id = packet.get("packet_id")
    require(isinstance(packet_id, str) and packet_id.startswith("KVMEM-"), "memory_packet_id_invalid")
    entries = packet.get("entries")
    require(isinstance(entries, list) and len(entries) == packet.get("selected_item_count") and len(entries) > 0, "memory_packet_entries_invalid")
    observed_bytes = 0
    for entry in entries:
        require(isinstance(entry, dict), "memory_packet_entry_invalid")
        content = entry.get("content")
        content_hash = entry.get("content_sha256")
        require(isinstance(content, str) and isinstance(content_hash, str), "memory_packet_entry_content_invalid")
        require(hashlib.sha256(content.encode("utf-8")).hexdigest() == content_hash, "memory_packet_entry_hash_mismatch")
        observed_bytes += len(content.encode("utf-8"))
    require(hashlib.sha256(canonical(entries)).hexdigest() == packet.get("entries_sha256"), "memory_packet_entries_hash_mismatch")
    require(observed_bytes == packet.get("selected_content_bytes"), "memory_packet_content_bytes_mismatch")


def validate_submission(payload: Mapping[str, Any]) -> dict[str, Any]:
    require(payload.get("schema") == SUBMISSION_SCHEMA, "memory_submission_schema_invalid")
    require(payload.get("task_id") == TASK_ID, "memory_submission_task_invalid")
    require(payload.get("transport_origin") == "STEGOS_RESIDENT_LOCAL", "memory_submission_origin_invalid")
    require(payload.get("request_grants_execution_authority") is False, "memory_submission_execution_authority_forbidden")
    require(payload.get("claim_or_fence_minted") is False, "memory_submission_claim_forbidden")
    require(payload.get("credential_material_present") is False, "memory_submission_credentials_forbidden")
    require(payload.get("authority_effect") == "NONE_SUBMISSION_ONLY", "memory_submission_authority_effect_invalid")
    packet = payload.get("packet")
    require(isinstance(packet, dict), "memory_submission_packet_required")
    validate_packet(packet)
    observed = packet_sha256(packet)
    require(payload.get("packet_sha256") == observed, "memory_submission_packet_hash_mismatch")
    require(payload.get("packet_id") == packet.get("packet_id"), "memory_submission_packet_id_mismatch")
    return dict(packet)


def _write_once(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(dict(value), indent=2, sort_keys=True) + "\n"
    if path.exists():
        require(path.read_text(encoding="utf-8") == rendered, "memory_intr_write_once_collision")
        return
    path.write_text(rendered, encoding="utf-8")
    require(path.read_text(encoding="utf-8") == rendered, "memory_intr_receipt_readback_mismatch")


def admit(*, runtime_root: Path, payload: Mapping[str, Any], transport_payload_sha256: str) -> dict[str, Any]:
    packet = validate_submission(payload)
    require(isinstance(transport_payload_sha256, str) and transport_payload_sha256.startswith("sha256:") and len(transport_payload_sha256) == 71, "memory_intr_transport_hash_invalid")
    body = {
        "schema": RECEIPT_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "disposition": "ALLOW",
        "task_id": TASK_ID,
        "packet_id": packet["packet_id"],
        "packet_sha256": packet_sha256(packet),
        "entries_sha256": packet["entries_sha256"],
        "transport_origin": "STEGOS_RESIDENT_LOCAL",
        "transport_payload_sha256": transport_payload_sha256,
        "exact_packet_validated": True,
        "private_packet_persisted_by_ingress": False,
        "provider_request_materialized": False,
        "provider_ingress_admission_observed": False,
        "provider_execution_observed": False,
        "kv_writeback_observed": False,
        "claim_or_fence_minted": False,
        "credential_material_present": False,
        "heartbeat_grants_execution_authority": False,
        "request_grants_execution_authority": False,
        "authority_effect": "NONE_INGRESS_ADMISSION_ONLY",
        "admitted_at": now(),
    }
    receipt = {**body, "receipt_hash": sha_uri(body)}
    path = runtime_root / RECEIPT_DIR / f"{packet['packet_id']}.json"
    _write_once(path, receipt)
    latest = runtime_root / LATEST
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt
