#!/usr/bin/env python3
"""Consume one bounded Bootstrap v1 Universal InTr bundle-delivery resident request."""
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
REQUEST_REL = Path("control/resident-execution-request.d/bootstrap-v1-intr-bundle-delivery-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/bootstrap-v1-intr-bundle-delivery-request-consumption.latest.json")
TARGET_TASK = "BOOTSTRAP-V1-INTR-BUNDLE-DELIVERY-001"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"

NONSECRET_ENV = {
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME",
    "LOCALAPPDATA", "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT",
    "STEGVERSE_HEARTBEAT_SOURCE_ROOT", "STEGVERSE_BOOTSTRAP_V1_INTR_ROUTE_CONFIG",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def clean_exec_env(source: Mapping[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    env = {key: values[key] for key in NONSECRET_ENV if values.get(key)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE_FOR_PUBLIC_BUNDLE_DELIVERY",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "package_execution_authority": False,
        "sdk_admission_authority": False,
        "release_activation_authority": False,
        "publication_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        if request.get(key) != wanted:
            raise RuntimeError(f"Bootstrap v1 InTr resident request {key} mismatch")
    if not isinstance(request.get("request_id"), str) or not request["request_id"].strip():
        raise RuntimeError("Bootstrap v1 InTr resident request_id missing")


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def terminally_consumed(runtime: Path, request: Mapping[str, Any], request_hash: str) -> bool:
    path = runtime / CONSUMPTION_REL
    if not path.is_file():
        return False
    try:
        receipt = load_json(path)
    except Exception:
        return False
    return (
        receipt.get("request_id") == request.get("request_id")
        and receipt.get("request_sha256") == request_hash
        and receipt.get("terminal_delivery_observed") is True
    )


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name("." + path.name + ".tmp")
    temp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


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
            "schema": "stegverse.bootstrap.intr-bundle-delivery-request-consumption/v1",
            "state": "NO_REQUEST",
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }

    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    if terminally_consumed(runtime, request, request_hash):
        return {
            "schema": "stegverse.bootstrap.intr-bundle-delivery-request-consumption/v1",
            "state": "ALREADY_CONSUMED",
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }

    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"Bootstrap v1 resident execution entrypoint missing: {entrypoint}")
    command = [
        sys.executable,
        str(entrypoint),
        "--source-root", str(source),
        "--runtime-root", str(runtime),
        "--task-id", TARGET_TASK,
    ]
    completed = runner(
        command,
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        env=clean_exec_env(env),
        timeout=180,
    )
    result = parse_last_json(completed.stdout)
    transition = None
    if isinstance(result, dict):
        transition = result.get("transition_id")
        nested = result.get("execution_result")
        if isinstance(nested, dict) and nested.get("transition_id"):
            transition = nested.get("transition_id")
    terminal = transition == "BOOTSTRAP_V1_INTR_BUNDLE_DELIVERY_OBSERVED"

    receipt = {
        "schema": "stegverse.bootstrap.intr-bundle-delivery-request-consumption/v1",
        "state": "COMPLETED" if terminal else "ATTEMPT_RECORDED",
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "runtime_execution_attempted": True,
        "terminal_delivery_observed": terminal,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE_FOR_PUBLIC_BUNDLE_DELIVERY",
        "second_machine_required": False,
        "network_source_fetch_performed": False,
        "package_execution_authority": False,
        "sdk_admission_authority": False,
        "release_activation_authority": False,
        "publication_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    atomic_json(runtime / CONSUMPTION_REL, receipt)
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
