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

TERMINAL_GOAL_STATES = {"COMPLETE", "COMPLETED", "TERMINAL", "RELEASED", "RETIRED"}
RETIRED_STATE = "RETIRED"
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
        if len(vector) != 14 or not vector.isdigit():
            raise ValueError(f"invalid cosv_task_vector for {task_id}: expected 14 digits")
    return {
        "task_id": task_id,
        "cosv_task_vector": vector,
        "state": str(task.get("state") or task.get("coordination_state") or "ACTIVE").strip().upper(),
        "authority_class": str(task.get("authority_class") or "MACHINE_GOVERNED").strip().upper(),
        "handoff": task.get("handoff"),
        "applicable_handoffs": list(task.get("applicable_handoffs") or []),
        "dependencies": list(task.get("dependencies") or task.get("dependency_refs") or []),
        "adjacent_tasks": list(task.get("adjacent_tasks") or task.get("adjacent_task_refs") or []),
        "integration_candidates": list(task.get("integration_candidates") or []),
        "receipts": list(task.get("receipts") or task.get("existing_evidence_refs") or []),
        "source_state_vector_ref": task.get("source_state_vector_ref"),
        "registry_ref": task.get("registry_ref"),
        "canonical_record": task.get("canonical_record"),
        "execution_request_refs": list(task.get("execution_request_refs") or []),
        "next_admissible_work": task.get("next_admissible_work"),
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
        for key in ("dependencies", "adjacent_tasks", "integration_candidates", "receipts", "applicable_handoffs", "execution_request_refs"):
            merged[key] = list(dict.fromkeys([*previous.get(key, []), *task.get(key, [])]))
        for key in ("cosv_task_vector", "state", "authority_class", "handoff", "canonical_record", "source_state_vector_ref", "registry_ref", "next_admissible_work"):
            if task.get(key) not in (None, ""):
                merged[key] = task[key]
        merged["admissible_repair_available"] = bool(previous.get("admissible_repair_available") or task.get("admissible_repair_available"))
        merged["next_transition_available"] = bool(previous.get("next_transition_available") or task.get("next_transition_available"))
        by_id[task_id] = merged
    return [by_id[task_id] for task_id in order]


def _select_execution_refs(record: dict[str, Any], source_refs: list[str]) -> list[str]:
    refs: list[str] = []
    for key in ("execution_request_ref", "resident_execution_request_ref", "continuation_request_ref", "work_request_ref"):
        value = record.get(key)
        if isinstance(value, str) and value:
            refs.append(value)
    for key in ("execution_request_refs", "resident_execution_request_refs", "continuation_request_refs", "work_request_refs"):
        value = record.get(key)
        if isinstance(value, list):
            refs.extend(str(item) for item in value if isinstance(item, str) and item)
    refs.extend(ref for ref in source_refs if ref.startswith("control/resident-execution-request.d/") and ref.endswith(".json"))
    return list(dict.fromkeys(refs))


def _derive_next_admissible_work(record: dict[str, Any], execution_refs: list[str]) -> dict[str, Any] | None:
    state = str(record.get("coordination_state") or record.get("state") or "ACTIVE").strip().upper()
    if state == RETIRED_STATE:
        return None
    explicit = record.get("next_admissible_work")
    if isinstance(explicit, dict):
        return explicit
    if isinstance(explicit, str) and explicit:
        return {"kind": "CANONICAL_NEXT_ADMISSIBLE_WORK", "ref": explicit}
    for key in ("next_transition", "next_action", "next_work", "continuation_action"):
        value = record.get(key)
        if isinstance(value, dict):
            return {"kind": key.upper(), **value}
        if isinstance(value, str) and value:
            return {"kind": key.upper(), "ref": value}
    if execution_refs:
        return {"kind": "EXISTING_EXECUTION_REQUEST", "ref": execution_refs[0], "all_candidate_refs": execution_refs}
    return None


def resolve_compact_task_pointer(
    task_id: str,
    cosv_task_vector: str,
    *,
    task_index_path: Path = TASK_INDEX_PATH,
    task_registry_path: Path = TASK_REGISTRY_PATH,
) -> dict[str, Any]:
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
    matches = [row for row in rows if isinstance(row, dict) and row.get("task_id") == task_id]
    if len(matches) != 1:
        raise ValueError("task_id must resolve exactly once in canonical task-vector index")
    pointer = matches[0]
    if str(pointer.get("vector") or "") != vector:
        raise ValueError("task_id/COSV vector binding mismatch")

    registry = _load_json(task_registry_path)
    rows = registry.get("tasks") if isinstance(registry, dict) else None
    if not isinstance(rows, list):
        raise ValueError("canonical task registry shape is invalid")
    matches = [row for row in rows if isinstance(row, dict) and row.get("task_id") == task_id]
    if len(matches) != 1:
        raise ValueError("task_id must resolve exactly once in canonical task registry")
    record = matches[0]

    state = str(record.get("coordination_state") or record.get("state") or "ACTIVE").strip().upper()
    source_refs = [str(ref) for ref in list(record.get("source_refs") or []) if isinstance(ref, str)]
    handoffs = [ref for ref in source_refs if ref.endswith("_MIRROR_HANDOFF.md")]
    explicit_handoff = record.get("handoff")
    if isinstance(explicit_handoff, str) and explicit_handoff.endswith("_MIRROR_HANDOFF.md"):
        handoffs.append(explicit_handoff)
    handoffs = list(dict.fromkeys(handoffs))
    execution_refs = [] if state == RETIRED_STATE else _select_execution_refs(record, source_refs)
    next_work = _derive_next_admissible_work(record, execution_refs)

    return {
        "task_id": task_id,
        "cosv_task_vector": vector,
        "state": state,
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
        "next_transition_available": False if state == RETIRED_STATE else bool(record.get("next_transition_available", True)),
        "execution_request_refs": execution_refs,
        "next_admissible_work": next_work,
        "retired_terminal": state == RETIRED_STATE,
        "history_reviewable": state == RETIRED_STATE,
        "resurrection_execution_permitted": False,
    }


def _build_continuation_request(task: dict[str, Any]) -> dict[str, Any] | None:
    if task.get("state") == RETIRED_STATE:
        return None
    next_work = task.get("next_admissible_work")
    if not isinstance(next_work, dict):
        return None
    return {
        "schema": "stegverse.machine-continuation-request/v1",
        "task_id": task["task_id"],
        "cosv_task_vector": task.get("cosv_task_vector"),
        "state": task.get("state"),
        "handoff": task.get("handoff"),
        "next_admissible_work": next_work,
        "execution_request_refs": list(task.get("execution_request_refs") or []),
        "automatic_pickup_required": True,
        "status_only_response_is_completion": False,
        "human_reentry_required": False,
    }


def _history_review_projection(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "stegverse.retired-task-history-review/v1",
        "task_id": task["task_id"],
        "cosv_task_vector": task.get("cosv_task_vector"),
        "state": RETIRED_STATE,
        "handoffs": list(task.get("applicable_handoffs") or []),
        "evidence_refs": list(task.get("receipts") or []),
        "source_state_vector_ref": task.get("source_state_vector_ref"),
        "registry_ref": task.get("registry_ref"),
        "review_only": True,
        "execution_permitted": False,
        "continuation_permitted": False,
        "claim_or_fence_permitted": False,
        "transition_permitted": False,
        "new_work_requires_new_task_id": True,
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
    if payload.get("task_id") is not None or payload.get("cosv_task_vector") is not None:
        if payload.get("task_id") is None or payload.get("cosv_task_vector") is None:
            raise ValueError("compact continuation requires both task_id and cosv_task_vector")
        compact_resolution = resolve_compact_task_pointer(str(payload["task_id"]), str(payload["cosv_task_vector"]))
        returned.append(compact_resolution)

    tasks = _deduplicate([_normalize_task(row) for row in returned])
    goal_id = str(payload.get("goal_id") or "").strip()
    if not goal_id and compact_resolution is not None:
        goal_id = str(compact_resolution.get("root_correlation_id") or compact_resolution["task_id"])
    if not goal_id:
        raise ValueError("goal_id is required unless task_id + cosv_task_vector resolves it canonically")

    goal_state = str(payload.get("goal_state") or "ACTIVE").strip().upper()
    retired_tasks = [row for row in tasks if row["state"] == RETIRED_STATE]
    terminal_tasks = [row for row in tasks if row["state"] in TERMINAL_GOAL_STATES]
    active_tasks = [row for row in tasks if row["state"] not in TERMINAL_GOAL_STATES]
    human_review_tasks = [row for row in active_tasks if row["authority_class"] in HUMAN_REVIEW_STATES or row["state"] in HUMAN_REVIEW_STATES]
    no_repair_denials = [row for row in active_tasks if row["state"] == "DENY" and not row["admissible_repair_available"] and not row["next_transition_available"]]
    continuation_requests = [request for request in (_build_continuation_request(row) for row in active_tasks) if request is not None]
    history_review_requested = bool(payload.get("history_review") or payload.get("review_retired_task"))
    history_review = [_history_review_projection(row) for row in retired_tasks] if history_review_requested else []

    if retired_tasks and not active_tasks:
        disposition = "RETIRED_HISTORY_REVIEW" if history_review_requested else "RETIRED_TERMINAL"
        surface_response = True
        continue_machine_work = False
    elif goal_state == RETIRED_STATE or goal_state in TERMINAL_GOAL_STATES or bool(payload.get("goal_complete")):
        disposition = "GOAL_COMPLETE"
        surface_response = True
        continue_machine_work = False
    elif human_review_tasks or payload.get("human_review_required"):
        disposition = "HUMAN_REVIEW_REQUIRED"
        surface_response = True
        continue_machine_work = False
    elif no_repair_denials or payload.get("hard_machine_stop"):
        disposition = "MACHINE_STOP_NO_ADMISSIBLE_REPAIR"
        surface_response = True
        continue_machine_work = False
    elif active_tasks and not continuation_requests:
        disposition = "CONTINUATION_RESOLUTION_INCOMPLETE"
        surface_response = True
        continue_machine_work = False
    else:
        surface_response = iteration % report_interval == 0
        disposition = "REPORT_AND_CONTINUE" if surface_response else "CONTINUE_AUTONOMOUSLY"
        continue_machine_work = True

    return {
        "schema": "stegverse.goal-resolution-continuation-evaluation/v4",
        "goal_id": goal_id,
        "iteration": iteration,
        "report_interval_iterations": report_interval,
        "disposition": disposition,
        "surface_response": surface_response,
        "continue_machine_work": continue_machine_work,
        "automatic_reingestion": True,
        "automatic_pickup_required": bool(continuation_requests),
        "compact_pointer_resolved": compact_resolution is not None,
        "compact_pointer_resolution": compact_resolution,
        "returned_task_count": len(tasks),
        "active_task_count": len(active_tasks),
        "terminal_task_count": len(terminal_tasks),
        "retired_task_count": len(retired_tasks),
        "retired_task_ids": [row["task_id"] for row in retired_tasks],
        "retired_is_terminal": True,
        "retired_resurrection_review_only": True,
        "history_review": history_review,
        "human_review_task_ids": [row["task_id"] for row in human_review_tasks],
        "continuation_requests": continuation_requests,
        "deduplicated_task_ids": [row["task_id"] for row in tasks],
        "authority_effect": "NONE_COORDINATION_EVALUATION_ONLY",
        "workercoordinator_claim_fence_still_required": True,
        "interlock_intr_transition_admission_still_required": True,
        "credential_authority": contract["credential_authority"],
        "periodic_report_stops_machine_work": False,
        "status_only_result_is_valid_continuation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate bounded autonomous goal-resolution continuation.")
    parser.add_argument("input", type=Path, help="JSON observation or compact task_id + COSV continuation pointer")
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    args = parser.parse_args()
    print(json.dumps(evaluate(_load_json(args.input), _load_json(args.contract)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
