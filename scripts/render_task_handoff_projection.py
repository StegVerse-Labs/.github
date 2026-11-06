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


_SAFE_TASK_ID = __import__("re").compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,200}$")


def _vector_task_id(vector: dict[str, Any]) -> str | None:
    if isinstance(vector.get("task_id"), str):
        return vector["task_id"]
    identity = vector.get("identity")
    if isinstance(identity, str) and ":task:" in identity:
        return identity.rsplit(":task:", 1)[1]
    return None


def resolve_task(registry: dict[str, Any], task_id: str, root: Path | None = None) -> tuple[dict[str, Any], str]:
    """Find a task in the Registry, else in the repository's other canonical task sources.

    The Registry wins. Only when it holds no row for ``task_id`` are the per-task
    canonical record, the task vector and the reusable-task bundle consulted, in that
    order, by exact file name and matching identity. The returned source is projected so
    a reader can tell a Registry row from a fallback.
    """
    matches = [task for task in registry.get("tasks", []) if task.get("task_id") == task_id]
    if len(matches) > 1:
        raise SystemExit(f"FAIL_CLOSED: expected exactly one task {task_id}, found {len(matches)}")
    if matches:
        return matches[0], "AGGREGATE_REGISTRY"
    if root is not None and _SAFE_TASK_ID.match(task_id):
        record = root / "data" / "canonical-task-records" / f"{task_id}.json"
        if record.is_file():
            value = load(record)
            if value.get("task_id") == task_id:
                return value, "STANDALONE_CANONICAL_TASK_RECORD"
        vector = root / "control" / "task-vectors" / f"{task_id}.json"
        if vector.is_file():
            value = load(vector)
            if _vector_task_id(value) == task_id:
                return {"task_id": task_id, "coordination_state": value.get("coordination_state"),
                        "cosv": value.get("cosv") or value.get("vector"), "source_refs": [str(vector.relative_to(root))]}, "TASK_VECTOR"
        bundle = root / "source-bundles" / "reusable-task-registry.d" / f"{task_id}.json"
        if bundle.is_file():
            value = load(bundle)
            if value.get("reusable_task_id") == task_id:
                return {"task_id": task_id, "goal": value.get("purpose"), "coordination_state": None,
                        "source_refs": [str(bundle.relative_to(root))]}, "REUSABLE_TASK_BUNDLE"
    raise SystemExit(f"FAIL_CLOSED: expected exactly one task {task_id}, found 0")


WORK_ITEM_KINDS = {"PULL_REQUEST", "ISSUE"}
WORK_ITEM_STATES = {"DRAFT", "OPEN", "HELD", "MERGED", "CLOSED"}


def project_work_items(items: Any) -> tuple[list[dict[str, Any]], int]:
    """Keep well-formed work items; count, never guess at, malformed ones."""
    kept: list[dict[str, Any]] = []
    rejected = 0
    for item in items if isinstance(items, list) else []:
        if (isinstance(item, dict) and item.get("kind") in WORK_ITEM_KINDS
                and isinstance(item.get("repo"), str) and "/" in item["repo"]
                and isinstance(item.get("number"), int) and item["number"] > 0
                and item.get("state") in WORK_ITEM_STATES
                and isinstance(item.get("owner_approved"), bool)):
            kept.append({key: item.get(key) for key in ("kind", "repo", "number", "state", "head", "ci", "owner_approved")})
        else:
            rejected += 1
    return kept, rejected


def project_owner_questions(registry: dict[str, Any], task_id: str) -> list[dict[str, Any]]:
    """Registry-level human actions for this task: question, documented default, source."""
    actions = registry.get("human_actions") or []
    return [
        {key: action.get(key) for key in ("id", "question", "default_until_answered", "source_ref", "state")}
        for action in actions
        if isinstance(action, dict) and action.get("task_id") == task_id
    ]


def resolve_component_profile(task: dict[str, Any], root: Path) -> dict[str, Any] | None:
    task_id = str(task.get("task_id") or "")
    if not task_id:
        return None
    path = root / "data" / "goal-task-component-profiles" / f"{task_id}.json"
    if not path.is_file():
        return None
    value = load(path)
    return value if value.get("task_id") == task_id else None


