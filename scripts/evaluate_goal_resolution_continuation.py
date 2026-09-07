#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "control/entity-autonomous-governed-progression-contract.json"

TERMINAL_GOAL_STATES = {"COMPLETE", "COMPLETED", "TERMINAL", "RELEASED"}
HUMAN_REVIEW_STATES = {
    "HUMAN_REVIEW_REQUIRED",
    "USER_ACTION_REQUIRED",
    "HUMAN_ONLY",
    "USER_ONLY",
    "LEGAL_PERSON_SIGNATURE",
    "OWNER_EXPLICIT_CONSENT",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_task(task: dict[str, Any]) -> dict[str, Any]:
    task_id = str(task.get("task_id") or "").strip()
    if not task_id:
        raise ValueError("task_id is required for every returned task")

    vector = task.get("cosv_task_vector")
    if vector is not None:
        vector = str(vector).strip()
        if len(vector) != 14 or any(ch not in "0123456789" for ch in vector):
            raise ValueError(f"invalid cosv_task_vector for {task_id}: expected 14 digits")

    authority_class = str(task.get("authority_class") or "MACHINE_GOVERNED").strip().upper()
    state = str(task.get("state") or "ACTIVE").strip().upper()

    return {
        "task_id": task_id,
        "cosv_task_vector": vector,
        "state": state,
        "authority_class": authority_class,
        "handoff": task.get("handoff"),
        "dependencies": list(task.get("dependencies") or []),
        "adjacent_tasks": list(task.get("adjacent_tasks") or []),
        "integration_candidates": list(task.get("integration_candidates") or []),
        "receipts": list(task.get("receipts") or []),
        "admissible_repair_available": bool(task.get("admissible_repair_available", False)),
        "next_transition_available": bool(task.get("next_transition_available", True)),
    }


def _deduplicate(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for task in tasks:
        task_id = task["task_id"]
        if task_id not in by_id:
            by_id[task_id] = task
            order.append(task_id)
            continue

        previous = by_id[task_id]
        merged = dict(previous)
        for key in ("dependencies", "adjacent_tasks", "integration_candidates", "receipts"):
            merged[key] = list(dict.fromkeys([*previous.get(key, []), *task.get(key, [])]))
        for key in ("cosv_task_vector", "state", "authority_class", "handoff"):
            if task.get(key) not in (None, ""):
                merged[key] = task[key]
        merged["admissible_repair_available"] = bool(
            previous.get("admissible_repair_available") or task.get("admissible_repair_available")
        )
        merged["next_transition_available"] = bool(
            previous.get("next_transition_available") or task.get("next_transition_available")
        )
        by_id[task_id] = merged
    return [by_id[task_id] for task_id in order]


def evaluate(payload: dict[str, Any], contract: dict[str, Any] | None = None) -> dict[str, Any]:
    if contract is None:
        contract = _load_json(CONTRACT_PATH)

    continuation = contract["goal_resolution_continuation"]
    report_interval = int(continuation["default_report_interval_iterations"])

    iteration = int(payload.get("iteration") or 1)
    if iteration < 1:
        raise ValueError("iteration must be >= 1")

    goal_id = str(payload.get("goal_id") or "").strip()
    if not goal_id:
        raise ValueError("goal_id is required")

    goal_state = str(payload.get("goal_state") or "ACTIVE").strip().upper()
    tasks = _deduplicate([_normalize_task(row) for row in list(payload.get("returned_tasks") or [])])

    human_review_tasks = [
        row for row in tasks if row["authority_class"] in HUMAN_REVIEW_STATES or row["state"] in HUMAN_REVIEW_STATES
    ]
    terminal_tasks = [row for row in tasks if row["state"] in TERMINAL_GOAL_STATES]
    active_tasks = [row for row in tasks if row["state"] not in TERMINAL_GOAL_STATES]

    no_repair_denials = [
        row
        for row in active_tasks
        if row["state"] == "DENY"
        and not row["admissible_repair_available"]
        and not row["next_transition_available"]
    ]

    human_review_required = bool(human_review_tasks or payload.get("human_review_required"))
    goal_complete = goal_state in TERMINAL_GOAL_STATES or bool(payload.get("goal_complete"))
    hard_machine_stop = bool(no_repair_denials or payload.get("hard_machine_stop"))

    if goal_complete:
        disposition = "GOAL_COMPLETE"
        surface_response = True
        continue_machine_work = False
    elif human_review_required:
        disposition = "HUMAN_REVIEW_REQUIRED"
        surface_response = True
        continue_machine_work = False
    elif hard_machine_stop:
        disposition = "MACHINE_STOP_NO_ADMISSIBLE_REPAIR"
        surface_response = True
        continue_machine_work = False
    else:
        surface_response = iteration % report_interval == 0
        disposition = "REPORT_AND_CONTINUE" if surface_response else "CONTINUE_AUTONOMOUSLY"
        continue_machine_work = True

    continuation_pointers = [
        {
            "task_id": row["task_id"],
            "cosv_task_vector": row["cosv_task_vector"],
            "handoff": row["handoff"],
            "state": row["state"],
        }
        for row in active_tasks
    ]

    return {
        "schema": "stegverse.goal-resolution-continuation-evaluation/v1",
        "goal_id": goal_id,
        "iteration": iteration,
        "report_interval_iterations": report_interval,
        "disposition": disposition,
        "surface_response": surface_response,
        "continue_machine_work": continue_machine_work,
        "automatic_reingestion": True,
        "returned_task_count": len(tasks),
        "active_task_count": len(active_tasks),
        "terminal_task_count": len(terminal_tasks),
        "human_review_task_ids": [row["task_id"] for row in human_review_tasks],
        "continuation_pointers": continuation_pointers,
        "deduplicated_task_ids": [row["task_id"] for row in tasks],
        "authority_effect": "NONE_COORDINATION_EVALUATION_ONLY",
        "workercoordinator_claim_fence_still_required": True,
        "interlock_intr_transition_admission_still_required": True,
        "credential_authority": contract["credential_authority"],
        "periodic_report_stops_machine_work": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate bounded autonomous goal-resolution continuation.")
    parser.add_argument("input", type=Path, help="JSON observation containing goal state and returned task/COSV/handoff state")
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    args = parser.parse_args()

    result = evaluate(_load_json(args.input), _load_json(args.contract))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
