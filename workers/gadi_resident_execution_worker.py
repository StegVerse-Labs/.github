#!/usr/bin/env python3
"""ProcessWorkerAdapter protocol bridge for GADI resident execution.

This worker does not create claims, fences, InTr decisions, runtime bindings,
actuator effects, credentials, or a second runtime. It receives the already-fenced
WorkerCoordinator task row through the canonical process-worker invocation, passes
that exact row to the existing GADI dispatcher for local staging, and translates
the dispatcher result into the standard worker-response envelope.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from scripts.dispatch_gadi_resident_execution import dispatch

TASK_ID = "GADI-RESIDENT-EXECUTION-001"
DISPATCH_RECEIPT = "receipts/sovereign-host/gadi-resident-dispatch.latest.json"
CONSUMPTION_RECEIPT = "receipts/sovereign-host/gadi-resident-execution-consumption.latest.json"


def validate_invocation(invocation: dict[str, Any]) -> dict[str, Any]:
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        raise ValueError("worker invocation schema mismatch")
    task = invocation.get("task")
    scope = invocation.get("scope")
    if not isinstance(task, dict) or not isinstance(scope, dict):
        raise ValueError("worker invocation task/scope missing")
    if task.get("task_id") != TASK_ID:
        raise ValueError("worker invocation task mismatch")
    if task.get("state") != "ACTIVE":
        raise ValueError("worker invocation task is not ACTIVE")
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


def response_for_dispatch(result: dict[str, Any]) -> dict[str, Any]:
    consumed = result.get("state") == "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED"
    evidence = [DISPATCH_RECEIPT]
    checkpoint = DISPATCH_RECEIPT
    if consumed:
        evidence.append(CONSUMPTION_RECEIPT)
        checkpoint = CONSUMPTION_RECEIPT
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED" if consumed else "HANDOFF_READY",
        "transition_id": "GADI_RESIDENT_EVIDENCE_CONSUMED" if consumed else "GADI_RUNTIME_EVIDENCE_NOT_READY",
        "transition_sequence": 1,
        "expected_next_transition": None if consumed else "GADI_RUNTIME_EVIDENCE_READY",
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": checkpoint,
        "evidence_refs": evidence,
        "cost_observation": {
            "compute_units": 1,
            "token_units": 0,
            "storage_bytes": 0,
            "network_bytes": 0,
            "operator_seconds": 0,
            "external_cost_usd": 0,
            "latency_ms": None,
            "failure_recovery_units": 0 if consumed else 1,
            "services_used": [],
        },
        "authority_effect": "NONE_WORKER_PROTOCOL_TRANSLATION_ONLY",
    }


def run(
    invocation: dict[str, Any],
    *,
    root: Path,
    dispatcher: Callable[..., dict[str, Any]] = dispatch,
) -> dict[str, Any]:
    task = validate_invocation(invocation)
    result = dispatcher(root, root, current_worker_claim=task)
    if not isinstance(result, dict):
        raise RuntimeError("GADI dispatcher returned no machine result")
    return response_for_dispatch(result)


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
        if not isinstance(invocation, dict):
            raise ValueError("worker invocation must be a JSON object")
        response = run(invocation, root=Path.cwd())
    except Exception as exc:
        # ProcessWorkerAdapter expects a valid worker-response envelope. Returning
        # HANDOFF_READY relinquishes the current claim; it does not promote the
        # failure into execution evidence or retain stale ownership.
        response = {
            "schema": "stegverse.worker-response/v0.1",
            "state": "HANDOFF_READY",
            "transition_id": "GADI_WORKER_PROTOCOL_FAIL_CLOSED",
            "transition_sequence": 1,
            "expected_next_transition": "GADI_RUNTIME_EVIDENCE_READY",
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
