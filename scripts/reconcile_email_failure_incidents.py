#!/usr/bin/env python3
"""Map native email failure incidents for StegHealth remediation ownership.

This mapper is deliberately read-only with respect to task identity and execution.
It normalizes each incident, records existing canonical Task/COSV hints when an exact
match already exists, and emits one durable failure-map package for StegHealth.

StegHealth owns corrective-task creation. This mapper MUST NOT create a task, assign
a new COSV vector, mutate the Canonical Task Registry, invoke Canonical Work ingress,
or grant execution authority.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TERMINAL_STATES = {"CLOSED", "SUPERSEDED"}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object:{path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def incident_text(incident: dict[str, Any]) -> str:
    return json.dumps(incident, sort_keys=True, ensure_ascii=False)


def repo_from_incident(incident: dict[str, Any]) -> str:
    explicit = str(incident.get("normalized_repository") or "").strip()
    if explicit and explicit != "unknown-repo" and "/" in explicit:
        return explicit
    text = incident_text(incident)
    match = re.search(r"\[([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\]", text)
    return match.group(1) if match else "unknown-repo"


def existing_hint(incident: dict[str, Any], tasks: list[dict[str, Any]], vector_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    text = incident_text(incident).lower()
    incident_id = str(incident.get("incident_id") or "")
    matches = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            continue
        if task.get("systemic_incident_ref") == incident_id or task_id.lower() in text:
            if task.get("coordination_state") not in TERMINAL_STATES:
                matches.append(task)
    if len(matches) > 1:
        return {"state": "AMBIGUOUS_EXISTING_TASK_MATCH", "task_ids": sorted(str(row["task_id"]) for row in matches)}
    if not matches:
        return None
    task = matches[0]
    vector_matches = [row for row in vector_rows if isinstance(row, dict) and row.get("task_id") == task.get("task_id")]
    vector = vector_matches[0].get("vector") if len(vector_matches) == 1 else None
    return {
        "state": "EXACT_EXISTING_TASK_HINT",
        "task_id": task.get("task_id"),
        "coordination_state": task.get("coordination_state"),
        "cosv_task_vector": vector,
    }


def map_failures(monitor: dict[str, Any], registry: dict[str, Any] | None, vector_index: dict[str, Any] | None, monitor_receipt_ref: str) -> dict[str, Any]:
    incidents = monitor.get("incidents")
    require(isinstance(incidents, list), "monitor incidents missing")
    tasks = registry.get("tasks", []) if isinstance(registry, dict) else []
    vectors = vector_index.get("tasks", []) if isinstance(vector_index, dict) else []
    require(isinstance(tasks, list), "canonical task registry tasks invalid")
    require(isinstance(vectors, list), "task-vector index tasks invalid")

    mapped = []
    for incident in incidents:
        require(isinstance(incident, dict), "incident must be object")
        mapped.append({
            "incident_id": incident.get("incident_id"),
            "kind": incident.get("kind"),
            "repository": repo_from_incident(incident),
            "workflow": incident.get("normalized_workflow"),
            "error_signature": incident.get("normalized_error_signature"),
            "observation_count": incident.get("observation_count"),
            "observation_refs": list(incident.get("observation_refs") or []),
            "existing_canonical_task_hint": existing_hint(incident, tasks, vectors),
            "source_monitor_receipt_ref": monitor_receipt_ref,
            "required_owner": "StegVerse-Labs/StegHealth",
            "required_owner_action": "RECONCILE_AND_CREATE_OR_RESUME_CORRECTIVE_TASK",
        })

    return {
        "schema": "stegverse.email-failure-map-for-steghealth/v1",
        "failure_count": len(mapped),
        "failures": mapped,
        "task_creation_owner": "StegVerse-Labs/StegHealth",
        "mapper_creates_tasks": False,
        "mapper_assigns_new_cosv": False,
        "mapper_mutates_task_registry": False,
        "mapper_invokes_canonical_work": False,
        "archive_may_not_discard_unowned_failure": True,
        "authority_effect": "NONE_FAILURE_MAPPING_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--monitor-receipt", type=Path, required=True)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--vector-index", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    monitor = load(args.monitor_receipt)
    registry = load(args.registry) if args.registry and args.registry.is_file() else None
    vector_index = load(args.vector_index) if args.vector_index and args.vector_index.is_file() else None
    result = map_failures(monitor, registry, vector_index, str(args.monitor_receipt))
    write_json(args.output, result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
