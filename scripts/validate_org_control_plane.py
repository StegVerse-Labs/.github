#!/usr/bin/env python3
"""Validate the minimum StegVerse-Labs organization control-plane state."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "control" / "org-state.json"
TASKS = ROOT / "tasks"

DURABLE_STATES = {"proposed", "queued", "active", "checkin_pending", "completed"}
FLAGS = {"blocked", "suspended", "superseded", "reconciliation_required"}
CONTROL_REPO = "StegVerse-Labs/.github"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing required file: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")


def validate_claim(claim: dict, *, optional: bool) -> None:
    repository = claim.get("repository", {})
    full_name = repository.get("full_name")
    if not full_name or "/" not in full_name:
        fail("claim repository.full_name must be fully qualified")
    if full_name == CONTROL_REPO:
        fail("the organization control repository is not claimable")
    scope = claim.get("scope", {})
    for required in ("contracts", "release_surfaces"):
        if required not in scope or not isinstance(scope[required], list):
            fail(f"claim scope.{required} must be present as a list")
    if optional and claim.get("preemptible") is not True:
        fail("optional claims must declare preemptible=true")


def validate_task(path: Path, task: dict) -> None:
    task_id = task.get("task_id")
    if path.stem != task_id:
        fail(f"task filename {path.name} must match task_id {task_id}")
    if task.get("status") not in DURABLE_STATES:
        fail(f"{task_id}: invalid durable status")
    unknown_flags = set(task.get("flags", [])) - FLAGS
    if unknown_flags:
        fail(f"{task_id}: unknown flags: {sorted(unknown_flags)}")
    requirements = task.get("requirements", {})
    for claim in requirements.get("mandatory", []):
        validate_claim(claim, optional=False)
    for claim in requirements.get("optional", []):
        validate_claim(claim, optional=True)


def detect_dependency_cycles(tasks: dict[str, dict]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            fail(f"dependency cycle detected at {task_id}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dep in tasks[task_id].get("dependencies", []):
            if dep in tasks:
                visit(dep)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in tasks:
        visit(task_id)


def main() -> None:
    state = load_json(STATE)
    control = state.get("organization", {}).get("control_repository", {})
    if control.get("full_name") != CONTROL_REPO or control.get("claimable") is not False:
        fail("control repository identity or claimable=false invariant is missing")
    if set(state.get("durable_task_states", [])) != DURABLE_STATES:
        fail("org-state durable task states do not match v0.2")

    tasks: dict[str, dict] = {}
    if TASKS.exists():
        for path in sorted(TASKS.glob("TASK-*.json")):
            task = load_json(path)
            validate_task(path, task)
            task_id = task["task_id"]
            if task_id in tasks:
                fail(f"duplicate task identity: {task_id}")
            tasks[task_id] = task
    detect_dependency_cycles(tasks)

    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_cosv_ecosystem_adoption.py")],
        cwd=ROOT,
        check=True,
    )

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "repository_operational_state.py"),
            "validate",
            str(ROOT / "examples" / "repository_operational_state.example.json"),
        ],
        cwd=ROOT,
        check=True,
    )

    subprocess.run(
        [sys.executable, "-m", "unittest", "tests.test_repository_operational_state"],
        cwd=ROOT,
        check=True,
    )

    print(
        json.dumps(
            {
                "valid": True,
                "schema": state.get("schema"),
                "generation": state.get("generation"),
                "task_count": len(tasks),
                "control_repository_claimable": False,
                "dependency_cycles": False,
                "repository_operational_state": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
