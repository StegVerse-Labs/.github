#!/usr/bin/env python3
"""Select and optionally advance one canonical machine-owned task from the Task Registry.

The Task Registry is the work-discovery starting point. This script does not create
new task identity, mint WorkerCoordinator claim/fence authority, grant credentials,
or authorize a transition. It enumerates canonical Task Registry rows, optionally
enriches them from matching task-record shards without allowing a shard to override
registry truth, prioritizes StegVerse ecosystem repair/remediation/canonicalization
work inside the current root Goal Task, runs the existing Task Registry collision
check-in, and only then delegates one selected registered task to the existing
Canonical Work / Interlock-InTr bootstrap.

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
WORKER_RUNTIME = ROOT / "scripts" / "run_worker_runtime.py"
WORKER_REGISTRY_FRAGMENTS = ROOT / "control" / "worker-registry.d"
CALLER_SURFACE = "INTERNAL_CANONICAL_WORK_BOOTSTRAP"
PROGRESSION_CONTROLLER_TASK_ID = "ENTITY-AUTONOMOUS-GOVERNED-PROGRESSION-RUNTIME-ADOPTION-001"
NOTIFICATION_REL = Path("requests/tv-tvc/goal-task-completion-github-notification.latest.json")
REPAIR_PRIORITY_CLASSES = {
    "ECOSYSTEM_REPAIR",
    "ECOSYSTEM_REMEDIATION",
    "ECOSYSTEM_CANONICALIZATION",
    "ECOSYSTEM_RECONCILIATION",
    "REGRESSION_REPAIR",
}
REPAIR_PRIORITY_TOKENS = (
    "REPAIR",
    "REMEDIAT",
    "CANONICALIZ",
    "RECONCIL",
    "CORRECTION",
    "REGRESSION",
    "FIX",
)


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


def progression_context(
    current_goal_task_id: str | None = None,
    records_dir: Path = RECORDS,
) -> tuple[str, dict[str, Any] | None, dict[str, Any], str]:
    controller = load(records_dir / f"{PROGRESSION_CONTROLLER_TASK_ID}.json")
    controller_lineage_goal_id = str(controller.get("root_correlation_id") or "").strip()
    if not controller_lineage_goal_id:
        raise RuntimeError("progression controller missing lineage root Goal Task ID")
    header = controller.get("latest_goal_task_block_header")
    notification = controller.get("goal_completion_notification")
    if not isinstance(header, dict):
        raise RuntimeError("progression controller missing latest Goal Task block header projection")
    if not isinstance(notification, dict):
        raise RuntimeError("progression controller missing Goal completion notification contract")
    header_goal_task_id = str(header.get("goal_task_id") or "").strip()
    goal_task_id = str(current_goal_task_id or header_goal_task_id).strip()
    if not goal_task_id:
        raise RuntimeError("current root Goal Task ID is unavailable")
    completion_header = header if header_goal_task_id == goal_task_id else None
    return goal_task_id, completion_header, notification, controller_lineage_goal_id


def canonical_registry_rows(registry_path: Path = REGISTRY) -> list[dict[str, Any]]:
    registry = load(registry_path)
    rows = registry.get("tasks")
    if not isinstance(rows, list):
        raise RuntimeError("canonical Task Registry tasks must be a list")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in rows:
        if not isinstance(raw, dict):
            raise RuntimeError("canonical Task Registry task rows must be objects")
        task_id = str(raw.get("task_id") or "").strip()
        if not task_id:
            raise RuntimeError("canonical Task Registry task row missing task_id")
        if task_id in seen:
            raise RuntimeError(f"duplicate canonical Task Registry task: {task_id}")
        seen.add(task_id)
        result.append(dict(raw))
    return result


def canonical_goal_record(goal_task_id: str, registry_path: Path = REGISTRY) -> dict[str, Any]:
    matches = [row for row in canonical_registry_rows(registry_path) if row.get("task_id") == goal_task_id]
    if len(matches) != 1:
        raise RuntimeError("Goal Task must resolve exactly once in canonical Task Registry")
    return matches[0]


def registry_candidate_projection(registry_record: dict[str, Any], records_dir: Path = RECORDS) -> dict[str, Any]:
    """Enrich one registry row without allowing a shard to rewrite registry truth."""
    task_id = str(registry_record.get("task_id") or "").strip()
    if not task_id:
        raise RuntimeError("registry candidate missing task_id")
    projected = dict(registry_record)
    shard_path = records_dir / f"{task_id}.json"
    if not shard_path.is_file():
        return projected
    shard = load(shard_path)
    if shard.get("task_id") != task_id:
        raise RuntimeError(f"canonical task shard identity mismatch: {task_id}")
    for identity_key in ("correlation_id", "root_correlation_id", "parent_task_id"):
        registry_value = registry_record.get(identity_key)
        shard_value = shard.get(identity_key)
        if registry_value is not None and shard_value is not None and registry_value != shard_value:
            raise RuntimeError(f"canonical task shard {identity_key} mismatch: {task_id}")
    for key, value in shard.items():
        projected.setdefault(key, value)
    return projected


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
    coordination_state = str(record.get("coordination_state") or "").upper()
    checkout_state = str(record.get("checkout_state") or "").upper()
    active_checked_out = coordination_state == "ACTIVE" and checkout_state == "CHECKED_OUT"
    if coordination_state != "PROPOSED" and not active_checked_out:
        return False
    if checkout_state in {"SUPERSEDED", "COMPLETED", "RETIRED"}:
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


def workercoordinator_target_candidate(
    record: dict[str, Any],
    fragments_dir: Path = WORKER_REGISTRY_FRAGMENTS,
) -> bool:
    """Return true only for an already-admitted state-triggerable WorkerCoordinator task."""
    if str(record.get("coordination_state") or "").upper() != "ACTIVE":
        return False
    if str(record.get("checkout_state") or "").upper() != "CHECKED_OUT":
        return False
    if record.get("human_action_ref") not in {None, ""}:
        return False
    if "INGRESS_ADMITTED" in (record.get("allowed_next_transitions") or []):
        return False
    task_id = str(record.get("task_id") or "").strip()
    if not task_id or not fragments_dir.is_dir():
        return False

    matches: list[dict[str, Any]] = []
    for path in sorted(fragments_dir.glob("*.json")):
        fragment = load(path)
        if fragment.get("schema") != "stegverse.worker-registry-fragment/v0.1":
            continue
        for declared in fragment.get("tasks", []):
            if isinstance(declared, dict) and declared.get("task_id") == task_id:
                matches.append(declared)
    if len(matches) != 1:
        return False

    task = matches[0]
    admission = task.get("admission") or {}
    return (
        task.get("state") == "HANDOFF_READY"
        and not task.get("claim_id")
        and not task.get("worker_id")
        and not task.get("worker_instance_id")
        and admission.get("authority_domain") == "INDEPENDENT_TASK_CONTROL"
        and admission.get("claim_state") == "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM"
        and admission.get("carrier_trigger_required") is False
    )


def delegation_mode(record: dict[str, Any]) -> str | None:
    if workercoordinator_target_candidate(record):
        return "WORKERCOORDINATOR_TARGETED_STATE_TRANSITION"
    if machine_ingress_candidate(record):
        return "CANONICAL_WORK_INGRESS"
    return None


def ecosystem_priority_class(record: dict[str, Any]) -> str:
    explicit = str(record.get("work_priority_class") or "").strip().upper()
    if explicit in REPAIR_PRIORITY_CLASSES:
        return explicit
    searchable_parts: list[str] = [
        str(record.get("task_id") or ""),
        str(record.get("goal") or ""),
        str(record.get("problem") or ""),
        str(record.get("constraint") or ""),
    ]
    for key in ("source_refs", "handoff_projection_refs"):
        values = record.get(key) or []
        if isinstance(values, list):
            searchable_parts.extend(str(value) for value in values)
    searchable = " ".join(searchable_parts).upper()
    if any(token in searchable for token in REPAIR_PRIORITY_TOKENS):
        return "ECOSYSTEM_REPAIR_REMEDIATION_CANONICALIZATION"
    return "ORDINARY_GOAL_WORK"


def candidate_sort_key(record: dict[str, Any]) -> tuple[int, int, str]:
    repair_first = 0 if ecosystem_priority_class(record) != "ORDINARY_GOAL_WORK" else 1
    checkout_rank = 0 if record.get("checkout_state") == "CHECKED_OUT" else 1
    return repair_first, checkout_rank, str(record["task_id"])


def load_candidates(
    records_dir: Path = RECORDS,
    excluded_task_ids: set[str] | None = None,
    goal_task_id: str | None = None,
    registry_path: Path = REGISTRY,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for registry_record in canonical_registry_rows(registry_path):
        task_id = str(registry_record["task_id"])
        root_id = str(registry_record.get("root_correlation_id") or registry_record.get("correlation_id") or task_id)
        if goal_task_id and root_id != goal_task_id:
            continue
        record = registry_candidate_projection(registry_record, records_dir)
        if delegation_mode(record) is not None and task_id not in (excluded_task_ids or set()):
            rows.append(record)
    rows.sort(key=candidate_sort_key)
    return rows


def collision_check(task_id: str) -> dict[str, Any]:
    registry_generation = int(load(REGISTRY).get("generation", -1))
    if registry_generation < 0:
        raise RuntimeError("canonical Task Registry generation unavailable")
    proc = subprocess.run(
        [sys.executable, str(CHECKIN)],
        cwd=str(ROOT),
        input=json.dumps({"task_id": task_id, "caller_surface": CALLER_SURFACE, "observed_registry_generation": registry_generation}),
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


def select_task(
    records_dir: Path = RECORDS,
    excluded_task_ids: set[str] | None = None,
    goal_task_id: str | None = None,
    registry_path: Path = REGISTRY,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    considered: list[dict[str, Any]] = []
    for record in load_candidates(records_dir, excluded_task_ids, goal_task_id, registry_path):
        task_id = str(record["task_id"])
        checkin = collision_check(task_id)
        considered.append({
            "task_id": task_id,
            "priority_class": ecosystem_priority_class(record),
            "checkout_state": record.get("checkout_state"),
            "delegation_mode": delegation_mode(record),
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
    parser.add_argument("--goal-task-id")
    args = parser.parse_args()
    excluded_task_ids = {str(task_id).strip() for task_id in args.exclude_task_id if str(task_id).strip()}

    goal_task_id, header, notification, controller_lineage_goal_id = progression_context(args.goal_task_id)
    goal_context_source = "EXPLICIT_CURRENT_GOAL_TASK" if args.goal_task_id else "PROGRESSION_HEADER_FALLBACK"
    goal_record = canonical_goal_record(goal_task_id)
    if goal_completion_validated(goal_record) and header is None:
        receipt = {
            "schema": "stegverse.task-registry-canonical-work-cycle/v1",
            "state": "GOAL_TASK_COMPLETED_NOTIFICATION_HEADER_UNAVAILABLE",
            "start_point": "CANONICAL_TASK_REGISTRY",
            "goal_task_id": goal_task_id,
            "goal_context_source": goal_context_source,
            "progression_controller_lineage_goal_id": controller_lineage_goal_id,
            "goal_completion_validated": True,
            "continue_machine_work": False,
            "selected_task_id": None,
            "successor_selection_performed": False,
            "completion_notification_request": None,
            "completion_notification_pending_reason": "CURRENT_GOAL_TASK_BLOCK_HEADER_NOT_PROJECTED",
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "authority_effect": "NONE_FAIL_CLOSED_TERMINAL_STOP_ONLY",
        }
        print(json.dumps(receipt, sort_keys=True))
        return 0
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
            "goal_context_source": goal_context_source,
            "progression_controller_lineage_goal_id": controller_lineage_goal_id,
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
    candidates = load_candidates(excluded_task_ids=excluded_task_ids, goal_task_id=goal_task_id)
    receipt: dict[str, Any] = {
        "schema": "stegverse.task-registry-canonical-work-cycle/v1",
        "start_point": "CANONICAL_TASK_REGISTRY",
        "candidate_identity_source": "CANONICAL_TASK_REGISTRY",
        "task_record_shards_are_optional_enrichment_only": True,
        "goal_task_id": goal_task_id,
        "goal_context_source": goal_context_source,
        "progression_controller_lineage_goal_id": controller_lineage_goal_id,
        "goal_completion_validated": False,
        "selection_priority_rule": "ECOSYSTEM_REPAIR_REMEDIATION_CANONICALIZATION_FIRST",
        "progression_controller_excluded_from_work_selection": True,
        "explicit_request_task_ids_excluded": sorted(excluded_task_ids),
        "selected_task_id": selected.get("task_id") if selected else None,
        "selected_delegation_mode": delegation_mode(selected) if selected else None,
        "candidate_count": len(candidates),
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

    mode = delegation_mode(selected)
    if mode == "WORKERCOORDINATOR_TARGETED_STATE_TRANSITION":
        command = [
            sys.executable,
            str(WORKER_RUNTIME),
            "--task-id",
            str(selected["task_id"]),
        ]
    else:
        command = [
            sys.executable,
            str(BOOTSTRAP),
            "--task-id",
            str(selected["task_id"]),
            "--runtime-root",
            str(args.runtime_root.expanduser().resolve()),
        ]
    completed = subprocess.run(command, cwd=str(ROOT), text=True, capture_output=True, check=False)
    delegated_state = (
        "DELEGATED_TO_EXISTING_WORKERCOORDINATOR_STATE_TRANSITION"
        if mode == "WORKERCOORDINATOR_TARGETED_STATE_TRANSITION"
        else "DELEGATED_TO_EXISTING_CANONICAL_WORK_PATH"
    )
    receipt.update({
        "state": delegated_state if completed.returncode == 0 else "EXISTING_PATH_DELEGATION_RECORDED_FAILURE",
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