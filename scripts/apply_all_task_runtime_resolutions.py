#!/usr/bin/env python3
"""Apply a complete set of runtime-profile resolution receipts to the canonical task registry.

This is projection persistence only. It preserves task coordination state and never
mints WorkerCoordinator claim/fence, Interlock/InTr admission, credentials, deployment,
or execution authority. The operation is fail-closed and atomic: all supplied task
resolutions must validate against the same runtime-profile map generation before the
registry is replaced.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from apply_task_runtime_resolution_projection import load, project


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError("FAIL_CLOSED: " + reason)


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("data/canonical-task-registry.json"))
    parser.add_argument("--map", type=Path, default=Path("control/runtime-profile-map.json"))
    parser.add_argument("--resolution-dir", type=Path, default=Path("receipts/runtime-profile-map/task-resolutions"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    registry = load(args.registry)
    runtime_map = load(args.map)
    require(args.resolution_dir.is_dir(), "runtime-resolution directory missing")

    expected = {
        str(task.get("task_id"))
        for task in registry.get("tasks", [])
        if isinstance(task.get("task_id"), str) and isinstance(task.get("runtime_requirements"), dict)
    }
    resolution_paths = sorted(args.resolution_dir.glob("*.json"))
    by_task: dict[str, Path] = {}
    for path in resolution_paths:
        value = load(path)
        task_id = value.get("task_id")
        require(isinstance(task_id, str) and task_id, f"resolution task identity missing:{path}")
        require(task_id not in by_task, f"duplicate runtime resolution:{task_id}")
        by_task[task_id] = path

    require(set(by_task) == expected, "runtime-resolution set does not exactly match tasks declaring runtime requirements")

    proposed = registry
    applied: list[dict[str, Any]] = []
    map_ref = str(args.map)
    for task_id in sorted(expected):
        resolution = load(by_task[task_id])
        before_generation = int(proposed.get("generation", 0))
        proposed = project(proposed, runtime_map, resolution, map_ref)
        applied.append({
            "task_id": task_id,
            "resolution_ref": str(by_task[task_id]),
            "candidate_profile_ids": resolution.get("candidate_profile_ids", []),
            "map_generation": runtime_map.get("generation"),
            "registry_generation_before": before_generation,
            "registry_generation_after": proposed.get("generation"),
            "projection_only": True,
            "selection_grants_authority": False,
        })

    proposed["status"] = "RUNTIME_PROFILE_CANDIDATES_PROJECTED_NO_AUTHORITY_GRANTED"
    proposed.setdefault("projection_receipts", {})["runtime_profile_resolution_batch"] = {
        "map_ref": map_ref,
        "map_generation": runtime_map.get("generation"),
        "task_count": len(applied),
        "tasks": [row["task_id"] for row in applied],
        "projection_only": True,
        "selection_grants_authority": False,
    }

    if args.apply:
        atomic_write(args.registry, proposed)
    elif args.output:
        atomic_write(args.output, proposed)
    else:
        print(json.dumps(proposed, indent=2, sort_keys=True))

    print(json.dumps({
        "schema": "stegverse.runtime-profile-resolution-batch-application/v1",
        "state": "APPLIED" if args.apply else "PROJECTED",
        "map_generation": runtime_map.get("generation"),
        "task_count": len(applied),
        "tasks": applied,
        "coordination_state_changed": False,
        "claim_or_fence_minted": False,
        "execution_authority_granted": False,
        "authority_effect": "NONE_PROJECTION_PERSISTENCE_ONLY"
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
