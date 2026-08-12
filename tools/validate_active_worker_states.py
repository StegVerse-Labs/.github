#!/usr/bin/env python3
"""Enforce the StegVerse active-work invariant on canonical worker state.

Historical registry rows are reconciled against authoritative handoffs and
registry fragments before deciding whether work is unowned. An unresolved task
is valid only when it is directly bound/claimed, authorized to an available
machine worker, actively continued by a named resolution/recovery dependency,
or proven terminal by an authoritative handoff.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "control" / "worker-registry.json"
POLICY = ROOT / "control" / "active-worker-state-policy.json"
HANDOFF_ROOT = ROOT / "handoffs"
FRAGMENT_ROOT = ROOT / "control" / "worker-registry.d"
TERMINAL = {"COMPLETED", "COMPLETE", "COMPLETE_RELEASED", "SUPERSEDED"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_handoffs() -> dict[str, dict]:
    result: dict[str, dict] = {}
    for path in HANDOFF_ROOT.rglob("*.json"):
        try:
            row = load(path)
        except Exception:
            continue
        task = row.get("task") if isinstance(row.get("task"), dict) else {}
        task_id = task.get("task_id")
        if isinstance(task_id, str) and task_id:
            result[task_id] = row
    return result


def load_fragment_active_tasks() -> set[str]:
    active: set[str] = set()
    if not FRAGMENT_ROOT.exists():
        return active
    for path in FRAGMENT_ROOT.glob("*.json"):
        try:
            row = load(path)
        except Exception:
            continue
        workers = [w for w in row.get("workers", []) if w.get("status") == "AVAILABLE" and w.get("adapter_ref")]
        if not workers:
            continue
        worker_caps = [set(w.get("capabilities", [])) for w in workers]
        for task in row.get("tasks", []):
            if task.get("state") not in {"HANDOFF_READY", "ACTIVATION_PENDING", "ACTIVE", "CLAIMED"}:
                continue
            if task.get("executor_binding") not in {"AUTHORIZED", "BOUND"}:
                continue
            handoff_ref = task.get("handoff_ref")
            if not handoff_ref:
                continue
            try:
                handoff = load(ROOT / handoff_ref)
            except Exception:
                continue
            required = set((handoff.get("execution") or {}).get("required_capabilities", []))
            if any(required.issubset(caps) for caps in worker_caps):
                active.add(str(task.get("task_id")))
    return active


def authoritative_terminal(task_id: str, handoffs: dict[str, dict]) -> bool:
    handoff = handoffs.get(task_id) or {}
    state = str(handoff.get("state", ""))
    task_state = str((handoff.get("task") or {}).get("operational_state", ""))
    return state in TERMINAL or task_state in TERMINAL


def continuation_dependency(task_id: str, handoffs: dict[str, dict]) -> str | None:
    handoff = handoffs.get(task_id) or {}
    for key in ("constraint", "block"):
        node = handoff.get(key)
        if isinstance(node, dict):
            dependency = node.get("dependency")
            if isinstance(dependency, str) and dependency:
                return dependency.removeprefix("task:")
    return None


def validate(
    registry: dict,
    policy: dict,
    handoffs: dict[str, dict] | None = None,
    fragment_active_tasks: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    handoffs = handoffs or {}
    fragment_active_tasks = fragment_active_tasks or set()
    forbidden = policy["forbidden_unresolved_state"]

    # A task can be actively continued by a separately authorized recovery or
    # resolution task without giving that successor the parent's authority.
    def has_active_continuation(task_id: str) -> bool:
        dep = continuation_dependency(task_id, handoffs)
        return bool(dep and dep in fragment_active_tasks)

    for task in registry.get("tasks", []):
        raw_state = str(task.get("state", ""))
        task_id = str(task.get("task_id", "<unknown>"))
        if raw_state in TERMINAL or authoritative_terminal(task_id, handoffs):
            continue

        binding = str(task.get("executor_binding", ""))
        timing = task.get("heartbeat_timing") or {}
        claim_id = task.get("claim_id")
        handoff_ref = task.get("handoff_ref")
        fragment_owned = task_id in fragment_active_tasks
        successor_owned = has_active_continuation(task_id)

        if not handoff_ref:
            errors.append(f"{task_id}: unresolved task lacks durable handoff_ref")

        if raw_state == forbidden:
            if binding == "BOUND" and claim_id and timing.get("expected_next_transition"):
                continue
            if fragment_owned or successor_owned:
                continue
            errors.append(f"{task_id}: unresolved passive BLOCKED state has no active solution owner")

        if binding in {"", "UNBOUND"}:
            if fragment_owned or successor_owned:
                continue
            errors.append(f"{task_id}: unresolved task has no bound/authorized executor")
        elif binding == "BOUND":
            if not claim_id:
                errors.append(f"{task_id}: bound worker lacks claim_id")
            if not timing.get("expected_next_transition"):
                errors.append(f"{task_id}: bound worker lacks expected_next_transition")
        elif binding == "AUTHORIZED":
            if not handoff_ref:
                errors.append(f"{task_id}: authorized machine lane lacks handoff")
        elif binding == "RELEASED":
            errors.append(f"{task_id}: unresolved task cannot have RELEASED executor binding")
    return errors


def main() -> int:
    registry = load(REGISTRY)
    policy = load(POLICY)
    handoffs = load_handoffs()
    fragment_active = load_fragment_active_tasks()
    errors = validate(registry, policy, handoffs, fragment_active)
    if errors:
        for error in errors:
            print(f"ACTIVE_WORK_INVALID: {error}")
        return 1
    print(f"ACTIVE_WORKER_STATE_INVARIANT_PASS fragment_active_tasks={len(fragment_active)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
