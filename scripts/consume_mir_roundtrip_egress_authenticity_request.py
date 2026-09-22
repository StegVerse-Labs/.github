#!/usr/bin/env python3
"""Consume the standing MIR event through the proven SV002 event-triggered order.

The standing request is itself the event input. This consumer invokes the bounded
event driver directly; it does not require WorkerCoordinator to create the event,
mint a claim/fence, or authorize execution. Interlock/InTr remains transition
authority. Canonical Master Records custody/reconstruction is required after every
observed governed state transition.
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

TASK_ID = "MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001"
COSV = "50000000100000"
REQUEST_REL = Path("control/resident-execution-request.d/mir-roundtrip-egress-authenticity-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/mir-roundtrip-egress-authenticity-request-consumption.latest.json")
TARGET_RECEIPT_REL = Path("receipts/mir-roundtrip-egress-authenticity/current.latest.json")
HOSTED = ("GITHUB_ACTIONS", "CI", "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
)
NONSECRET = (
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_MICRO_NODE_RUNTIME_ROOT", "STEGVERSE_TVC_ROOT", "STEGVERSE_TV_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT", "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT",
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT", "STEGVERSE_MASTER_RECORDS_ENDPOINT",
    "STEGVERSE_MASTER_RECORDS_TOKEN", "STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS",
    "STEGVERSE_STEGOS_ROOT", "STEGVERSE_STEGOS_SOURCE_ROOT", "STEGVERSE_SITE_ROOT",
    "STEGVERSE_REPO_ROOTS_JSON", "STEGVERSE_SDK_SOURCE_ROOT", "PYTHONPATH", "TMPDIR",
)


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"json_object_required:{path}")
    return value


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def clean_env(source: dict[str, str] | None = None) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    hosted = [name for name in HOSTED if truthy(values.get(name))]
    require(not hosted, "hosted environment may not consume sovereign MIR execution request:" + ",".join(sorted(hosted)))
    env = {name: values[name] for name in NONSECRET if values.get(name)}
    for name in FORBIDDEN:
        if name not in {"STEGVERSE_MASTER_RECORDS_TOKEN"}:
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


def validate_request(request: dict[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "mode": "MIR_MIRROR_DUPLICATE_FIRST_EVENT_DRIVEN_EGRESS_AUTHENTICITY",
        "entrypoint": "scripts/execute_mir_event_driven_roundtrip.py",
        "execution_owner": "EXISTING_INTERLOCK_INTR_EVENT_MATERIALIZATION_AND_STEGOS_EVENT_EPHEMERAL_RUNTIME",
        "workercoordinator_claim_required_for_event_creation": False,
        "requires_current_workercoordinator_claim_fence": False,
        "claim_or_fence_minted_by_request": False,
        "request_grants_execution_authority": False,
        "generic_sv002_route_reproof_required": False,
        "manual_device_prerequisite": False,
        "second_machine_required": False,
        "network_source_fetch_allowed": False,
        "credential_authority": "TV/TVC",
        "transition_authority": "INTERLOCK_INTR",
        "custody_authority": "MASTER_RECORDS",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, wanted in expected.items():
        require(request.get(key) == wanted, f"mir_resident_request_{key}_mismatch")


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: dict[str, str] | None = None) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = source / REQUEST_REL
    require(request_path.is_file(), "mir_resident_execution_request_missing")
    request = load(request_path)
    validate_request(request)
    request_sha = stable_hash(request)

    target_receipt_path = runtime / TARGET_RECEIPT_REL
    if target_receipt_path.is_file():
        prior = load(target_receipt_path)
        if (
            prior.get("schema") == "stegverse.mir-roundtrip-egress-authenticity-receipt/v1"
            and prior.get("goal_task_id") == TASK_ID
            and prior.get("cosv_task_vector") == COSV
            and prior.get("successful_one_way_mir_transport_identified") is True
            and prior.get("master_records_reconstructs_each_observed_transition") is True
        ):
            receipt = {
                "schema": "stegverse.mir-roundtrip-egress-authenticity-request-consumption/v1",
                "state": "ALREADY_CONSUMED_ONE_WAY_CONFIRMED",
                "task_id": TASK_ID,
                "cosv_task_vector": COSV,
                "request_sha256": request_sha,
                "target_receipt_ref": str(target_receipt_path),
                "reexecution_performed": False,
                "continue_to_governed_return": True,
                "workercoordinator_claim_required_for_event_creation": False,
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": "NONE",
                "authority_effect": "NONE_CONSUMPTION_EVIDENCE_ONLY",
            }
            atomic_json(runtime / CONSUMPTION_REL, receipt)
            return receipt

    entrypoint_rel = Path(str(request["entrypoint"]))
    entrypoint = source / entrypoint_rel
    require(entrypoint.is_file(), "mir_event_driven_entrypoint_missing")
    command = [
        sys.executable,
        str(entrypoint),
        "--source-root", str(source),
        "--runtime-root", str(runtime),
    ]
    completed = runner(
        command,
        cwd=source,
        capture_output=True,
        text=True,
        check=False,
        env=clean_env(env),
        timeout=1200,
    )
    result = parse_last_json(completed.stdout)
    target = load(target_receipt_path) if target_receipt_path.is_file() else None
    one_way = bool(
        isinstance(target, dict)
        and target.get("schema") == "stegverse.mir-roundtrip-egress-authenticity-receipt/v1"
        and target.get("goal_task_id") == TASK_ID
        and target.get("cosv_task_vector") == COSV
        and target.get("successful_one_way_mir_transport_identified") is True
        and target.get("master_records_reconstructs_each_observed_transition") is True
    )
    receipt = {
        "schema": "stegverse.mir-roundtrip-egress-authenticity-request-consumption/v1",
        "state": "ONE_WAY_CONFIRMED" if one_way else "EVENT_EXECUTION_ATTEMPT_RECORDED",
        "task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "request_sha256": request_sha,
        "command": command,
        "execution_returncode": completed.returncode,
        "event_execution_result": result,
        "target_receipt_ref": str(target_receipt_path),
        "target_receipt_observed": target is not None,
        "successful_one_way_mir_transport_identified": one_way,
        "continue_to_governed_return": one_way,
        "workercoordinator_claim_required_for_event_creation": False,
        "claim_or_fence_minted_by_request": False,
        "generic_sv002_route_reproof_performed": False,
        "manual_device_prerequisite": False,
        "second_machine_required": False,
        "network_source_fetch_performed": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "request_grants_execution_authority": False,
        "authority_effect": "NONE_CONSUMPTION_EVIDENCE_ONLY",
    }
    atomic_json(runtime / CONSUMPTION_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = consume(args.source_root, args.runtime_root)
    except Exception as exc:
        receipt = {
            "schema": "stegverse.mir-roundtrip-egress-authenticity-request-consumption/v1",
            "state": "REQUEST_CONSUMPTION_EXCEPTION",
            "task_id": TASK_ID,
            "cosv_task_vector": COSV,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "workercoordinator_claim_required_for_event_creation": False,
            "manual_device_prerequisite": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "authority_effect": "NONE_FAIL_CLOSED",
        }
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("state") in {"ALREADY_CONSUMED_ONE_WAY_CONFIRMED", "ONE_WAY_CONFIRMED", "EVENT_EXECUTION_ATTEMPT_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
