#!/usr/bin/env python3
"""Select and optionally advance one canonical machine-owned task from the Task Registry.

The Task Registry is the work-discovery starting point. This script does not create
new task identity, mint WorkerCoordinator claim/fence authority, grant credentials,
or authorize a transition. It filters existing canonical task records, runs the
existing Task Registry collision check-in, and only then delegates one selected
registered task to the existing Canonical Work / Interlock-InTr bootstrap.

Goal-bounded progression stops before any further task selection once the current
Goal Task has a canonically validated completion claim. That terminal event emits
one secret-free GitHub completion-notification request whose body contains only the
six task-block header lines through STATUS. Provider execution remains TV/TVC-owned.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data" / "canonical-task-records"
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
CHECKIN = ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py"
BOOTSTRAP = ROOT / "scripts" / "install_and_run_canonical_work_event_bootstrap.py"
CALLER_SURFACE = "INTERNAL_CANONICAL_WORK_BOOTSTRAP"
PROGRESSION_CONTROLLER_TASK_ID = "ENTITY-AUTONOMOUS-GOVERNED-PROGRESSION-RUNTIME-ADOPTION-001"
NOTIFICATION_REL = Path("requests/tv-tvc/goal-task-completion-github-notification.latest.json")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"canonical task record must be an object: {path}")
    return value


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def progression_context(records_dir: Path = RECORDS) -> tuple[str, dict[str, Any], dict[str, Any]]:
    controller = load(records_dir / f"{PROGRESSION_CONTROLLER_TASK_ID}.json")
    goal_task_id = str(controller.get("root_correlation_id") or "").strip()
    if not goal_task_id:
        raise RuntimeError("progression controller missing root Goal Task ID")
    header = controller.get("latest_goal_task_block_header")
    notification = controller.get("goal_completion_notification")
    if not isinstance(header, dict):
        raise RuntimeError("progression controller missing latest Goal Task block header projection")
    if not isinstance(notification, dict):
        raise RuntimeError("progression controller missing Goal completion notification contract")
    if header.get("goal_task_id") != goal_task_id:
        raise RuntimeError("Goal Task block header identity mismatch")
    return goal_task_id, header, notification


def canonical_goal_record(goal_task_id: str, registry_path: Path = REGISTRY) -> dict[str, Any]:
    registry = load(registry_path)
    rows = registry.get("tasks")
    if not isinstance(rows, list):
        raise RuntimeError("canonical Task Registry tasks must be a list")
    matches = [row for row in rows if isinstance(row, dict) and row.get("task_id") == goal_task_id]
    if len(matches) != 1:
        raise RuntimeError("Goal Task must resolve exactly once in canonical Task Registry")
    return matches[0]


def goal_completion_validated(goal_record: dict[str, Any]) -> bool:
    completion = goal_record.get("completion") or {}
    return bool(completion.get("claimed") is True and completion.get("validated") is True)


def completion_task_block_lines(header: dict[str, Any], goal_record: dict[str, Any]) -> list[str]:
    required = (
        "goal_task_id",
        "handoff_task_id",
        "cosv_id",
        "session_prompt_count",
        "goal_prompt_count",
    )
    for key in required:
        if header.get(key) in {None, ""}:
            raise RuntimeError(f"Goal Task block header missing {key}")
    terminal_status = "RETIRED" if str(goal_record.get("coordination_state") or "").upper() == "RETIRED" else "INACTIVE"
    return [
        f"Goal Task ID: {header['goal_task_id']};",
        f"Handoff Task ID: {header['handoff_task_id']};",
        f"COSV ID: {header['cosv_id']};",
        f"Session Prompt Count: {header['session_prompt_count']};",
        f"Goal Prompt Count: {header['goal_prompt_count']}.",
        f"STATUS: {terminal_status}.",
    ]


def build_completion_notification_request(
    goal_task_id: str,
    header: dict[str, Any],
    notification: dict[str, Any],
    goal_record: dict[str, Any],
) -> dict[str, Any]:
    lines = completion_task_block_lines(header, goal_record)
    if notification.get("summary_included") is not False or notification.get("manual_work_included") is not False:
        raise RuntimeError("completion notification must exclude Summary of work and Manual Work")
    if notification.get("credential_authority") != "TV/TVC":
        raise RuntimeError("completion notification credential authority must remain TV/TVC")
    return {
        "schema": "stegverse.goal-task-completion-github-notification-request/v1",
        "state": "REQUESTED",
        "goal_task_id": goal_task_id,
        "terminal_goal_completion_validated": True,
        "stop_autonomous_progression": True,
        "select_successor_before_notification": False,
        "provider": "GITHUB",
        "operation": "CREATE_GOAL_COMPLETION_NOTIFICATION_ISSUE",
        "repository": notification.get("notification_repository"),
        "assignees": [notification.get("notification_assignee")],
        "title": f"Goal Task completed: {goal_task_id}",
        "body": "\n".join(lines),
        "body_line_count": 6,
        "summary_included": False,
        "manual_work_included": False,
        "credential_authority": "TV/TVC",
        "github_actions_runtime_authority": "NONE",
        "provider_execution_authority_granted_by_request": False,
        "email_delivery": notification.get("email_delivery"),
        "authority_effect": "NONE_NOTIFICATION_REQUEST_ONLY",
    }


def machine_ingress_candidate(record: dict[str, Any], excluded_task_ids: set[str] | None = None) -> bool:
    task_id = str(record.get("task_id") or "")
    excluded = excluded_task_ids or set()
    if task_id == PROGRESSION_CONTROLLER_TASK_ID or task_id in excluded:
        return False
    if record.get("coordination_state") != "PROPOSED":
        return False
    if record.get("checkout_state") in {"SUPERSEDED", "COMPLETED", "RETIRED"}:
        return False
    if "INGRESS_ADMITTED" not in (record.get("allowed_next_transitions") or []):
        return False
    if record.get("human_action_ref") not in {None, ""}:
        return False
    if not isinstance(record.get("runtime_requirements"), dict):
        return False
    claim = record.get("worker_claim") or {}
    if claim.get("authority") != "WORKERCOORDINATOR" or claim.get("projection_only") is not True:
        return False
    if claim.get("claim_ref") is not None or claim.get("fence_ref") is not None:
        return False
    authority = record.get("authority_model") or {}
    if authority.get("task_registry_mints_execution_authority") is not False:
        return False
    if authority.get("interlock_intr_required_for_governed_ingress_egress") is not True:
        return False
    return True


def load_candidates(records_dir: Path = RECORDS, excluded_task_ids: set[str] | None = None, goal_task_id: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(records_dir.glob("*.json")):
        record = load(path)
        task_id = str(record.get("task_id") or "").strip()
        if not task_id:
            raise RuntimeError(f"canonical task record missing task_id: {path}")
        if task_id in seen:
            raise RuntimeError(f"duplicate canonical task record: {task_id}")
        seen.add(task_id)
        if goal_task_id and str(record.get("root_correlation_id") or record.get("correlation_id") or task_id) != goal_task_id:
            continue
        if machine_ingress_candidate(record, excluded_task_ids):
            rows.append(record)
    rows.sort(key=lambda row: (0 if row.get("checkout_state") == "CHECKED_OUT" else 1, str(row["task_id"])))
    return rows


def collision_check(task_id: str) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(CHECKIN)],
        cwd=str(ROOT),
        input=json.dumps({"task_id": task_id, "caller_surface": CALLER_SURFACE}),
        text=True,
        capture_output=True,
        check=True,
    )
    result = json.loads(proc.stdout)
    if result.get("schema") != "stegverse.task-registry-checkin-disposition/v1":
        raise RuntimeError("Task Registry check-in schema mismatch")
    if result.get("task_id") != task_id:
        raise RuntimeError("Task Registry check-in identity mismatch")
    if result.get("authority_effect") != "NONE":
        raise RuntimeError("Task Registry check-in attempted authority effect")
    return result


def select_task(records_dir: Path = RECORDS, excluded_task_ids: set[str] | None = None, goal_task_id: str | None = None) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    considered: list[dict[str, Any]] = []
    for record in load_candidates(records_dir, excluded_task_ids, goal_task_id):
        task_id = str(record["task_id"])
        checkin = collision_check(task_id)
        considered.append({
            "task_id": task_id,
            "checkout_state": record.get("checkout_state"),
            "disposition": checkin.get("disposition"),
            "collision_candidates": checkin.get("collision_candidates") or [],
        })
        if checkin.get("disposition") == "CONTINUE":
            return record, considered
    return None, considered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--select-only", action="store_true")
    parser.add_argument("--exclude-task-id", action="append", default=[])
    args = parser.parse_args()
    excluded_task_ids = {str(task_id).strip() for task_id in args.exclude_task_id if str(task_id).strip()}

    goal_task_id, header, notification = progression_context()
    goal_record = canonical_goal_record(goal_task_id)
    if goal_completion_validated(goal_record):
        notification_request = build_completion_notification_request(goal_task_id, header, notification, goal_record)
        notification_ref = None
        if args.runtime_root is not None:
            notification_path = args.runtime_root.expanduser().resolve() / NOTIFICATION_REL
            atomic_json(notification_path, notification_request)
            notification_ref = str(notification_path)
        receipt = {
            "schema": "stegverse.task-registry-canonical-work-cycle/v1",
            "state": "GOAL_TASK_COMPLETED_TERMINAL_NOTIFICATION_REQUESTED",
            "start_point": "CANONICAL_TASK_REGISTRY",
            "goal_task_id": goal_task_id,
            "goal_completion_validated": True,
            "continue_machine_work": False,
            "selected_task_id": None,
            "successor_selection_performed": False,
            "completion_notification_request": notification_request,
            "completion_notification_request_ref": notification_ref,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "authority_effect": "NONE_TERMINAL_STOP_AND_NOTIFICATION_REQUEST_ONLY",
        }
        print(json.dumps(receipt, sort_keys=True))
        return 0

    selected, considered = select_task(excluded_task_ids=excluded_task_ids, goal_task_id=goal_task_id)
    receipt: dict[str, Any] = {
        "schema": "stegverse.task-registry-canonical-work-cycle/v1",
        "start_point": "CANONICAL_TASK_REGISTRY",
        "goal_task_id": goal_task_id,
        "goal_completion_validated": False,
        "progression_controller_excluded_from_work_selection": True,
        "explicit_request_task_ids_excluded": sorted(excluded_task_ids),
        "selected_task_id": selected.get("task_id") if selected else None,
        "candidate_count": len(load_candidates(excluded_task_ids=excluded_task_ids, goal_task_id=goal_task_id)),
        "considered": considered,
        "workercoordinator_claim_or_fence_minted": False,
        "interlock_intr_transition_authority_preserved": True,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "human_checkpoint_inserted": False,
        "authority_effect": "NONE_SELECTION_AND_DELEGATION_ONLY",
    }
    if selected is None:
        receipt["state"] = "NO_ADMISSIBLE_NONCOLLIDING_TASK"
        print(json.dumps(receipt, sort_keys=True))
        return 0

    if args.select_only:
        receipt["state"] = "TASK_SELECTED_FOR_EXISTING_CANONICAL_WORK_PATH"
        print(json.dumps(receipt, sort_keys=True))
        return 0

    if args.runtime_root is None:
        raise SystemExit("--runtime-root is required unless --select-only is used")

    command = [
        sys.executable,
        str(BOOTSTRAP),
        "--task-id",
        str(selected["task_id"]),
        "--runtime-root",
        str(args.runtime_root.expanduser().resolve()),
    ]
    completed = subprocess.run(command, cwd=str(ROOT), text=True, capture_output=True, check=False)
    receipt.update({
        "state": "DELEGATED_TO_EXISTING_CANONICAL_WORK_PATH" if completed.returncode == 0 else "CANONICAL_WORK_DELEGATION_RECORDED_FAILURE",
        "delegation_returncode": completed.returncode,
        "delegation_command": command,
        "delegation_stdout": completed.stdout,
        "delegation_stderr": completed.stderr,
        "task_registry_mints_execution_authority": False,
    })
    print(json.dumps(receipt, sort_keys=True))
    return 0 if completed.returncode == 0 else completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
