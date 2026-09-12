#!/usr/bin/env python3
"""Admission adapter for TVC recipient-authority signing on the existing Universal InTr listener.

This module starts no server and grants no credential/signing authority. Only invocation
through the shared Universal InTr listener may emit its write-once INGRESS_ADMITTED
receipt. The receipt admits one exact non-secret operation request; it does not itself
perform signing or user verification.
"""
from __future__ import annotations

import hashlib
import json
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
from build_tvc_recipient_admission_sign_intr_request import (  # noqa: E402
    DESTINATION,
    DOWNSTREAM_OWNER,
    OPERATION_ID,
    PAYLOAD_SCHEMA,
    REQUEST_SCHEMA,
    REQUEST_STATE,
    canonical,
    sha_uri,
)

INGRESS_SCHEMA = "stegverse.tvc.recipient-admission-sign-intr-ingress/v1"
RECEIPT_DIR_REL = Path("receipts/sovereign-network/tvc-recipient-admission-sign-intr-ingress")
LATEST_REL = Path("receipts/sovereign-network/tvc-recipient-admission-sign-intr-ingress.latest.json")
PAYLOAD_DIR_REL = Path("intr-payloads/tvc-recipient-admission-sign")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_tvc_recipient_admission_sign(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and payload.get("destination") == DESTINATION
        and payload.get("downstream_owner_ref") == DOWNSTREAM_OWNER
        and payload.get("operation_id") == OPERATION_ID
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
        "interlock_required": True,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "transport_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_transfer": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for field, wanted in expected.items():
        require(request.get(field) == wanted, "request_" + field + "_mismatch")
    for field in ("materialization_id", "packet_id", "transport_intent_hash", "payload_hash", "payload_ref", "request_hash"):
        require(isinstance(request.get(field), str) and bool(request[field]), "request_" + field + "_required")
    body = dict(request)
    claimed = body.pop("request_hash", None)
    require(claimed == sha_uri(body), "request_hash_mismatch")


def validate_payload(payload: Mapping[str, Any]) -> None:
    expected = {
        "schema": PAYLOAD_SCHEMA,
        "goal_task_id": DOWNSTREAM_OWNER,
        "operation": OPERATION_ID,
        "purpose": "TVC_RECIPIENT_CAPABILITY_ADMISSION",
        "credential_authority": "TV/TVC",
        "requested_transition": "INGRESS_ADMITTED",
        "user_verification_authority": "KV/SKAP Vault",
        "user_verification_performed_here": False,
        "credential_material_present": False,
        "private_key_material_present": False,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_PAYLOAD_ONLY",
    }
    for field, wanted in expected.items():
        require(payload.get(field) == wanted, "payload_" + field + "_mismatch")
    for field in ("platform_request_sha256", "authority_public_jwk_sha256", "message_sha256"):
        value = payload.get(field)
        require(isinstance(value, str) and value.startswith("sha256:") and len(value) == 71, "payload_" + field + "_invalid")
    require(isinstance(payload.get("authority_key_id"), str) and payload["authority_key_id"].startswith("tvc://authority-key/p256/"), "payload_authority_key_id_invalid")
    require(isinstance(payload.get("request_nonce"), str) and len(payload["request_nonce"]) >= 16, "payload_request_nonce_invalid")


def _admission_sha256(body: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical(dict(body))).hexdigest()


def admit(*, runtime_root: Path, body: bytes, headers: Mapping[str, str]) -> dict[str, Any]:
    transport = transport_boundary.validate_transport_headers(headers, body)
    try:
        request = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError("request_json_invalid") from exc
    require(isinstance(request, dict), "request_object_required")
    require(is_tvc_recipient_admission_sign(request), "tvc_recipient_sign_destination_mismatch")
    validate_request(request)

    mid = str(request["materialization_id"])
    require(mid.startswith("INTR-MAT-") and len(mid) == 33, "materialization_id_invalid")
    payload_path = runtime_root / PAYLOAD_DIR_REL / f"{mid}.json"
    require(payload_path.is_file(), "exact_payload_sidecar_missing")
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "payload_object_required")
    validate_payload(payload)
    require(sha_uri(payload) == request["payload_hash"], "payload_hash_mismatch")

    request_path = runtime_root / transport_boundary.REQUEST_DIR_REL / f"{mid}.json"
    transport_boundary._write_once(request_path, json.dumps(request, sort_keys=True, indent=2).encode("utf-8") + b"\n")

    receipt_path = runtime_root / RECEIPT_DIR_REL / f"{mid}.json"
    if receipt_path.exists():
        existing = json.loads(receipt_path.read_text(encoding="utf-8"))
        require(existing.get("request_hash") == request["request_hash"] and existing.get("state") == "INGRESS_ADMITTED", "write_once_collision")
        return existing

    admission_ref = "intr://tvc-recipient-admission-sign/" + mid.removeprefix("INTR-MAT-")
    receipt_body = {
        "schema": INGRESS_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "admission_state": "ADMITTED",
        "admission_ref": admission_ref,
        "materialization_id": mid,
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "platform_request_sha256": payload["platform_request_sha256"],
        "operation_id": OPERATION_ID,
        "packet_id": request["packet_id"],
        "authority_key_id": payload["authority_key_id"],
        "authority_public_jwk_sha256": payload["authority_public_jwk_sha256"],
        "message_sha256": payload["message_sha256"],
        "request_nonce": payload["request_nonce"],
        "transport_origin": transport.get("origin"),
        "transport_authorization_id": transport.get("authorization_id"),
        "transport_payload_sha256": transport.get("payload_sha256"),
        "exact_request_validated": True,
        "exact_payload_validated": True,
        "runtime_execution_attempted": False,
        "claim_or_fence_minted": False,
        "user_verification_performed_here": False,
        "user_verification_authority": "KV/SKAP Vault",
        "credential_authority": "TV/TVC",
        "transition_authority": "Interlock/InTr",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "INGRESS_TRANSITION_ONLY",
        "admitted_at": now(),
    }
    receipt = {**receipt_body, "admission_sha256": _admission_sha256(receipt_body)}
    raw = json.dumps(receipt, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    transport_boundary._write_once(receipt_path, raw)
    latest = runtime_root / LATEST_REL
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_bytes(raw)
    return receipt


__all__ = ["INGRESS_SCHEMA", "is_tvc_recipient_admission_sign", "validate_request", "validate_payload", "admit"]
