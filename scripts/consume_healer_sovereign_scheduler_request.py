#!/usr/bin/env python3
"""Consume the standing Healer sovereign scheduler resident request."""
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
REQUEST_REL = Path("control/resident-execution-request.d/healer-sovereign-scheduler-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/healer-sovereign-scheduler-request-consumption.latest.json")
TARGET_TASK = "SHWP-HEALER-SOVEREIGN-SCHEDULER-001"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
NONSECRET_ENV = {
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_HEALER_ROOT", "STEGVERSE_REPO_ROOTS_JSON", "STEGVERSE_TVC_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT", "STEGVERSE_HIL_INTR_ROUTE_CONFIG",
    "STEGVERSE_EVALUATOR_INTR_ROUTE_CONFIG", "STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def clean_env(source: dict[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    env = {key: values[key] for key in NONSECRET_ENV if values.get(key)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def validate_request(request: dict[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
        "standing_request": True,
        "recurrence": "EACH_ELIGIBLE_RESIDENT_SCHEDULER_CYCLE",
    }
    for key, value in expected.items():
        if request.get(key) != value:
            raise RuntimeError(f"Healer resident request {key} mismatch")
    if not isinstance(request.get("request_id"), str) or not request["request_id"].strip():
        raise RuntimeError("request_id missing")


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([x.strip() for x in stdout.splitlines() if x.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def resolve_source_root(source_root: Path, runtime_root: Path, values: dict[str, str]) -> tuple[Path | None, str]:
    """Keep canonical source distinct from mutable resident runtime.

    The continuous WorkerCoordinator dispatcher historically supplies its own
    resident root for both dispatcher arguments. The sovereign service already
    carries STEGVERSE_HEARTBEAT_SOURCE_ROOT, so the Healer refresh bridge consumes
    that non-secret local source locator when source/runtime would otherwise
    collapse. No network checkout is attempted here.
    """
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    if source != runtime:
        return (source, "DISPATCHER_DISTINCT_SOURCE") if source.is_dir() else (None, "DISPATCHER_SOURCE_MISSING")

    raw = str(values.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT") or "").strip()
    if not raw:
        return None, "DISTINCT_SOURCE_ROOT_NOT_PROVIDED"
    candidate = Path(raw).expanduser().resolve()
    if candidate == runtime:
        return None, "SOURCE_ROOT_EQUALS_RUNTIME"
    if not candidate.is_dir():
        return None, "SOURCE_ROOT_NOT_MATERIALIZED"
    required = candidate / TARGET_ENTRYPOINT
    if not required.is_file():
        return None, "SOURCE_ROOT_INCOMPLETE"
    return candidate, "STEGVERSE_HEARTBEAT_SOURCE_ROOT"


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: dict[str, str] | None = None) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    runtime = runtime_root.expanduser().resolve()
    source, source_resolution = resolve_source_root(source_root, runtime_root, values)
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema": "stegverse.healer-resident-request-consumption/v1", "state": "NO_REQUEST", "runtime_execution_attempted": False, "standing_request": True, "authority_effect": "NONE"}

    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    if source is None:
        receipt = {
            "schema": "stegverse.healer-resident-request-consumption/v1",
            "state": "ATTEMPT_RECORDED",
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "task_id": TARGET_TASK,
            "mode": TARGET_MODE,
            "standing_request": True,
            "recurrence": request["recurrence"],
            "source_resolution": source_resolution,
            "runtime_execution_attempted": False,
            "scheduler_cycle_completion_observed": False,
            "terminal_scheduler_completion_observed": False,
            "retry_allowed": True,
            "request_consumed": False,
            "request_granted_authority": False,
            "heartbeat_grants_execution_authority": False,
            "github_token_required": False,
            "github_token_runtime_authority": "NONE",
            "credential_authority": "TV/TVC",
            "credential_requirement": "NONE",
            "second_machine_required": False,
            "network_source_fetch_performed": False,
            "blocker": "DISTINCT_LOCAL_CANONICAL_SOURCE_REQUIRED",
            "authority_effect": "NONE_REQUEST_ONLY",
        }
        path = runtime / CONSUMPTION_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt

    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"Healer resident execution entrypoint missing: {entrypoint}")

    command = [sys.executable, str(entrypoint), "--source-root", str(source), "--runtime-root", str(runtime), "--task-id", TARGET_TASK]
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=clean_env(values), timeout=1200)
    result = parse_last_json(completed.stdout)
    execution_result = result.get("execution_result") if isinstance(result, dict) else None
    transition = execution_result.get("transition_id") if isinstance(execution_result, dict) else None
    if transition is None and isinstance(result, dict):
        transition = result.get("transition_id")
    cycle_completed = transition == "HEALER_SOVEREIGN_SCHEDULER_COMPLETED"

    receipt = {
        "schema": "stegverse.healer-resident-request-consumption/v1",
        "state": "CYCLE_COMPLETED" if cycle_completed else "ATTEMPT_RECORDED",
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "standing_request": True,
        "recurrence": request["recurrence"],
        "source_root": str(source),
        "runtime_root": str(runtime),
        "source_resolution": source_resolution,
        "source_runtime_separated": source != runtime,
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "runtime_execution_attempted": True,
        "scheduler_cycle_completion_observed": cycle_completed,
        "terminal_scheduler_completion_observed": False,
        "retry_allowed": True,
        "request_consumed": False,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "second_machine_required": False,
        "network_source_fetch_performed": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    path = runtime / CONSUMPTION_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
