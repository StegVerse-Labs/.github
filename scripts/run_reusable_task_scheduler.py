#!/usr/bin/env python3
"""Neutral one-shot scheduler for registered reusable tasks.

The scheduler owns only reusable-task scheduling semantics: due selection, slot
idempotency, bounded retry/backoff, and child invocation through the canonical
reusable-task trigger. Child completion/boundary evidence is preserved exactly.
It mints no WorkerCoordinator claim/fence, InTr admission, credential, provider,
publication, user-verification, HeartBeat, Master Records, or runtime authority.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
RETRY_STATE_SCHEMA = "stegverse.reusable-task-scheduler-slot-attempt-state/v1"
SUCCESS_STATES = {"AUTOMATABLE_STEPS_EXHAUSTED", "ENTROPY_RECOVERY_RECORDED"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name("." + path.name + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


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
    repository = str(row.get("repository") or "").split("/")[-1].lower()
    aliases = {str(x).lower() for x in row.get("aliases", [])}
    return scope in {identity, repository} or scope in aliases


def slot_id(task_id: str, now: datetime, invocation_key: str | None = None) -> str:
    identity = str(invocation_key or task_id).strip()
    if not identity:
        raise RuntimeError("reusable scheduler invocation identity must be non-empty")
    compact = identity.replace("RT-", "rt-").lower().replace("_", "-")
    return f"{compact}-{now.strftime('%Y%m%dT%H')}Z"


def retry_policy(row: dict[str, Any]) -> tuple[int, int]:
    interval = row.get("retry_interval_minutes", 15)
    maximum = row.get("max_attempts_per_slot", 4)
    if not isinstance(interval, int) or interval < 1 or interval > 60:
        raise RuntimeError("retry_interval_minutes must be integer 1..60")
    if not isinstance(maximum, int) or maximum < 1 or maximum > 12:
        raise RuntimeError("max_attempts_per_slot must be integer 1..12")
    return interval, maximum


def retry_state_path(runtime_root: Path, invocation_id: str) -> Path:
    return runtime_root / "receipts" / "reusable-task" / f"{invocation_id}.attempt-state.json"


def load_retry_state(path: Path, invocation_id: str) -> dict[str, Any]:
    if not path.is_file():
        return {"schema": RETRY_STATE_SCHEMA, "invocation_id": invocation_id, "attempt_count": 0, "last_attempt_at": None}
    value = load_json(path)
    if value.get("schema") != RETRY_STATE_SCHEMA or value.get("invocation_id") != invocation_id:
        raise RuntimeError("reusable scheduler retry state identity mismatch")
    count = value.get("attempt_count")
    if not isinstance(count, int) or count < 0:
        raise RuntimeError("reusable scheduler attempt_count invalid")
    return value


def retry_gate(row: dict[str, Any], state: dict[str, Any], now: datetime) -> tuple[bool, str | None, str | None]:
    interval, maximum = retry_policy(row)
    count = int(state.get("attempt_count") or 0)
    if count >= maximum:
        return False, "MAX_ATTEMPTS_REACHED_FOR_SLOT", None
    last = state.get("last_attempt_at")
    if not last:
        return True, None, None
    parsed = datetime.fromisoformat(str(last).replace("Z", "+00:00")).astimezone(timezone.utc)
    retry_at = parsed + timedelta(minutes=interval)
    if now < retry_at:
        return False, "RETRY_BACKOFF_ACTIVE", retry_at.isoformat().replace("+00:00", "Z")
    return True, None, retry_at.isoformat().replace("+00:00", "Z")


def _child_boundary(receipt: dict[str, Any] | None) -> Any:
    if not isinstance(receipt, dict):
        return None
    return receipt.get("boundary")


def execute_child(row: dict[str, Any], roots: dict[str, Path], runtime_root: Path, now: datetime) -> dict[str, Any]:
    child_id = str(row.get("reusable_task_id") or "")
    if not child_id or child_id == SELF_ID:
        raise RuntimeError("scheduler may not schedule itself or an empty identity")
    repository = str(row.get("repository") or "")
    interval, maximum = retry_policy(row)
    base = {
        "reusable_task_id": child_id,
        "tracking_task_id": row.get("tracking_task_id"),
        "cosv_task_vector": row.get("cosv_task_vector"),
        "repository": repository,
        "invocation_key": str(row.get("invocation_key") or "").strip() or None,
        "retry_interval_minutes": interval,
        "max_attempts_per_slot": maximum,
    }
    if not runtime_root.is_dir():
        return {**base, "state": "BOUNDARY_RECORDED", "boundary": "RESIDENT_RUNTIME_ROOT_NOT_MATERIALIZED", "slot_satisfied": False}
    root = roots.get(repository)
    if root is None:
        return {**base, "state": "BOUNDARY_RECORDED", "boundary": "LOCAL_REPOSITORY_NOT_MATERIALIZED", "slot_satisfied": False}
    trigger = root / "scripts" / "trigger_reusable_task.py"
    if not trigger.is_file():
        return {**base, "state": "BOUNDARY_RECORDED", "boundary": "REUSABLE_TASK_TRIGGER_NOT_MATERIALIZED", "slot_satisfied": False}

    invocation_key = str(row.get("invocation_key") or "").strip() or None
    invocation_id = slot_id(child_id, now, invocation_key)
    receipt_path = runtime_root / "receipts" / "reusable-task" / f"{invocation_id}.latest.json"
    retry_path = retry_state_path(runtime_root, invocation_id)
    prior = load_json(receipt_path) if receipt_path.is_file() else None
    prior_state = prior.get("state") if isinstance(prior, dict) else None
    if prior_state in SUCCESS_STATES:
        return {
            **base,
            "state": "COMPLETE",
            "outcome": "ALREADY_RAN_THIS_SCHEDULE_SLOT",
            "invocation_id": invocation_id,
            "receipt_ref": str(receipt_path),
            "child_receipt_state": prior_state,
            "child_boundary": _child_boundary(prior),
            "slot_satisfied": True,
            "source_root": str(root),
            "runtime_root": str(runtime_root),
        }

    retry_state = load_retry_state(retry_path, invocation_id)
    may_attempt, deferred_reason, retry_at = retry_gate(row, retry_state, now)
    if not may_attempt:
        return {
            **base,
            "state": "DEFERRED",
            "outcome": deferred_reason,
            "invocation_id": invocation_id,
            "receipt_ref": str(receipt_path),
            "child_receipt_state": prior_state,
            "child_boundary": _child_boundary(prior),
            "retry_state_ref": str(retry_path),
            "attempt_count": retry_state["attempt_count"],
            "next_retry_at": retry_at,
            "slot_satisfied": False,
            "source_root": str(root),
            "runtime_root": str(runtime_root),
        }

    params = dict(row.get("parameters") or {})
    params.setdefault("source_root", str(root))
    params.setdefault("runtime_root", str(runtime_root))
    command = [
        sys.executable, str(trigger),
        "--reusable-task-id", child_id,
        "--invocation-id", invocation_id,
        "--parameters-json", json.dumps(params, sort_keys=True, separators=(",", ":")),
        "--receipt", str(receipt_path),
    ]
    tracking, cosv = row.get("tracking_task_id"), row.get("cosv_task_vector")
    if row.get("cosv_binding_policy") == "CANONICAL_INDEX_EXACT_EMITTED_ONLY":
        # The neutral scheduler only observes an already-governed COSV issuance.
        # It does not calculate a task vector, authorize the task, or fall back to
        # another task's vector when its exact canonical row is absent.
        if not tracking or cosv is not None:
            raise RuntimeError("canonical COSV lookup requires task identity and no provisional vector")
        canonical = roots.get("StegVerse-Labs/.github")
        if canonical is None:
            return {**base, "state":"BOUNDARY_RECORDED", "boundary":"CANONICAL_COSV_SOURCE_NOT_MATERIALIZED", "slot_satisfied":False}
        index_path = canonical / "control/task-vector-index.json"
        record_path = canonical / "data/canonical-task-records" / (str(tracking) + ".json")
        if not index_path.is_file() or not record_path.is_file():
            return {**base, "state":"BOUNDARY_RECORDED", "boundary":"CANONICAL_COSV_NOT_EMITTED", "slot_satisfied":False}
        index = load_json(index_path)
        record = load_json(record_path)
        matches = [x for x in index.get("tasks", []) if isinstance(x, dict) and x.get("task_id") == tracking]
        if len(matches) != 1 or record.get("task_id") != tracking:
            return {**base, "state":"BOUNDARY_RECORDED", "boundary":"CANONICAL_COSV_NOT_EMITTED", "slot_satisfied":False}
        issued = matches[0]
        cosv = issued.get("vector")
        ref = issued.get("source_state_vector_ref")
        if (issued.get("vector_state") != "EMITTED" or issued.get("authority_effect") != "NONE"
                or issued.get("repository") != "StegVerse-Labs/.github"
                or not isinstance(cosv, str) or len(cosv) != 14 or not cosv.isdigit()
                or record.get("cosv_task_vector") != cosv
                or record.get("source_state_vector_ref") != ref
                or not isinstance(ref, str) or ref != f"control/task-vectors/{tracking}.json"):
            return {**base, "state":"BOUNDARY_RECORDED", "boundary":"CANONICAL_COSV_IDENTITY_MISMATCH", "slot_satisfied":False}
        source_record = load_json(canonical / ref) if (canonical / ref).is_file() else None
        if not isinstance(source_record, dict) or source_record.get("vector_state") != "EMITTED" or source_record.get("vector") != cosv or source_record.get("identity") != f"StegVerse-Labs/.github:task:{tracking}" or source_record.get("authority_effect") != "NONE":
            return {**base, "state":"BOUNDARY_RECORDED", "boundary":"CANONICAL_COSV_RECORD_MISMATCH", "slot_satisfied":False}
    if tracking or cosv:
        if not tracking or not cosv:
            raise RuntimeError("tracking_task_id and cosv_task_vector must be paired")
        command.extend(["--task-id", str(tracking), "--cosv-task-vector", str(cosv)])
    env = {
        "PATH": os.getenv("PATH", ""),
        "HOME": os.getenv("HOME", ""),
        "STEGVERSE_REPO_ROOTS_JSON": json.dumps({k: str(v) for k, v in roots.items()}, sort_keys=True),
        "STEGVERSE_HEARTBEAT_ROOT": str(runtime_root),
        "STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY": "NONE",
        "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC",
    }
    # Existing local source locator only; this is not a provider credential or
    # permission to fetch source. The trusted SES wrapper sees it, never candidate code.
    tvc_root = roots.get("StegVerse-Labs/TVC")
    if tvc_root is not None and tvc_root.is_dir():
        env["STEGVERSE_TVC_ROOT"] = str(tvc_root)
    for name in ("STEGVERSE_KV_ROOT", "STEGVERSE_KV_PROVIDER_MATERIALIZED_ROOT"):
        if os.getenv(name):
            env[name] = os.environ[name]
    completed = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, check=False)
    child_receipt = load_json(receipt_path) if receipt_path.is_file() else None
    child_state = child_receipt.get("state") if isinstance(child_receipt, dict) else "NO_RECEIPT"
    ok = completed.returncode == 0 and child_state in SUCCESS_STATES
    attempt_count = int(retry_state.get("attempt_count") or 0) + 1
    attempt_state = {
        "schema": RETRY_STATE_SCHEMA,
        "invocation_id": invocation_id,
        "attempt_count": attempt_count,
        "last_attempt_at": now.isoformat().replace("+00:00", "Z"),
        "last_receipt_state": child_state,
        "last_returncode": completed.returncode,
        "slot_satisfied": ok,
    }
    write_json(retry_path, attempt_state)
    next_retry = None if ok or attempt_count >= maximum else (now + timedelta(minutes=interval)).isoformat().replace("+00:00", "Z")
    return {
        **base,
        "state": "COMPLETE" if ok else "BOUNDARY_RECORDED",
        "outcome": "REUSABLE_TASK_SCHEDULE_SLOT_EXECUTED" if ok else "REUSABLE_TASK_SCHEDULE_SLOT_RETRYABLE",
        "invocation_id": invocation_id,
        "returncode": completed.returncode,
        "receipt_ref": str(receipt_path),
        "child_receipt_state": child_state,
        "child_boundary": _child_boundary(child_receipt),
        "retry_state_ref": str(retry_path),
        "attempt_count": attempt_count,
        "slot_satisfied": ok,
        "same_slot_retry_permitted": not ok and attempt_count < maximum,
        "next_retry_at": next_retry,
        "source_root": str(root),
        "runtime_root": str(runtime_root),
    }


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
        outcomes.append(execute_child(row, roots, runtime_root, now))

    declared = json.loads(os.environ.get("STEGVERSE_REUSABLE_TASK_COMPLETION_PREDICATES_JSON", "[]"))
    advanced_states = {"COMPLETE", "BOUNDARY_RECORDED"}
    all_advanced = all(
        isinstance(outcome, dict) and outcome.get("state") in advanced_states
        for outcome in outcomes
    )
    blocking_outcomes = [
        {
            "reusable_task_id": outcome.get("reusable_task_id"),
            "state": outcome.get("state"),
            "outcome": outcome.get("outcome"),
            "child_receipt_state": outcome.get("child_receipt_state"),
            "child_boundary": outcome.get("child_boundary"),
            "attempt_count": outcome.get("attempt_count"),
            "next_retry_at": outcome.get("next_retry_at"),
        }
        for outcome in outcomes
        if not isinstance(outcome, dict) or outcome.get("state") not in advanced_states
    ]
    result = {
        "schema": RESULT_SCHEMA,
        "invocation_id": manifest["invocation_id"],
        "reusable_task_id": SELF_ID,
        "manifest_hash": manifest["manifest_hash"],
        "runtime_observed": True,
        "completion_evidence_observed": all_advanced,
        "completion_predicates_satisfied": declared if all_advanced else [],
        "schedule_path": str(schedule_path),
        "runtime_root": str(runtime_root),
        "due_task_count": len(outcomes),
        "outcomes": outcomes,
        "all_due_tasks_advanced_to_completion_or_authentic_boundary": all_advanced,
        "blocking_outcomes": blocking_outcomes,
        "state_transition_dependency": {
            "predecessor": "DUE_CHILD_STATE_EVALUATED",
            "successor": "ALL_DUE_REUSABLE_TASKS_ADVANCED_TO_COMPLETION_OR_AUTHENTIC_BOUNDARY",
            "successor_admissible": all_advanced,
            "rule": "SUCCESSOR_REQUIRES_EVERY_DUE_CHILD_TO_REACH_COMPLETE_OR_BOUNDARY_RECORDED;_DEFERRED_OR_UNOBSERVED_CHILD_STATE_BLOCKS_SUCCESSOR",
        },
        "authority_effect": "NONE",
    }
    result_path = Path(os.environ["STEGVERSE_REUSABLE_TASK_RESULT_PATH"])
    write_json(result_path, result)
    print(json.dumps(result, sort_keys=True))
    return 0 if all_advanced else 3


if __name__ == "__main__":
    raise SystemExit(main())
