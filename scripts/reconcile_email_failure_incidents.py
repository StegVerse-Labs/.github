#!/usr/bin/env python3
"""Reconcile native email failure incidents into canonical corrective work.

This is coordination/task-ingress preparation, not execution authority. It preserves
the established email-monitor behavior that actionable GitHub failures become durable
corrective work instead of disappearing when their source email is archived.

For each incident:
- reuse an existing nonterminal canonical task when the incident already names/binds it;
- otherwise derive one deterministic adjacent corrective task after duplicate checks;
- ensure a task.v1 COSV pointer exists;
- emit the exact Task/COSV handoff and whether Canonical Work ingress should be initiated.

WorkerCoordinator remains claim/fence authority. Interlock/InTr remains governed task
transition authority. This utility never grants execution authority itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

DEFAULT_VECTOR = "10100000100000"
TERMINAL_STATES = {"CLOSED", "SUPERSEDED"}
ACTIVE_STATES = {"INGRESS_ADMITTED", "CLAIMABLE", "CLAIMED", "IN_PROGRESS", "COMPLETION_CLAIMED", "TRANSFERRED", "REOPENED_DUE_TO_NEW_EVIDENCE", "COMPLETION_REVOKED"}


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
    return match.group(1) if match else "StegVerse-Labs/.github"


def workflow_from_incident(incident: dict[str, Any]) -> str:
    value = str(incident.get("normalized_workflow") or "unknown-workflow").strip()
    return value or "unknown-workflow"


def deterministic_task_id(incident_id: str) -> str:
    digest = hashlib.sha256(incident_id.encode("utf-8")).hexdigest()[:20].upper()
    return f"EMAIL-FAILURE-CORRECTION-{digest}"


def find_existing_task(incident: dict[str, Any], tasks: list[dict[str, Any]]) -> dict[str, Any] | None:
    incident_id = str(incident.get("incident_id") or "")
    by_incident = [task for task in tasks if task.get("systemic_incident_ref") == incident_id]
    if len(by_incident) == 1:
        return by_incident[0]
    if len(by_incident) > 1:
        raise RuntimeError(f"incident binds multiple canonical tasks:{incident_id}")

    text = incident_text(incident).lower()
    matches = [task for task in tasks if isinstance(task.get("task_id"), str) and task["task_id"].lower() in text]
    nonterminal = [task for task in matches if task.get("coordination_state") not in TERMINAL_STATES]
    if len(nonterminal) == 1:
        return nonterminal[0]
    if len(nonterminal) > 1:
        raise RuntimeError(f"incident names multiple nonterminal tasks:{incident_id}")
    return None


def ensure_vector(task_id: str, vector_index: dict[str, Any], vector_dir: Path, evidence_refs: list[str]) -> str:
    rows = vector_index.setdefault("tasks", [])
    require(isinstance(rows, list), "task-vector index tasks invalid")
    matches = [row for row in rows if isinstance(row, dict) and row.get("task_id") == task_id]
    if len(matches) > 1:
        raise RuntimeError(f"duplicate COSV pointer:{task_id}")
    if matches:
        vector = matches[0].get("vector")
        require(isinstance(vector, str) and len(vector) == 14 and vector.isdigit(), f"invalid COSV pointer:{task_id}")
        return vector

    vector = DEFAULT_VECTOR
    vector_path = vector_dir / f"{task_id}.json"
    vector_record = {
        "identity": f"StegVerse-Labs/.github:task:{task_id}",
        "profile": "task.v1",
        "level": "task",
        "vector": vector,
        "evidence_refs": evidence_refs,
        "observed_at": None,
        "exact_metrics": {
            "symbol_order": "LRUIVGOCMTBEAP",
            "lifecycle": "UNCLAIMED",
            "archive_ready": False,
            "unassigned_work": 1,
            "chat_owned_implementation": 0,
            "chat_owned_validation": 0,
            "chat_owned_integration": 0,
            "chat_owned_observation": 0,
            "chat_owned_credentials": 0,
            "canonical_owner_installed": True,
            "thread_required": False,
            "blocker_count": 0,
            "evidence_complete": False,
            "activated": False,
            "propagated": False,
        },
    }
    write_json(vector_path, vector_record)
    rows.append({
        "task_id": task_id,
        "repository": "StegVerse-Labs/.github",
        "registry_ref": "data/canonical-task-registry.json",
        "source_state_vector_ref": str(vector_path),
        "vector": vector,
        "vector_state": "EMITTED",
        "authority_effect": "NONE",
    })
    return vector


def make_task(incident: dict[str, Any], task_id: str, monitor_receipt_ref: str) -> dict[str, Any]:
    incident_id = str(incident.get("incident_id") or "")
    repo = repo_from_incident(incident)
    workflow = workflow_from_incident(incident)
    refs = [monitor_receipt_ref] + [str(x) for x in incident.get("observation_refs", []) if str(x)]
    return {
        "schema": "stegverse.canonical-task-record/v1",
        "task_id": task_id,
        "correlation_id": task_id,
        "root_correlation_id": incident_id or task_id,
        "parent_task_id": None,
        "goal": f"Resolve GitHub failure incident {incident_id} for {repo} / {workflow}; inspect authentic workflow evidence, correct the root cause, validate the correction, and continue until resolved or genuine human review is required.",
        "coordination_state": "PROPOSED",
        "source_refs": refs,
        "targets": {
            "organizations": [repo.split("/", 1)[0]] if "/" in repo else ["StegVerse-Labs"],
            "repositories": [repo],
            "components": ["github-failure-correction", "email-failure-graph", "canonical-work-ingress"],
        },
        "dependencies": [],
        "blockers": [],
        "systemic_incident_ref": incident_id or None,
        "adjacent_task_refs": ["STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001", "STEGVERSE-CANONICAL-WORK-COORDINATION-001"],
        "existing_evidence_refs": refs,
        "expected_evidence_predicates": [
            "AUTHENTIC_GITHUB_FAILURE_EVIDENCE_RECONCILED",
            "ROOT_CAUSE_CORRECTED_OR_GENUINE_HUMAN_BOUNDARY_RECORDED",
            "CORRECTION_VALIDATED",
            "POST_CORRECTION_FAILURE_STATE_RECONCILED",
        ],
        "runtime_requirements": {
            "capabilities": ["canonical_artifact_validation", "github_workflow_failure_reconciliation"],
            "environment": "SOVEREIGN_RESIDENT",
            "direction": "INTERNAL",
            "mutation_required": True,
            "deployment_required": False,
            "current_observation_required": True,
        },
        "runtime_resolution": None,
        "worker_claim": {"authority": "WORKERCOORDINATOR", "claim_ref": None, "fence_ref": None, "projection_only": True},
        "human_action_ref": None,
        "completion": {"claimed": False, "validated": False, "reconciliation_ref": None},
        "allowed_next_transitions": ["INGRESS_ADMITTED"],
        "handoff_projection_refs": ["docs/NATIVE_EMAIL_ACTION_MONITOR_MIRROR_HANDOFF.md"],
        "authority_model": {
            "task_registry_mints_execution_authority": False,
            "source_state_proves_execution": False,
            "worker_claim_authority": "WORKERCOORDINATOR",
            "master_records_reality_authority": True,
            "interlock_intr_required_for_governed_ingress_egress": True,
        },
    }


def reconcile(monitor: dict[str, Any], registry: dict[str, Any], vector_index: dict[str, Any], vector_dir: Path, monitor_receipt_ref: str) -> dict[str, Any]:
    incidents = monitor.get("incidents")
    require(isinstance(incidents, list), "monitor incidents missing")
    tasks = registry.get("tasks")
    require(isinstance(tasks, list), "canonical task registry tasks missing")

    handoffs: list[dict[str, Any]] = []
    changed = False
    for incident in incidents:
        require(isinstance(incident, dict), "incident must be object")
        existing = find_existing_task(incident, tasks)
        if existing is not None and existing.get("coordination_state") not in TERMINAL_STATES:
            task = existing
            disposition = "EXISTING_CORRECTIVE_TASK_REUSED"
        else:
            task_id = deterministic_task_id(str(incident.get("incident_id") or incident_text(incident)))
            by_id = next((row for row in tasks if isinstance(row, dict) and row.get("task_id") == task_id), None)
            if by_id is None:
                task = make_task(incident, task_id, monitor_receipt_ref)
                tasks.append(task)
                changed = True
                disposition = "NEW_ADJACENT_CORRECTIVE_TASK_REGISTERED"
            else:
                task = by_id
                disposition = "EXISTING_DERIVED_CORRECTIVE_TASK_REUSED"

        evidence_refs = [monitor_receipt_ref] + [str(x) for x in incident.get("observation_refs", []) if str(x)]
        vector = ensure_vector(str(task["task_id"]), vector_index, vector_dir, evidence_refs)
        state = str(task.get("coordination_state") or "")
        if state == "PROPOSED":
            action = "INITIATE_CANONICAL_WORK_INGRESS"
        elif state in ACTIVE_STATES:
            action = "REINITIATE_OR_CONTINUE_EXISTING_TASK_THROUGH_CANONICAL_HANDOFF"
        elif state in TERMINAL_STATES:
            action = "DERIVE_SUCCESSOR_REQUIRED"
        else:
            action = "RECONCILE_CURRENT_TASK_STATE"
        handoffs.append({
            "incident_id": incident.get("incident_id"),
            "task_id": task["task_id"],
            "cosv_task_vector": vector,
            "coordination_state": state,
            "disposition": disposition,
            "next_action": action,
            "email_observation_mints_execution_authority": False,
            "workercoordinator_claim_fence_still_required": True,
            "interlock_intr_transition_still_required": True,
        })

    if changed:
        registry["generation"] = int(registry.get("generation") or 0) + 1

    return {
        "schema": "stegverse.email-failure-canonical-work-handoff/v1",
        "incident_count": len(incidents),
        "corrective_task_count": len(handoffs),
        "registry_changed": changed,
        "task_handoffs": handoffs,
        "automatic_corrective_task_derivation": True,
        "automatic_canonical_ingress_required_for_proposed_tasks": True,
        "email_archive_may_not_discard_corrective_work": True,
        "authority_effect": "NONE_COORDINATION_AND_TASK_INGRESS_PREPARATION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--monitor-receipt", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--vector-index", type=Path, required=True)
    parser.add_argument("--vector-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    monitor = load(args.monitor_receipt)
    registry = load(args.registry)
    vector_index = load(args.vector_index)
    result = reconcile(monitor, registry, vector_index, args.vector_dir, str(args.monitor_receipt))
    write_json(args.registry, registry)
    write_json(args.vector_index, vector_index)
    write_json(args.output, result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
