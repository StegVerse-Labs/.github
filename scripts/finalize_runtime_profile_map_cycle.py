#!/usr/bin/env python3
"""Finalize one resident runtime-profile-map cycle after map/resolution generation.

Applies all runtime-resolution projections atomically, validates the canonical work
coordination projection contract, emits non-authorizing routing-readiness receipts,
builds one exact-hash custody input package, and when an already-local Master Records
root is available invokes only its bounded custody consumer. No authority is created.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False, timeout=1200)


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def maybe_custody(root: Path, custody_package: Path) -> dict[str, Any]:
    mr_root_value = os.environ.get("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT")
    if not mr_root_value:
        return {
            "state": "MASTER_RECORDS_LOCAL_ROOT_NOT_DECLARED",
            "attempted": False,
            "custody_performed": False,
            "authority_effect": "NONE_OBSERVATION_ONLY",
        }
    mr_root = Path(mr_root_value).expanduser().resolve()
    consumer = mr_root / "scripts/ingest_runtime_profile_map_custody.py"
    if not consumer.is_file():
        return {
            "state": "MASTER_RECORDS_CUSTODY_CONSUMER_NOT_MATERIALIZED",
            "attempted": False,
            "custody_performed": False,
            "master_records_root": str(mr_root),
            "authority_effect": "NONE_OBSERVATION_ONLY",
        }
    completed = run([
        sys.executable, str(consumer),
        "--package", str(custody_package),
        "--artifact-root", str(root),
        "--custody-root", str(mr_root / "custody/runtime-profile-map"),
    ], mr_root)
    parsed = parse_last_json(completed.stdout)
    accepted = completed.returncode == 0 and isinstance(parsed, dict) and parsed.get("state") == "CUSTODY_ACCEPTED"
    return {
        "state": "CUSTODY_ACCEPTED" if accepted else "CUSTODY_ATTEMPT_RECORDED",
        "attempted": True,
        "custody_performed": accepted,
        "returncode": completed.returncode,
        "result": parsed,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "authority_effect": "NONE_MASTER_RECORDS_CUSTODY_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    registry = root / "data/canonical-task-registry.json"
    runtime_map = root / "control/runtime-profile-map.json"
    resolution_dir = root / "receipts/runtime-profile-map/task-resolutions"
    readiness_dir = root / "receipts/runtime-profile-map/routing-readiness"
    custody_package = root / "receipts/runtime-profile-map/custody/runtime-profile-map-custody-package.latest.json"

    applied = run([
        sys.executable, str(root / "scripts/apply_all_task_runtime_resolutions.py"),
        "--registry", str(registry), "--map", str(runtime_map),
        "--resolution-dir", str(resolution_dir), "--apply",
    ], root)
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
            "receipt_sha256": sha256(out),
            "disposition": value.get("disposition"),
            "routing_ready_for_workercoordinator_review": value.get("routing_ready_for_workercoordinator_review"),
            "execution_authority_granted": False,
        })

    custody = run([
        sys.executable, str(root / "scripts/build_runtime_profile_map_custody_package.py"),
        "--root", str(root), "--output", str(custody_package),
    ], root)
    if custody.returncode != 0 or not custody_package.is_file():
        raise SystemExit("FAIL_CLOSED: runtime-profile-map custody package generation failed\n" + custody.stderr[-4000:] + custody.stdout[-4000:])

    custody_result = maybe_custody(root, custody_package)

    result = {
        "schema": "stegverse.runtime-profile-map-cycle-finalization/v1",
        "state": "FINALIZED_NON_AUTHORIZING",
        "map_generation": load(runtime_map).get("generation"),
        "registry_generation": current.get("generation"),
        "routing_readiness": readiness_rows,
        "routing_readiness_count": len(readiness_rows),
        "canonical_coordination_validation_passed": True,
        "custody_package_ref": str(custody_package),
        "custody_package_sha256": sha256(custody_package),
        "master_records_custody": custody_result,
        "coordination_state_changed": False,
        "claim_or_fence_minted": False,
        "execution_authority_granted": False,
        "workercoordinator_admission_still_required": True,
        "interlock_intr_transition_admission_still_required": True,
        "master_records_custody_still_required": not bool(custody_result.get("custody_performed")),
        "authority_effect": "NONE_COORDINATION_PROJECTION_FINALIZATION_ONLY",
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
