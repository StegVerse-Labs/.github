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

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/ungoverned-ai-defensive-envelope-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/ungoverned-ai-defensive-envelope-request-consumption.latest.json")
TARGET_TASK = "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
HOSTED = ("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","VERCEL_ENV","CF_PAGES","CLOUDFLARE_WORKERS")
NONSECRET = (
    "PATH","HOME","LANG","LC_ALL","XDG_STATE_HOME","XDG_CONFIG_HOME","LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE","STEGVERSE_HEARTBEAT_ROOT","STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_TVC_ROOT",
)
FORBIDDEN = (
    "GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "OPENAI_API_KEY","ANTHROPIC_API_KEY","DEEPSEEK_API_KEY","STEGVERSE_PROVIDER_TOKEN",
    "STEGVERSE_MASTER_RECORDS_TOKEN","MASTER_RECORDS_RECEIPT_KEY",
    "STEGVERSE_VAULT_AGENT_SOCKET","STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET",
)

def truthy(value: Any) -> bool:
    return str(value or "").strip().lower() not in {"","0","false","no"}

def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object:{path}")
    return value

def stable(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema":"stegverse.resident-execution-request/v1",
        "state":"REQUESTED",
        "request_id":"RESIDENT-EXEC-UNGOVERNED-AI-DEFENSIVE-ENVELOPE-001",
        "task_id":TARGET_TASK,
        "mode":TARGET_MODE,
        "entrypoint":TARGET_ENTRYPOINT,
        "fresh_fence_minimum_exclusive":0,
        "credential_authority":"TV/TVC",
        "credential_material_required":False,
        "github_token_required":False,
        "github_token_runtime_authority":"NONE",
        "heartbeat_grants_execution_authority":False,
        "second_machine_required":False,
        "device_confirmation_required":False,
        "remote_connected_device_required":False,
        "absence_of_connected_device_is_blocker":False,
        "network_source_fetch_allowed":False,
        "request_granted_authority":False,
        "external_provider_origin_required_for_this_probe":False,
        "authority_effect":"NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if request.get(key) != wanted:
            raise RuntimeError(f"defensive-envelope resident request {key} mismatch")
    if request.get("entrypoint_arguments") != ["--task-id", TARGET_TASK]:
        raise RuntimeError("defensive-envelope resident request entrypoint_arguments mismatch")

def clean_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not consume defensive-envelope request:" + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET if values.get(name)}
    for name in FORBIDDEN:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env

def last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None

def previously_terminal(runtime: Path, request: Mapping[str, Any], request_hash: str) -> bool:
    path = runtime / CONSUMPTION_REL
    if not path.is_file():
        return False
    try:
        value = load(path)
    except Exception:
        return False
    return bool(
        value.get("request_id") == request.get("request_id")
        and value.get("request_sha256") == request_hash
        and value.get("terminal") is True
        and value.get("runtime_execution_attempted") is True
    )

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
            "schema":"stegverse.ungoverned-ai-defensive-envelope-request-consumption/v1",
            "state":"NO_REQUEST","runtime_execution_attempted":False,"authority_effect":"NONE",
        }
    request = load(request_path)
    validate_request(request)
    request_hash = stable(request)
    if previously_terminal(runtime, request, request_hash):
        return {
            "schema":"stegverse.ungoverned-ai-defensive-envelope-request-consumption/v1",
            "state":"ALREADY_TERMINAL","request_id":request["request_id"],
            "request_sha256":request_hash,"runtime_execution_attempted":False,"authority_effect":"NONE",
        }
    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError("defensive-envelope targeted execution entrypoint missing")
    command = [
        sys.executable, str(entrypoint),
        "--source-root", str(source),
        "--runtime-root", str(runtime),
        "--task-id", TARGET_TASK,
    ]
    done = runner(
        command, cwd=runtime, capture_output=True, text=True, check=False,
        env=clean_env(env), timeout=600,
    )
    result = last_json(done.stdout)
    worker_result = result.get("execution_result") if isinstance(result, dict) else None
    attempted = bool(isinstance(result, dict) and result.get("runtime_execution_attempted") is True)
    bridge_valid = bool(
        isinstance(result, dict)
        and result.get("mode") == TARGET_MODE
        and result.get("task_id") == TARGET_TASK
        and attempted
        and result.get("network_fetch_performed") is False
        and result.get("github_token_runtime_authority") == "NONE"
        and result.get("credential_authority") == "TV/TVC"
        and result.get("authority_effect") == "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY"
    )
    terminal = bool(
        bridge_valid
        and isinstance(worker_result, dict)
        and worker_result.get("state") == "COMPLETED"
        and worker_result.get("transition_id") == "UNGOVERNED_AI_DEFENSIVE_ENVELOPE_REPRESENTATIVE_BOUNDARY_OBSERVED"
    )
    receipt = {
        "schema":"stegverse.ungoverned-ai-defensive-envelope-request-consumption/v1",
        "state":"COMPLETED" if terminal else ("ATTEMPT_RECORDED" if attempted else "FAIL_CLOSED"),
        "request_id":request["request_id"],
        "request_sha256":request_hash,
        "task_id":TARGET_TASK,
        "mode":TARGET_MODE,
        "command":command,
        "execution_returncode":done.returncode,
        "execution_result_observed":isinstance(result, dict),
        "execution_result":result,
        "bridge_contract_valid":bridge_valid,
        "runtime_execution_attempted":attempted,
        "terminal":terminal,
        "request_granted_authority":False,
        "heartbeat_grants_execution_authority":False,
        "github_token_required":False,
        "github_token_runtime_authority":"NONE",
        "credential_authority":"TV/TVC",
        "credential_material_forwarded":False,
        "external_provider_origin_claimed":False,
        "network_source_fetch_performed":False,
        "second_machine_required":False,
        "remote_connected_device_required":False,
        "authority_effect":"NONE_REQUEST_CONSUMPTION_ONLY",
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
    return 0 if receipt["state"] in {"NO_REQUEST","ALREADY_TERMINAL","ATTEMPT_RECORDED","COMPLETED"} else 1

if __name__ == "__main__":
    raise SystemExit(main())
