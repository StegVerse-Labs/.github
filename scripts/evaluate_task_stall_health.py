#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "data/task-stall-detection-contract.json"
SHARDED_INDEX_DIR = ROOT / "control/task-vector-index.d"
MONOLITHIC_INDEX_PATH = ROOT / "control/task-vector-index.json"
MONOLITHIC_REGISTRY_PATH = ROOT / "data/canonical-task-registry.json"

TERMINAL_STATES = {"RETIRED", "SUPERSEDED", "INVALID"}
SATISFIED_DEP_STATES = {"SATISFIED", "RESOLVED", "COMPLETE", "COMPLETED", "PASS"}
BLOCKING_DEP_STATES = {"BLOCKED", "DENY", "FAILED", "UNRESOLVED"}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _int(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _resolve_record(task_id: str, vector: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    shard = SHARDED_INDEX_DIR / f"{task_id}.json"
    if shard.exists():
        pointer = _load_json(shard)
        if pointer.get("task_id") != task_id:
            raise ValueError("sharded task index identity mismatch")
        if str(pointer.get("vector") or "") != vector:
            raise ValueError("task_id/COSV vector binding mismatch")
        registry_ref = pointer.get("registry_ref")
        if not isinstance(registry_ref, str) or not registry_ref:
            raise ValueError("sharded task index is missing registry_ref")
        record_path = ROOT / registry_ref
        if not record_path.exists():
            raise ValueError("sharded task registry_ref does not exist")
        record = _load_json(record_path)
        if record.get("task_id") != task_id:
            raise ValueError("sharded canonical task record identity mismatch")
        return pointer, record, registry_ref

    index = _load_json(MONOLITHIC_INDEX_PATH)
    rows = index.get("tasks") if isinstance(index, dict) else None
    if not isinstance(rows, list):
        raise ValueError("canonical task-vector index shape is invalid")
    matches = [row for row in rows if isinstance(row, dict) and row.get("task_id") == task_id]
    if len(matches) != 1:
        raise ValueError("task_id must resolve exactly once in canonical task-vector index")
    pointer = matches[0]
    if str(pointer.get("vector") or "") != vector:
        raise ValueError("task_id/COSV vector binding mismatch")

    registry = _load_json(MONOLITHIC_REGISTRY_PATH)
    task_rows = registry.get("tasks") if isinstance(registry, dict) else None
    if not isinstance(task_rows, list):
        raise ValueError("canonical task registry shape is invalid")
    record_matches = [row for row in task_rows if isinstance(row, dict) and row.get("task_id") == task_id]
    if len(record_matches) != 1:
        raise ValueError("task_id must resolve exactly once in canonical task registry")
    return pointer, record_matches[0], "data/canonical-task-registry.json"


def _next_work(record: dict[str, Any]) -> Any:
    for key in ("next_admissible_work", "next_transition", "next_action", "next_work", "continuation_action"):
        value = record.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _blocking_dependencies(record: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for dep in list(record.get("dependencies") or record.get("dependency_refs") or []):
        if not isinstance(dep, dict):
            continue
        state = str(dep.get("state") or "").strip().upper()
        if dep.get("prevents_transition") is True or state in BLOCKING_DEP_STATES:
            result.append(dep)
    return result


def evaluate_task_health(task_id: str, vector: str, *, now: datetime | None = None) -> dict[str, Any]:
    if not task_id:
        raise ValueError("task_id is required")
    if len(vector) != 14 or not vector.isdigit():
        raise ValueError("cosv_task_vector must be a 14-digit task.v1 vector")

    contract = _load_json(CONTRACT_PATH)
    defaults = contract["defaults"]
    pointer, record, registry_ref = _resolve_record(task_id, vector)

    state = str(record.get("coordination_state") or record.get("state") or "ACTIVE").strip().upper()
    health_obs = record.get("task_health") if isinstance(record.get("task_health"), dict) else {}
    blockers = list(record.get("blockers") or [])
    blocking_dependencies = _blocking_dependencies(record)
    waiting_condition = record.get("waiting_condition") or health_obs.get("waiting_condition")
    next_work = _next_work(record)

    attempts = _int(health_obs.get("continuation_attempts_since_progress", record.get("continuation_attempts_since_progress", 0)))
    same_resolution_count = _int(health_obs.get("same_resolution_count", record.get("same_resolution_count", 0)))
    attempts_threshold = _int(health_obs.get("attempts_without_progress_to_stall", defaults["attempts_without_progress_to_stall"]), 3) or 3
    same_resolution_threshold = _int(health_obs.get("same_resolution_count_to_stall", defaults["same_resolution_count_to_stall"]), 3) or 3
    wall_clock_threshold = health_obs.get("wall_clock_stall_seconds", record.get("wall_clock_stall_seconds", defaults.get("wall_clock_stall_seconds")))
    wall_clock_threshold = _int(wall_clock_threshold) if wall_clock_threshold is not None else None
    last_progress_at = _parse_time(health_obs.get("last_progress_at", record.get("last_progress_at")))
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    time_stalled = False
    seconds_since_progress: int | None = None
    if wall_clock_threshold is not None and last_progress_at is not None:
        seconds_since_progress = max(0, int((now - last_progress_at).total_seconds()))
        time_stalled = seconds_since_progress >= wall_clock_threshold

    reasons: list[str] = []
    if state in TERMINAL_STATES:
        health = "TERMINAL"
        reasons.append(f"lifecycle is {state}")
    elif blockers or blocking_dependencies:
        health = "BLOCKED"
        if blockers:
            reasons.append(f"{len(blockers)} explicit blocker(s)")
        if blocking_dependencies:
            reasons.append(f"{len(blocking_dependencies)} dependency condition(s) prevent progression")
    elif waiting_condition not in (None, "", [], {}):
        health = "WAITING"
        reasons.append("explicit waiting condition is recorded")
    elif next_work in (None, "", [], {}):
        health = "STUCK"
        reasons.append("nonterminal task has no resolvable next admissible work and no explicit wait/block condition")
    elif attempts >= attempts_threshold or same_resolution_count >= same_resolution_threshold or time_stalled:
        health = "STALLED"
        if attempts >= attempts_threshold:
            reasons.append(f"{attempts} continuation attempts since last progress (threshold {attempts_threshold})")
        if same_resolution_count >= same_resolution_threshold:
            reasons.append(f"same continuation resolution repeated {same_resolution_count} times (threshold {same_resolution_threshold})")
        if time_stalled:
            reasons.append(f"{seconds_since_progress} seconds since progress (threshold {wall_clock_threshold})")
    else:
        health = "PROGRESSING"
        reasons.append("continuation path exists and no stall threshold is exceeded")

    return {
        "schema": "stegverse.task-stall-health-evaluation/v1",
        "task_id": task_id,
        "cosv_task_vector": vector,
        "pointer_binding_verified": True,
        "registry_ref": registry_ref,
        "source_state_vector_ref": pointer.get("source_state_vector_ref"),
        "lifecycle": state,
        "health": health,
        "reasons": reasons,
        "next_admissible_work": next_work,
        "blocking_dependency_count": len(blocking_dependencies),
        "blocker_count": len(blockers),
        "waiting_condition": waiting_condition,
        "continuation_attempts_since_progress": attempts,
        "same_resolution_count": same_resolution_count,
        "last_progress_at": last_progress_at.isoformat().replace("+00:00", "Z") if last_progress_at else None,
        "seconds_since_progress": seconds_since_progress,
        "stall_thresholds": {
            "attempts_without_progress": attempts_threshold,
            "same_resolution_count": same_resolution_threshold,
            "wall_clock_seconds": wall_clock_threshold,
        },
        "health_is_lifecycle": False,
        "percentage_complete_inferred": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Derive canonical task stall/stuck health from Task ID + COSV.")
    parser.add_argument("task_id")
    parser.add_argument("cosv_task_vector")
    parser.add_argument("--now", help="Optional ISO-8601 UTC/reference time for deterministic tests")
    args = parser.parse_args()
    now = _parse_time(args.now) if args.now else None
    print(json.dumps(evaluate_task_health(args.task_id, args.cosv_task_vector, now=now), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
