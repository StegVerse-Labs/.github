#!/usr/bin/env python3
"""Consume the standing native email-action monitor resident request.

The request is revisited by the existing resident request dispatcher, which is
already driven by the canonical HB/oscillator worker-runtime cycle. This consumer
creates no scheduler, heartbeat, claim, fence, provider credential, or mailbox
authority. It locates the already-local StegOps broker and TVC provider-operation
command, executes one bounded monitor pass, and records a secret-free receipt.
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
REQUEST_REL = Path("control/resident-execution-request.d/native-email-action-monitor-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/native-email-action-monitor-request-consumption.latest.json")
MONITOR_RECEIPT_REL = Path("receipts/sovereign-host/native-email-action-monitor.latest.json")
TASK_ID = "STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001"
MODE = "NATIVE_EMAIL_ACTION_MONITOR"
ENTRYPOINT = "scripts/consume_native_email_action_monitor_request.py"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected JSON object:{path}")
    return value


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_receipt(runtime: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    path = runtime / CONSUMPTION_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)
    return receipt


def validate_request(request: Mapping[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "mode": MODE,
        "entrypoint": ENTRYPOINT,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "oscillator_grants_execution_authority": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "request_granted_authority": False,
        "standing_request": True,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        require(request.get(key) == wanted, f"native email resident request {key} mismatch")
    require(isinstance(request.get("request_id"), str) and bool(request.get("request_id")), "request_id required")


def repo_roots_from_env(values: Mapping[str, str]) -> list[Path]:
    roots: list[Path] = []
    raw = values.get("STEGVERSE_REPO_ROOTS_JSON")
    if raw:
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = None
        if isinstance(parsed, dict):
            for value in parsed.values():
                if isinstance(value, str) and value:
                    roots.append(Path(value).expanduser())
        elif isinstance(parsed, list):
            for value in parsed:
                if isinstance(value, str) and value:
                    roots.append(Path(value).expanduser())
    return roots


def resolve_repo(source: Path, values: Mapping[str, str], *, env_name: str, repo_name: str) -> Path | None:
    candidates: list[Path] = []
    explicit = values.get(env_name)
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend(repo_roots_from_env(values))
    candidates.extend((source.parent / repo_name, source.parent.parent / repo_name))
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            continue
        if resolved.name == repo_name and resolved.is_dir():
            return resolved
    return None


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def pending(runtime: Path, request: Mapping[str, Any], request_hash: str, reason: str, **extra: Any) -> dict[str, Any]:
    return write_receipt(runtime, {
        "schema": "stegverse.native-email-action-monitor-request-consumption/v1",
        "state": "ATTEMPT_RECORDED",
        "request_id": request.get("request_id"),
        "request_sha256": request_hash,
        "task_id": TASK_ID,
        "provider_route_ready": False,
        "runtime_execution_attempted": False,
        "retry_allowed": True,
        "pending_reason": reason,
        "credential_authority": "TV/TVC",
        "credential_material_exported": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "oscillator_grants_execution_authority": False,
        "second_machine_required": False,
        "authority_effect": "NONE_REQUEST_ONLY",
        **extra,
    })


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    values = dict(os.environ if env is None else env)
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        request_path = source / REQUEST_REL
    if not request_path.is_file():
        return {"schema": "stegverse.native-email-action-monitor-request-consumption/v1", "state": "NO_REQUEST", "runtime_execution_attempted": False, "authority_effect": "NONE"}
    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)

    monitor = runtime / "scripts/run_native_email_action_monitor.py"
    if not monitor.is_file():
        monitor = source / "scripts/run_native_email_action_monitor.py"
    if not monitor.is_file():
        return pending(runtime, request, request_hash, "MONITOR_ENTRYPOINT_NOT_MATERIALIZED")

    stegops = resolve_repo(source, values, env_name="STEGVERSE_STEGOPS_ORCHESTRATOR_ROOT", repo_name="StegOps-Orchestrator")
    if stegops is None:
        return pending(runtime, request, request_hash, "STEGOPS_PROVIDER_OWNER_ROOT_NOT_MATERIALIZED")
    broker = stegops / "scripts/native_email_tvc_broker.py"
    if not broker.is_file():
        return pending(runtime, request, request_hash, "STEGOPS_NATIVE_EMAIL_BROKER_NOT_MATERIALIZED", stegops_root=str(stegops))

    tvc = resolve_repo(source, values, env_name="STEGVERSE_TVC_ROOT", repo_name="TVC")
    if tvc is None:
        return pending(runtime, request, request_hash, "TVC_ROOT_NOT_MATERIALIZED")
    provider = tvc / "scripts/tvc_mail_provider_operation.py"
    if not provider.is_file():
        return pending(runtime, request, request_hash, "TVC_MAIL_PROVIDER_OPERATION_NOT_MATERIALIZED", tvc_root=str(tvc))

    monitor_receipt = runtime / MONITOR_RECEIPT_REL
    broker_command = [sys.executable, str(broker), "--tvc-provider-command", sys.executable, str(provider)]
    command = [
        sys.executable, str(monitor),
        "--output", str(monitor_receipt),
        "--batch-limit", "100",
        "--broker-json", json.dumps(broker_command, separators=(",", ":")),
    ]
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=dict(values), timeout=900)
    monitor_result = load_json(monitor_receipt) if monitor_receipt.is_file() else parse_last_json(completed.stdout)
    success = bool(completed.returncode == 0 and isinstance(monitor_result, dict) and monitor_result.get("schema") == "stegverse.native-email-action-monitor-receipt/v1" and monitor_result.get("state") == "PASS")
    return write_receipt(runtime, {
        "schema": "stegverse.native-email-action-monitor-request-consumption/v1",
        "state": "COMPLETED" if success else "ATTEMPT_RECORDED",
        "request_id": request.get("request_id"),
        "request_sha256": request_hash,
        "task_id": TASK_ID,
        "standing_request": True,
        "provider_route_ready": True,
        "runtime_execution_attempted": True,
        "execution_returncode": completed.returncode,
        "monitor_receipt_ref": str(monitor_receipt),
        "monitor_result": monitor_result,
        "retry_allowed": True,
        "credential_authority": "TV/TVC",
        "credential_material_exported": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "oscillator_grants_execution_authority": False,
        "hb_continuation_is_trigger_only": True,
        "second_machine_required": False,
        "authority_effect": "NONE_MAILBOX_MAINTENANCE_EXECUTION_EVIDENCE_ONLY",
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = consume(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state") in {"NO_REQUEST", "ATTEMPT_RECORDED", "COMPLETED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
