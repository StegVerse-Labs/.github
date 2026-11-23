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
        "master_records_organization_record_required_for_egress": True,
        "same_execution_required": True,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in required.items():
        if request.get(key) != wanted:
            raise RuntimeError(f"DeepSeek resident request {key} mismatch")


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    env_source = os.environ if source is None else source
    for key in FORBIDDEN:
        if key in env_source and str(env_source[key]).strip():
            raise RuntimeError(f"Forbidden environment variable present: {key}")
    for key in HOSTED:
        if truthy(env_source.get(key)):
            raise RuntimeError(f"Hosted/CI environment variable present: {key}")
    
    cleaned: dict[str, str] = {}
    for key in NONSECRET:
        val = env_source.get(key)
        if val is not None:
            cleaned[key] = str(val)
    return cleaned


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume DeepSeek resident execution request.")
    parser.add_argument("--execute", action="store_true", help="Execute the target entrypoint.")
    args = parser.parse_args()

    request_path = ROOT / REQUEST_REL
    if not request_path.is_file():
        print(f"Error: Request file not found at {request_path}", file=sys.stderr)
        return 1

    request = load(request_path)
    validate_request(request)

    env = clean_env()

    consumption_path = ROOT / CONSUMPTION_REL
    consumption_path.parent.mkdir(parents=True, exist_ok=True)

    consumption_record = {
        "schema": "stegverse.resident-execution-request-consumption/v1",
        "task_id": TARGET_TASK,
        "request_hash": stable(request),
        "status": "CONSUMED",
    }
    consumption_path.write_text(json.dumps(consumption_record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.execute:
        entrypoint_path = ROOT / TARGET_ENTRYPOINT
        if not entrypoint_path.is_file():
            print(f"Error: Target entrypoint not found at {entrypoint_path}", file=sys.stderr)
            return 1
        
        cmd = [sys.executable, str(entrypoint_path)]
        result = subprocess.run(cmd, cwd=ROOT, env=env)
        return result.return0 if hasattr(result, "return0") else result.returncode

    print(f"Successfully validated and consumed DeepSeek resident execution request for {TARGET_TASK}")
    return 0


if __name__ == "__main__":
    sys.exit(main())