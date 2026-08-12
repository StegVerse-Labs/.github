#!/usr/bin/env python3
"""Enforce the StegVerse active-work invariant on canonical worker state.

Historical registry rows are reconciled against newer authoritative executable
handoffs before deciding whether work is unresolved. A constraint response is
allowed only when a worker remains bound/claimed with a concrete next heartbeat
transition. An unresolved unbound task is invalid and must be assigned,
derived/escalated, completed, or superseded.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "control" / "worker-registry.json"
POLICY = ROOT / "control" / "active-worker-state-policy.json"
HANDOFF_ROOT = ROOT / "handoffs"
TERMINAL = {"COMPLETED", "COMPLETE", "COMPLETE_RELEASED", "SUPERSEDED"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_handoffs() -> dict[str, dict]:
    result: dict[str, dict] = {}
    for path in HANDOFF_ROOT.glob("*.json"):
        try:
            row = load(path)
        except Exception:
            continue
        task = row.get("task") if isinstance(row.get("task"), dict) else {}
        task_id = task.get("task_id")
        if isinstance(task_id, str) and task_id:
            result[task_id] = row
    return result


def authoritative_terminal(task_id: str, handoffs: dict[str, dict]) -> bool:
    handoff = handoffs.get(task_id) or {}
    state = str(handoff.get("state", ""))
    task_state = str((handoff.get("task") or {}).get("operational_state", ""))
    return state in TERMINAL or task_state in TERMINAL


def validate(registry: dict, policy: dict, handoffs: dict[str, dict] | None = None) -> list[str]:
    errors: list[str] = []
    handoffs = handoffs or {}
    forbidden = policy["forbidden_unresolved_state"]
    for task in registry.get("tasks", []):
        raw_state = str(task.get("state", ""))
        task_id = str(task.get("task_id", "<unknown>"))
        if raw_state in TERMINAL or authoritative_terminal(task_id, handoffs):
            continue

        binding = str(task.get("executor_binding", ""))
        timing = task.get("heartbeat_timing") or {}
        claim_id = task.get("claim_id")
        handoff_ref = task.get("handoff_ref")

        if not handoff_ref:
            errors.append(f"{task_id}: unresolved task lacks durable handoff_ref")

        if raw_state == forbidden:
            # A historical BLOCKED response is a constraint only when the task
            # is demonstrably still owned and has a next solution transition.
            if binding == "BOUND" and claim_id and timing.get("expected_next_transition"):
                continue
            errors.append(f"{task_id}: unresolved passive BLOCKED state has no active solution owner")

        if binding in {"", "UNBOUND"}:
            errors.append(f"{task_id}: unresolved task has no bound/authorized executor")
        elif binding == "BOUND":
            if not claim_id:
                errors.append(f"{task_id}: bound worker lacks claim_id")
            if not timing.get("expected_next_transition"):
                errors.append(f"{task_id}: bound worker lacks expected_next_transition")
        elif binding == "AUTHORIZED":
            # AUTHORIZED is admissible only as a machine-owned activation lane;
            # the handoff must remain durable and the heartbeat will allocate the
            # fenced claim. This is not a terminal state and cannot be archived
            # merely because the worker is registered.
            if not handoff_ref:
                errors.append(f"{task_id}: authorized machine lane lacks handoff")
        elif binding == "RELEASED":
            errors.append(f"{task_id}: unresolved task cannot have RELEASED executor binding")
    return errors


def main() -> int:
    registry = load(REGISTRY)
    policy = load(POLICY)
    errors = validate(registry, policy, load_handoffs())
    if errors:
        for error in errors:
            print(f"ACTIVE_WORK_INVALID: {error}")
        return 1
    print("ACTIVE_WORKER_STATE_INVARIANT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
