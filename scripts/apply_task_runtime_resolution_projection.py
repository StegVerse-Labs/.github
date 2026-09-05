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


def project(registry: dict[str, Any], runtime_map: dict[str, Any], resolution: dict[str, Any], map_ref: str) -> dict[str, Any]:
    require(resolution.get("schema") == "stegverse.canonical-task-runtime-resolution/v1", "resolution schema mismatch")
    require(resolution.get("projection_only") is True, "runtime resolution must be projection-only")
    require(resolution.get("selection_grants_authority") is False, "runtime resolution cannot grant authority")
    require(resolution.get("map_generation") == runtime_map.get("generation"), "runtime map generation drift")
    require(resolution.get("map_ref") == map_ref, "runtime map reference drift")

    task_id = resolution.get("task_id")
    correlation_id = resolution.get("correlation_id")
    proposed = copy.deepcopy(registry)
    matches = [t for t in proposed.get("tasks", []) if t.get("task_id") == task_id]
    require(len(matches) == 1, "task identity must resolve exactly once")
    task = matches[0]
    require(task.get("correlation_id") == correlation_id, "correlation identity drift")
    require(task.get("runtime_requirements") == resolution.get("requirements"), "runtime requirements drift")

    candidates = resolution.get("candidate_profile_ids")
    require(isinstance(candidates, list), "candidate profile list required")
    known = {p.get("profile_id") for p in runtime_map.get("profiles", [])}
    require(all(c in known for c in candidates), "resolution references unknown runtime profile")

    task["runtime_resolution"] = {
        "map_ref": map_ref,
        "map_generation": runtime_map.get("generation"),
        "candidate_profile_ids": candidates,
        "resolved_at": resolution.get("resolved_at"),
        "projection_only": True,
        "selection_grants_authority": False,
    }
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
    parser.add_argument("--resolution", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    registry = load(args.registry)
    runtime_map = load(args.map)
    resolution = load(args.resolution)
    result = project(registry, runtime_map, resolution, str(args.map))
    raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.apply:
        args.registry.write_text(raw, encoding="utf-8")
    elif args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
