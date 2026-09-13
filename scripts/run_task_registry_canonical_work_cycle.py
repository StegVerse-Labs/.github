#!/usr/bin/env python3
"""Select and optionally advance one canonical machine-owned task from the Task Registry.

The Task Registry is the work-discovery starting point. This script does not create
new task identity, mint WorkerCoordinator claim/fence authority, grant credentials,
or authorize a transition. It filters existing canonical task records, runs the
existing Task Registry collision check-in, and only then delegates one selected
registered task to the existing Canonical Work / Interlock-InTr bootstrap.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data" / "canonical-task-records"
CHECKIN = ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py"
BOOTSTRAP = ROOT / "scripts" / "install_and_run_canonical_work_event_bootstrap.py"
CALLER_SURFACE = "INTERNAL_CANONICAL_WORK_BOOTSTRAP"
PROGRESSION_CONTROLLER_TASK_ID = "ENTITY-AUTONOMOUS-GOVERNED-PROGRESSION-RUNTIME-ADOPTION-001"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"canonical task record must be an object: {path}")
    return value


def machine_ingress_candidate(record: dict[str, Any], excluded_task_ids: set[str] | None = None) -> bool:
    task_id = str(record.get("task_id") or "")
    excluded = excluded_task_ids or set()
    if task_id == PROGRESSION_CONTROLLER_TASK_ID or task_id in excluded:
        return False
    if record.get("coordination_state") != "PROPOSED":
        return False
    if record.get("checkout_state") in {"SUPERSEDED", "COMPLETED", "RETIRED"}:
        return False
    if "INGRESS_ADMITTED" not in (record.get("allowed_next_transitions") or []):
        return False
    if record.get("human_action_ref") not in {None, ""}:
        return False
    if not isinstance(record.get("runtime_requirements"), dict):
        return False
    claim = record.get("worker_claim") or {}
    if claim.get("authority") != "WORKERCOORDINATOR" or claim.get("projection_only") is not True:
        return False
    if claim.get("claim_ref") is not None or claim.get("fence_ref") is not None:
        return False
    authority = record.get("authority_model") or {}
    if authority.get("task_registry_mints_execution_authority") is not False:
        return False
    if authority.get("interlock_intr_required_for_governed_ingress_egress") is not True:
        return False
    return True


def load_candidates(records_dir: Path = RECORDS, excluded_task_ids: set[str] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(records_dir.glob("*.json")):
        record = load(path)
        task_id = str(record.get("task_id") or "").strip()
        if not task_id:
            raise RuntimeError(f"canonical task record missing task_id: {path}")
        if task_id in seen:
            raise RuntimeError(f"duplicate canonical task record: {task_id}")
        seen.add(task_id)
        if machine_ingress_candidate(record, excluded_task_ids):
            rows.append(record)
    rows.sort(key=lambda row: (0 if row.get("checkout_state") == "CHECKED_OUT" else 1, str(row["task_id"])))
    return rows


def collision_check(task_id: str) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(CHECKIN)],
        cwd=str(ROOT),
        input=json.dumps({"task_id": task_id, "caller_surface": CALLER_SURFACE}),
        text=True,
        capture_output=True,
        check=True,
    )
    result = json.loads(proc.stdout)
    if result.get("schema") != "stegverse.task-registry-checkin-disposition/v1":
        raise RuntimeError("Task Registry check-in schema mismatch")
    if result.get("task_id") != task_id:
        raise RuntimeError("Task Registry check-in identity mismatch")
    if result.get("authority_effect") != "NONE":
        raise RuntimeError("Task Registry check-in attempted authority effect")
    return result


def select_task(records_dir: Path = RECORDS, excluded_task_ids: set[str] | None = None) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    considered: list[dict[str, Any]] = []
    for record in load_candidates(records_dir, excluded_task_ids):
        task_id = str(record["task_id"])
        checkin = collision_check(task_id)
        considered.append({
            "task_id": task_id,
            "checkout_state": record.get("checkout_state"),
            "disposition": checkin.get("disposition"),
            "collision_candidates": checkin.get("collision_candidates") or [],
        })
        if checkin.get("disposition") == "CONTINUE":
            return record, considered
    return None, considered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--select-only", action="store_true")
    parser.add_argument("--exclude-task-id", action="append", default=[])
    args = parser.parse_args()
    excluded_task_ids = {str(task_id).strip() for task_id in args.exclude_task_id if str(task_id).strip()}

    selected, considered = select_task(excluded_task_ids=excluded_task_ids)
    receipt: dict[str, Any] = {
        "schema": "stegverse.task-registry-canonical-work-cycle/v1",
        "start_point": "CANONICAL_TASK_REGISTRY",
        "progression_controller_excluded_from_work_selection": True,
        "explicit_request_task_ids_excluded": sorted(excluded_task_ids),
        "selected_task_id": selected.get("task_id") if selected else None,
        "candidate_count": len(load_candidates(excluded_task_ids=excluded_task_ids)),
        "considered": considered,
        "workercoordinator_claim_or_fence_minted": False,
        "interlock_intr_transition_authority_preserved": True,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "human_checkpoint_inserted": False,
        "authority_effect": "NONE_SELECTION_AND_DELEGATION_ONLY",
    }
    if selected is None:
        receipt["state"] = "NO_ADMISSIBLE_NONCOLLIDING_TASK"
        print(json.dumps(receipt, sort_keys=True))
        return 0

    if args.select_only:
        receipt["state"] = "TASK_SELECTED_FOR_EXISTING_CANONICAL_WORK_PATH"
        print(json.dumps(receipt, sort_keys=True))
        return 0

    if args.runtime_root is None:
        raise SystemExit("--runtime-root is required unless --select-only is used")

    command = [
        sys.executable,
        str(BOOTSTRAP),
        "--task-id",
        str(selected["task_id"]),
        "--runtime-root",
        str(args.runtime_root.expanduser().resolve()),
    ]
    completed = subprocess.run(command, cwd=str(ROOT), text=True, capture_output=True, check=False)
    receipt.update({
        "state": "DELEGATED_TO_EXISTING_CANONICAL_WORK_PATH" if completed.returncode == 0 else "CANONICAL_WORK_DELEGATION_RECORDED_FAILURE",
        "delegation_returncode": completed.returncode,
        "delegation_command": command,
        "delegation_stdout": completed.stdout,
        "delegation_stderr": completed.stderr,
        "task_registry_mints_execution_authority": False,
    })
    print(json.dumps(receipt, sort_keys=True))
    return 0 if completed.returncode == 0 else completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
