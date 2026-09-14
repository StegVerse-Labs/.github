#!/usr/bin/env python3
"""Evaluate whether a canonical task has sufficient runtime-routing information for WorkerCoordinator review.

This is a coordination gate, not authorization. It does not admit the task, create a
claim/fence, satisfy completion evidence predicates, or infer process liveness. It
exists to prevent workers from reporting a generic "runtime missing" condition when
the canonical map already provides compatible runtime candidates, and to report the
exact unresolved routing predicate when it does not.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from match_runtime_profile import evaluate

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data/canonical-task-registry.json"
DEFAULT_RECORDS_DIR = ROOT / "data/canonical-task-records"
DEFAULT_MAP = ROOT / "control/runtime-profile-map.json"

COMPLETION_ONLY_DEPENDENCY_KINDS = {"RUNTIME_PREDICATE", "EVIDENCE"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object required:{path}")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError("FAIL_CLOSED: " + reason)


def find_task(registry: dict[str, Any], task_id: str, records_dir: Path) -> tuple[dict[str, Any], str]:
    """Resolve a canonical task from the aggregate registry or its standalone shard."""
    rows = [row for row in registry.get("tasks", []) if row.get("task_id") == task_id]
    require(len(rows) <= 1, "task identity must not duplicate in aggregate registry")
    if rows:
        return rows[0], "AGGREGATE_REGISTRY"

    record_path = records_dir / f"{task_id}.json"
    if record_path.is_file():
        record = load(record_path)
        require(record.get("task_id") == task_id, "standalone task record identity mismatch")
        return record, "STANDALONE_CANONICAL_TASK_RECORD"

    require(False, "canonical task identity must resolve exactly once")
    raise AssertionError("unreachable")


def resolve_routing_projection(task: dict[str, Any], runtime_map: dict[str, Any]) -> dict[str, Any]:
    """Resolve routing candidates for WorkerCoordinator review without claiming observation.

    Current observation remains a completion/runtime-evidence predicate. Routing review only
    needs a declared compatible route; WorkerCoordinator, Interlock/InTr, and Master Records
    still decide admission, transition, and observed reality.
    """
    requirements = task.get("runtime_requirements")
    require(isinstance(requirements, dict), "task has no explicit runtime requirements")
    required = set(requirements.get("capabilities", []))
    evaluated = [
        evaluate(
            profile,
            required,
            requirements.get("environment"),
            requirements.get("direction"),
            bool(requirements.get("mutation_required", False)),
            bool(requirements.get("deployment_required", False)),
            False,
        )
        for profile in runtime_map.get("profiles", [])
    ]
    compatible = sorted(
        [row for row in evaluated if row.get("compatible")],
        key=lambda row: str(row.get("profile_id")),
    )
    return {
        "map_generation": runtime_map.get("generation"),
        "candidate_profile_ids": [row.get("profile_id") for row in compatible],
        "candidate_count": len(compatible),
        "evaluated": evaluated,
        "projection_only": True,
        "selection_grants_authority": False,
        "current_observation_required_for_completion": bool(requirements.get("current_observation_required", False)),
        "workercoordinator_admission_still_required": True,
        "interlock_intr_transition_admission_still_required": True,
        "master_records_reconciliation_still_required": True,
        "authority_effect": "NONE_ROUTING_CANDIDATE_PROJECTION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--records-dir", type=Path, default=DEFAULT_RECORDS_DIR)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    args = parser.parse_args()

    registry = load(args.registry)
    runtime_map = load(args.map)
    task, task_source = find_task(registry, args.task_id, args.records_dir)

    requirements = task.get("runtime_requirements")
    require(isinstance(requirements, dict), "task has no explicit runtime requirements")
    stored_resolution = task.get("runtime_resolution")
    projected_resolution = resolve_routing_projection(task, runtime_map)

    stored_resolution_current = bool(
        isinstance(stored_resolution, dict)
        and stored_resolution.get("projection_only") is True
        and stored_resolution.get("selection_grants_authority") is False
        and stored_resolution.get("map_generation") == runtime_map.get("generation")
    )
    candidate_profile_ids = (
        stored_resolution.get("candidate_profile_ids", [])
        if stored_resolution_current else projected_resolution["candidate_profile_ids"]
    )
    resolution_source = "STORED_RUNTIME_RESOLUTION" if stored_resolution_current else "IN_MEMORY_CANONICAL_MAP_PROJECTION"

    predicates: dict[str, dict[str, Any]] = {}
    predicates["task_identity_resolved"] = {"satisfied": True, "source": task_source}
    predicates["runtime_requirements_declared"] = {"satisfied": True, "evidence": "canonical_task.runtime_requirements"}
    predicates["runtime_resolution_current"] = {
        "satisfied": stored_resolution_current,
        "resolution_source": resolution_source,
        "expected_map_generation": runtime_map.get("generation"),
        "observed_map_generation": stored_resolution.get("map_generation") if isinstance(stored_resolution, dict) else None,
        "in_memory_projection_candidate_profile_ids": projected_resolution["candidate_profile_ids"],
        "projection_persistence_required": not stored_resolution_current,
    }

    known_profiles = {p.get("profile_id") for p in runtime_map.get("profiles", [])}
    candidates_valid = bool(candidate_profile_ids) and all(candidate in known_profiles for candidate in candidate_profile_ids)
    predicates["compatible_runtime_candidate_exists"] = {
        "satisfied": candidates_valid,
        "candidate_profile_ids": candidate_profile_ids,
    }

    unresolved_route_blocking_dependencies: list[str] = []
    unresolved_completion_dependencies: list[str] = []
    for dependency in task.get("dependencies", []):
        if dependency.get("state") in {"RESOLVED", "NOT_APPLICABLE"}:
            continue
        dependency_id = dependency.get("dependency_id")
        if dependency.get("kind") in COMPLETION_ONLY_DEPENDENCY_KINDS:
            unresolved_completion_dependencies.append(dependency_id)
        else:
            unresolved_route_blocking_dependencies.append(dependency_id)

    predicates["route_blocking_dependencies_resolved"] = {
        "satisfied": not unresolved_route_blocking_dependencies,
        "unresolved_route_blocking_dependency_ids": unresolved_route_blocking_dependencies,
    }
    predicates["completion_evidence_predicates_pending"] = {
        "satisfied": not unresolved_completion_dependencies,
        "unresolved_completion_dependency_ids": unresolved_completion_dependencies,
        "blocks_routing_readiness": False,
        "blocks_completion": bool(unresolved_completion_dependencies),
    }

    blockers = task.get("blockers", [])
    predicates["no_active_task_blockers"] = {"satisfied": not blockers, "blockers": blockers}

    claim = task.get("worker_claim") or {}
    existing_claim = bool(claim.get("claim_ref") or claim.get("fence_ref"))
    predicates["workercoordinator_claim_not_duplicated"] = {
        "satisfied": not existing_claim,
        "existing_claim_ref": claim.get("claim_ref"),
        "existing_fence_ref": claim.get("fence_ref"),
        "note": "Existing ownership is not failure; reuse/wait/transfer must be resolved through WorkerCoordinator."
    }

    routing_ready = all(
        predicates[name]["satisfied"]
        for name in (
            "runtime_requirements_declared",
            "compatible_runtime_candidate_exists",
            "route_blocking_dependencies_resolved",
            "no_active_task_blockers",
            "workercoordinator_claim_not_duplicated",
        )
    )

    if not candidates_valid:
        disposition = "NO_COMPATIBLE_RUNTIME_PROFILE_CANDIDATE"
    elif unresolved_route_blocking_dependencies or blockers:
        disposition = "TASK_ROUTE_BLOCKING_DEPENDENCY_OR_BLOCKER_PREVENTS_ROUTING"
    elif existing_claim:
        disposition = "EXISTING_WORKERCOORDINATOR_OWNERSHIP_REUSE_WAIT_OR_TRANSFER"
    elif not stored_resolution_current:
        disposition = "ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW_WITH_RUNTIME_RESOLUTION_PERSISTENCE_PENDING"
    else:
        disposition = "ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW"

    result = {
        "schema": "stegverse.task-runtime-routing-readiness/v1",
        "task_id": task.get("task_id"),
        "correlation_id": task.get("correlation_id"),
        "coordination_state": task.get("coordination_state"),
        "task_source": task_source,
        "map_ref": str(args.map),
        "map_generation": runtime_map.get("generation"),
        "routing_projection": projected_resolution,
        "predicates": predicates,
        "routing_ready_for_workercoordinator_review": routing_ready,
        "disposition": disposition,
        "generic_runtime_missing_claim_allowed": False,
        "execution_authority_granted": False,
        "claim_or_fence_minted": False,
        "interlock_intr_transition_admission_still_required": True,
        "workercoordinator_admission_still_required": True,
        "master_records_reconciliation_still_required": True,
        "source_or_ci_validation_satisfies_completion": False,
        "authority_effect": "NONE_ROUTING_READINESS_ONLY",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
