#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "control/entity-autonomous-governed-progression-contract.json"
TASK_INDEX_PATH = ROOT / "control/task-vector-index.json"
TASK_REGISTRY_PATH = ROOT / "data/canonical-task-registry.json"

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
    state = str(task.get("state") or task.get("coordination_state") or "ACTIVE").strip().upper()

    return {
        "task_id": task_id,
        "cosv_task_vector": vector,
        "state": state,
        "authority_class": authority_class,
        "handoff": task.get("handoff"),
        "dependencies": list(task.get("dependencies") or task.get("dependency_refs") or []),
        "adjacent_tasks": list(task.get("adjacent_tasks") or task.get("adjacent_task_refs") or []),
        "integration_candidates": list(task.get("integration_candidates") or []),
        "receipts": list(task.get("receipts") or task.get("existing_evidence_refs") or []),
        "admissible_repair_available": bool(task.get("admissible_repair_available", False)),
        "next_transition_available": bool(task.get("next_transition_available", True)),
        "canonical_record": task.get("canonical_record"),
        "applicable_handoffs": list(task.get("applicable_handoffs") or []),
        "source_state_vector_ref": task.get("source_state_vector_ref"),
        "registry_ref": task.get("registry_ref"),
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
        for key in (
            "dependencies",
            "adjacent_tasks",
            "integration_candidates",
            "receipts",
            "applicable_handoffs",
        ):
            merged[key] = list(dict.fromkeys([*previous.get(key, []), *task.get(key, [])]))
        for key in (
            "cosv_task_vector",
            "state",
            "authority_class",
            "handoff",
            "canonical_record",
            "source_state_vector_ref",
            "registry_ref",
        ):
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


def resolve_compact_task_pointer(
    task_id: str,
    cosv_task_vector: str,
    *,
    task_index_path: Path = TASK_INDEX_PATH,
    task_registry_path: Path = TASK_REGISTRY_PATH,
) -> dict[str, Any]:
    """Resolve task_id + COSV task.v1 vector into canonical continuation context.

    Resolution is non-authorizing. It verifies the compact pointer, loads the canonical
    task record, and projects applicable mirror handoffs and canonical references so a
    caller does not need to restate task prose or pre-expand returned_tasks.
    """
    task_id = str(task_id or "").strip()
    vector = str(cosv_task_vector or "").strip()
    if not task_id:
        raise ValueError("task_id is required for compact continuation")
    if len(vector) != 14 or not vector.isdigit():
        raise ValueError("cosv_task_vector must be a 14-digit task.v1 vector")

    index = _load_json(task_index_path)
    rows = index.get("tasks") if isinstance(index, dict) else None
    if not isinstance(rows, list):
        raise ValueError("canonical task-vector index shape is invalid")
    index_matches = [row for row in rows if isinstance(row, dict) and row.get("task_id") == task_id]
    if len(index_matches) != 1:
        raise ValueError("task_id must resolve exactly once in canonical task-vector index")
    pointer = index_matches[0]
    if str(pointer.get("vector") or "") != vector:
        raise ValueError("task_id/COSV vector binding mismatch")

    registry = _load_json(task_registry_path)
    task_rows = registry.get("tasks") if isinstance(registry, dict) else None
    if not isinstance(task_rows, list):
        raise ValueError("canonical task registry shape is invalid")
    registry_matches = [row for row in task_rows if isinstance(row, dict) and row.get("task_id") == task_id]
    if len(registry_matches) != 1:
        raise ValueError("task_id must resolve exactly once in canonical task registry")
    record = registry_matches[0]

    source_refs = [str(ref) for ref in list(record.get("source_refs") or []) if isinstance(ref, str)]
    handoffs = [ref for ref in source_refs if ref.endswith("_MIRROR_HANDOFF.md")]
    explicit_handoff = record.get("handoff")
    if isinstance(explicit_handoff, str) and explicit_handoff.endswith("_MIRROR_HANDOFF.md"):
        handoffs.append(explicit_handoff)
    handoffs = list(dict.fromkeys(handoffs))

    return {
        "task_id": task_id,
        "cosv_task_vector": vector,
        "state": record.get("coordination_state") or record.get("state") or "ACTIVE",
        "authority_class": record.get("authority_class") or "MACHINE_GOVERNED",
        "handoff": handoffs[0] if handoffs else None,
        "applicable_handoffs": handoffs,
        "dependencies": list(record.get("dependency_refs") or record.get("dependencies") or []),
        "adjacent_tasks": list(record.get("adjacent_task_refs") or record.get("adjacent_tasks") or []),
        "integration_candidates": list(record.get("integration_candidates") or []),
        "receipts": list(record.get("existing_evidence_refs") or record.get("receipts") or []),
        "source_state_vector_ref": pointer.get("source_state_vector_ref"),
        "registry_ref": pointer.get("registry_ref") or str(task_registry_path.relative_to(ROOT)),
        "canonical_record": record,
        "root_correlation_id": record.get("root_correlation_id") or record.get("correlation_id") or task_id,
        "pointer_binding_verified": True,
        "authority_effect": "NONE_COORDINATION_RESOLUTION_ONLY",
        "admissible_repair_available": bool(record.get("admissible_repair_available", False)),
        "next_transition_available": bool(record.get("next_transition_available", True)),
    }


def evaluate(payload: dict[str, Any], contract: dict[str, Any] | None = None) -> dict[str, Any]:
    if contract is None:
        contract = _load_json(CONTRACT_PATH)

    continuation = contract["goal_resolution_continuation"]
    report_interval = int(continuation["default_report_interval_iterations"])

    iteration = int(payload.get("iteration") or 1)
    if iteration < 1:
        raise ValueError("iteration must be >= 1")

    returned = list(payload.get("returned_tasks") or [])
    compact_resolution: dict[str, Any] | None = None
    compact_task_id = payload.get("task_id")
    compact_vector = payload.get("cosv_task_vector")
    if compact_task_id is not None or compact_vector is not None:
        if compact_task_id is None or compact_vector is None:
            raise ValueError("compact continuation requires both task_id and cosv_task_vector")
        compact_resolution = resolve_compact_task_pointer(str(compact_task_id), str(compact_vector))
        returned.append(compact_resolution)

    tasks = _deduplicate([_normalize_task(row) for row in returned])

    goal_id = str(payload.get("goal_id") or "").strip()
    if not goal_id and compact_resolution is not None:
        goal_id = str(compact_resolution.get("root_correlation_id") or compact_resolution["task_id"])
    if not goal_id:
        raise ValueError("goal_id is required unless task_id + cosv_task_vector resolves it canonically")

    goal_state = str(payload.get("goal_state") or "ACTIVE").strip().upper()

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
            "applicable_handoffs": row.get("applicable_handoffs", []),
            "source_state_vector_ref": row.get("source_state_vector_ref"),
            "registry_ref": row.get("registry_ref"),
            "state": row["state"],
        }
        for row in active_tasks
    ]

    return {
        "schema": "stegverse.goal-resolution-continuation-evaluation/v2",
        "goal_id": goal_id,
        "iteration": iteration,
        "report_interval_iterations": report_interval,
        "disposition": disposition,
        "surface_response": surface_response,
        "continue_machine_work": continue_machine_work,
        "automatic_reingestion": True,
        "compact_pointer_resolved": compact_resolution is not None,
        "compact_pointer_resolution": compact_resolution,
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
    parser.add_argument("input", type=Path, help="JSON observation or compact task_id + COSV continuation pointer")
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    args = parser.parse_args()

    result = evaluate(_load_json(args.input), _load_json(args.contract))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
