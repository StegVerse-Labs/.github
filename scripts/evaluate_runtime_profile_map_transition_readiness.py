#!/usr/bin/env python3
"""Evaluate post-reconciliation transition readiness for one canonical task.

This is a non-authorizing decision projection. It combines current canonical task
state, current runtime-routing readiness, current Master Records reconciliation,
and current WorkerCoordinator projection to identify the next governance review
class. It never mutates task state, mints claim/fence, advances HB/oscillator, or
grants Interlock/InTr admission.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object required:{path}")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError("FAIL_CLOSED: " + reason)


def find_task(registry: dict[str, Any], task_id: str) -> dict[str, Any]:
    rows = [row for row in registry.get("tasks", []) if row.get("task_id") == task_id]
    require(len(rows) == 1, "task identity must resolve exactly once")
    return rows[0]


def evaluate(task: dict[str, Any], readiness: dict[str, Any], reconciliation: dict[str, Any], worker_registry: dict[str, Any]) -> dict[str, Any]:
    task_id = task.get("task_id")
    correlation_id = task.get("correlation_id")
    require(readiness.get("task_id") == task_id, "routing readiness task mismatch")
    require(reconciliation.get("task_id") == task_id, "reconciliation task mismatch")
    require(reconciliation.get("correlation_id") == correlation_id, "reconciliation correlation mismatch")

    worker_matches = [row for row in worker_registry.get("tasks", []) if row.get("task_id") == task_id or row.get("goal_id") == task_id]
    require(len(worker_matches) <= 1, "ambiguous WorkerCoordinator projection")
    worker = worker_matches[0] if worker_matches else None
    current_claim = worker.get("claim_id") if isinstance(worker, dict) else None
    current_fence = None
    if isinstance(worker, dict):
        timing = worker.get("heartbeat_timing")
        if isinstance(timing, dict):
            current_fence = timing.get("fencing_token")

    recon_state = reconciliation.get("state")
    route_disposition = readiness.get("disposition")
    unresolved = [d.get("dependency_id") for d in task.get("dependencies", []) if d.get("state") not in {"RESOLVED", "NOT_APPLICABLE"}]
    blockers = task.get("blockers", [])

    if recon_state == "CONFLICT":
        disposition = "BLOCK_FOR_RECONCILIATION_CONFLICT"
        next_review = "RECONCILIATION_REPAIR_OR_COMPLETION_REVOCATION_REVIEW"
    elif recon_state == "TASK_AHEAD_OF_EVIDENCE":
        disposition = "WAIT_FOR_REQUIRED_EVIDENCE"
        next_review = "MASTER_RECORDS_EVIDENCE_REVIEW"
    elif recon_state == "REALITY_AHEAD_OF_TASK":
        disposition = "RECONCILE_TASK_STATE_WITH_OBSERVED_REALITY"
        next_review = "INTERLOCK_INTR_TASK_STATE_RECONCILIATION_REVIEW"
    elif recon_state == "UNKNOWN":
        disposition = "WAIT_OR_REQUEST_EVIDENCE_RECONCILIATION"
        next_review = "MASTER_RECORDS_EVIDENCE_REVIEW"
    elif unresolved or blockers:
        disposition = "DEPENDENCY_OR_BLOCKER_PREVENTS_TRANSITION"
        next_review = "DEPENDENCY_REEVALUATION"
    elif current_claim:
        disposition = "EXISTING_WORKERCOORDINATOR_OWNERSHIP_REUSE_WAIT_OR_TRANSFER"
        next_review = "WORKERCOORDINATOR_EXISTING_CLAIM_REVIEW"
    elif route_disposition == "ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW":
        disposition = "ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW"
        next_review = "WORKERCOORDINATOR_ADMISSION_REVIEW"
    else:
        disposition = "NO_CURRENT_TRANSITION_CANDIDATE"
        next_review = "CANONICAL_COORDINATION_REEVALUATION"

    return {
        "schema": "stegverse.runtime-profile-map-transition-readiness/v1",
        "task_id": task_id,
        "correlation_id": correlation_id,
        "task_coordination_state": task.get("coordination_state"),
        "runtime_routing_disposition": route_disposition,
        "master_records_reconciliation_state": recon_state,
        "unresolved_dependencies": unresolved,
        "blocker_count": len(blockers),
        "workercoordinator_claim_ref": current_claim,
        "workercoordinator_fence_projection": current_fence,
        "disposition": disposition,
        "next_governance_review": next_review,
        "task_state_changed": False,
        "claim_or_fence_minted": False,
        "execution_authority_granted": False,
        "interlock_intr_admission_granted": False,
        "heartbeat_or_oscillator_advanced": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_TRANSITION_READINESS_PROJECTION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--registry", type=Path, default=Path("data/canonical-task-registry.json"))
    parser.add_argument("--worker-registry", type=Path, default=Path("control/worker-registry.json"))
    parser.add_argument("--routing-readiness", type=Path, required=True)
    parser.add_argument("--reconciliation", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    registry = load(args.registry)
    task = find_task(registry, args.task_id)
    result = evaluate(task, load(args.routing_readiness), load(args.reconciliation), load(args.worker_registry))
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
