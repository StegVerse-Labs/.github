#!/usr/bin/env python3
"""Map native email failures and delegate corrective-task creation to StegHealth.

Ownership is intentionally split:
- this .github entrypoint maps/deduplicates failure evidence and may provide exact
  existing Task/COSV hints;
- StegHealth owns corrective-task creation/resumption decisions and emits task records;
- this entrypoint may import only those StegHealth-created canonical candidates into
  the live Canonical Task Registry and task-vector index for ordinary Canonical Work;
- WorkerCoordinator and Interlock/InTr retain execution/transition authority.

This module MUST NOT invent corrective task identity itself.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

TERMINAL_STATES = {"CLOSED", "SUPERSEDED"}
STEGHEALTH_OWNER = "StegVerse-Labs/StegHealth"


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
    match = re.search(r"\[([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\]", incident_text(incident))
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


def build_failure_map(monitor: dict[str, Any], registry: dict[str, Any], vector_index: dict[str, Any], monitor_receipt_ref: str) -> dict[str, Any]:
    incidents = monitor.get("incidents")
    require(isinstance(incidents, list), "monitor incidents missing")
    tasks = registry.get("tasks")
    vectors = vector_index.get("tasks")
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
            "required_owner": STEGHEALTH_OWNER,
            "required_owner_action": "RECONCILE_AND_CREATE_OR_RESUME_CORRECTIVE_TASK",
        })
    return {
        "schema": "stegverse.email-failure-map-for-steghealth/v1",
        "failure_count": len(mapped),
        "failures": mapped,
        "task_creation_owner": STEGHEALTH_OWNER,
        "mapper_creates_tasks": False,
        "mapper_assigns_new_cosv": False,
        "mapper_mutates_task_registry": False,
        "mapper_invokes_canonical_work": False,
        "archive_may_not_discard_unowned_failure": True,
        "authority_effect": "NONE_FAILURE_MAPPING_ONLY",
    }


def repo_roots(values: Mapping[str, str]) -> list[Path]:
    result: list[Path] = []
    raw = values.get("STEGVERSE_REPO_ROOTS_JSON")
    if raw:
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = None
        if isinstance(parsed, dict):
            result.extend(Path(v).expanduser() for v in parsed.values() if isinstance(v, str) and v)
        elif isinstance(parsed, list):
            result.extend(Path(v).expanduser() for v in parsed if isinstance(v, str) and v)
    return result


def resolve_steghealth(values: Mapping[str, str], registry: Path) -> Path | None:
    candidates: list[Path] = []
    explicit = values.get("STEGVERSE_STEGHEALTH_ROOT")
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend(repo_roots(values))
    base = registry.resolve().parents[2] if len(registry.resolve().parents) > 2 else registry.resolve().parent
    candidates.extend((base / "StegHealth", base.parent / "StegHealth"))
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            continue
        if resolved.name == "StegHealth" and (resolved / "tools/consume_ecosystem_failure_map.py").is_file():
            return resolved
    return None


def import_steghealth_candidates(registry: dict[str, Any], vector_index: dict[str, Any], vector_dir: Path, owner_result: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    require(owner_result.get("task_creation_owner") == STEGHEALTH_OWNER, "StegHealth task-creation owner mismatch")
    candidates = owner_result.get("canonical_task_candidates")
    handoffs = owner_result.get("task_handoffs")
    require(isinstance(candidates, list), "StegHealth canonical_task_candidates missing")
    require(isinstance(handoffs, list), "StegHealth task_handoffs missing")
    tasks = registry.get("tasks")
    rows = vector_index.get("tasks")
    require(isinstance(tasks, list), "registry tasks invalid")
    require(isinstance(rows, list), "vector index tasks invalid")
    changed = False

    handoff_by_id = {row.get("task_id"): row for row in handoffs if isinstance(row, dict) and isinstance(row.get("task_id"), str)}
    for candidate in candidates:
        require(isinstance(candidate, dict), "StegHealth canonical task candidate must be object")
        require(candidate.get("schema") == "stegverse.canonical-task-record/v1", "StegHealth canonical candidate schema mismatch")
        task_id = candidate.get("task_id")
        require(isinstance(task_id, str) and task_id.startswith("STEGHEALTH-FAILURE-REMEDIATION-"), "StegHealth corrective task id namespace invalid")
        existing = [row for row in tasks if isinstance(row, dict) and row.get("task_id") == task_id]
        require(len(existing) <= 1, f"duplicate canonical task identity:{task_id}")
        if not existing:
            tasks.append(candidate)
            changed = True
        handoff = handoff_by_id.get(task_id) or {}
        vector = handoff.get("cosv_task_vector")
        require(isinstance(vector, str) and len(vector) == 14 and vector.isdigit(), f"StegHealth corrective COSV invalid:{task_id}")
        vector_matches = [row for row in rows if isinstance(row, dict) and row.get("task_id") == task_id]
        require(len(vector_matches) <= 1, f"duplicate corrective COSV identity:{task_id}")
        if not vector_matches:
            vector_path = vector_dir / f"{task_id}.json"
            write_json(vector_path, {
                "identity": f"StegVerse-Labs/StegHealth:task:{task_id}",
                "profile": "task.v1",
                "level": "task",
                "vector": vector,
                "evidence_refs": list(candidate.get("existing_evidence_refs") or []),
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
            })
            rows.append({
                "task_id": task_id,
                "repository": STEGHEALTH_OWNER,
                "registry_ref": f"StegVerse-Labs/StegHealth:tasks/failure-remediation/{task_id}.json",
                "source_state_vector_ref": str(vector_path),
                "vector": vector,
                "vector_state": "EMITTED",
                "authority_effect": "NONE",
            })
            changed = True
    if changed:
        registry["generation"] = int(registry.get("generation") or 0) + 1
    return changed, handoffs


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
    failure_map = build_failure_map(monitor, registry, vector_index, str(args.monitor_receipt))
    map_path = args.output.with_name(args.output.stem + ".failure-map.json")
    write_json(map_path, failure_map)

    steghealth = resolve_steghealth(os.environ, args.registry)
    if steghealth is None:
        result = {
            "schema": "stegverse.email-failure-canonical-work-handoff/v1",
            "state": "STEGHEALTH_OWNER_NOT_MATERIALIZED",
            "task_creation_owner": STEGHEALTH_OWNER,
            "failure_map_ref": str(map_path),
            "retry_required": True,
            "task_handoffs": [],
            "registry_changed": False,
            "authority_effect": "NONE_FAILURE_MAPPING_ONLY",
        }
        write_json(args.output, result)
        print(json.dumps(result, sort_keys=True))
        return 0

    owner_output = args.output.with_name(args.output.stem + ".steghealth.json")
    completed = subprocess.run([
        sys.executable,
        str(steghealth / "tools/consume_ecosystem_failure_map.py"),
        "--failure-map", str(map_path),
        "--state-root", str(steghealth),
        "--output", str(owner_output),
    ], cwd=str(steghealth), capture_output=True, text=True, check=False, timeout=300)
    if completed.returncode != 0 or not owner_output.is_file():
        result = {
            "schema": "stegverse.email-failure-canonical-work-handoff/v1",
            "state": "STEGHEALTH_OWNER_ATTEMPT_FAILED",
            "task_creation_owner": STEGHEALTH_OWNER,
            "failure_map_ref": str(map_path),
            "retry_required": True,
            "returncode": completed.returncode,
            "task_handoffs": [],
            "registry_changed": False,
            "authority_effect": "NONE_FAILURE_MAPPING_ONLY",
        }
        write_json(args.output, result)
        print(json.dumps(result, sort_keys=True))
        return 0

    owner_result = load(owner_output)
    changed, handoffs = import_steghealth_candidates(registry, vector_index, args.vector_dir, owner_result)
    if changed:
        write_json(args.registry, registry)
        write_json(args.vector_index, vector_index)

    normalized_handoffs = []
    for row in handoffs:
        if not isinstance(row, dict):
            continue
        action = row.get("next_action")
        if action in {"INITIATE_CANONICAL_WORK_INGRESS", "INITIATE_OR_CONTINUE_CANONICAL_INGRESS"}:
            next_action = "INITIATE_CANONICAL_WORK_INGRESS"
        else:
            next_action = "REINITIATE_OR_CONTINUE_EXISTING_TASK_THROUGH_CANONICAL_HANDOFF"
        normalized_handoffs.append({
            **row,
            "next_action": next_action,
            "task_creation_owner": STEGHEALTH_OWNER,
            "email_observation_mints_execution_authority": False,
            "workercoordinator_claim_fence_still_required": True,
            "interlock_intr_transition_still_required": True,
        })

    result = {
        "schema": "stegverse.email-failure-canonical-work-handoff/v1",
        "state": "STEGHEALTH_TASK_CREATION_COMPLETE",
        "task_creation_owner": STEGHEALTH_OWNER,
        "failure_map_ref": str(map_path),
        "steghealth_result_ref": str(owner_output),
        "corrective_task_count": len(normalized_handoffs),
        "registry_changed": changed,
        "task_handoffs": normalized_handoffs,
        "automatic_corrective_task_derivation": True,
        "automatic_canonical_ingress_required_for_proposed_tasks": True,
        "email_archive_may_not_discard_corrective_work": True,
        "retry_required": False,
        "authority_effect": "NONE_STEGHEALTH_TASK_CREATION_IMPORTED_FOR_CANONICAL_INGRESS",
    }
    write_json(args.output, result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
