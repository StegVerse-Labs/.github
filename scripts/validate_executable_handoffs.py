#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HANDOFF_ROOT = ROOT / "handoffs"
EXECUTABLE_SCHEMA = "stegverse.executable-handoff/v0.1"
TERMINAL = {"COMPLETED"}
VALID_SUCCESSOR_POLICIES = {"NONE", "INHERIT_OR_NARROW", "SEPARATE_AUTHORIZATION_REQUIRED_FOR_EXPANSION"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_one(path: Path, handoff: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    prefix = str(path.relative_to(ROOT))
    require(handoff.get("schema") == EXECUTABLE_SCHEMA, f"{prefix}: unsupported schema", errors)
    goal = handoff.get("goal") if isinstance(handoff.get("goal"), dict) else {}
    task = handoff.get("task") if isinstance(handoff.get("task"), dict) else {}
    authority = handoff.get("authority") if isinstance(handoff.get("authority"), dict) else {}
    execution = handoff.get("execution") if isinstance(handoff.get("execution"), dict) else {}
    completion = handoff.get("completion") if isinstance(handoff.get("completion"), dict) else {}

    for key in ("goal_id", "objective"):
        require(isinstance(goal.get(key), str) and bool(goal.get(key)), f"{prefix}: goal.{key} required", errors)
    for key in ("success_predicates", "failure_predicates", "authority_ceiling"):
        value = goal.get(key)
        require(isinstance(value, list) and value and all(isinstance(item, str) and item for item in value), f"{prefix}: goal.{key} must be non-empty string list", errors)
    require(goal.get("successor_policy") in VALID_SUCCESSOR_POLICIES, f"{prefix}: goal.successor_policy invalid", errors)
    require(isinstance(goal.get("max_successor_depth"), int) and goal.get("max_successor_depth", -1) >= 0, f"{prefix}: goal.max_successor_depth invalid", errors)

    for key in ("task_id", "repository", "canonical_owner_ref", "canonical_lineage_key"):
        require(isinstance(task.get(key), str) and bool(task.get(key)), f"{prefix}: task.{key} required", errors)
    require(isinstance(task.get("source_refs"), list) and bool(task.get("source_refs")), f"{prefix}: task.source_refs required", errors)
    require(isinstance(task.get("derivation_depth"), int) and task.get("derivation_depth", -1) >= 0, f"{prefix}: task.derivation_depth invalid", errors)
    parent = task.get("parent_task_id")
    require(parent is None or (isinstance(parent, str) and bool(parent)), f"{prefix}: task.parent_task_id invalid", errors)
    require(isinstance(task.get("derivation_reason"), (str, type(None))), f"{prefix}: task.derivation_reason invalid", errors)

    require(authority.get("heartbeat_grants_execution_authority") is False, f"{prefix}: heartbeat must not grant execution authority", errors)
    for key in ("authority_source", "policy_version"):
        require(isinstance(authority.get(key), str) and bool(authority.get(key)), f"{prefix}: authority.{key} required", errors)

    require(isinstance(execution.get("required_capabilities"), list) and bool(execution.get("required_capabilities")), f"{prefix}: execution.required_capabilities required", errors)
    require(isinstance(execution.get("allowed_paths"), list), f"{prefix}: execution.allowed_paths required", errors)
    require(isinstance(execution.get("allowed_services"), list), f"{prefix}: execution.allowed_services required", errors)
    require(isinstance(execution.get("max_actions"), int) and execution.get("max_actions", 0) >= 1, f"{prefix}: execution.max_actions invalid", errors)
    require(isinstance(execution.get("max_retries"), int) and execution.get("max_retries", -1) >= 0, f"{prefix}: execution.max_retries invalid", errors)
    require(isinstance(execution.get("external_cost_ceiling_usd"), (int, float)) and execution.get("external_cost_ceiling_usd", -1) >= 0, f"{prefix}: execution.external_cost_ceiling_usd invalid", errors)
    require(isinstance(execution.get("runtime_window_beats"), int) and execution.get("runtime_window_beats", 0) >= 1, f"{prefix}: execution.runtime_window_beats invalid", errors)
    require(isinstance(execution.get("rate_class"), str) and bool(execution.get("rate_class")), f"{prefix}: execution.rate_class required", errors)

    terminal = completion.get("terminal_when")
    require(isinstance(terminal, list) and terminal and all(isinstance(item, str) and item for item in terminal), f"{prefix}: completion.terminal_when required", errors)
    require(isinstance(completion.get("next_authorized_action"), str) and bool(completion.get("next_authorized_action")), f"{prefix}: completion.next_authorized_action required", errors)
    return errors


def main() -> int:
    paths = sorted(HANDOFF_ROOT.glob("*.json"))
    handoffs: dict[str, tuple[Path, dict[str, Any]]] = {}
    errors: list[str] = []
    skipped_non_executable = 0
    for path in paths:
        try:
            value = load(path)
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)}: unreadable: {exc}")
            continue
        # `handoffs/` also contains durable transfer/session records. They have
        # their own schemas and owners and must not be coerced into executable
        # worker authority. This validator owns executable-handoff/v0.1 only.
        if value.get("schema") != EXECUTABLE_SCHEMA:
            skipped_non_executable += 1
            continue
        errors.extend(validate_one(path, value))
        task = value.get("task") or {}
        task_id = task.get("task_id")
        if isinstance(task_id, str) and task_id:
            if task_id in handoffs:
                errors.append(f"duplicate task_id: {task_id}")
            handoffs[task_id] = (path, value)

    active_lanes: dict[tuple[str, str], str] = {}
    active_goals: dict[tuple[str, str, str], str] = {}
    for task_id, (path, value) in handoffs.items():
        if value.get("state") in TERMINAL:
            continue
        task = value.get("task") or {}
        goal = value.get("goal") or {}
        lane_key = (str(task.get("canonical_owner_ref")), str(task.get("canonical_lineage_key")))
        goal_key = (str(task.get("canonical_owner_ref")), str(task.get("repository")), str(goal.get("goal_id")))
        if lane_key in active_lanes:
            errors.append(f"{path.relative_to(ROOT)}: duplicate live canonical lineage with {active_lanes[lane_key]}")
        else:
            active_lanes[lane_key] = task_id
        if goal_key in active_goals:
            errors.append(f"{path.relative_to(ROOT)}: duplicate live canonical goal lane with {active_goals[goal_key]}")
        else:
            active_goals[goal_key] = task_id

        parent_id = task.get("parent_task_id")
        if not parent_id:
            require(task.get("derivation_depth") == 0, f"{path.relative_to(ROOT)}: root derivation_depth must be 0", errors)
            continue
        parent_entry = handoffs.get(parent_id)
        if parent_entry is None:
            source_refs = set(task.get("source_refs") or [])
            require(any(parent_id in ref for ref in source_refs), f"{path.relative_to(ROOT)}: external parent {parent_id} must be evidenced in source_refs", errors)
            continue
        parent_path, parent = parent_entry
        parent_task = parent.get("task") or {}
        parent_goal = parent.get("goal") or {}
        require(task.get("derivation_depth") == int(parent_task.get("derivation_depth", -1)) + 1, f"{path.relative_to(ROOT)}: derivation_depth must be parent+1", errors)
        require(task.get("derivation_depth", 0) <= int(parent_goal.get("max_successor_depth", -1)), f"{path.relative_to(ROOT)}: successor depth exceeds parent max", errors)
        require(parent_goal.get("successor_policy") != "NONE", f"{path.relative_to(ROOT)}: parent {parent_id} prohibits successors", errors)
        require(str(parent_path.relative_to(ROOT)) in set(task.get("source_refs") or []), f"{path.relative_to(ROOT)}: parent HANDOFF ref missing from source_refs", errors)

    if errors:
        for error in errors:
            print(f"HANDOFF_INVALID:{error}")
        return 1
    print(f"EXECUTABLE_HANDOFF_VALIDATION_PASS count={len(handoffs)} live_lanes={len(active_lanes)} skipped_non_executable={skipped_non_executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
