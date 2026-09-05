#!/usr/bin/env python3
"""Finalize one resident runtime-profile-map cycle after map/resolution generation.

Applies all runtime-resolution projections atomically, validates the canonical work
coordination source/runtime projection contract, then emits one non-authorizing
routing-readiness receipt per canonical task with runtime requirements.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"object required:{path}")
    return value


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False, timeout=1200)


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    registry = root / "data/canonical-task-registry.json"
    runtime_map = root / "control/runtime-profile-map.json"
    resolution_dir = root / "receipts/runtime-profile-map/task-resolutions"
    readiness_dir = root / "receipts/runtime-profile-map/routing-readiness"

    apply_cmd = [
        sys.executable, str(root / "scripts/apply_all_task_runtime_resolutions.py"),
        "--registry", str(registry), "--map", str(runtime_map),
        "--resolution-dir", str(resolution_dir), "--apply",
    ]
    applied = run(apply_cmd, root)
    if applied.returncode != 0:
        raise SystemExit("FAIL_CLOSED: runtime-resolution batch persistence failed\n" + applied.stderr[-4000:])

    validation = run([sys.executable, str(root / "scripts/validate_canonical_work_coordination.py")], root)
    if validation.returncode != 0:
        raise SystemExit("FAIL_CLOSED: canonical coordination validation failed\n" + validation.stderr[-4000:] + validation.stdout[-4000:])

    current = load(registry)
    readiness_rows: list[dict[str, Any]] = []
    for task in current.get("tasks", []):
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not isinstance(task.get("runtime_requirements"), dict):
            continue
        completed = run([
            sys.executable, str(root / "scripts/evaluate_task_runtime_routing_readiness.py"),
            task_id, "--registry", str(registry), "--map", str(runtime_map),
        ], root)
        if completed.returncode != 0:
            raise SystemExit(f"FAIL_CLOSED: routing readiness failed:{task_id}\n" + completed.stderr[-4000:])
        value = json.loads(completed.stdout)
        out = readiness_dir / f"{task_id}.json"
        atomic_text(out, json.dumps(value, indent=2, sort_keys=True) + "\n")
        readiness_rows.append({
            "task_id": task_id,
            "receipt_ref": str(out),
            "disposition": value.get("disposition"),
            "routing_ready_for_workercoordinator_review": value.get("routing_ready_for_workercoordinator_review"),
            "execution_authority_granted": False,
        })

    result = {
        "schema": "stegverse.runtime-profile-map-cycle-finalization/v1",
        "state": "FINALIZED_NON_AUTHORIZING",
        "map_generation": load(runtime_map).get("generation"),
        "registry_generation": current.get("generation"),
        "routing_readiness": readiness_rows,
        "routing_readiness_count": len(readiness_rows),
        "canonical_coordination_validation_passed": True,
        "coordination_state_changed": False,
        "claim_or_fence_minted": False,
        "execution_authority_granted": False,
        "workercoordinator_admission_still_required": True,
        "interlock_intr_transition_admission_still_required": True,
        "authority_effect": "NONE_COORDINATION_PROJECTION_FINALIZATION_ONLY",
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
