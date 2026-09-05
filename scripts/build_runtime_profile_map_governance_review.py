#!/usr/bin/env python3
"""Build one exact-evidence governance-review package for a canonical task.

This package identifies the authority/review class that should inspect the current
post-reconciliation transition-readiness result. It does not grant admission,
execution, claim/fence, transition, credential, deployment, or consequence authority.
"""
from __future__ import annotations

import argparse
import hashlib
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_task(registry: dict[str, Any], task_id: str) -> dict[str, Any]:
    rows = [row for row in registry.get("tasks", []) if row.get("task_id") == task_id]
    require(len(rows) == 1, "task identity must resolve exactly once")
    return rows[0]


def review_authority(next_review: str | None) -> str:
    value = str(next_review or "")
    if value.startswith("WORKERCOORDINATOR_"):
        return "WORKERCOORDINATOR"
    if value.startswith("INTERLOCK_INTR_"):
        return "INTERLOCK_INTR"
    if value.startswith("MASTER_RECORDS_") or value.startswith("RECONCILIATION_"):
        return "MASTER_RECORDS_RECONCILIATION"
    if value == "DEPENDENCY_REEVALUATION":
        return "CANONICAL_COORDINATION"
    return "CANONICAL_COORDINATION"


def artifact(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"required evidence missing:{path}")
    return {"ref": str(path), "sha256": sha256(path)}


def build(task_id: str, registry_path: Path, worker_path: Path, routing_path: Path, reconciliation_path: Path, transition_path: Path) -> dict[str, Any]:
    registry = load(registry_path)
    task = find_task(registry, task_id)
    routing = load(routing_path)
    reconciliation = load(reconciliation_path)
    transition = load(transition_path)
    worker_registry = load(worker_path)

    correlation_id = task.get("correlation_id")
    require(routing.get("task_id") == task_id, "routing readiness task mismatch")
    require(reconciliation.get("task_id") == task_id, "reconciliation task mismatch")
    require(reconciliation.get("correlation_id") == correlation_id, "reconciliation correlation mismatch")
    require(transition.get("task_id") == task_id, "transition readiness task mismatch")
    require(transition.get("correlation_id") == correlation_id, "transition readiness correlation mismatch")
    require(transition.get("execution_authority_granted") is False, "transition readiness cannot grant execution authority")
    require(transition.get("claim_or_fence_minted") is False, "transition readiness cannot mint claim/fence")
    require(transition.get("interlock_intr_admission_granted") is False, "transition readiness cannot grant InTr admission")

    worker_matches = [row for row in worker_registry.get("tasks", []) if row.get("task_id") == task_id or row.get("goal_id") == task_id]
    require(len(worker_matches) <= 1, "ambiguous WorkerCoordinator projection")
    worker = worker_matches[0] if worker_matches else None

    next_review = transition.get("next_governance_review")
    return {
        "schema": "stegverse.runtime-profile-map-governance-review/v1",
        "task_id": task_id,
        "correlation_id": correlation_id,
        "task_coordination_state": task.get("coordination_state"),
        "transition_readiness_disposition": transition.get("disposition"),
        "next_governance_review": next_review,
        "review_authority_class": review_authority(next_review),
        "workercoordinator_projection": {
            "matched": worker is not None,
            "claim_id": worker.get("claim_id") if isinstance(worker, dict) else None,
            "worker_id": worker.get("worker_id") if isinstance(worker, dict) else None,
            "worker_instance_id": worker.get("worker_instance_id") if isinstance(worker, dict) else None,
            "state": worker.get("state") if isinstance(worker, dict) else None,
        },
        "evidence": {
            "canonical_task_registry": artifact(registry_path),
            "worker_registry": artifact(worker_path),
            "runtime_routing_readiness": artifact(routing_path),
            "master_records_reconciliation": artifact(reconciliation_path),
            "transition_readiness": artifact(transition_path),
        },
        "review_required_before_transition": True,
        "task_state_changed": False,
        "claim_or_fence_minted": False,
        "execution_authority_granted": False,
        "interlock_intr_admission_granted": False,
        "credential_authority": "TV/TVC",
        "heartbeat_or_oscillator_advanced": False,
        "authority_effect": "NONE_GOVERNANCE_REVIEW_PACKAGE_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--registry", type=Path, default=Path("data/canonical-task-registry.json"))
    parser.add_argument("--worker-registry", type=Path, default=Path("control/worker-registry.json"))
    parser.add_argument("--routing-readiness", type=Path, required=True)
    parser.add_argument("--reconciliation", type=Path, required=True)
    parser.add_argument("--transition-readiness", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build(args.task_id, args.registry, args.worker_registry, args.routing_readiness, args.reconciliation, args.transition_readiness)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
