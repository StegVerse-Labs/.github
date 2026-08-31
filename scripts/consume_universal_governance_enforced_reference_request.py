#!/usr/bin/env python3
"""Consume the Universal Governance ENFORCED reference resident request."""
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
REQUEST_REL = Path("control/resident-execution-request.d/universal-governance-enforced-reference-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/universal-governance-enforced-reference-request-consumption.latest.json")
TARGET_TASK = "SHWP-UNIVERSAL-GOVERNANCE-ENFORCED-REFERENCE-001"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
TERMINAL_TRANSITION = "UNIVERSAL_GOVERNANCE_REFERENCE_ENFORCED_BOUNDARY_OBSERVED"
NONSECRET_ENV = {
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_STEGCORE_SOURCE_ROOT", "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    "STEGVERSE_REPO_ROOTS_JSON",
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
        "mode": TARGET_MODE,
        "entrypoint": TARGET_ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, expected_value in expected.items():
        if request.get(key) != expected_value:
            raise RuntimeError(f"Universal Governance resident request {key} mismatch")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not request_id.strip():
        raise RuntimeError("request_id missing")
    if request.get("required_nonsecret_source_locators") != [
        "STEGVERSE_STEGCORE_SOURCE_ROOT",
        "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    ]:
        raise RuntimeError("Universal Governance source locator contract mismatch")

def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([x.strip() for x in stdout.splitlines() if x.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None

def terminally_consumed(runtime: Path, request_id: str, request_hash: str) -> bool:
    path = runtime / CONSUMPTION_REL
    if not path.is_file():
        return False
    try:
        receipt = load_json(path)
    except Exception:
        return False
    return bool(
        receipt.get("request_id") == request_id
        and receipt.get("request_sha256") == request_hash
        and receipt.get("reference_enforced_boundary_observed") is True
        and receipt.get("bypass_negative_control_passed") is True
        and receipt.get("master_records_custody_accepted") is True
        and receipt.get("real_external_system_enforced_activation") is False
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
            "schema": "stegverse.universal-governance-resident-request-consumption/v1",
            "state": "NO_REQUEST",
            "runtime_execution_attempted": False,
            "authority_effect": "NONE",
        }

    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)
    request_id = request["request_id"]
    if terminally_consumed(runtime, request_id, request_hash):
        return {
            "schema": "stegverse.universal-governance-resident-request-consumption/v1",
            "state": "ALREADY_CONSUMED",
            "request_id": request_id,
            "request_sha256": request_hash,
            "runtime_execution_attempted": False,
            "reference_enforced_boundary_observed": True,
            "bypass_negative_control_passed": True,
            "master_records_custody_accepted": True,
            "real_external_system_enforced_activation": False,
            "authority_effect": "NONE_REQUEST_ONLY",
        }

    entrypoint = runtime / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"Universal Governance resident execution entrypoint missing: {entrypoint}")

    command = [
        sys.executable, str(entrypoint),
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
        env=clean_env(env),
        timeout=1200,
    )
    result = parse_last_json(completed.stdout)
    worker = result.get("execution_result") if isinstance(result, dict) else None
    transition = worker.get("transition_id") if isinstance(worker, dict) else None
    terminal = transition == TERMINAL_TRANSITION and worker.get("state") == "COMPLETED" if isinstance(worker, dict) else False

    evidence_refs = worker.get("evidence_refs") if isinstance(worker, dict) else []
    local_receipt = None
    if terminal and isinstance(evidence_refs, list):
        for ref in evidence_refs:
            if isinstance(ref, str) and ref:
                candidate = Path(ref).expanduser()
                if not candidate.is_absolute():
                    candidate = (Path.home() / ".stegverse/state/universal-governance-enforced-reference" / candidate).resolve()
                if candidate.is_file():
                    local_receipt = load_json(candidate)
                    break

    reference_observed = bool(local_receipt and local_receipt.get("reference_enforced_boundary_observed") is True)
    bypass_passed = bool(local_receipt and local_receipt.get("bypass_negative_control_passed") is True)
    custody_accepted = bool(local_receipt and local_receipt.get("master_records_custody_accepted") is True)
    external_false = bool(local_receipt and local_receipt.get("real_external_system_enforced_activation") is False)
    complete = terminal and reference_observed and bypass_passed and custody_accepted and external_false

    receipt = {
        "schema": "stegverse.universal-governance-resident-request-consumption/v1",
        "state": "COMPLETED" if complete else "ATTEMPT_RECORDED",
        "request_id": request_id,
        "request_sha256": request_hash,
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "runtime_execution_attempted": True,
        "reference_enforced_boundary_observed": reference_observed,
        "bypass_negative_control_passed": bypass_passed,
        "master_records_custody_accepted": custody_accepted,
        "real_external_system_enforced_activation": False if complete else None,
        "retry_allowed": not complete,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "second_machine_required": False,
        "network_source_fetch_performed": False,
        "authority_effect": "NONE_REQUEST_ONLY",
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
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
