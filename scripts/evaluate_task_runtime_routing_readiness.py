#!/usr/bin/env python3
"""Evaluate whether a canonical task has sufficient runtime-routing information for WorkerCoordinator review.

This is a coordination gate, not authorization. It does not admit the task, create a
claim/fence, satisfy dependencies, or infer process liveness. It exists to prevent
workers from reporting a generic "runtime missing" condition when the canonical map
already provides compatible runtime candidates, and to report the exact unresolved
routing predicate when it does not.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object required:{path}")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError("FAIL_CLOSED: " + reason)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--registry", type=Path, default=ROOT / "data/canonical-task-registry.json")
    parser.add_argument("--map", type=Path, default=ROOT / "control/runtime-profile-map.json")
    args = parser.parse_args()

    registry = load(args.registry)
    runtime_map = load(args.map)
    matches = [t for t in registry.get("tasks", []) if t.get("task_id") == args.task_id]
    require(len(matches) == 1, "canonical task identity must resolve exactly once")
    task = matches[0]

    requirements = task.get("runtime_requirements")
    require(isinstance(requirements, dict), "task has no explicit runtime requirements")
    resolution = task.get("runtime_resolution")

    predicates: dict[str, dict[str, Any]] = {}
    predicates["runtime_requirements_declared"] = {"satisfied": True, "evidence": "canonical_task.runtime_requirements"}

    current_resolution = bool(
        isinstance(resolution, dict)
        and resolution.get("projection_only") is True
        and resolution.get("selection_grants_authority") is False
        and resolution.get("map_generation") == runtime_map.get("generation")
    )
    predicates["runtime_resolution_current"] = {
        "satisfied": current_resolution,
        "expected_map_generation": runtime_map.get("generation"),
        "observed_map_generation": resolution.get("map_generation") if isinstance(resolution, dict) else None,
    }

    candidates = resolution.get("candidate_profile_ids", []) if current_resolution else []
    known_profiles = {p.get("profile_id") for p in runtime_map.get("profiles", [])}
    candidates_valid = bool(candidates) and all(candidate in known_profiles for candidate in candidates)
    predicates["compatible_runtime_candidate_exists"] = {
        "satisfied": candidates_valid,
        "candidate_profile_ids": candidates,
    }

    unresolved_dependencies = [
        d.get("dependency_id") for d in task.get("dependencies", [])
        if d.get("state") not in {"RESOLVED", "NOT_APPLICABLE"}
    ]
    predicates["task_dependencies_resolved"] = {
        "satisfied": not unresolved_dependencies,
        "unresolved_dependency_ids": unresolved_dependencies,
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
            "runtime_resolution_current",
            "compatible_runtime_candidate_exists",
            "task_dependencies_resolved",
            "no_active_task_blockers",
            "workercoordinator_claim_not_duplicated",
        )
    )

    if not current_resolution:
        disposition = "RUNTIME_PROFILE_RESOLUTION_REQUIRED"
    elif not candidates_valid:
        disposition = "NO_COMPATIBLE_RUNTIME_PROFILE_CANDIDATE"
    elif unresolved_dependencies or blockers:
        disposition = "TASK_DEPENDENCY_OR_BLOCKER_PREVENTS_ROUTING"
    elif existing_claim:
        disposition = "EXISTING_WORKERCOORDINATOR_OWNERSHIP_REUSE_WAIT_OR_TRANSFER"
    else:
        disposition = "ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW"

    result = {
        "schema": "stegverse.task-runtime-routing-readiness/v1",
        "task_id": task.get("task_id"),
        "correlation_id": task.get("correlation_id"),
        "coordination_state": task.get("coordination_state"),
        "map_ref": str(args.map),
        "map_generation": runtime_map.get("generation"),
        "predicates": predicates,
        "routing_ready_for_workercoordinator_review": routing_ready,
        "disposition": disposition,
        "generic_runtime_missing_claim_allowed": False,
        "execution_authority_granted": False,
        "claim_or_fence_minted": False,
        "interlock_intr_transition_admission_still_required": True,
        "workercoordinator_admission_still_required": True,
        "authority_effect": "NONE_ROUTING_READINESS_ONLY",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
