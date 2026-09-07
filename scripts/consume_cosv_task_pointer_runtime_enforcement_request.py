#!/usr/bin/env python3
"""Consume the canonical COSV task-pointer runtime-enforcement request."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/cosv-task-pointer-runtime-enforcement-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/cosv-task-pointer-runtime-enforcement-request-consumption.latest.json")
TARGET_TASK = "COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001"
TARGET_VECTOR = "10100000100000"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
NONSECRET_ENV = {
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    "STEGVERSE_TVC_ROOT", "STEGVERSE_TV_ROOT", "STEGVERSE_REPO_ROOTS_JSON",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
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
        "cosv_profile": "task.v1",
        "cosv_task_vector": TARGET_VECTOR,
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, expected_value in expected.items():
        if request.get(key) != expected_value:
            raise RuntimeError(f"COSV task-pointer resident request {key} mismatch")
    argv = request.get("argv")
    if not isinstance(argv, list):
        raise RuntimeError("COSV task-pointer resident request argv missing")
    required_tail = ["--task-id", TARGET_TASK, "--cosv-task-vector", TARGET_VECTOR]
    if argv[-4:] != required_tail:
        raise RuntimeError("COSV task-pointer resident request argv pointer binding mismatch")


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def consume(
    source_root: Path,
    runtime_root: Path,
    *,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {
            "schema": "stegverse.cosv-task-pointer-runtime-enforcement-consumption/v1",
            "state": "NO_REQUEST",
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }

    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    request_id = str(request.get("request_id") or "")
    if not request_id:
        raise RuntimeError("COSV task-pointer resident request request_id missing")

    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"COSV task-pointer execution entrypoint missing: {entrypoint}")

    command = [
        sys.executable, str(entrypoint),
        "--source-root", str(source),
        "--runtime-root", str(runtime),
        "--task-id", TARGET_TASK,
        "--cosv-task-vector", TARGET_VECTOR,
    ]
    completed = runner(
        command,
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        env=clean_env(env),
        timeout=1200,
    )
    result = parse_last_json(completed.stdout)
    pointer = result.get("cosv_task_pointer") if isinstance(result, dict) else None
    pointer_verified = bool(
        isinstance(pointer, dict)
        and pointer.get("task_id") == TARGET_TASK
        and pointer.get("vector") == TARGET_VECTOR
        and pointer.get("binding_verified") is True
        and pointer.get("authority_effect") == "NONE"
    )
    worker_result = result.get("execution_result") if isinstance(result, dict) else None
    worker_observed = isinstance(worker_result, dict)
    state = "ATTEMPT_RECORDED" if pointer_verified else "POINTER_ENFORCEMENT_NOT_OBSERVED"

    receipt = {
        "schema": "stegverse.cosv-task-pointer-runtime-enforcement-consumption/v1",
        "state": state,
        "request_id": request_id,
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "cosv_profile": "task.v1",
        "cosv_task_vector": TARGET_VECTOR,
        "mode": TARGET_MODE,
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "runtime_execution_attempted": True,
        "pointer_binding_verified_before_execution": pointer_verified,
        "worker_execution_result_observed": worker_observed,
        "broader_task_complete": False,
        "retry_allowed": True,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "second_machine_required": False,
        "network_source_fetch_performed": False,
        "authority_effect": "NONE_REQUEST_CONSUMPTION_ONLY",
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
    return 0 if receipt["state"] in {"NO_REQUEST", "ATTEMPT_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
