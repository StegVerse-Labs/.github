#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "control" / "archive-readiness.json"
REGISTRY_PATH = ROOT / "control" / "worker-registry.json"

TERMINAL = {"COMPLETED", "COMPLETE", "CLOSED", "CANCELLED", "SUPERSEDED", "FAILED_TERMINAL"}
ACTIVE_MACHINE_STATES = {"CLAIMED", "ACTIVE", "EXPIRING", "HANDOFF_WRITING", "FAILED_RETRYABLE"}
HUMAN_BOUNDARY_STATE = "HUMAN_AUTHORITY_REQUIRED"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def active_machine_executor(task: dict[str, Any]) -> bool:
    if task.get("state") not in ACTIVE_MACHINE_STATES:
        return False
    if task.get("executor_binding") not in {"BOUND", "AUTHORIZED"}:
        return False
    if not isinstance(task.get("worker_id"), str) or not task.get("worker_id"):
        return False
    if not isinstance(task.get("claim_id"), str) or not task.get("claim_id"):
        return False
    timing = task.get("heartbeat_timing")
    if not isinstance(timing, dict):
        return False
    if not isinstance(timing.get("fencing_token"), int) or not timing.get("current_transition"):
        return False
    if timing.get("expected_next_transition") is None and task.get("state") != "HANDOFF_WRITING":
        return False
    lease = task.get("lease")
    has_lease = isinstance(lease, dict) and bool(lease)
    has_runtime_window = isinstance(timing.get("expiry_epoch"), int) and isinstance(timing.get("start_epoch"), int)
    return has_lease or has_runtime_window


def active_session_claim(entry: dict[str, Any], root: Path, now: datetime) -> bool:
    ref = entry.get("active_session_claim_ref")
    if not isinstance(ref, str) or not ref:
        return False
    path = root / ref
    if not path.is_file():
        return False
    claim = load(path)
    if claim.get("claim_state") != "ACTIVE":
        return False
    task_id = entry.get("task_id")
    session_task_id = entry.get("session_task_id")
    if task_id and claim.get("task_id") not in {task_id, session_task_id}:
        return False
    expires = claim.get("claim_expires_at")
    if isinstance(expires, str):
        parsed = parse_time(expires)
        if parsed is None or parsed <= now:
            return False
    release = claim.get("claim_release_condition")
    collision = claim.get("collision_scope")
    return isinstance(release, str) and bool(release) and isinstance(collision, dict)


def explicit_human_boundary(entry: dict[str, Any], task: dict[str, Any]) -> bool:
    if task.get("state") != HUMAN_BOUNDARY_STATE:
        return False
    boundary = entry.get("human_authority_boundary")
    if not isinstance(boundary, dict):
        return False
    return all(isinstance(boundary.get(key), str) and bool(boundary.get(key)) for key in ("owner", "required_action", "durable_ref"))


def blocked_with_active_resolver(entry: dict[str, Any], tasks: dict[str, dict[str, Any]]) -> bool:
    resolver_id = entry.get("resolver_task_id")
    if not isinstance(resolver_id, str) or not resolver_id:
        return False
    resolver = tasks.get(resolver_id)
    if not isinstance(resolver, dict) or not active_machine_executor(resolver):
        return False
    release = entry.get("machine_observable_release_condition")
    return isinstance(release, str) and bool(release)


def evaluate(gate: dict[str, Any], registry: dict[str, Any], root: Path = ROOT, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    tasks = {t["task_id"]: t for t in registry.get("tasks", []) if isinstance(t, dict) and isinstance(t.get("task_id"), str)}
    rows: list[dict[str, Any]] = []
    for entry in gate.get("unfinished_production_tasks", []):
        task_id = entry.get("task_id")
        task = tasks.get(task_id, {})
        state = task.get("state") or entry.get("registry_state")
        if state in TERMINAL:
            continuation = "TERMINAL"
            safe = True
        elif active_machine_executor(task):
            continuation = "ACTIVE_MACHINE_EXECUTOR"
            safe = True
        elif active_session_claim(entry, root, now):
            continuation = "ACTIVE_SESSION_CLAIM"
            safe = True
        elif explicit_human_boundary(entry, task):
            continuation = "EXPLICIT_HUMAN_AUTHORITY_BOUNDARY"
            safe = True
        elif state == "BLOCKED" and blocked_with_active_resolver(entry, tasks):
            continuation = "BLOCKED_WITH_ACTIVE_MACHINE_RESOLVER"
            safe = True
        else:
            continuation = "NO_PROVEN_EXECUTABLE_CONTINUATION"
            safe = False
        rows.append({
            "task_id": task_id,
            "state": state,
            "progress_class": entry.get("progress_class"),
            "continuation_class": continuation,
            "archive_safe": safe,
        })

    all_safe = all(row["archive_safe"] for row in rows)
    return {
        "schema": "stegverse.archive-readiness-evaluation/v2",
        "goal_id": gate.get("goal_id"),
        "unfinished_count": len(rows),
        "all_unfinished_have_executable_continuation": all_safe,
        "archive_allowed": all_safe,
        "rows": rows,
        "rules": {
            "progress_label_alone_is_insufficient": True,
            "durable_record_alone_is_insufficient": True,
            "unfinished_requires_active_machine_or_session_executor_or_explicit_human_boundary": True,
            "blocked_requires_active_resolver_and_machine_observable_release_condition": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assert-ready", action="store_true")
    args = parser.parse_args()
    result = evaluate(load(GATE_PATH), load(REGISTRY_PATH))
    claimed = bool(load(GATE_PATH).get("thread_archive_ready"))
    errors: list[str] = []
    if claimed and not result["archive_allowed"]:
        errors.append("premature-archive-ready-without-executable-continuation")
    print(json.dumps({"ok": not errors, "claimed_archive_ready": claimed, "evaluation": result, "errors": errors}, indent=2, sort_keys=True))
    if errors or (args.assert_ready and not result["archive_allowed"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
