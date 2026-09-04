#!/usr/bin/env python3
"""Reevaluate canonical task dependencies after explicit dependency-state changes.

This utility proposes registry updates only. It does not admit task transitions,
claim work, or mutate WorkerCoordinator ownership. A resolved dependency may
remove a blocker and expose a next candidate transition, but current governance
is still required before that transition occurs.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit("FAIL_CLOSED: registry object required")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dependency_id")
    parser.add_argument("--state", choices=["RESOLVED", "UNRESOLVED", "UNKNOWN"], required=True)
    parser.add_argument("--registry", default="data/canonical-task-registry.json")
    parser.add_argument("--output")
    args = parser.parse_args()

    registry = load(Path(args.registry))
    proposed = copy.deepcopy(registry)
    affected: list[dict[str, Any]] = []

    for task in proposed.get("tasks", []):
        dependencies = task.get("dependencies", [])
        matches = [dep for dep in dependencies if dep.get("dependency_id") == args.dependency_id]
        if not matches:
            continue
        require(len(matches) == 1, f"duplicate dependency identity in {task.get('task_id')}")
        dep = matches[0]
        previous = dep.get("state")
        dep["state"] = args.state

        blockers = task.get("blockers", [])
        before_blockers = len(blockers)
        if args.state == "RESOLVED":
            task["blockers"] = [b for b in blockers if b.get("dependency_id") != args.dependency_id]
        after_blockers = len(task.get("blockers", []))

        if args.state != "RESOLVED" and not any(b.get("dependency_id") == args.dependency_id for b in task.get("blockers", [])):
            task.setdefault("blockers", []).append({
                "blocker_id": "BLOCK-" + args.dependency_id,
                "dependency_id": args.dependency_id,
                "reason": "DEPENDENCY_NOT_RESOLVED",
            })

        unresolved = [d for d in task.get("dependencies", []) if d.get("state") != "RESOLVED"]
        next_candidates = list(task.get("allowed_next_transitions", [])) if not unresolved and not task.get("blockers") else []
        affected.append({
            "task_id": task.get("task_id"),
            "previous_dependency_state": previous,
            "proposed_dependency_state": args.state,
            "blockers_removed": before_blockers - after_blockers,
            "remaining_unresolved_dependencies": [d.get("dependency_id") for d in unresolved],
            "next_transition_candidates": next_candidates,
        })

    require(bool(affected), "dependency_id not referenced by any canonical task")
    proposed["generation"] = int(registry.get("generation", 0)) + 1
    proposed["status"] = "PROPOSED_DEPENDENCY_REEVALUATION_NOT_ADMITTED"
    proposed.setdefault("nonclaims", [])
    for value in [
        "DEPENDENCY_REEVALUATION_DOES_NOT_ADMIT_TASK_TRANSITION",
        "DEPENDENCY_REEVALUATION_DOES_NOT_MINT_WORKERCOORDINATOR_CLAIM_OR_FENCE",
        "DEPENDENCY_RESOLUTION_DOES_NOT_PROVE_DOWNSTREAM_WORK_OCCURRED",
    ]:
        if value not in proposed["nonclaims"]:
            proposed["nonclaims"].append(value)

    result = {
        "schema": "stegverse.canonical-task-dependency-reevaluation/v1",
        "dependency_id": args.dependency_id,
        "dependency_state": args.state,
        "affected": affected,
        "proposed_registry": proposed,
        "authority_effect": "NONE_PROPOSAL_ONLY",
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
