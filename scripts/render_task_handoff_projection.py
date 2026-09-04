#!/usr/bin/env python3
"""Render a session-safe handoff projection from canonical task state.

The output is a projection only. It does not mutate task state, create claims,
or prove runtime transitions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def find_task(registry: dict[str, Any], task_id: str) -> dict[str, Any]:
    matches = [task for task in registry.get("tasks", []) if task.get("task_id") == task_id]
    if len(matches) != 1:
        raise SystemExit(f"FAIL_CLOSED: expected exactly one task {task_id}, found {len(matches)}")
    return matches[0]


def build_projection(task: dict[str, Any]) -> dict[str, Any]:
    unresolved_dependencies = [
        dep for dep in task.get("dependencies", [])
        if dep.get("state") in {"UNKNOWN", "UNRESOLVED"}
    ]
    return {
        "schema": "stegverse.canonical-task-handoff-projection/v1",
        "task_id": task.get("task_id"),
        "correlation_id": task.get("correlation_id"),
        "goal": task.get("goal"),
        "coordination_state": task.get("coordination_state"),
        "targets": task.get("targets", {}),
        "worker_claim_projection": task.get("worker_claim", {}),
        "blockers": task.get("blockers", []),
        "unresolved_dependencies": unresolved_dependencies,
        "systemic_incident_ref": task.get("systemic_incident_ref"),
        "human_action_ref": task.get("human_action_ref"),
        "adjacent_task_refs": task.get("adjacent_task_refs", []),
        "existing_evidence_refs": task.get("existing_evidence_refs", []),
        "expected_evidence_predicates": task.get("expected_evidence_predicates", []),
        "completion": task.get("completion", {}),
        "next_admissible_transition_candidates": task.get("allowed_next_transitions", []),
        "source_refs": task.get("source_refs", []),
        "continuation_rule": "RECONCILE_ADJACENT_EVIDENCE_DEPENDENCIES_AND_WORKERCOORDINATOR_CLAIMS_BEFORE_EXECUTION",
        "session_archive_rule": "SESSION_MAY_END_ONLY_WHEN_NO_UNIQUE_TASK_CONTINUITY_REMAINS_ONLY_IN_SESSION_CONTEXT",
        "authority_nonclaims": [
            "HANDOFF_PROJECTION_IS_NOT_EXECUTION_AUTHORITY",
            "HANDOFF_PROJECTION_IS_NOT_A_WORKERCOORDINATOR_CLAIM",
            "HANDOFF_PROJECTION_IS_NOT_MASTER_RECORDS_REALITY_EVIDENCE",
            "HANDOFF_PROJECTION_IS_NOT_INTERLOCK_INTR_ADMISSION"
        ]
    }


def as_markdown(projection: dict[str, Any]) -> str:
    def dump(value: Any) -> str:
        return json.dumps(value, indent=2, sort_keys=True)

    return "\n".join([
        f"# Canonical Task Handoff — {projection['task_id']}",
        "",
        f"Correlation: `{projection['correlation_id']}`",
        f"State: `{projection['coordination_state']}`",
        "",
        "## Goal",
        projection.get("goal") or "",
        "",
        "## WorkerCoordinator claim projection",
        "```json",
        dump(projection.get("worker_claim_projection", {})),
        "```",
        "",
        "## Blockers / unresolved dependencies",
        "```json",
        dump({"blockers": projection.get("blockers", []), "dependencies": projection.get("unresolved_dependencies", [])}),
        "```",
        "",
        "## Adjacent tasks / existing evidence",
        "```json",
        dump({"adjacent_task_refs": projection.get("adjacent_task_refs", []), "existing_evidence_refs": projection.get("existing_evidence_refs", [])}),
        "```",
        "",
        "## Evidence still required",
        "```json",
        dump(projection.get("expected_evidence_predicates", [])),
        "```",
        "",
        "## Next transition candidates",
        "```json",
        dump(projection.get("next_admissible_transition_candidates", [])),
        "```",
        "",
        "## Continuation rule",
        projection["continuation_rule"],
        "",
        "This is a projection of canonical task state, not an independent source of truth or execution authority.",
        ""
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="data/canonical-task-registry.json")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output")
    args = parser.parse_args()

    task = find_task(load(Path(args.registry)), args.task_id)
    projection = build_projection(task)
    text = (json.dumps(projection, indent=2, sort_keys=True) + "\n") if args.format == "json" else as_markdown(projection)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
