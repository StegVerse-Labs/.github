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

ACTIVE_STATE = "ACTIVE"
COMPLETED_STATE = "COMPLETED"
RETIRED_STATE = "RETIRED"
SUPERSEDED_STATE = "SUPERSEDED"
INVALID_STATE = "INVALID"
CANONICAL_TASK_STATES = {ACTIVE_STATE, COMPLETED_STATE, RETIRED_STATE, SUPERSEDED_STATE, INVALID_STATE}
TERMINAL_GOAL_STATES = {RETIRED_STATE}
HUMAN_REVIEW_STATES = {
    "HUMAN_REVIEW_REQUIRED",
    "USER_ACTION_REQUIRED",
    "HUMAN_ONLY",
    "USER_ONLY",
    "LEGAL_PERSON_SIGNATURE",
    "OWNER_EXPLICIT_CONSENT",
}
CLOSURE_KINDS = {
    "CLOSURE_VERIFICATION",
    "PROPAGATION_VERIFICATION",
    "RELEASE_VERIFICATION",
    "RETIREMENT_VERIFICATION",
    "RETIRE_TASK",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _state(value: Any) -> str:
    state = str(value or ACTIVE_STATE).strip().upper()
    return state if state in CANONICAL_TASK_STATES else INVALID_STATE


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
        "state": _state(task.get("state") or task.get("coordination_state")),
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
        "successor_task_id": task.get("successor_task_id"),
        "successor_cosv_task_vector": task.get("successor_cosv_task_vector"),
        "closure_predicates_satisfied": bool(task.get("closure_predicates_satisfied", False)),
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
        for key in ("cosv_task_vector", "state", "authority_class", "handoff", "canonical_record", "source_state_vector_ref", "registry_ref", "next_admissible_work", "successor_task_id", "successor_cosv_task_vector"):
            if task.get(key) not in (None, ""):
                merged[key] = task[key]
        merged["closure_predicates_satisfied"] = bool(previous.get("closure_predicates_satisfied") or task.get("closure_predicates_satisfied"))
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


def _work_kind(work: dict[str, Any] | None) -> str | None:
    if not isinstance(work, dict):
        return None
    value = work.get("kind")
    return str(value).strip().upper() if value else None


def _derive_next_work(record: dict[str, Any], execution_refs: list[str], state: str) -> dict[str, Any] | None:
    if state in {RETIRED_STATE, SUPERSEDED_STATE, INVALID_STATE}:
        return None
    explicit = record.get("next_admissible_work")
    if isinstance(explicit, dict):
        work = explicit
    elif isinstance(explicit, str) and explicit:
        work = {"kind": "CANONICAL_NEXT_ADMISSIBLE_WORK", "ref": explicit}
    else:
        work = None
        for key in ("next_transition", "next_action", "next_work", "continuation_action"):
            value = record.get(key)
            if isinstance(value, dict):
                work = {"kind": key.upper(), **value}
                break
            if isinstance(value, str) and value:
                work = {"kind": key.upper(), "ref": value}
                break
        if work is None and execution_refs:
            work = {"kind": "EXISTING_EXECUTION_REQUEST", "ref": execution_refs[0], "all_candidate_refs": execution_refs}
    if state == COMPLETED_STATE and _work_kind(work) not in CLOSURE_KINDS:
        return None
    return work


def resolve_compact_task_pointer(task_id: str, cosv_task_vector: str, *, task_index_path: Path = TASK_INDEX_PATH, task_registry_path: Path = TASK_REGISTRY_PATH) -> dict[str, Any]:
    task_id = str(task_id or "").strip()
    vector = str(cosv_task_vector or "").strip()
    if not task_id:
        raise ValueError("task_id is required for compact continuation")
    if len(vector) != 14 or not vector.isdigit():
        raise ValueError("cosv_task_vector must be a 14-digit task.v1 vector")

    index = _load_json(task_index_path)
    index_rows = index.get("tasks") if isinstance(index, dict) else None
    if not isinstance(index_rows, list):
        raise ValueError("canonical task-vector index shape is invalid")
    pointer_matches = [row for row in index_rows if isinstance(row, dict) and row.get("task_id") == task_id]
    if len(pointer_matches) != 1:
        raise ValueError("task_id must resolve exactly once in canonical task-vector index")
    pointer = pointer_matches[0]
    if str(pointer.get("vector") or "") != vector:
        raise ValueError("task_id/COSV vector binding mismatch")

    registry = _load_json(task_registry_path)
    registry_rows = registry.get("tasks") if isinstance(registry, dict) else None
    if not isinstance(registry_rows, list):
        raise ValueError("canonical task registry shape is invalid")
    matches = [row for row in registry_rows if isinstance(row, dict) and row.get("task_id") == task_id]
    if len(matches) != 1:
        raise ValueError("task_id must resolve exactly once in canonical task registry")
    record = matches[0]
    raw_state = record.get("coordination_state") or record.get("state")
    state = _state(raw_state)

    source_refs = [str(ref) for ref in list(record.get("source_refs") or []) if isinstance(ref, str)]
    handoffs = [ref for ref in source_refs if ref.endswith("_MIRROR_HANDOFF.md")]
    explicit_handoff = record.get("handoff")
    if isinstance(explicit_handoff, str) and explicit_handoff.endswith("_MIRROR_HANDOFF.md"):
        handoffs.append(explicit_handoff)
    handoffs = list(dict.fromkeys(handoffs))

    execution_refs = [] if state in {RETIRED_STATE, SUPERSEDED_STATE, INVALID_STATE} else _select_execution_refs(record, source_refs)
    next_work = _derive_next_work(record, execution_refs, state)
    successor_task_id = record.get("successor_task_id") or record.get("superseded_by_task_id")
    successor_vector = record.get("successor_cosv_task_vector") or record.get("superseded_by_cosv_task_vector")
    closure_ok = bool(record.get("closure_predicates_satisfied", False))

    return {
        "task_id": task_id,
        "cosv_task_vector": vector,
        "state": state,
        "raw_state": raw_state,
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
        "execution_request_refs": execution_refs,
        "next_admissible_work": next_work,
        "successor_task_id": successor_task_id,
        "successor_cosv_task_vector": successor_vector,
        "closure_predicates_satisfied": closure_ok,
        "admissible_repair_available": bool(record.get("admissible_repair_available", False)),
        "next_transition_available": state in {ACTIVE_STATE, COMPLETED_STATE} and bool(record.get("next_transition_available", True)),
        "retired_terminal": state == RETIRED_STATE,
        "history_reviewable": state == RETIRED_STATE,
        "resurrection_execution_permitted": False,
    }


def _build_continuation_request(task: dict[str, Any]) -> dict[str, Any] | None:
    if task.get("state") not in {ACTIVE_STATE, COMPLETED_STATE}:
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


def _superseded_redirect(task: dict[str, Any]) -> dict[str, Any] | None:
    successor = task.get("successor_task_id")
    if not successor:
        return None
    return {
        "schema": "stegverse.superseded-task-redirect/v1",
        "from_task_id": task["task_id"],
        "from_cosv_task_vector": task.get("cosv_task_vector"),
        "to_task_id": successor,
        "to_cosv_task_vector": task.get("successor_cosv_task_vector"),
        "redirect_only": True,
        "source_task_execution_permitted": False,
    }


def evaluate(payload: dict[str, Any], contract: dict[str, Any] | None = None) -> dict[str, Any]:
    if contract is None:
        contract = _load_json(CONTRACT_PATH)
    report_interval = int(contract["goal_resolution_continuation"]["default_report_interval_iterations"])
    iteration = int(payload.get("iteration") or 1)
    if iteration < 1:
        raise ValueError("iteration must be >= 1")

    returned = list(payload.get("returned_tasks") or [])
    compact_resolution = None
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

    active = [row for row in tasks if row["state"] == ACTIVE_STATE]
    completed = [row for row in tasks if row["state"] == COMPLETED_STATE]
    retired = [row for row in tasks if row["state"] == RETIRED_STATE]
    superseded = [row for row in tasks if row["state"] == SUPERSEDED_STATE]
    invalid = [row for row in tasks if row["state"] == INVALID_STATE]
    human_review = [row for row in active + completed if row["authority_class"] in HUMAN_REVIEW_STATES]
    continuation_requests = [req for req in (_build_continuation_request(row) for row in active + completed) if req]
    history_requested = bool(payload.get("history_review") or payload.get("review_retired_task"))
    history_review = [_history_review_projection(row) for row in retired] if history_requested else []
    redirects = [redirect for redirect in (_superseded_redirect(row) for row in superseded) if redirect]

    incomplete_completed = [row for row in completed if not row["closure_predicates_satisfied"] and row.get("next_admissible_work") is None]
    completed_ready_to_retire = [row for row in completed if row["closure_predicates_satisfied"]]

    if invalid:
        disposition, surface_response, continue_machine_work = "INVALID_CANONICAL_TASK_STATE", True, False
    elif retired and not (active or completed or superseded):
        disposition = "RETIRED_HISTORY_REVIEW" if history_requested else "RETIRED_TERMINAL"
        surface_response, continue_machine_work = True, False
    elif superseded and not (active or completed):
        disposition = "SUPERSEDED_REDIRECT" if len(redirects) == len(superseded) else "SUPERSEDED_SUCCESSOR_UNRESOLVED"
        surface_response, continue_machine_work = True, False
    elif completed_ready_to_retire and not active and not incomplete_completed:
        disposition, surface_response, continue_machine_work = "COMPLETED_READY_TO_RETIRE", True, False
    elif human_review or payload.get("human_review_required"):
        disposition, surface_response, continue_machine_work = "HUMAN_REVIEW_REQUIRED", True, False
    elif incomplete_completed:
        disposition, surface_response, continue_machine_work = "COMPLETED_CLOSURE_RESOLUTION_INCOMPLETE", True, False
    elif (active or completed) and not continuation_requests:
        disposition, surface_response, continue_machine_work = "CONTINUATION_RESOLUTION_INCOMPLETE", True, False
    else:
        surface_response = iteration % report_interval == 0
        disposition = "REPORT_AND_CONTINUE" if surface_response else "CONTINUE_AUTONOMOUSLY"
        continue_machine_work = True

    return {
        "schema": "stegverse.goal-resolution-continuation-evaluation/v5",
        "goal_id": goal_id,
        "iteration": iteration,
        "canonical_task_states": sorted(CANONICAL_TASK_STATES),
        "disposition": disposition,
        "surface_response": surface_response,
        "continue_machine_work": continue_machine_work,
        "automatic_reingestion": True,
        "automatic_pickup_required": bool(continuation_requests),
        "compact_pointer_resolved": compact_resolution is not None,
        "compact_pointer_resolution": compact_resolution,
        "active_task_ids": [row["task_id"] for row in active],
        "completed_task_ids": [row["task_id"] for row in completed],
        "completed_ready_to_retire_task_ids": [row["task_id"] for row in completed_ready_to_retire],
        "retired_task_ids": [row["task_id"] for row in retired],
        "superseded_task_ids": [row["task_id"] for row in superseded],
        "invalid_task_ids": [row["task_id"] for row in invalid],
        "retired_is_terminal": True,
        "retired_resurrection_review_only": True,
        "history_review": history_review,
        "superseded_redirects": redirects,
        "continuation_requests": continuation_requests,
        "new_work_from_retired_requires_new_task_id": True,
        "stale_handoff_cannot_override_canonical_state": True,
        "status_only_result_is_valid_continuation": False,
        "authority_effect": "NONE_COORDINATION_EVALUATION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate canonical task lifecycle and continuation.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    args = parser.parse_args()
    print(json.dumps(evaluate(_load_json(args.input), _load_json(args.contract)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
