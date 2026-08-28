#!/usr/bin/env python3
"""Consume one bounded ARA Graph resident execution request after local source refresh.

The request is intent only. It grants no claim, fence, credential, provider-operation,
heartbeat, release, scheduler, or network-source authority. The consumer invokes only
the existing generic resident refresh bridge in TARGETED_INDEPENDENT_TASK_CONTROL mode
for the already-registered SHWP-ARA-GRAPH-RUNTIME-086 task.

A request id + content hash is attempted at most once on one resident runtime. Provider
success, mailbox mutation, and capability activation remain matters for the task's own
secret-free runtime receipts and are never inferred from this consumer.
"""
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
REQUEST_REL = Path("control/resident-execution-request.d/ara-graph-runtime-086.json")
CONSUMPTION_REL = Path(
    "receipts/sovereign-host/ara-graph-resident-execution-request-consumption.latest.json"
)
TARGET_TASK = "SHWP-ARA-GRAPH-RUNTIME-086"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
MINIMUM_FENCE_EXCLUSIVE = 22

HOSTED_ENV = (
    "GITHUB_ACTIONS",
    "CI",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "VERCEL_ENV",
    "CF_PAGES",
    "CLOUDFLARE_WORKERS",
)
FORBIDDEN_SECRET_ENV = (
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_PAT",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "STEGVERSE_MAIL_CLIENT_SECRET",
    "STEGVERSE_MAIL_ACCESS_TOKEN",
    "STEGVERSE_MAIL_REFRESH_TOKEN",
    "AZURE_CLIENT_SECRET",
    "OAUTH_TOKEN",
    "ACCESS_TOKEN",
    "REFRESH_TOKEN",
)
NONSECRET_ENV = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "XDG_STATE_HOME",
    "XDG_CONFIG_HOME",
    "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE",
    "STEGVERSE_HEARTBEAT_ROOT",
    "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_TVC_ROOT",
    "STEGVERSE_ARA_MAIL_SENDER",
    "STEGVERSE_ARA_MAIL_RECIPIENT",
    "STEGVERSE_VAULT_AGENT_SOCKET",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    ).hexdigest()


def validate_request(request: Mapping[str, Any]) -> None:
    required = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "fresh_fence_minimum_exclusive": MINIMUM_FENCE_EXCLUSIVE,
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
    for key, expected in required.items():
        if request.get(key) != expected:
            raise RuntimeError(f"ARA Graph resident execution request {key} mismatch")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not request_id.strip():
        raise RuntimeError("ARA Graph resident execution request_id missing")


def clean_exec_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError(
            "hosted environment may not consume ARA Graph sovereign request: "
            + ",".join(sorted(hosted))
        )
    env = {name: values[name] for name in NONSECRET_ENV if values.get(name)}
    for name in FORBIDDEN_SECRET_ENV:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def previously_consumed(runtime_root: Path, request: Mapping[str, Any], request_hash: str) -> bool:
    path = runtime_root / CONSUMPTION_REL
    if not path.is_file():
        return False
    try:
        receipt = load_json(path)
    except Exception:
        return False
    return (
        receipt.get("request_id") == request.get("request_id")
        and receipt.get("request_sha256") == request_hash
        and receipt.get("runtime_execution_attempted") is True
    )


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            candidate = json.loads(line)
        except Exception:
            continue
        if isinstance(candidate, dict):
            return candidate
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
            "schema": "stegverse.ara-graph-resident-execution-request-consumption/v1",
            "state": "NO_REQUEST",
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }

    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    if previously_consumed(runtime, request, request_hash):
        return {
            "schema": "stegverse.ara-graph-resident-execution-request-consumption/v1",
            "state": "ALREADY_CONSUMED",
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }

    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"ARA Graph resident execution entrypoint missing: {entrypoint}")

    command = [
        sys.executable,
        str(entrypoint),
        "--source-root",
        str(source),
        "--runtime-root",
        str(runtime),
        "--task-id",
        TARGET_TASK,
    ]
    completed = runner(
        command,
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        env=clean_exec_env(env),
        timeout=900,
    )
    result = parse_last_json(completed.stdout)
    bridge_valid = bool(
        isinstance(result, dict)
        and result.get("mode") == TARGET_MODE
        and result.get("task_id") == TARGET_TASK
        and result.get("runtime_execution_attempted") is True
        and result.get("network_fetch_performed") is False
        and result.get("github_token_runtime_authority") == "NONE"
        and result.get("credential_authority") == "TV/TVC"
        and result.get("second_machine_required") is False
        and result.get("authority_effect") == "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY"
    )
    state = "ATTEMPT_RECORDED" if bridge_valid else "FAIL_CLOSED"

    receipt = {
        "schema": "stegverse.ara-graph-resident-execution-request-consumption/v1",
        "state": state,
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "bridge_contract_valid": bridge_valid,
        "runtime_execution_attempted": True,
        "request_granted_authority": False,
        "provider_success_claimed": False,
        "activation_claimed": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "provider_credential_material_allowed": False,
        "second_machine_required": False,
        "network_source_fetch_performed": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    receipt_path = runtime / CONSUMPTION_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Consume one bounded ARA Graph resident execution request."
    )
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    if receipt["state"] in {"NO_REQUEST", "ALREADY_CONSUMED"}:
        return 0
    return 0 if receipt["state"] == "ATTEMPT_RECORDED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
