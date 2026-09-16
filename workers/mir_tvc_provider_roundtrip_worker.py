#!/usr/bin/env python3
"""WorkerCoordinator protocol bridge for MIR TVC provider roundtrip.

This bridge creates no runtime, scheduler, broker, credential path, InTr authority,
or Master Records authority. It accepts only an already-fenced WorkerCoordinator
invocation, resolves the already-local TVC source root, constructs the exact admitted
MIR-RUN2-EVENT-001 non-secret request, and delegates credential use to the existing
TVC non-exportable provider broker through its Unix vault socket.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

TASK_ID = "MIR-TVC-PROVIDER-ROUNDTRIP-001"
REQUEST_ID = "MIR-RUN2-EVENT-001"
TEST_ID = "MIR-STEGVERSE-HISTORICAL-ACCOUNTING-RUN-002"
IDEMPOTENCY_KEY = "MIR-RUN2-STEGVERSE-SDK-ROUNDTRIP-20260912"
EVENT_TYPE = "mir.agent.action.completed"
OCCURRED_AT = "2026-09-12T19:11:41Z"
CONSUMER = "StegVerse-org/StegVerse-SDK"
RECEIPT_REF = "receipts/mir-tvc-provider-roundtrip/MIR-RUN2-EVENT-001.latest.json"


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


def run(invocation: dict[str, Any], *, root: Path) -> dict[str, Any]:
    task = _validate_invocation(invocation)
    tvc_root_raw = (os.getenv("STEGVERSE_TVC_ROOT") or "").strip()
    if not tvc_root_raw:
        raise RuntimeError("STEGVERSE_TVC_ROOT not materialized")
    tvc_root = Path(tvc_root_raw).expanduser().resolve()
    broker = _load_tvc_broker(tvc_root)
    socket_path = (os.getenv("STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET") or "/run/stegverse/vault-broker.sock").strip()
    if not socket_path.startswith("/"):
        raise RuntimeError("canonical TVC vault broker socket path invalid")
    request = _request()
    result = broker.forward_to_local_vault_broker(request, socket_path=socket_path, timeout_seconds=60)
    if not isinstance(result, dict) or result.get("decision") != "ALLOW_OPERATION_RESULT":
        raise RuntimeError("canonical TVC broker did not return ALLOW_OPERATION_RESULT")
    use_receipt = result.get("use_receipt")
    if not isinstance(use_receipt, dict):
        raise RuntimeError("canonical TVC broker use_receipt missing")
    receipt = {
        "schema": "stegverse.mir-tvc-provider-roundtrip-receipt/v1",
        "goal_task_id": TASK_ID,
        "request_id": REQUEST_ID,
        "claim_id": task.get("claim_id"),
        "fencing_token": task.get("heartbeat_timing", {}).get("fencing_token"),
        "provider_operation_result": result,
        "ready_state": "READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND",
        "completion_candidate": "AUTHENTIC_TVC_MIR_PROVIDER_SESSION_OBSERVED",
        "intr_admission_required": True,
        "master_records_custody_required": True,
        "authority_effect": "NONE_EXECUTION_EVIDENCE_ONLY",
    }
    _write_receipt(root, receipt)
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED",
        "transition_id": "MIR_TVC_PROVIDER_OPERATION_COMPLETED",
        "transition_sequence": 1,
        "expected_next_transition": "INTERLOCK_INTR_RECEIPT_ADMISSION",
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
            "failure_recovery_units": 0,
            "services_used": ["mir"],
        },
        "authority_effect": "NONE_WORKER_PROTOCOL_TRANSLATION_ONLY",
    }


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
        if not isinstance(invocation, dict):
            raise ValueError("worker invocation must be a JSON object")
        response = run(invocation, root=Path.cwd())
    except Exception as exc:
        response = {
            "schema": "stegverse.worker-response/v0.1",
            "state": "HANDOFF_READY",
            "transition_id": "MIR_TVC_PROVIDER_OPERATION_FAIL_CLOSED",
            "transition_sequence": 1,
            "expected_next_transition": "MIR_TVC_PROVIDER_OPERATION_RETRY_AFTER_RECORDED_BOUNDARY",
            "expected_next_earliest_epoch": None,
            "expected_next_latest_epoch": None,
            "checkpoint_ref": None,
            "evidence_refs": [],
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
            "error_type": type(exc).__name__,
            "error": str(exc),
            "authority_effect": "NONE_FAIL_CLOSED",
        }
    print(json.dumps(response, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
