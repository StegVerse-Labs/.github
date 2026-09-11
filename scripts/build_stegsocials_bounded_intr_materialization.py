#!/usr/bin/env python3
"""Build the organization-owned Universal InTr request for one bounded StegSocials ingress.

Input is an already-source-validated `stegverse.universal-work-interlock/v1`
INGRESS/RECEIVED record emitted by StegSocials. This builder does not admit the
record and cannot create an InTr admission receipt. It only binds the exact
record into the existing event-ephemeral Universal InTr materialization shape
owned by StegVerse-Labs/.github.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
PAYLOAD_SCHEMA = "stegverse.stegsocials-bounded-intr-payload/v1"
WORK_SCHEMA = "stegverse.universal-work-interlock/v1"
INTENT_SCHEMA = "stegsocials.bounded-group-intr-execution-intent.v1"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "StegSocials:BoundedSocialIngress"}
DOWNSTREAM_OWNER = "SS-KV-SKAP-SOCIAL-RELEASE-001"
BOUNDARY_PATH = ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"]
OPERATION_ID = "BOUNDED_SOCIAL_INTR_INGRESS"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object_required:{path}")
    return value


def validate_received(record: Mapping[str, Any]) -> None:
    expected = {
        "schema": WORK_SCHEMA,
        "direction": "INGRESS",
        "state": "RECEIVED",
        "organization": "StegVerse-Labs",
        "repository": "StegVerse-Labs/StegSocials",
        "component": "bounded-group-social-publication",
        "next_owner": "INTERLOCK_INTR",
        "human_action_required": False,
        "admission_receipt_ref": None,
        "runtime_admission_observed": False,
    }
    for key, wanted in expected.items():
        require(record.get(key) == wanted, f"received_{key}_mismatch")
    for key in ("work_id", "correlation_id", "goal", "recorded_at"):
        require(isinstance(record.get(key), str) and bool(str(record[key]).strip()), f"received_{key}_required")
    source = record.get("source")
    require(isinstance(source, dict) and source.get("type") == "RUNTIME_EVENT", "received_source_invalid")
    authority = record.get("authority")
    require(isinstance(authority, dict), "received_authority_required")
    require(authority.get("credential_authority") == "TV/TVC", "received_credential_authority_drift")
    require(authority.get("github_token_runtime_authority") == "NONE", "received_github_authority_drift")
    require(authority.get("heartbeat_granted_authority") is False, "received_heartbeat_authority_drift")
    require(authority.get("interlock_self_grants_authority") is False, "received_interlock_self_authority_drift")
    require(authority.get("intr_self_grants_authority") is False, "received_intr_self_authority_drift")
    intent = record.get("bounded_social_intent")
    require(isinstance(intent, dict) and intent.get("schema") == INTENT_SCHEMA, "received_bounded_intent_invalid")
    require(intent.get("task_id") == DOWNSTREAM_OWNER, "received_task_binding_mismatch")
    require(intent.get("stable_work_id") == record.get("work_id"), "received_work_id_binding_mismatch")
    require(intent.get("correlation_id") == record.get("correlation_id"), "received_correlation_binding_mismatch")
    require(intent.get("requested_transition") == "INGRESS_ADMITTED", "received_requested_transition_invalid")
    require(intent.get("intr_admission_receipt_ref") is None, "received_synthetic_intr_receipt_forbidden")
    require(intent.get("tv_tvc_skap_session_receipt_ref") is None, "received_synthetic_skap_receipt_forbidden")
    require(intent.get("request_grants_execution_authority") is False, "received_execution_authority_forbidden")
    require(intent.get("provider_operation_authorized") is False, "received_provider_authority_forbidden")
    require(intent.get("secret_material_present") is False and intent.get("raw_credential_material") is None, "received_secret_material_forbidden")


def build(record: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_received(record)
    intent = record["bounded_social_intent"]
    payload = {
        "schema": PAYLOAD_SCHEMA,
        "goal_task_id": DOWNSTREAM_OWNER,
        "work_id": record["work_id"],
        "correlation_id": record["correlation_id"],
        "group_id": intent["group_id"],
        "use_index": intent["use_index"],
        "participant_approval_receipt_ref": intent["participant_approval_receipt_ref"],
        "state_ref": intent["state_ref"],
        "content_ref": intent["content_ref"],
        "content_hash": intent["content_hash"],
        "platform": intent["platform"],
        "account_ref": intent["account_ref"],
        "universal_work_interlock_received": dict(record),
        "runtime_admission_observed": False,
        "admission_receipt_ref": None,
        "credential_material_present": False,
        "provider_operation_authorized": False,
        "request_grants_execution_authority": False,
        "authority_effect": "NONE_PAYLOAD_ONLY",
    }
    payload_hash = sha_uri(payload)
    packet_seed = f"{record['work_id']}:{intent['group_id']}:{intent['use_index']}:{payload_hash}"
    packet_id = "SS-INTR-" + hashlib.sha256(packet_seed.encode("utf-8")).hexdigest()[:24]
    materialization_id = "INTR-MAT-" + hashlib.sha256((packet_id + ":" + payload_hash).encode("utf-8")).hexdigest()[:24]
    payload_ref = f"runtime://intr-payloads/stegsocials-bounded-social/{materialization_id}.json"
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
        "payload_ref": payload_ref,
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
    parser.add_argument("--received-record", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--request-output", type=Path)
    args = parser.parse_args()

    record = load_object(args.received_record)
    payload, request = build(record)
    runtime = args.runtime_root.expanduser().resolve()
    payload_path = runtime / "intr-payloads" / "stegsocials-bounded-social" / f"{request['materialization_id']}.json"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_raw = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if payload_path.exists():
        require(payload_path.read_text(encoding="utf-8") == payload_raw, "payload_write_once_collision")
    else:
        payload_path.write_text(payload_raw, encoding="utf-8")
    output = args.request_output or (runtime / "outbound" / "stegsocials-bounded-intr-request.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state":"MATERIALIZATION_REQUEST_BUILT","request_ref":str(output),"payload_ref":str(payload_path),"materialization_id":request["materialization_id"],"request_hash":request["request_hash"],"authority_effect":"NONE_SOURCE_ONLY"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
