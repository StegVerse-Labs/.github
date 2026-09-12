#!/usr/bin/env python3
"""Build a non-authorizing Universal InTr request for one TVC recipient-admission sign operation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
PAYLOAD_SCHEMA = "stegverse.tvc.recipient-admission-sign-intr-payload/v1"
PLATFORM_REQUEST_SCHEMA = "stegverse.vault.agent.platform-recipient-admission-sign-request.v1"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "TVC:RecipientAdmissionAuthoritySign"}
DOWNSTREAM_OWNER = "TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001"
BOUNDARY_PATH = ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"]
OPERATION_ID = "TVC_RECIPIENT_ADMISSION_AUTHORITY_SIGN"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def validate_platform_request(request: Mapping[str, Any]) -> None:
    require(request.get("schema") == PLATFORM_REQUEST_SCHEMA, "platform_request_schema_invalid")
    require(request.get("purpose") == "TVC_RECIPIENT_CAPABILITY_ADMISSION", "platform_request_purpose_invalid")
    require(request.get("credentialAuthority") == "TV/TVC", "platform_request_credential_authority_invalid")
    require(request.get("transitionAuthority") == "Interlock/InTr", "platform_request_transition_authority_invalid")
    require(isinstance(request.get("authorityKeyID"), str) and request["authorityKeyID"].startswith("tvc://authority-key/p256/"), "authority_key_id_invalid")
    for field in ("authorityPublicJWKSHA256", "messageSHA256"):
        value = request.get(field)
        require(isinstance(value, str) and value.startswith("sha256:") and len(value) == 71, field + "_invalid")
    require(isinstance(request.get("requestNonce"), str) and len(request["requestNonce"]) >= 16, "request_nonce_invalid")
    require(request.get("privateKeyMaterialRequested") is False, "private_key_material_request_forbidden")
    require(request.get("recipientKeyReuseAllowed") is False, "recipient_key_reuse_forbidden")
    require(request.get("publicInvocationAllowed") is False, "public_invocation_forbidden")
    require(not request.get("requiredNodeID") and not request.get("pinnedDeviceID"), "device_pin_forbidden")


def build(platform_request: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_platform_request(platform_request)
    exact = dict(platform_request)
    platform_request_sha256 = sha_uri(exact)
    payload = {
        "schema": PAYLOAD_SCHEMA,
        "goal_task_id": DOWNSTREAM_OWNER,
        "operation": OPERATION_ID,
        "platform_request_sha256": platform_request_sha256,
        "purpose": exact["purpose"],
        "authority_key_id": exact["authorityKeyID"],
        "authority_public_jwk_sha256": exact["authorityPublicJWKSHA256"],
        "message_sha256": exact["messageSHA256"],
        "request_nonce": exact["requestNonce"],
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
    payload_hash = sha_uri(payload)
    packet_seed = platform_request_sha256 + ":" + payload_hash
    packet_id = "TVC-SIGN-INTR-" + hashlib.sha256(packet_seed.encode()).hexdigest()[:24]
    materialization_id = "INTR-MAT-" + hashlib.sha256((packet_id + ":" + payload_hash).encode()).hexdigest()[:24]
    transport_intent = {
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "boundary_path": BOUNDARY_PATH,
        "destination": DESTINATION,
        "downstream_owner_ref": DOWNSTREAM_OWNER,
        "operation_id": OPERATION_ID,
        "packet_id": packet_id,
        "payload_hash": payload_hash,
    }
    request = {
        "schema": REQUEST_SCHEMA,
        "state": REQUEST_STATE,
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "materialization_id": materialization_id,
        "operation_id": OPERATION_ID,
        "packet_id": packet_id,
        "transport_intent_hash": sha_uri(transport_intent),
        "payload_hash": payload_hash,
        "payload_ref": f"runtime://intr-payloads/tvc-recipient-admission-sign/{materialization_id}.json",
        "destination": DESTINATION,
        "boundary_path": BOUNDARY_PATH,
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
    request["request_hash"] = sha_uri(request)
    return payload, request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform-request", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--request-output", type=Path)
    args = parser.parse_args()
    platform_request = json.loads(args.platform_request.read_text(encoding="utf-8"))
    payload, request = build(platform_request)
    runtime = args.runtime_root.expanduser().resolve()
    payload_path = runtime / "intr-payloads" / "tvc-recipient-admission-sign" / f"{request['materialization_id']}.json"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    if payload_path.exists():
        require(payload_path.read_text(encoding="utf-8") == raw, "payload_write_once_collision")
    else:
        payload_path.write_text(raw, encoding="utf-8")
    output = args.request_output or (runtime / "outbound" / "tvc-recipient-admission-sign-intr-request.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(request, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"state":"MATERIALIZATION_REQUEST_BUILT","materialization_id":request["materialization_id"],"request_hash":request["request_hash"],"platform_request_sha256":payload["platform_request_sha256"],"authority_effect":"NONE_SOURCE_ONLY"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
