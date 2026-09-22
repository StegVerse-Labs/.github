#!/usr/bin/env python3
"""WorkerCoordinator protocol bridge for MIR TVC provider roundtrip.

This bridge creates no runtime, scheduler, broker, credential path, InTr authority,
or Master Records authority. It accepts only an already-fenced WorkerCoordinator
invocation, uses the already-local generic RTC-INTERLOCK-INTR-TRANSPORT-008
Universal InTr transport around the exact TVC broker transaction with the canonical
StegVerse SDK consumer identity, delegates credential use to the existing TVC
non-exportable provider broker, and invokes the registered reusable lifecycle trigger.
Transport evidence never substitutes for explicit Interlock admission.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

TASK_ID = "MIR-TVC-PROVIDER-ROUNDTRIP-001"
COSV = "50000000100000"
REQUEST_ID = "MIR-RUN2-EVENT-001"
TEST_ID = "MIR-STEGVERSE-HISTORICAL-ACCOUNTING-RUN-002"
IDEMPOTENCY_KEY = "MIR-RUN2-STEGVERSE-SDK-ROUNDTRIP-20260912"
EVENT_TYPE = "mir.agent.action.completed"
OCCURRED_AT = "2026-09-12T19:11:41Z"
CONSUMER = "StegVerse-org/StegVerse-SDK"
RECEIPT_REF = "receipts/mir-tvc-provider-roundtrip/MIR-RUN2-EVENT-001.latest.json"
REUSABLE_MANIFEST_REF = "manifests/reusable-task-invocations/MIR-TVC-PROVIDER-ROUNDTRIP-001.TVC-CAPABILITY-RUNTIME-002.json"
REUSABLE_TRIGGER_RECEIPT_REF = "receipts/reusable-task/MIR-TVC-PROVIDER-ROUNDTRIP-001.TVC-CAPABILITY-RUNTIME-002.latest.json"
INTR_COMPONENT = "RTC-INTERLOCK-INTR-TRANSPORT-008"
INTR_REQUEST_SCHEMA = "stegverse.external-provider.operation-request/v1"
INTR_RESPONSE_SCHEMA = "stegverse.external-provider.operation-response/v1"
INTR_SOURCE_SUBSYSTEM = CONSUMER
INTR_DESTINATION_SUBSYSTEM = "TVC:ProviderOperationBroker"


class ProviderOutcomeUnknown(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _load_tvc_broker(tvc_root: Path):
    source = tvc_root / "tvc_provider_operation_broker.py"
    if not source.is_file():
        raise RuntimeError("canonical TVC provider broker source not materialized")
    if str(tvc_root) not in sys.path:
        sys.path.insert(0, str(tvc_root))
    spec = importlib.util.spec_from_file_location("mir_tvc_provider_operation_broker", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load canonical TVC provider broker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_intr_transport(stegos_root: Path):
    source = stegos_root / "stegos" / "universal_intr_transport.py"
    if not source.is_file():
        raise RuntimeError("canonical StegOS Universal InTr transport source not materialized")
    if str(stegos_root) not in sys.path:
        sys.path.insert(0, str(stegos_root))
    from stegos import universal_intr_transport
    return universal_intr_transport

def _validate_invocation(invocation: dict[str, Any]) -> dict[str, Any]:
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        raise ValueError("worker invocation schema mismatch")
    task = invocation.get("task")
    scope = invocation.get("scope")
    if not isinstance(task, dict) or not isinstance(scope, dict):
        raise ValueError("worker invocation task/scope missing")
    if task.get("task_id") != TASK_ID or task.get("state") != "ACTIVE":
        raise ValueError("worker invocation task is not active MIR goal")
    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), dict) else {}
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id:
        raise ValueError("worker invocation claim missing")
    if not isinstance(fence, int) or fence < 1:
        raise ValueError("worker invocation fence missing")
    if scope.get("claim_id") != claim_id or scope.get("fencing_token") != fence:
        raise ValueError("worker invocation scope claim/fence mismatch")
    if not claim_id.endswith(f"-G{fence}"):
        raise ValueError("worker invocation claim generation mismatch")
    return task


def _request() -> dict[str, Any]:
    body = {
        "userExternalId": CONSUMER,
        "eventType": EVENT_TYPE,
        "occurredAt": OCCURRED_AT,
    }
    body_sha = _sha(body)
    operation = {
        "provider": "mir",
        "operation": "mir_history_accounting",
        "provider_operation": "SUBMIT_EVENT",
        "endpoint_origin": "https://mirregistry.com",
        "path": "/v1/events",
        "method": "POST",
        "request_id": REQUEST_ID,
        "test_id": TEST_ID,
        "revision": 1,
        "body": body,
        "body_sha256": body_sha,
        "idempotency_key": IDEMPOTENCY_KEY,
        "consumer_credential_access": False,
        "github_actions_credential_access": False,
        "credential_plaintext_returned": False,
        "return_secret_material": False,
        "wallet_contacted": False,
        "signed": False,
        "broadcast": False,
    }
    lease = {
        "decision": "ALLOW_CAPABILITY_LEASE",
        "consumer": CONSUMER,
        "provider": "mir",
        "operation": "mir_history_accounting",
        "provider_operation": "SUBMIT_EVENT",
        "request_id": REQUEST_ID,
        "test_id": TEST_ID,
        "revision": 1,
        "endpoint_origin": "https://mirregistry.com",
        "path": "/v1/events",
        "method": "POST",
        "body_sha256": body_sha,
        "idempotency_key": IDEMPOTENCY_KEY,
        "single_use": True,
        "secret_values_exported": False,
        "protected_values_exposed": False,
        "signing_authority": False,
        "broadcast_authority": False,
        "custody_authority": False,
        "authority_granted": False,
    }
    return {
        "schema": "stegverse.vault.non_exportable_operation_request.v1",
        "secret_ref": "vault://tvc/providers/mir/api-key",
        "lease_receipt": lease,
        "operation": operation,
        "single_use": True,
        "export_allowed": False,
        "return_secret_material": False,
    }


def _write_receipt(root: Path, value: dict[str, Any]) -> None:
    path = root / RECEIPT_REF
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_receipt(root: Path) -> dict[str, Any] | None:
    path = root / RECEIPT_REF
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def _task_identity(invocation: object) -> tuple[str | None, int | None]:
    if not isinstance(invocation, dict):
        return None, None
    task = invocation.get("task")
    if not isinstance(task, dict):
        return None, None
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), dict) else {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")
    return (claim_id if isinstance(claim_id, str) and claim_id else None, fence if isinstance(fence, int) else None)


def _boundary_ref(task: dict[str, Any], suffix: str) -> str:
    claim = task["claim_id"]
    fence = task["heartbeat_timing"]["fencing_token"]
    return f"workercoordinator://{claim}/fence/{fence}/TVC:ProviderOperationBroker/{suffix}"


def _intr_request_payload(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": INTR_REQUEST_SCHEMA,
        "provider": "mir",
        "request_id": REQUEST_ID,
        "request_hash": _sha(request),
        "lease_ref": _sha(request["lease_receipt"]),
    }


def _prepare_intr_request(connector, request: dict[str, Any]):
    return connector.prepare(
        _intr_request_payload(request),
        payload_schema=INTR_REQUEST_SCHEMA,
        operation="REQUEST_PROVIDER_OPERATION",
        operation_id=REQUEST_ID,
    )


def _admit_intr_request(connector, request: dict[str, Any], task: dict[str, Any]):
    packet = _prepare_intr_request(connector, request)
    receipt = connector.accept_hop(
        packet,
        hop_index=1,
        receipt_id=f"{REQUEST_ID}-INTR-REQUEST-G{task['heartbeat_timing']['fencing_token']}",
        boundary_identity_ref=_boundary_ref(task, "request"),
        recorded_at=_now(),
        prior_receipt_hash=packet.intent.get("prior_transport_receipt_hash"),
        transition_state="RECEIVED",
    )
    result = connector.validate_complete(packet, [receipt])
    return packet, {
        "intent": packet.intent,
        "receipts": [receipt],
        "transport_result": result,
    }


def _admit_intr_response(connector, request_packet, request_receipts: list[dict[str, Any]], provider_result: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "schema": INTR_RESPONSE_SCHEMA,
        "provider": "mir",
        "request_id": REQUEST_ID,
        "response_hash": _sha(provider_result),
    }
    packet = connector.prepare_response(
        request_packet,
        request_receipts,
        payload,
        payload_schema=INTR_RESPONSE_SCHEMA,
        operation_id=f"{REQUEST_ID}-RETURN",
    )
    receipt = connector.accept_hop(
        packet,
        hop_index=1,
        receipt_id=f"{REQUEST_ID}-INTR-RESPONSE-G{task['heartbeat_timing']['fencing_token']}",
        boundary_identity_ref=_boundary_ref(task, "response"),
        recorded_at=_now(),
        prior_receipt_hash=packet.intent.get("prior_transport_receipt_hash"),
        transition_state="RECEIVED",
    )
    result = connector.validate_complete(packet, [receipt])
    return {
        "intent": packet.intent,
        "receipts": [receipt],
        "transport_result": result,
    }


def _post_provider_failure(root: Path, receipt: dict[str, Any], exc: Exception) -> dict[str, Any]:
    value = dict(receipt)
    value["state"] = "FAIL_CLOSED_POST_PROVIDER_OPERATION_RECEIPT"
    value["post_provider_failure_type"] = type(exc).__name__
    value["post_provider_failure"] = str(exc)
    value["provider_operation_retry_allowed"] = False
    value["retry_requires_reconciliation_of_existing_transaction"] = True
    value["authority_effect"] = "NONE_FAIL_CLOSED_EXISTING_CONSEQUENCE_EVIDENCE_ONLY"
    _write_receipt(root, value)
    return value


def _unknown_provider_outcome(root: Path, task: dict[str, Any], request_lane: dict[str, Any], exc: Exception) -> dict[str, Any]:
    receipt = {
        "schema": "stegverse.mir-tvc-provider-roundtrip-receipt/v1",
        "state": "FAIL_CLOSED_PROVIDER_OPERATION_OUTCOME_UNKNOWN",
        "goal_task_id": TASK_ID,
        "request_id": REQUEST_ID,
        "claim_id": task.get("claim_id"),
        "fencing_token": task.get("heartbeat_timing", {}).get("fencing_token"),
        "provider_operation": "SUBMIT_EVENT",
        "provider_operation_completed": None,
        "provider_operation_outcome_known": False,
        "allow_operation_result_observed": False,
        "use_receipt_observed": False,
        "intr_transport": {"profile_id": INTR_PROFILE, "request": request_lane, "response": None},
        "failure_type": type(exc).__name__,
        "failure": str(exc),
        "provider_operation_retry_allowed": False,
        "blind_consequence_retry_allowed": False,
        "reconciliation_required_before_any_provider_retry": True,
        "credential_material_retained": False,
        "secret_values_exported": False,
        "protected_values_exposed": False,
        "authority_effect": "NONE_FAIL_CLOSED_UNKNOWN_PROVIDER_OUTCOME",
    }
    _write_receipt(root, receipt)
    return receipt


def _retain_failure(root: Path, invocation: object, exc: Exception) -> dict[str, Any]:
    existing = _load_receipt(root)
    if isinstance(existing, dict) and existing.get("request_id") == REQUEST_ID:
        if existing.get("provider_operation_completed") is True or existing.get("provider_operation_outcome_known") is False:
            return _post_provider_failure(root, existing, exc) if existing.get("provider_operation_completed") is True else existing
    claim_id, fence = _task_identity(invocation)
    receipt = {
        "schema": "stegverse.mir-tvc-provider-roundtrip-receipt/v1",
        "state": "FAIL_CLOSED_EXECUTION_RECEIPT",
        "goal_task_id": TASK_ID,
        "request_id": REQUEST_ID,
        "claim_id": claim_id,
        "fencing_token": fence,
        "provider_operation": "SUBMIT_EVENT",
        "provider_operation_completed": False,
        "provider_operation_outcome_known": True,
        "allow_operation_result_observed": False,
        "use_receipt_observed": False,
        "failure_type": type(exc).__name__,
        "failure": str(exc),
        "retry_requires_fresh_workercoordinator_cycle": True,
        "intr_admission_required": True,
        "master_records_custody_required": True,
        "credential_material_retained": False,
        "secret_values_exported": False,
        "protected_values_exposed": False,
        "authority_effect": "NONE_FAIL_CLOSED_EXECUTION_EVIDENCE_ONLY",
    }
    _write_receipt(root, receipt)
    return receipt


def _parse_trigger_receipt(stdout: str) -> dict[str, Any]:
    value = json.loads(stdout)
    if not isinstance(value, dict) or value.get("schema") != "stegverse.reusable-task-trigger-receipt/v1":
        raise RuntimeError("reusable trigger receipt invalid")
    return value


def _continue_reusable_lifecycle(root: Path) -> dict[str, Any]:
    manifest_path = root / REUSABLE_MANIFEST_REF
    if not manifest_path.is_file():
        raise RuntimeError("MIR TVC reusable invocation manifest not materialized")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("task_id") != TASK_ID or manifest.get("cosv_task_vector") != COSV:
        raise RuntimeError("MIR TVC reusable invocation task/COSV binding mismatch")
    parameters = manifest.get("parameters")
    if not isinstance(parameters, dict) or parameters.get("provider_operation_receipt_ref") != RECEIPT_REF:
        raise RuntimeError("MIR TVC reusable invocation provider receipt binding mismatch")
    trigger = root / "scripts" / "trigger_reusable_task.py"
    if not trigger.is_file():
        raise RuntimeError("reusable trigger driver not materialized")
    trigger_receipt = root / REUSABLE_TRIGGER_RECEIPT_REF
    command = [
        sys.executable,
        str(trigger),
        "--reusable-task-id", str(manifest["reusable_task_id"]),
        "--invocation-id", str(manifest["invocation_id"]),
        "--parameters-json", json.dumps(parameters, sort_keys=True, separators=(",", ":")),
        "--task-id", TASK_ID,
        "--cosv-task-vector", COSV,
        "--receipt", str(trigger_receipt),
    ]
    completed = subprocess.run(command, cwd=root, env=os.environ.copy(), text=True, capture_output=True, check=False, timeout=150)
    if completed.returncode != 0:
        raise RuntimeError(f"reusable trigger driver failed:{completed.returncode}:{completed.stderr[-1000:]}")
    result = _parse_trigger_receipt(completed.stdout)
    if result.get("state") == "ENTROPY_RECOVERY_RECORDED" and result.get("continuation") == "NONE_FOR_THIS_INVOCATION":
        return {
            "schema": "stegverse.worker-response/v0.1",
            "state": "COMPLETED",
            "transition_id": "MIR_TVC_PROVIDER_SESSION_OBSERVED",
            "transition_sequence": 2,
            "expected_next_transition": None,
            "expected_next_earliest_epoch": None,
            "expected_next_latest_epoch": None,
            "checkpoint_ref": REUSABLE_TRIGGER_RECEIPT_REF,
            "evidence_refs": [
                RECEIPT_REF,
                REUSABLE_TRIGGER_RECEIPT_REF,
                str(result.get("master_records_custody_ref") or ""),
                str(result.get("master_records_reconstructed_request_ref") or ""),
                str(result.get("entropy_recovery_ref") or ""),
            ],
            "cost_observation": {
                "compute_units": 1,
                "token_units": 0,
                "storage_bytes": 0,
                "network_bytes": 0,
                "operator_seconds": 0,
                "external_cost_usd": 0,
                "latency_ms": None,
                "failure_recovery_units": 0,
                "services_used": ["mir", "master-records"],
            },
            "authority_effect": "NONE_SAME_TRANSACTION_EVIDENCE_RECONCILIATION_ONLY",
        }
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "HANDOFF_READY",
        "transition_id": "MIR_TVC_PROVIDER_SESSION_LIFECYCLE_BOUNDARY",
        "transition_sequence": 2,
        "expected_next_transition": "RECONCILE_EXISTING_PROVIDER_TRANSACTION_LIFECYCLE_BOUNDARY",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": REUSABLE_TRIGGER_RECEIPT_REF,
        "evidence_refs": [RECEIPT_REF, REUSABLE_TRIGGER_RECEIPT_REF],
        "cost_observation": {
            "compute_units": 1,
            "token_units": 0,
            "storage_bytes": 0,
            "network_bytes": 0,
            "operator_seconds": 0,
            "external_cost_usd": 0,
            "latency_ms": None,
            "failure_recovery_units": 1,
            "services_used": ["mir"],
        },
        "boundary": result.get("boundary"),
        "provider_operation_retry_allowed": False,
        "authority_effect": "NONE_FAIL_CLOSED_EXISTING_TRANSACTION_CONTINUATION",
    }


def _roots() -> tuple[Path, Path]:
    tvc_raw = (os.getenv("STEGVERSE_TVC_ROOT") or "").strip()
    stegos_raw = (os.getenv("STEGVERSE_STEGOS_ROOT") or "").strip()
    if not tvc_raw:
        raise RuntimeError("STEGVERSE_TVC_ROOT not materialized")
    if not stegos_raw:
        raise RuntimeError("STEGVERSE_STEGOS_ROOT not materialized")
    return Path(tvc_raw).expanduser().resolve(), Path(stegos_raw).expanduser().resolve()


def _resume_completed_provider(root: Path, task: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    if existing.get("provider_operation_outcome_known") is False:
        raise ProviderOutcomeUnknown("existing provider operation outcome is unknown; blind retry prohibited")
    result = existing.get("provider_operation_result")
    intr = existing.get("intr_transport")
    if existing.get("provider_operation_completed") is not True or not isinstance(result, dict) or not isinstance(intr, dict):
        raise RuntimeError("existing receipt is not a resumable completed provider transaction")
    request_lane = intr.get("request")
    if not isinstance(request_lane, dict) or not isinstance(request_lane.get("receipts"), list):
        raise RuntimeError("completed provider consequence lacks pre-provider canonical InTr request receipt")
    if isinstance(intr.get("response"), dict) and intr["response"].get("transport_result", {}).get("state") == "TRANSPORT_COMPLETE":
        if existing.get("state") != "COMPLETED_PROVIDER_OPERATION_RECEIPT":
            existing = dict(existing)
            existing["state"] = "COMPLETED_PROVIDER_OPERATION_RECEIPT"
            existing.pop("post_provider_failure_type", None)
            existing.pop("post_provider_failure", None)
            existing["provider_operation_retry_allowed"] = False
            existing["authority_effect"] = "NONE_EXECUTION_EVIDENCE_ONLY"
            _write_receipt(root, existing)
        return _continue_reusable_lifecycle(root)

    _, stegos_root = _roots()
    connector = _load_intr_connector(stegos_root)
    request = _request()
    packet = _prepare_intr_request(connector, request)
    request_receipts = request_lane["receipts"]
    connector.validate_complete(packet, request_receipts)
    response_lane = _admit_intr_response(connector, packet, request_receipts, result, task)
    completed_receipt = dict(existing)
    completed_receipt["state"] = "COMPLETED_PROVIDER_OPERATION_RECEIPT"
    completed_receipt["intr_transport"] = {"profile_id": INTR_PROFILE, "request": request_lane, "response": response_lane}
    completed_receipt["provider_operation_retry_allowed"] = False
    completed_receipt["authority_effect"] = "NONE_EXECUTION_EVIDENCE_ONLY"
    _write_receipt(root, completed_receipt)
    return _continue_reusable_lifecycle(root)


def run(invocation: dict[str, Any], *, root: Path) -> dict[str, Any]:
    task = _validate_invocation(invocation)
    existing = _load_receipt(root)
    if isinstance(existing, dict) and existing.get("request_id") == REQUEST_ID:
        if existing.get("provider_operation_outcome_known") is False:
            raise ProviderOutcomeUnknown("existing provider operation outcome is unknown; blind retry prohibited")
        if existing.get("provider_operation_completed") is True:
            return _resume_completed_provider(root, task, existing)

    tvc_root, stegos_root = _roots()
    broker = _load_tvc_broker(tvc_root)
    connector = _load_intr_connector(stegos_root)
    socket_path = (os.getenv("STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET") or "/run/stegverse/vault-broker.sock").strip()
    if not socket_path.startswith("/"):
        raise RuntimeError("canonical TVC vault broker socket path invalid")
    request = _request()

    # TVC validates the exact lease/profile/live-operation boundary before the InTr
    # transport receipt is admitted. This source validation grants no credential use.
    broker.validate_request(request)
    request_packet, request_lane = _admit_intr_request(connector, request, task)

    try:
        result = broker.forward_to_local_vault_broker(request, socket_path=socket_path, timeout_seconds=60)
    except Exception as exc:
        _unknown_provider_outcome(root, task, request_lane, exc)
        raise ProviderOutcomeUnknown(str(exc)) from exc

    if not isinstance(result, dict) or result.get("decision") != "ALLOW_OPERATION_RESULT":
        raise RuntimeError("canonical TVC broker did not return ALLOW_OPERATION_RESULT")
    use_receipt = result.get("use_receipt")
    if not isinstance(use_receipt, dict):
        raise RuntimeError("canonical TVC broker use_receipt missing")

    # Persist consequence evidence before response transport so a later local failure
    # can never cause a blind second provider consequence.
    interim = {
        "schema": "stegverse.mir-tvc-provider-roundtrip-receipt/v1",
        "state": "PROVIDER_OPERATION_COMPLETED_INTR_RESPONSE_PENDING",
        "goal_task_id": TASK_ID,
        "request_id": REQUEST_ID,
        "claim_id": task.get("claim_id"),
        "fencing_token": task.get("heartbeat_timing", {}).get("fencing_token"),
        "provider_operation": "SUBMIT_EVENT",
        "provider_operation_completed": True,
        "provider_operation_outcome_known": True,
        "provider_operation_result": result,
        "allow_operation_result_observed": True,
        "use_receipt_observed": True,
        "ready_state": "READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND",
        "completion_candidate": "AUTHENTIC_TVC_MIR_PROVIDER_SESSION_OBSERVED",
        "intr_transport": {"profile_id": INTR_PROFILE, "request": request_lane, "response": None},
        "master_records_custody_required": True,
        "provider_operation_retry_allowed": False,
        "blind_consequence_retry_allowed": False,
        "credential_material_retained": False,
        "secret_values_exported": False,
        "protected_values_exposed": False,
        "authority_effect": "NONE_EXECUTION_EVIDENCE_ONLY",
    }
    _write_receipt(root, interim)

    try:
        response_lane = _admit_intr_response(connector, request_packet, request_lane["receipts"], result, task)
    except Exception as exc:
        _post_provider_failure(root, interim, exc)
        raise

    receipt = dict(interim)
    receipt["state"] = "COMPLETED_PROVIDER_OPERATION_RECEIPT"
    receipt["intr_transport"] = {"profile_id": INTR_PROFILE, "request": request_lane, "response": response_lane}
    _write_receipt(root, receipt)
    return _continue_reusable_lifecycle(root)


def main() -> int:
    invocation: object = None
    try:
        invocation = json.load(sys.stdin)
        if not isinstance(invocation, dict):
            raise ValueError("worker invocation must be a JSON object")
        response = run(invocation, root=Path.cwd())
    except Exception as exc:
        retained = _retain_failure(Path.cwd(), invocation, exc)
        unknown = retained.get("provider_operation_outcome_known") is False
        response = {
            "schema": "stegverse.worker-response/v0.1",
            "state": "HANDOFF_READY",
            "transition_id": "MIR_TVC_PROVIDER_OPERATION_OUTCOME_UNKNOWN" if unknown else "MIR_TVC_PROVIDER_OPERATION_FAIL_CLOSED",
            "transition_sequence": 1,
            "expected_next_transition": "RECONCILE_PROVIDER_OPERATION_OUTCOME_WITHOUT_BLIND_RETRY" if unknown else "MIR_TVC_PROVIDER_OPERATION_RETRY_AFTER_RECORDED_BOUNDARY",
            "expected_next_earliest_epoch": None,
            "expected_next_latest_epoch": None,
            "checkpoint_ref": RECEIPT_REF,
            "evidence_refs": [RECEIPT_REF],
            "cost_observation": {
                "compute_units": 1,
                "token_units": 0,
                "storage_bytes": 0,
                "network_bytes": 0,
                "operator_seconds": 0,
                "external_cost_usd": 0,
                "latency_ms": None,
                "failure_recovery_units": 1,
                "services_used": [],
            },
            "provider_operation_retry_allowed": retained.get("provider_operation_retry_allowed", not unknown),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "authority_effect": "NONE_FAIL_CLOSED",
        }
    print(json.dumps(response, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
