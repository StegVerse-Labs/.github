#!/usr/bin/env python3
"""Consume the bounded sovereign relay return-path resident request exactly once.

The request is intent only. It invokes the already-admitted WorkerCoordinator task
through the existing targeted resident bridge and carries no credential, route,
claim, fence, heartbeat, transition, or repository authority.
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

REQUEST_REL = Path("control/resident-execution-request.d/stegos-sovereign-relay-return-path-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/stegos-sovereign-relay-return-path-request-consumption.latest.json")
TARGET_TASK = "SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "VERCEL_ENV",
    "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "PRIVATE_KEY",
    "ROOT_PRIVATE_KEY", "RECOVERY_SHARE", "SEED", "MNEMONIC", "TVC_TOKEN",
)
NONSECRET_ENV = (
    "PATH", "HOME", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA", "STEGVERSE_SOVEREIGN_NODE",
    "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_STEGOS_ROOT", "STEGVERSE_TVC_ROOT", "STEGVERSE_ORG_CONTROL_ROOT",
    "STEGVERSE_HIL_STATE_ROOT", "STEGVERSE_RELAY_RUNTIME_BASE",
    "STEGVERSE_RELAY_EGRESS_BINDING", "STEGVERSE_RELAY_EGRESS_AUTHORIZATION",
    "STEGVERSE_RELAY_EGRESS_PAYLOAD",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_request(request: Mapping[str, Any]) -> None:
    required = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "network_source_fetch_allowed": False,
        "second_machine_required": False,
        "protected_material_allowed_in_request": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, expected in required.items():
        if request.get(key) != expected:
            raise RuntimeError(f"relay return resident request {key} mismatch")
    if not isinstance(request.get("request_id"), str) or not request["request_id"].strip():
        raise RuntimeError("relay return resident request_id missing")


def clean_exec_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if hosted:
        raise RuntimeError("hosted environment may not consume sovereign relay return request: " + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET_ENV if values.get(name)}
    for name in FORBIDDEN_ENV:
        env.pop(name, None)
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


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
        return {
            "schema": "stegverse.relay-return-resident-request-consumption/v1",
            "state": "NO_REQUEST",
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }
    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"relay return resident entrypoint missing: {entrypoint}")
    command = [
        sys.executable, str(entrypoint), "--source-root", str(source),
        "--runtime-root", str(runtime), "--task-id", TARGET_TASK,
    ]
    completed = runner(
        command, cwd=runtime, capture_output=True, text=True, check=False,
        env=clean_exec_env(env), timeout=1800,
    )
    result = parse_last_json(completed.stdout)
    terminal_path = runtime / "receipts/stegos-sovereign-relay" / f"{TARGET_TASK}.json"
    terminal = load_json(terminal_path) if terminal_path.is_file() else None
    terminal_verified = bool(
        isinstance(terminal, dict)
        and terminal.get("state") == "COMPLETED"
        and terminal.get("transition_id") == "SOVEREIGN_RELAY_RETURN_PATH_VERIFIED"
        and isinstance(terminal.get("round_trip_result"), dict)
        and terminal["round_trip_result"].get("state") == "RETURN_PATH_VERIFIED"
        and terminal["round_trip_result"].get("far_side_evidence_present") is True
        and terminal["round_trip_result"].get("durable_return_queue_verified") is True
        and terminal["round_trip_result"].get("interlock_ingestion_verified") is True
        and terminal.get("canonical_transition_committed") is False
    )
    receipt = {
        "schema": "stegverse.relay-return-resident-request-consumption/v1",
        "state": "RETURN_PATH_VERIFIED" if terminal_verified else "ATTEMPT_RECORDED",
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "terminal_receipt_observed": isinstance(terminal, dict),
        "terminal_receipt_verified": terminal_verified,
        "runtime_execution_attempted": True,
        "network_source_fetch_performed": False,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "second_machine_required": False,
        "canonical_transition_authority": "Interlock/InTr",
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    receipt_path = runtime / CONSUMPTION_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume the sovereign relay return-path resident request.")
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--runtime-root", required=True, type=Path)
    args = parser.parse_args()
    receipt = consume(args.source_root, args.runtime_root)
    return 0 if receipt.get("state") in {"NO_REQUEST", "ATTEMPT_RECORDED", "RETURN_PATH_VERIFIED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
