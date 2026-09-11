#!/usr/bin/env python3
"""Site publication extension for the shared profiled Universal InTr ingress.

This module owns no listener and grants no execution authority. It validates the
already-defined SITE_PUBLICATION_EVENT materialization request, persists it
write-once into the existing runtime queue, and emits a candidate-only ingress
receipt. Runtime lease execution remains separately fenced by WorkerCoordinator.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

PROFILE = "StegOS:SitePublicationRuntime"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": PROFILE}
DOWNSTREAM_OWNER = "StegVerse-Labs/StegOS:canonical-runtime-lane"
OPERATION_ID = "SITE_PUBLICATION_EVENT"
REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
RECEIPT_SCHEMA = "stegverse.site-publication-intr-ingress/v1"
RECEIPT_DIR = Path("receipts/sovereign-network/site-publication-intr-ingress")
LATEST = Path("receipts/sovereign-network/site-publication-intr-ingress.latest.json")
REQUEST_DIR = Path("intr-materialization")
AUTHORITY_EFFECT = "NONE_INGRESS_CANDIDATE_ONLY"


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


def is_site_publication(payload: Any) -> bool:
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
    for key, value in expected.items():
        require(request.get(key) == value, f"site_publication_{key}_mismatch")
    materialization_id = request.get("materialization_id")
    require(isinstance(materialization_id, str) and materialization_id.startswith("INTR-MAT-") and len(materialization_id) == 33, "materialization_id_invalid")
    require(all(ch in "0123456789abcdef" for ch in materialization_id[9:]), "materialization_id_invalid")
    for key in ("transport_intent_hash", "payload_hash", "request_hash"):
        value = request.get(key)
        require(isinstance(value, str) and value.startswith("sha256:") and len(value) == 71, f"{key}_invalid")
    payload_ref = request.get("payload_ref")
    require(isinstance(payload_ref, str) and payload_ref.startswith("artifact://site-publication-manifest/"), "payload_ref_invalid")
    require(payload_ref.rsplit("/", 1)[-1] == str(request["payload_hash"])[7:], "payload_ref_hash_mismatch")
    body = dict(request)
    claimed = body.pop("request_hash")
    require(claimed == sha_uri(body), "request_hash_mismatch")


def _write_once(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == raw, "write_once_collision")
        return
    path.write_bytes(raw)


def admit(*, runtime_root: Path, payload: Mapping[str, Any], transport_payload_sha256: str, source: Mapping[str, Any] | None = None) -> dict[str, Any]:
    request: Mapping[str, Any] = payload
    if isinstance(payload.get("node_outbox_entry"), dict):
        entry = payload["node_outbox_entry"]
        require(isinstance(entry.get("materialization_request"), dict), "node_outbox_materialization_request_required")
        request = entry["materialization_request"]
    validate_request(request)
    materialization_id = str(request["materialization_id"])
    runtime = runtime_root.expanduser().resolve()
    request_raw = json.dumps(dict(request), indent=2, sort_keys=True).encode("utf-8") + b"\n"
    request_path = runtime / REQUEST_DIR / f"{materialization_id}.json"
    _write_once(request_path, request_raw)
    source = dict(source or {})
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "state": "INGRESS_ADMITTED_CANDIDATE_ONLY",
        "materialization_id": materialization_id,
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "payload_ref": request["payload_ref"],
        "operation_id": OPERATION_ID,
        "packet_id": request["packet_id"],
        "destination": DESTINATION,
        "downstream_owner_ref": DOWNSTREAM_OWNER,
        "transport_payload_sha256": transport_payload_sha256,
        "node_id": source.get("node_id"),
        "interlock_id": source.get("interlock_id"),
        "outbox_entry_hash": source.get("outbox_entry_hash"),
        "queue_ref": str(request_path),
        "exact_request_validated": True,
        "write_once_persisted": True,
        "runtime_class": "EVENT_EPHEMERAL",
        "persistent_node_identity_required": True,
        "persistent_host_required": False,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "hosted_provider_required": False,
        "render_allowed": False,
        "runtime_materialization_attempted": False,
        "runtime_execution_observed": False,
        "public_https_profile_observed": False,
        "exact_http_readback_observed": False,
        "content_equivalence_observed": False,
        "lease_closure_observed": False,
        "final_publication_transition_admitted": False,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "heartbeat_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": AUTHORITY_EFFECT,
        "admitted_at": now(),
    }
    receipt["receipt_hash"] = sha_uri(receipt)
    raw = json.dumps(receipt, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    receipt_path = runtime / RECEIPT_DIR / f"{materialization_id}.json"
    _write_once(receipt_path, raw)
    latest = runtime / LATEST
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_bytes(raw)
    return receipt
