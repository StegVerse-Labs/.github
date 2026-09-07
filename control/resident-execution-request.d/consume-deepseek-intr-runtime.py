#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
REQUEST_REL = Path("control/resident-execution-request.d/deepseek-intr-runtime-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/deepseek-intr-runtime-request-consumption.latest.json")
TARGET_TASK = "SHWP-DEEPSEEK-INTR-RUNTIME-001"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
HOSTED = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
NONSECRET = (
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT", "STEGVERSE_TVC_ROOT", "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", "STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET",
)
FORBIDDEN = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "DEEPSEEK_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "STEGVERSE_PROVIDER_TOKEN",
    "STEGVERSE_MASTER_RECORDS_TOKEN",
)


def truthy(value: Any) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("expected object")
    return value


def stable(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def validate_request(request: Mapping[str, Any]) -> None:
    required = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "runtime_profile_id": "stegverse:runtime-profile:llm-adapter-deepseek:v1",
        "base_runtime_profile_id": "stegverse:runtime-profile:hb-intr-resident:v1",
        "protocol": "stegverse.intr.deepseek.transport.v1",
        "provider": "deepseek",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "provider_credential_material_allowed": False,
        "hosted_runtime_allowed": False,
        "master_records_custody_required_for_egress": True,
        "same_execution_required": True,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in required.items():
        if request.get(key) != wanted:
            raise RuntimeError(f"DeepSeek resident request {key} mismatch")


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [key for key in HOSTED if truthy(values.get(key))]
    if hosted:
        raise RuntimeError("hosted environment may not consume DeepSeek resident request: " + ",".join(sorted(hosted)))
    env = {key: values[key] for key in NONSECRET if values.get(key)}
    for key in FORBIDDEN:
        env.pop(key, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def previously_consumed(runtime: Path, request: Mapping[str, Any], request_hash: str) -> bool:
    path = runtime / CONSUMPTION_REL
    if not path.is_file():
        return False
    try:
        value = load(path)
    except Exception:
        return False
    return value.get("request_id") == request.get("request_id") and value.get("request_sha256") == request_hash and value.get("runtime_execution_attempted") is True and value.get("terminal") is True


def last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {"schema": "stegverse.deepseek-intr-resident-request-consumption/v1", "state": "NO_REQUEST", "runtime_execution_attempted": False, "authority_effect": "NONE"}
    request = load(request_path)
    validate_request(request)
    request_hash = stable(request)
    if previously_consumed(runtime, request, request_hash):
        return {"schema": "stegverse.deepseek-intr-resident-request-consumption/v1", "state": "ALREADY_TERMINAL", "request_id": request["request_id"], "request_sha256": request_hash, "runtime_execution_attempted": False, "authority_effect": "NONE"}
    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError("DeepSeek resident entrypoint missing")
    command = [sys.executable, str(entrypoint), "--source-root", str(source), "--runtime-root", str(runtime), "--task-id", TARGET_TASK]
    done = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=clean_env(env), timeout=600)
    result = last_json(done.stdout)
    worker_result = (result or {}).get("execution_result") if isinstance(result, dict) else None
    terminal = bool(isinstance(worker_result, dict) and worker_result.get("state") == "COMPLETED")
    attempted = bool(isinstance(result, dict) and result.get("runtime_execution_attempted") is True)
    receipt = {
        "schema": "stegverse.deepseek-intr-resident-request-consumption/v1",
        "state": "COMPLETED" if terminal else ("ATTEMPT_RECORDED" if attempted else "FAIL_CLOSED"),
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "command": command,
        "execution_returncode": done.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "runtime_execution_attempted": attempted,
        "terminal": terminal,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "credential_material_present": False,
        "second_machine_required": False,
        "network_source_fetch_performed": False,
        "authority_effect": "NONE_REQUEST_ONLY"
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
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"NO_REQUEST", "ALREADY_TERMINAL", "ATTEMPT_RECORDED", "COMPLETED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
