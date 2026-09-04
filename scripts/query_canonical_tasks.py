#!/usr/bin/env python3
"""Query the canonical task registry by topic without inventing new task state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def searchable(task: dict[str, Any]) -> str:
    parts: list[str] = [
        str(task.get("task_id", "")),
        str(task.get("correlation_id", "")),
        str(task.get("goal", "")),
        str(task.get("coordination_state", "")),
        str(task.get("systemic_incident_ref", "")),
        str(task.get("human_action_ref", "")),
    ]
    targets = task.get("targets", {})
    for key in ("organizations", "repositories", "components"):
        parts.extend(str(x) for x in targets.get(key, []))
    for dep in task.get("dependencies", []):
        parts.extend(str(dep.get(k, "")) for k in ("dependency_id", "kind", "state", "ref"))
    for blocker in task.get("blockers", []):
        parts.extend(str(blocker.get(k, "")) for k in ("blocker_id", "dependency_id", "reason"))
    parts.extend(str(x) for x in task.get("adjacent_task_refs", []))
    parts.extend(str(x) for x in task.get("existing_evidence_refs", []))
    parts.extend(str(x) for x in task.get("expected_evidence_predicates", []))
    return "\n".join(parts).lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("terms", nargs="*", help="Terms to match; all terms must match")
    parser.add_argument("--registry", default="data/canonical-task-registry.json")
    parser.add_argument("--state", action="append", default=[])
    parser.add_argument("--include-closed", action="store_true")
    args = parser.parse_args()

    registry = load(Path(args.registry))
    terms = [term.lower() for term in args.terms]
    states = set(args.state)

    results: list[dict[str, Any]] = []
    for task in registry.get("tasks", []):
        state = task.get("coordination_state")
        if not args.include_closed and state in {"CLOSED", "SUPERSEDED"}:
            continue
        if states and state not in states:
            continue
        haystack = searchable(task)
        if all(term in haystack for term in terms):
            results.append({
                "task_id": task.get("task_id"),
                "correlation_id": task.get("correlation_id"),
                "goal": task.get("goal"),
                "coordination_state": state,
                "blockers": task.get("blockers", []),
                "dependencies": task.get("dependencies", []),
                "worker_claim": task.get("worker_claim"),
                "adjacent_task_refs": task.get("adjacent_task_refs", []),
                "existing_evidence_refs": task.get("existing_evidence_refs", []),
                "allowed_next_transitions": task.get("allowed_next_transitions", []),
                "handoff_projection_refs": task.get("handoff_projection_refs", []),
            })

    print(json.dumps({
        "schema": "stegverse.canonical-task-query-result/v1",
        "query_terms": args.terms,
        "count": len(results),
        "tasks": results,
        "nonclaim": "QUERY_RESULT_DOES_NOT_GRANT_CLAIM_OR_EXECUTION_AUTHORITY"
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
