#!/usr/bin/env python3
"""Neutral one-shot scheduler for registered reusable tasks.

This runner is scheduling/orchestration only. It invokes the existing reusable-task
trigger for due child identities and preserves their exact completion/boundary state.
It mints no WorkerCoordinator claim/fence, InTr admission, credential, provider,
publication, user-verification, or runtime authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SELF_ID = "RT-REUSABLE-TASK-SCHEDULER-001"
SCHEDULE_SCHEMA = "stegverse.reusable-task-schedule/v1"
RESULT_SCHEMA = "stegverse.reusable-task-runner-result/v1"
SUCCESS_STATES = {"AUTOMATABLE_STEPS_EXHAUSTED", "ENTROPY_RECOVERY_RECORDED"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def parse_now(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)


def due(row: dict[str, Any], now: datetime) -> bool:
    if row.get("enabled", True) is not True:
        return False
    hours = row.get("run_hours_utc")
    return True if hours is None else now.hour in hours


def selected(row: dict[str, Any], scope: str) -> bool:
    if scope == "all":
        return True
    identity = str(row.get("reusable_task_id") or "").lower()
    aliases = {str(x).lower() for x in row.get("aliases", [])}
    return scope == identity or scope in aliases


def main() -> int:
    manifest_path = Path(os.environ["STEGVERSE_REUSABLE_TASK_MANIFEST"])
    manifest = load_json(manifest_path)
    if manifest.get("reusable_task_id") != SELF_ID:
        raise RuntimeError("scheduler manifest reusable task mismatch")
    parameters = manifest.get("parameters")
    if not isinstance(parameters, dict):
        raise RuntimeError("scheduler parameters missing")

    schedule_path = Path(str(parameters.get("schedule_path") or "")).expanduser().resolve()
    runtime_root = Path(str(parameters.get("runtime_root") or "")).expanduser().resolve()
    roots_raw = parameters.get("repo_roots_json") or os.getenv("STEGVERSE_REPO_ROOTS_JSON") or "{}"
    roots_doc = json.loads(roots_raw) if isinstance(roots_raw, str) else roots_raw
    if not isinstance(roots_doc, dict):
        raise RuntimeError("repo_roots_json must be an object")
    roots = {str(k): Path(str(v)).expanduser().resolve() for k, v in roots_doc.items()}
    scope = str(parameters.get("scope") or "all").lower()
    now = parse_now(str(parameters.get("now_utc") or "") or None)

    schedule = load_json(schedule_path)
    if schedule.get("schema") != SCHEDULE_SCHEMA or not isinstance(schedule.get("tasks"), list):
        raise RuntimeError("neutral reusable-task schedule schema mismatch")

    outcomes: list[dict[str, Any]] = []
    for row in schedule["tasks"]:
        if not isinstance(row, dict) or not due(row, now) or not selected(row, scope):
            continue
        child_id = str(row.get("reusable_task_id") or "")
        if not child_id or child_id == SELF_ID:
            raise RuntimeError("scheduler may not schedule itself or an empty identity")
        repository = str(row.get("repository") or "")
        root = roots.get(repository)
        if root is None:
            outcomes.append({"reusable_task_id": child_id, "state": "BOUNDARY_RECORDED", "boundary": "LOCAL_REPOSITORY_NOT_MATERIALIZED"})
            continue
        trigger = root / "scripts" / "trigger_reusable_task.py"
        if not trigger.is_file():
            outcomes.append({"reusable_task_id": child_id, "state": "BOUNDARY_RECORDED", "boundary": "REUSABLE_TASK_TRIGGER_NOT_MATERIALIZED"})
            continue
        invocation_id = f"{child_id.lower()}-{now.strftime('%Y%m%dT%H%M%SZ')}"
        receipt = runtime_root / "receipts" / "reusable-task" / f"{invocation_id}.latest.json"
        child_params = dict(row.get("parameters") or {})
        child_params.setdefault("source_root", str(root))
        child_params.setdefault("runtime_root", str(runtime_root))
        command = [sys.executable, str(trigger), "--reusable-task-id", child_id, "--invocation-id", invocation_id, "--parameters-json", json.dumps(child_params, sort_keys=True, separators=(",", ":")), "--receipt", str(receipt)]
        tracking = row.get("tracking_task_id")
        cosv = row.get("cosv_task_vector")
        if tracking or cosv:
            if not tracking or not cosv:
                raise RuntimeError("tracking_task_id and cosv_task_vector must be paired")
            command.extend(["--task-id", str(tracking), "--cosv-task-vector", str(cosv)])
        env = {"PATH": os.getenv("PATH", ""), "HOME": os.getenv("HOME", ""), "STEGVERSE_REPO_ROOTS_JSON": json.dumps({k: str(v) for k, v in roots.items()}, sort_keys=True), "STEGVERSE_HEARTBEAT_ROOT": str(runtime_root), "STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY": "NONE", "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC"}
        completed = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, check=False)
        child_receipt = load_json(receipt) if receipt.is_file() else None
        state = child_receipt.get("state") if isinstance(child_receipt, dict) else "NO_RECEIPT"
        outcomes.append({"reusable_task_id": child_id, "invocation_id": invocation_id, "returncode": completed.returncode, "state": state, "receipt_ref": str(receipt), "slot_satisfied": state in SUCCESS_STATES})

    declared = json.loads(os.environ.get("STEGVERSE_REUSABLE_TASK_COMPLETION_PREDICATES_JSON", "[]"))
    result = {
        "schema": RESULT_SCHEMA,
        "invocation_id": manifest["invocation_id"],
        "reusable_task_id": SELF_ID,
        "manifest_hash": manifest["manifest_hash"],
        "runtime_observed": True,
        "completion_evidence_observed": True,
        "completion_predicates_satisfied": declared,
        "schedule_path": str(schedule_path),
        "runtime_root": str(runtime_root),
        "due_task_count": len(outcomes),
        "outcomes": outcomes,
        "authority_effect": "NONE"
    }
    result_path = Path(os.environ["STEGVERSE_REUSABLE_TASK_RESULT_PATH"])
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
