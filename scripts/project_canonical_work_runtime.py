#!/usr/bin/env python3
"""Project canonical coordination against HB32 reference + WorkerCoordinator state.

This is a non-authorizing projection. It never advances heartbeat state, never mints
claims/fences, and never infers Interlock/InTr admission or Master Records reality.
The independent oscillator supplies reference timing only.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from heartbeat_runtime.intr_carrier_profile import derive_reference_from_unix_ms

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASK_REGISTRY = ROOT / "data" / "canonical-task-registry.json"
DEFAULT_WORKER_REGISTRY = ROOT / "control" / "worker-registry.json"
DEFAULT_PROFILE = ROOT / "control" / "canonical-work-runtime-profile.json"


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit(f"FAIL_CLOSED: {reason}")


def worker_projection(worker_registry: dict[str, Any], task_id: str) -> dict[str, Any]:
    matches = [task for task in worker_registry.get("tasks", []) if task.get("task_id") == task_id or task.get("goal_id") == task_id]
    if not matches:
        return {
            "matched": False,
            "claim_id": None,
            "worker_id": None,
            "worker_instance_id": None,
            "fencing_token": None,
            "worker_state": None,
            "projection_only": True,
            "authority": "WORKERCOORDINATOR"
        }
    require(len(matches) == 1, f"ambiguous WorkerCoordinator task match for {task_id}")
    task = matches[0]
    timing = task.get("heartbeat_timing") or {}
    timer = task.get("assignment_timer") or {}
    return {
        "matched": True,
        "claim_id": task.get("claim_id"),
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "fencing_token": timer.get("fencing_token", timing.get("fencing_token")),
        "worker_state": task.get("state"),
        "executor_binding": task.get("executor_binding"),
        "last_checkpoint_ref": task.get("last_checkpoint_ref"),
        "projection_only": True,
        "authority": "WORKERCOORDINATOR"
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-registry", default=str(DEFAULT_TASK_REGISTRY))
    parser.add_argument("--worker-registry", default=str(DEFAULT_WORKER_REGISTRY))
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--task-id", action="append", default=[])
    parser.add_argument("--output")
    args = parser.parse_args()

    registry = load(Path(args.task_registry))
    workers = load(Path(args.worker_registry))
    profile = load(Path(args.profile))

    require(profile.get("schema") == "stegverse.canonical-work-runtime-profile/v1", "runtime profile schema mismatch")
    hb = profile.get("heartbeat", {})
    require(hb.get("protocol_anchor") == "HB32", "HB32 protocol anchor required")
    require(hb.get("mechanism") == "INDEPENDENT_PHASE_OSCILLATOR", "independent oscillator required")
    require(hb.get("progression_dependency") == "OSCILLATOR_ONLY", "heartbeat progression must remain OSCILLATOR_ONLY")
    for key in ("carrier_grants_admission_authority", "carrier_grants_execution_authority", "carrier_grants_claim_or_fence_authority", "carrier_grants_transition_authority"):
        require(hb.get(key) is False, f"{key} must remain false")

    requested = set(args.task_id)
    now_ms = time.time_ns() // 1_000_000
    reference = derive_reference_from_unix_ms(now_ms)
    projected: list[dict[str, Any]] = []

    for task in registry.get("tasks", []):
        task_id = task.get("task_id")
        if requested and task_id not in requested:
            continue
        projected.append({
            "task_id": task_id,
            "correlation_id": task.get("correlation_id"),
            "coordination_state": task.get("coordination_state"),
            "dependencies": task.get("dependencies", []),
            "blockers": task.get("blockers", []),
            "allowed_next_transitions": task.get("allowed_next_transitions", []),
            "worker_claim_projection": worker_projection(workers, str(task_id)),
            "master_records_reconciliation": "NOT_SUPPLIED",
            "interlock_intr_ingress_observed": False,
            "interlock_intr_egress_observed": False,
            "heartbeat_reference": reference,
            "heartbeat_reference_grants_authority": False,
        })

    output = {
        "schema": "stegverse.canonical-work-runtime-projection/v1",
        "profile": "control/canonical-work-runtime-profile.json",
        "heartbeat": {
            "protocol_anchor": "HB32",
            "mechanism": "INDEPENDENT_PHASE_OSCILLATOR",
            "progression_dependency": "OSCILLATOR_ONLY",
            "reference": reference,
            "authority_effect": "NONE_REFERENCE_ONLY"
        },
        "tasks": projected,
        "nonclaims": [
            "PROJECTION_DOES_NOT_ADVANCE_HEARTBEAT",
            "PROJECTION_DOES_NOT_MINT_WORKERCOORDINATOR_CLAIM_OR_FENCE",
            "PROJECTION_DOES_NOT_PROVE_INTERLOCK_INTR_INGRESS_OR_EGRESS",
            "PROJECTION_DOES_NOT_PROVE_MASTER_RECORDS_REALITY",
            "PROJECTION_DOES_NOT_AUTHORIZE_TASK_EXECUTION"
        ]
    }

    raw = json.dumps(output, indent=2, sort_keys=True) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