def resolved_human_action_ref(task: dict[str, Any], component_profile: dict[str, Any] | None) -> str | None:
    action = task.get("human_action_ref")
    if not component_profile:
        return action
    historical = component_profile.get("historical_runtime_reuse") or {}
    resident_request = component_profile.get("resident_reconciliation_request")
    if historical.get("user_reverification_after_established_node_connectivity") is False and resident_request:
        return None
    return action


def normalize_dependency(dep: Any) -> dict[str, Any]:
    """Registry dependencies are objects or bare task-id references.

    A bare reference carries no observed state, so it projects as UNKNOWN (fail closed)
    instead of being dropped or crashing the projection.
    """
    if isinstance(dep, dict):
        return dep
    if isinstance(dep, str):
        return {"task_id": dep, "state": "UNKNOWN", "dependency_form": "TASK_ID_REFERENCE"}
    return {"state": "UNKNOWN", "dependency_form": "MALFORMED"}


def build_projection(task: dict[str, Any], component_profile: dict[str, Any] | None = None,
                     registry: dict[str, Any] | None = None, task_source: str = "AGGREGATE_REGISTRY") -> dict[str, Any]:
    work_items, rejected_work_items = project_work_items(task.get("work_items"))
    unresolved_dependencies = [
        dep for dep in map(normalize_dependency, task.get("dependencies", []))
        if dep.get("state") in {"UNKNOWN", "UNRESOLVED"}
    ]
    human_action = resolved_human_action_ref(task, component_profile)
    return {
        "schema": "stegverse.canonical-task-handoff-projection/v1",
        "task_id": task.get("task_id"),
        "correlation_id": task.get("correlation_id"),
        "goal": task.get("goal"),
        "coordination_state": task.get("coordination_state"),
        "task_source": task_source,
        "issue_ref": task.get("issue_ref"),
        "canonical_issue": task.get("canonical_issue"),
        "owners": task.get("owners", {}),
        "handoff_projection_refs": task.get("handoff_projection_refs", []),
        "work_items": work_items,
        "rejected_work_items": rejected_work_items,
        "owner_questions": project_owner_questions(registry or {}, str(task.get("task_id") or "")),
        "targets": task.get("targets", {}),
        "worker_claim_projection": task.get("worker_claim", {}),
        "blockers": task.get("blockers", []),
        "unresolved_dependencies": unresolved_dependencies,
        "systemic_incident_ref": task.get("systemic_incident_ref"),
        "human_action_ref": human_action,
        "human_action_resolution": "SUPPRESSED_BY_AUTOMATIC_RESIDENT_RECONCILIATION" if task.get("human_action_ref") and human_action is None else "CANONICAL_TASK_RECORD",
        "resident_reconciliation_request": (component_profile or {}).get("resident_reconciliation_request"),
        "adjacent_task_refs": task.get("adjacent_task_refs", []),
        "existing_evidence_refs": task.get("existing_evidence_refs", []),
        "expected_evidence_predicates": (component_profile or {}).get("goal_predicates") or task.get("expected_evidence_predicates", []),
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
        "## Work items / owner questions",
        "```json",
        dump({"task_source": projection.get("task_source"), "issue_ref": projection.get("issue_ref"),
              "canonical_issue": projection.get("canonical_issue"), "owners": projection.get("owners", {}),
              "work_items": projection.get("work_items", []), "rejected_work_items": projection.get("rejected_work_items", 0),
              "owner_questions": projection.get("owner_questions", [])}),
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

    root = Path(args.registry).resolve().parent.parent
    registry = load(Path(args.registry))
    task, source = resolve_task(registry, args.task_id, root)
    profile = resolve_component_profile(task, root)
    projection = build_projection(task, profile, registry, source)
    text = (json.dumps(projection, indent=2, sort_keys=True) + "\n") if args.format == "json" else as_markdown(projection)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
