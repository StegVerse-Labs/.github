#!/usr/bin/env python3
"""Resolve canonical task runtime candidates against the canonical runtime-profile map.

This is a deterministic projection only. It never grants task admission, execution,
claim/fence, credential, deployment, transition, or consequence authority.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from match_runtime_profile import evaluate

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data/canonical-task-registry.json"
DEFAULT_MAP = ROOT / "control/runtime-profile-map.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object required:{path}")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError("FAIL_CLOSED: " + reason)


def find_task(registry: dict[str, Any], task_id: str) -> dict[str, Any]:
    rows = [row for row in registry.get("tasks", []) if row.get("task_id") == task_id]
    require(len(rows) == 1, "task identity must resolve exactly once")
    return rows[0]


def resolve(task: dict[str, Any], runtime_map: dict[str, Any], map_ref: str) -> dict[str, Any]:
    requirements = task.get("runtime_requirements")
    require(isinstance(requirements, dict), "task runtime_requirements missing")
    required = set(requirements.get("capabilities", []))
    evaluated = [
        evaluate(
            profile,
            required,
            requirements.get("environment"),
            requirements.get("direction"),
            bool(requirements.get("mutation_required", False)),
            bool(requirements.get("deployment_required", False)),
            bool(requirements.get("current_observation_required", False)),
        )
        for profile in runtime_map.get("profiles", [])
    ]
    compatible = sorted(
        [row for row in evaluated if row.get("compatible")],
        key=lambda row: str(row.get("profile_id")),
    )
    return {
        "schema": "stegverse.canonical-task-runtime-resolution/v1",
        "task_id": task.get("task_id"),
        "correlation_id": task.get("correlation_id"),
        "map_ref": map_ref,
        "map_generation": runtime_map.get("generation"),
        "requirements": requirements,
        "candidate_profile_ids": [row.get("profile_id") for row in compatible],
        "candidate_count": len(compatible),
        "evaluated": evaluated,
        "resolved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "projection_only": True,
        "selection_grants_authority": False,
        "workercoordinator_admission_still_required": True,
        "interlock_intr_transition_admission_still_required": True,
        "master_records_reconciliation_still_required": True,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_RUNTIME_CANDIDATE_PROJECTION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    registry = load(args.registry)
    runtime_map = load(args.map)
    task = find_task(registry, args.task_id)
    result = resolve(task, runtime_map, str(args.map))
    raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
