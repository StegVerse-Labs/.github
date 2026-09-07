#!/usr/bin/env python3
"""Consume the bounded HIL sovereign-receiver resident execution request.

The request is intent only. It grants no claim, fence, credential, heartbeat,
transport, review, publication, or Master Records authority. The consumer may
invoke only the already-installed portable targeted execution bridge for
SHWP-HIL-SOVEREIGN-RECEIVER-001.

Before targeted execution, the consumer materializes the non-secret HIL
loopback/shared-Service-Gateway route config. Missing runtime/node route
predicates are retryable and MUST NOT burn the request. Successful same-device
local receiver READY is terminal for this resident request, while the broader
HIL lifecycle remains independently active for public rendezvous, TVC,
reconstruction, publication, and Master Records evidence.
"""
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
REQUEST_REL = Path("control/resident-execution-request.d/hil-sovereign-receiver-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json")
TARGET_TASK = "SHWP-HIL-SOVEREIGN-RECEIVER-001"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
ROUTE_MATERIALIZER = "scripts/materialize_hil_gateway_route_config.py"
TERMINAL_TRANSITIONS = {
    "HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED",
    "HIL_PUBLIC_HTTPS_RENDEZVOUS",
    "HIL_RECEIVER_RECEIPT_OBSERVED",
    "HIL_RECEIVER_EXACT_BYTE_RECONSTRUCTED",
    "HIL_TVC_LIFECYCLE_RECEIPT_OBSERVED",
}

NONSECRET_ENV = {
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
    "STEGVERSE_LLM_ADAPTER_ROOT",
    "STEGVERSE_HIL_STATE_ROOT",
    "STEGVERSE_HIL_RECEIVER_PORT",
    "STEGVERSE_HIL_INTR_ROUTE_CONFIG",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def clean_exec_env(source: dict[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    env = {name: values[name] for name in NONSECRET_ENV if name in values}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def validate_request(request: dict[str, Any]) -> None:
    required = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE_FOR_PARTICIPANT_INTAKE",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, expected in required.items():
        if request.get(key) != expected:
            raise RuntimeError(f"HIL resident execution request {key} mismatch")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not request_id.strip():
        raise RuntimeError("HIL resident execution request_id missing")


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            candidate = json.loads(line)
        except Exception:
            continue
        if isinstance(candidate, dict):
            return candidate
    return None


def terminal_transition(result: dict[str, Any] | None) -> str | None:
    if not isinstance(result, dict):
        return None
    candidates = [
        result.get("transition_id"),
        (result.get("execution_result") or {}).get("transition_id") if isinstance(result.get("execution_result"), dict) else None,
    ]
    for candidate in candidates:
        if candidate in TERMINAL_TRANSITIONS:
            return str(candidate)
    return None


def previously_consumed(runtime_root: Path, request: dict[str, Any], request_hash: str) -> bool:
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
        and receipt.get("terminal_hil_transition_observed") is True
    )


def write_receipt(runtime: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    receipt_path = runtime / CONSUMPTION_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def consume(
    source_root: Path,
    runtime_root: Path,
    *,
    runner=subprocess.run,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {
            "schema": "stegverse.hil-resident-execution-request-consumption/v1",
            "state": "NO_REQUEST",
            "runtime_execution_attempted": False,
            "terminal_hil_transition_observed": False,
            "authority_effect": "NONE",
        }

    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    if previously_consumed(runtime, request, request_hash):
        return {
            "schema": "stegverse.hil-resident-execution-request-consumption/v1",
            "state": "ALREADY_CONSUMED",
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "runtime_execution_attempted": False,
            "terminal_hil_transition_observed": True,
            "broader_hil_lifecycle_complete": False,
            "authority_effect": "NONE",
        }

    safe_env = clean_exec_env(env)
    materializer = runtime / ROUTE_MATERIALIZER
    if not materializer.is_file():
        materializer = source / ROUTE_MATERIALIZER
    if not materializer.is_file():
        raise RuntimeError(f"HIL Gateway route materializer missing: {materializer}")

    route_completed = runner(
        [sys.executable, str(materializer)],
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        env=safe_env,
        timeout=30,
    )
    route_result = parse_last_json(route_completed.stdout)
    if not isinstance(route_result, dict):
        raise RuntimeError("HIL Gateway route materializer returned no machine result")
    if route_result.get("state") == "PREDICATE_PENDING":
        return write_receipt(runtime, {
            "schema": "stegverse.hil-resident-execution-request-consumption/v1",
            "state": "PREDICATE_PENDING",
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "task_id": TARGET_TASK,
            "route_materialization": route_result,
            "runtime_execution_attempted": False,
            "terminal_hil_transition_observed": False,
            "broader_hil_lifecycle_complete": False,
            "retry_allowed": True,
            "request_granted_authority": False,
            "heartbeat_grants_execution_authority": False,
            "github_token_required": False,
            "github_token_runtime_authority": "NONE",
            "credential_authority": "TV/TVC",
            "second_machine_required": False,
            "authority_effect": "NONE_REQUEST_ONLY",
        })

    route_config = route_result.get("config") or {}
    route_path = route_result.get("path")
    if route_config.get("public_tls_terminated_by") != "STEGVERSE_SHARED_SERVICE_GATEWAY":
        raise RuntimeError("HIL route must terminate public TLS at shared Service Gateway")
    if route_config.get("credential_authority") != "TV/TVC":
        raise RuntimeError("HIL route credential authority drift")
    if route_config.get("g18_completion_required") is not False:
        raise RuntimeError("HIL route cannot depend on G18 completion")
    if isinstance(route_path, str) and route_path:
        safe_env["STEGVERSE_HIL_INTR_ROUTE_CONFIG"] = route_path

    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"HIL resident execution entrypoint missing: {entrypoint}")

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
        env=safe_env,
        timeout=180,
    )
    result = parse_last_json(completed.stdout)
    terminal = terminal_transition(result)
    state = "COMPLETED" if terminal else ("ATTEMPT_RECORDED" if isinstance(result, dict) else "FAIL_CLOSED")

    receipt = {
        "schema": "stegverse.hil-resident-execution-request-consumption/v1",
        "state": state,
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "route_materialization": route_result,
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "runtime_execution_attempted": True,
        "terminal_hil_transition": terminal,
        "terminal_hil_transition_observed": terminal is not None,
        "broader_hil_lifecycle_complete": terminal == "HIL_TVC_LIFECYCLE_RECEIPT_OBSERVED",
        "retry_allowed": terminal is None,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE_FOR_PARTICIPANT_INTAKE",
        "second_machine_required": False,
        "g18_completion_required": False,
        "network_source_fetch_performed": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    return write_receipt(runtime, receipt)


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume one bounded HIL resident execution request.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume(args.source_root, args.runtime_root)
    print(json.dumps(receipt, sort_keys=True))
    if receipt["state"] in {"NO_REQUEST", "ALREADY_CONSUMED", "PREDICATE_PENDING", "ATTEMPT_RECORDED", "COMPLETED"}:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
