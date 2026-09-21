#!/usr/bin/env python3
"""Project a deterministic runtime-profile resolution into one canonical task.

The input resolution is discovery evidence only. This utility does not grant task
admission, execution, claim/fence, credential, deployment, transition, or consequence
authority. It only records the current map generation and compatible profile IDs.
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
        raise RuntimeError(f"object required:{path}")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError("FAIL_CLOSED: " + reason)


def project_task_record(task: dict[str, Any], runtime_map: dict[str, Any], resolution: dict[str, Any], map_ref: str) -> dict[str, Any]:
    require(resolution.get("schema") == "stegverse.canonical-task-runtime-resolution/v1", "resolution schema mismatch")
    require(resolution.get("projection_only") is True, "runtime resolution must be projection-only")
    require(resolution.get("selection_grants_authority") is False, "runtime resolution cannot grant authority")
    require(resolution.get("map_generation") == runtime_map.get("generation"), "runtime map generation drift")
    require(resolution.get("map_ref") == map_ref, "runtime map reference drift")

    task_id = resolution.get("task_id")
    correlation_id = resolution.get("correlation_id")
    require(task.get("task_id") == task_id, "task identity drift")
    require(task.get("correlation_id") == correlation_id, "correlation identity drift")
    require(task.get("runtime_requirements") == resolution.get("requirements"), "runtime requirements drift")

    candidates = resolution.get("candidate_profile_ids")
    require(isinstance(candidates, list), "candidate profile list required")
    known = {p.get("profile_id") for p in runtime_map.get("profiles", [])}
    require(all(c in known for c in candidates), "resolution references unknown runtime profile")

    proposed = copy.deepcopy(task)
    proposed["runtime_resolution"] = {
        "map_ref": map_ref,
        "map_generation": runtime_map.get("generation"),
        "candidate_profile_ids": candidates,
        "resolved_at": resolution.get("resolved_at"),
        "projection_only": True,
        "selection_grants_authority": False,
    }
    return proposed


def project(registry: dict[str, Any], runtime_map: dict[str, Any], resolution: dict[str, Any], map_ref: str) -> dict[str, Any]:
    task_id = resolution.get("task_id")
    proposed = copy.deepcopy(registry)
    matches = [t for t in proposed.get("tasks", []) if t.get("task_id") == task_id]
    require(len(matches) == 1, "task identity must resolve exactly once")
    projected_task = project_task_record(matches[0], runtime_map, resolution, map_ref)
    matches[0].clear()
    matches[0].update(projected_task)
    proposed["generation"] = int(registry.get("generation", 0)) + 1
    proposed["status"] = "RUNTIME_PROFILE_CANDIDATES_PROJECTED_NO_AUTHORITY_GRANTED"
    nonclaims = proposed.setdefault("nonclaims", [])
    for value in (
        "RUNTIME_PROFILE_RESOLUTION_IS_PROJECTION_ONLY",
        "RUNTIME_PROFILE_SELECTION_DOES_NOT_GRANT_TASK_ADMISSION",
        "WORKERCOORDINATOR_CLAIM_FENCE_STILL_REQUIRED",
        "INTERLOCK_INTR_TRANSITION_ADMISSION_STILL_REQUIRED",
    ):
        if value not in nonclaims:
            nonclaims.append(value)
    return proposed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("data/canonical-task-registry.json"))
    parser.add_argument("--map", type=Path, default=Path("control/runtime-profile-map.json"))
    parser.add_argument("--records-dir", type=Path, default=Path("data/canonical-task-records"))
    parser.add_argument("--resolution", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    registry = load(args.registry)
    runtime_map = load(args.map)
    resolution = load(args.resolution)
    task_id = resolution.get("task_id")
    matches = [t for t in registry.get("tasks", []) if t.get("task_id") == task_id]
    require(len(matches) <= 1, "task identity duplicates in aggregate registry")

    target_kind = "AGGREGATE_CANONICAL_TASK_REGISTRY"
    target_path = args.registry
    if matches:
        result = project(registry, runtime_map, resolution, str(args.map))
    else:
        require(isinstance(task_id, str) and task_id, "runtime resolution task identity required")
        shard_path = args.records_dir / f"{task_id}.json"
        require(shard_path.is_file(), "task identity must resolve in aggregate registry or standalone canonical shard")
        task = load(shard_path)
        result = project_task_record(task, runtime_map, resolution, str(args.map))
        target_kind = "STANDALONE_CANONICAL_TASK_RECORD"
        target_path = shard_path

    raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.apply:
        target_path.write_text(raw, encoding="utf-8")
    elif args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")
    print(json.dumps({
        "schema": "stegverse.runtime-profile-resolution-persistence/v1",
        "task_id": task_id,
        "target_kind": target_kind,
        "target_ref": str(target_path),
        "projection_only": True,
        "selection_grants_authority": False,
        "coordination_state_changed": False,
        "claim_or_fence_minted": False,
        "execution_authority_granted": False,
        "authority_effect": "NONE_PROJECTION_PERSISTENCE_ONLY",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
