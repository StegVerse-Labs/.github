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
OWNER_REQUEST_REL = Path("control/resident-execution-request.d/stegagents-governed-runtime-targeted-001.json")
PURPOSE_REQUEST_REL = Path("control/resident-execution-request.d/sdk-tt-purpose-bound-worker-runtime-proof-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/stegagents-governed-runtime-targeted-request-consumption.latest.json")
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
TARGETS = {
    "STEGAGENTS-GOVERNED-RUNTIME-001": {
        "vector": "71000000101001",
        "request_rel": OWNER_REQUEST_REL,
    },
    "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001": {
        "vector": "71000000111111",
        "request_rel": PURPOSE_REQUEST_REL,
    },
}
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
NONSECRET_ENV = (
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_ENDPOINT", "STEGVERSE_MASTER_RECORDS_TOKEN", "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS",
    "MASTER_RECORDS_DB", "MASTER_RECORDS_RECEIPT_KEY", "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS",
    "STEGVERSE_TVC_ROOT", "STEGVERSE_TV_ROOT", "STEGVERSE_REPO_ROOTS_JSON",
    "STEGVERSE_SDK_SOURCE_ROOT", "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "STEGVERSE_WARRANT_JSON", "TV_POLICY_BUNDLE_SHA256", "TV_WARRANT_ISSUER_PUBKEY_B64", "TV_WARRANT_MAX_TTL_SECONDS",
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
        raise RuntimeError("hosted environment may not consume governed StegAgents targeted request:" + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET_ENV if values.get(name)}
    for name in FORBIDDEN:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def validate_request(request: dict[str, Any]) -> tuple[str, str]:
    task_id = str(request.get("task_id") or "")
    target = TARGETS.get(task_id)
    if not isinstance(target, dict):
        raise RuntimeError("governed StegAgents targeted request task_id mismatch")
    vector = str(target["vector"])
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": task_id,
        "cosv_profile": "task.v1",
        "cosv_task_vector": vector,
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "fresh_fence_minimum_exclusive": 0,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "provider_credential_material_allowed": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if request.get(key) != wanted:
            raise RuntimeError(f"governed StegAgents targeted request {key} mismatch")
    if request.get("argv") != ["--task-id", task_id, "--cosv-task-vector", vector]:
        raise RuntimeError("governed StegAgents targeted request argv mismatch")
    return task_id, vector


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
    request_path = None
    request = None
    for task_id in ("SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001", "STEGAGENTS-GOVERNED-RUNTIME-001"):
        candidate = runtime / TARGETS[task_id]["request_rel"]
        if candidate.is_file():
            request_path = candidate
            request = load_json(candidate)
            break
    if request_path is None or request is None:
        return {"schema": "stegverse.stegagents-governed-runtime-targeted-consumption/v1", "state": "NO_REQUEST", "runtime_execution_attempted": False, "authority_effect": "NONE"}
    task_id, vector = validate_request(request)
    request_hash = stable_hash(request)
    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"targeted execution entrypoint missing:{entrypoint}")
    command = [sys.executable, str(entrypoint), "--source-root", str(source), "--runtime-root", str(runtime), "--task-id", task_id, "--cosv-task-vector", vector]
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=clean_env(env), timeout=1800)
    result = parse_last_json(completed.stdout)
    pointer = result.get("cosv_task_pointer") if isinstance(result, dict) else None
    pointer_verified = bool(isinstance(pointer, dict) and pointer.get("task_id") == task_id and pointer.get("vector") == vector and pointer.get("binding_verified") is True and pointer.get("authority_effect") == "NONE")
    valid = bool(isinstance(result, dict) and result.get("mode") == TARGET_MODE and result.get("task_id") == task_id and result.get("runtime_execution_attempted") is True and result.get("network_fetch_performed") is False and result.get("github_token_runtime_authority") == "NONE" and result.get("credential_authority") == "TV/TVC" and result.get("authority_effect") == "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY" and pointer_verified)
    receipt = {
        "schema": "stegverse.stegagents-governed-runtime-targeted-consumption/v1",
        "state": "ATTEMPT_RECORDED" if valid else "FAIL_CLOSED",
        "request_id": request.get("request_id"),
        "request_sha256": request_hash,
        "task_id": task_id,
        "cosv_task_vector": vector,
        "mode": TARGET_MODE,
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "pointer_binding_verified_before_execution": pointer_verified,
        "runtime_execution_attempted": True,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "provider_credential_material_allowed": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "network_source_fetch_performed": False,
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
