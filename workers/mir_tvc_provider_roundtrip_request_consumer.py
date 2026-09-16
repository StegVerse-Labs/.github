#!/usr/bin/env python3
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
REQUEST_REL = Path("control/resident-execution-request.d/mir-tvc-provider-roundtrip-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/mir-tvc-provider-roundtrip-request-consumption.latest.json")
VECTOR_REL = Path("control/task-vector-index.d/MIR-TVC-PROVIDER-ROUNDTRIP-001.json")
TARGET_TASK = "MIR-TVC-PROVIDER-ROUNDTRIP-001"
TARGET_VECTOR = "50000000100000"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
TARGET_REQUEST = "MIR-RUN2-EVENT-001"
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
NONSECRET_ENV = (
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_TVC_ROOT", "STEGVERSE_TV_ROOT", "STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    "STEGVERSE_CORE_LITE_SOURCE_ROOT", "STEGVERSE_REPO_ROOTS_JSON",
)
FORBIDDEN = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN", "ACTIONS_RUNTIME_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ZAI_API_KEY", "PRIVATE_KEY", "SEED", "MNEMONIC",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object:{path}")
    return value


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not consume MIR TVC resident request:" + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET_ENV if values.get(name)}
    for name in FORBIDDEN:
        env.pop(name, None)
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
        "entrypoint": TARGET_ENTRYPOINT,
        "provider_request_id": TARGET_REQUEST,
        "provider_operation": "SUBMIT_EVENT",
        "fresh_fence_minimum_exclusive": 0,
        "credential_authority": "TV/TVC",
        "transition_authority": "INTERLOCK_INTR",
        "custody_authority": "MASTER_RECORDS",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "provider_credential_material_allowed": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "requires_current_workercoordinator_claim_fence": True,
        "requires_current_intr_admission": True,
        "requires_existing_tvc_vault_broker": True,
        "same_transaction_custody_required": True,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if request.get(key) != wanted:
            raise RuntimeError(f"MIR TVC resident request {key} mismatch")
    if request.get("argv") != ["--task-id", TARGET_TASK]:
        raise RuntimeError("MIR TVC resident request argv mismatch")


def validate_vector(runtime: Path) -> dict[str, Any]:
    vector = load_json(runtime / VECTOR_REL)
    checks = {
        "schema": "stegverse.cosv-task-vector-index-entry/v1",
        "task_id": TARGET_TASK,
        "vector": TARGET_VECTOR,
        "profile": "task.v1",
        "authority_effect": "NONE",
    }
    for key, wanted in checks.items():
        if vector.get(key) != wanted:
            raise RuntimeError(f"MIR TVC task-vector shard {key} mismatch")
    source_ref = vector.get("source_state_vector_ref")
    if not isinstance(source_ref, str) or not source_ref:
        raise RuntimeError("MIR TVC task-vector shard source provenance missing")
    return vector


def parse_last_json(stdout: str) -> dict[str, Any] | None:
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
        return {"schema": "stegverse.mir-tvc-provider-roundtrip-request-consumption/v1", "state": "NO_REQUEST", "runtime_execution_attempted": False, "authority_effect": "NONE"}
    request = load_json(request_path)
    validate_request(request)
    vector = validate_vector(runtime)
    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"MIR TVC execution entrypoint missing:{entrypoint}")
    command = [sys.executable, str(entrypoint), "--source-root", str(source), "--runtime-root", str(runtime), "--task-id", TARGET_TASK]
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=clean_env(env), timeout=1800)
    result = parse_last_json(completed.stdout)
    receipt = {
        "schema": "stegverse.mir-tvc-provider-roundtrip-request-consumption/v1",
        "state": "ATTEMPT_RECORDED" if isinstance(result, dict) else "FAIL_CLOSED",
        "request_id": request.get("request_id"),
        "request_sha256": stable_hash(request),
        "task_id": TARGET_TASK,
        "cosv_task_vector": TARGET_VECTOR,
        "cosv_source_state_vector_ref": vector.get("source_state_vector_ref"),
        "provider_request_id": TARGET_REQUEST,
        "provider_operation": "SUBMIT_EVENT",
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "runtime_execution_attempted": True,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "provider_credential_material_allowed": False,
        "transition_authority": "INTERLOCK_INTR",
        "custody_authority": "MASTER_RECORDS",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "network_source_fetch_performed": False,
        "second_machine_required": False,
        "authority_effect": "NONE_REQUEST_CONSUMPTION_ONLY",
    }
    destination = runtime / CONSUMPTION_REL
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
