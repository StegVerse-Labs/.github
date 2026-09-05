#!/usr/bin/env python3
"""Static fail-closed validation for the StegVerse Canonical Work Coordination System.

This validates source contracts only. It does not claim live Interlock/InTr task
admission, WorkerCoordinator execution ownership, Master Records reconciliation,
runtime-profile observation, or runtime closure.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_SCHEMA = ROOT / "schemas" / "canonical-task-record.schema.json"
RECON_SCHEMA = ROOT / "schemas" / "task-master-records-reconciliation.schema.json"
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
POLICY = ROOT / "data" / "task-coordination-policy.json"
HANDOFF = ROOT / "docs" / "CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md"
WORKER_REGISTRY = ROOT / "control" / "worker-registry.json"
RUNTIME_MAP = ROOT / "control" / "runtime-profile-map.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL_CLOSED: {message}")


def main() -> int:
    task_schema = load_json(TASK_SCHEMA)
    recon_schema = load_json(RECON_SCHEMA)
    registry = load_json(REGISTRY)
    policy = load_json(POLICY)
    worker_registry = load_json(WORKER_REGISTRY)
    runtime_map = load_json(RUNTIME_MAP)
    handoff = HANDOFF.read_text(encoding="utf-8")

    require(registry.get("schema") == "stegverse.canonical-task-registry/v1", "canonical registry schema missing")
    require(registry.get("authoritative_roles", {}).get("execution_claim_and_fence") == "control/worker-registry.json / WorkerCoordinator", "registry must reference WorkerCoordinator for claim/fence authority")
    require(registry.get("authoritative_roles", {}).get("observed_reality_and_reconstruction") == "MASTER_RECORDS", "Master Records reality authority missing")
    require(registry.get("authoritative_roles", {}).get("governed_task_ingress_egress") == "INTERLOCK_INTR", "Interlock/InTr ingress-egress authority missing")

    task_props = task_schema.get("properties", {})
    authority_props = task_props.get("authority_model", {}).get("properties", {})
    require(authority_props.get("task_registry_mints_execution_authority", {}).get("const") is False, "task schema must deny registry execution authority")
    require(authority_props.get("worker_claim_authority", {}).get("const") == "WORKERCOORDINATOR", "task schema must bind WorkerCoordinator claim authority")
    require(authority_props.get("master_records_reality_authority", {}).get("const") is True, "task schema must bind Master Records reality authority")

    runtime_resolution_props = task_props.get("runtime_resolution", {}).get("properties", {})
    require(runtime_resolution_props.get("projection_only", {}).get("const") is True, "runtime resolution must be projection-only")
    require(runtime_resolution_props.get("selection_grants_authority", {}).get("const") is False, "runtime resolution must deny selection authority")

    recon_states = set(recon_schema.get("properties", {}).get("state", {}).get("enum", []))
    expected_states = {"CONSISTENT", "TASK_AHEAD_OF_EVIDENCE", "REALITY_AHEAD_OF_TASK", "CONFLICT", "UNKNOWN", "ORPHANED_EVENT"}
    require(recon_states == expected_states, "reconciliation states are incomplete or drifted")

    invariants = set(policy.get("invariants", []))
    for invariant in {
        "ONE_CANONICAL_WORK_TRUTH_MANY_PROJECTIONS",
        "TASK_REGISTRY_DOES_NOT_MINT_EXECUTION_AUTHORITY",
        "WORKERCOORDINATOR_OWNS_EXECUTION_CLAIM_AND_FENCE",
        "MASTER_RECORDS_OWNS_OBSERVED_REALITY_AND_RECONSTRUCTION",
        "COMPLETION_CLAIM_REQUIRES_RECONCILIATION_BEFORE_CLOSURE",
        "MISSING_EVIDENCE_IS_NOT_PROOF_OF_NON_OCCURRENCE",
        "HANDOFFS_ARE_PROJECTIONS_NOT_INDEPENDENT_TRUTH",
    }:
        require(invariant in invariants, f"missing coordination invariant: {invariant}")

    runtime_discovery = policy.get("runtime_profile_discovery", {})
    require(runtime_discovery.get("canonical_map") == "control/runtime-profile-map.json", "canonical runtime map policy binding missing")
    require(runtime_discovery.get("match_grants_authority") is False, "runtime profile match must not grant authority")

    require(isinstance(worker_registry.get("tasks"), list), "existing WorkerCoordinator registry tasks missing")
    require(worker_registry.get("schema") == "stegverse.heartbeat-worker-registry/v0.1", "unexpected WorkerCoordinator registry schema")
    require(runtime_map.get("schema") == "stegverse.runtime-profile-map/v1", "runtime profile map schema missing")
    require(runtime_map.get("authority", {}).get("map_grants_execution_authority") is False, "runtime map cannot grant execution authority")
    require(runtime_map.get("authority", {}).get("capability_match_grants_authority") is False, "runtime map match cannot grant authority")

    task_ids: set[str] = set()
    correlation_ids: set[str] = set()
    for task in registry.get("tasks", []):
        task_id = task.get("task_id")
        correlation_id = task.get("correlation_id")
        require(isinstance(task_id, str) and task_id, "task_id missing")
        require(isinstance(correlation_id, str) and correlation_id, f"correlation_id missing for {task_id}")
        require(task_id not in task_ids, f"duplicate task_id: {task_id}")
        task_ids.add(task_id)
        correlation_ids.add(correlation_id)

        claim = task.get("worker_claim", {})
        require(claim.get("authority") == "WORKERCOORDINATOR", f"{task_id}: claim authority drift")
        require(claim.get("projection_only") is True, f"{task_id}: registry claim must be projection-only")

        requirements = task.get("runtime_requirements")
        require(isinstance(requirements, dict), f"{task_id}: runtime requirements missing")
        require(isinstance(requirements.get("capabilities"), list), f"{task_id}: runtime capabilities missing")
        for flag in ("mutation_required", "deployment_required", "current_observation_required"):
            require(isinstance(requirements.get(flag), bool), f"{task_id}: runtime requirement {flag} must be boolean")

        resolution = task.get("runtime_resolution")
        if resolution is not None:
            require(resolution.get("projection_only") is True, f"{task_id}: runtime resolution not projection-only")
            require(resolution.get("selection_grants_authority") is False, f"{task_id}: runtime resolution grants authority")
            require(resolution.get("map_generation") == runtime_map.get("generation"), f"{task_id}: stale runtime-map generation projection")
            known_profiles = {p.get("profile_id") for p in runtime_map.get("profiles", [])}
            require(set(resolution.get("candidate_profile_ids", [])).issubset(known_profiles), f"{task_id}: runtime resolution references unknown profile")

        completion = task.get("completion", {})
        state = task.get("coordination_state")
        if state == "CLOSED":
            require(completion.get("claimed") is True, f"{task_id}: CLOSED without completion claim")
            require(completion.get("validated") is True, f"{task_id}: CLOSED without validated completion")
            require(bool(completion.get("reconciliation_ref")), f"{task_id}: CLOSED without reconciliation reference")

        blocker_dependency_ids = {item.get("dependency_id") for item in task.get("blockers", [])}
        dependency_ids = {item.get("dependency_id") for item in task.get("dependencies", [])}
        require(blocker_dependency_ids.issubset(dependency_ids), f"{task_id}: blocker references non-existent dependency")

    required_handoff_phrases = [
        "one canonical work truth and many projections",
        "WorkerCoordinator remains authoritative for executable claim/fence ownership",
        "Task Registry and Master Records are intentionally comparable but not interchangeable",
        "A human action is represented once as a canonical dependency object",
        "Handoffs become projections of canonical coordination state",
    ]
    handoff_lower = handoff.lower()
    for phrase in required_handoff_phrases:
        require(phrase.lower() in handoff_lower, f"handoff missing required statement: {phrase}")

    print("PASS: canonical work coordination source contract is internally consistent")
    print(f"INFO: canonical task records={len(task_ids)} correlations={len(correlation_ids)}")
    print(f"INFO: existing WorkerCoordinator task records={len(worker_registry.get('tasks', []))}")
    print(f"INFO: runtime profile map profiles={len(runtime_map.get('profiles', []))} generation={runtime_map.get('generation')}")
    print("NONCLAIM: live Interlock/InTr, WorkerCoordinator, runtime-profile observation, Master Records reconciliation, and closure are not proven")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
