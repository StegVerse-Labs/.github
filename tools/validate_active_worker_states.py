#!/usr/bin/env python3
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "control" / "worker-registry.json"
POLICY = ROOT / "control" / "active-worker-state-policy.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(registry: dict, policy: dict) -> list[str]:
    errors: list[str] = []
    forbidden = policy["forbidden_unresolved_state"]
    terminal = {"COMPLETED", "COMPLETE", "SUPERSEDED"}
    for task in registry.get("tasks", []):
        state = str(task.get("state", ""))
        task_id = str(task.get("task_id", "<unknown>"))
        if state in terminal:
            continue
        if state == forbidden:
            errors.append(f"{task_id}: unresolved operational state BLOCKED is forbidden")
        binding = str(task.get("executor_binding", ""))
        if binding in {"", "UNBOUND"}:
            errors.append(f"{task_id}: unresolved task has no bound executor")
        handoff = task.get("handoff_ref")
        if not handoff:
            errors.append(f"{task_id}: unresolved task lacks durable handoff_ref")
        timing = task.get("heartbeat_timing") or {}
        if binding == "BOUND" and not task.get("claim_id"):
            errors.append(f"{task_id}: bound worker lacks claim_id")
        if binding == "BOUND" and not timing.get("expected_next_transition"):
            errors.append(f"{task_id}: bound worker lacks expected_next_transition")
    return errors


def main() -> int:
    registry = load(REGISTRY)
    policy = load(POLICY)
    errors = validate(registry, policy)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: active-worker state invariant satisfied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
