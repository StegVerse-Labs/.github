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
BOUNDARY_REL = Path("receipts/ai-defensive-envelope/ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json")
REQUIRED_DENIAL_PROBES = {"FILESYSTEM_OPEN", "NETWORK_IMPORT", "ENVIRONMENT_IMPORT"}
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

def _boundary_digest(value: Mapping[str, Any]) -> str:
    return "sha256:" + stable(value)


def verified_boundary_receipt(
    runtime: Path, worker_result: Mapping[str, Any] | None,
    *, previous_digest: str | None,
) -> dict[str, Any] | None:
    """Check a newly retained exact receipt, not just the worker completion flag."""
    if not isinstance(worker_result, Mapping):
        return None
    if worker_result.get("checkpoint_ref") != BOUNDARY_REL.as_posix():
        return None
    refs = worker_result.get("evidence_refs")
    if not isinstance(refs, list) or BOUNDARY_REL.as_posix() not in refs:
        return None
    path = runtime / BOUNDARY_REL
    if not path.is_file() or path.is_symlink():
        return None
    try:
        value = load(path)
    except (ValueError, OSError):
        return None
    digest = _boundary_digest(value)
    if previous_digest == digest:
        return None
    claim = value.get("claim")
    probe = value.get("probe")
    checks = value.get("checks")
    if not isinstance(claim, dict) or not isinstance(probe, dict) or not isinstance(checks, dict):
        return None
    fence = claim.get("fencing_token")
    claim_id = claim.get("claim_id")
    if not (
        value.get("schema") == "stegverse.ungoverned-ai-defensive-envelope-resident-boundary/v1"
        and value.get("task_id") == TARGET_TASK
        and value.get("component_id") == "RTC-NONCHATGPT-AI-DECISION-SANDBOX-011"
        and value.get("state") == "REPRESENTATIVE_BOUNDARY_PROBE_OBSERVED"
        and isinstance(fence, int) and not isinstance(fence, bool) and fence > 0
        and isinstance(claim_id, str) and claim_id.endswith(f"-G{fence}")
        and claim.get("worker_id") == "ungoverned-ai-defensive-envelope-worker"
        and value.get("tvc_source_floor") == "0b82b45de7d214fbdb2f24bc4027a6aeb31a7312"
        and isinstance(value.get("tvc_source_head"), str) and bool(value["tvc_source_head"])
        and value.get("external_provider_observed") is False
        and value.get("goal_runtime_completion_claimed") is False
    ):
        return None
    denied = probe.get("denied_interactions")
    if not isinstance(denied, list) or not REQUIRED_DENIAL_PROBES.issubset(
        row.get("probe_id") for row in denied if isinstance(row, dict)
    ):
        return None
    if not all(
        isinstance(row, dict) and row.get("decision") == "DENY"
        and row.get("consumed") is False and row.get("consequence_reachable") is False
        for row in denied
    ):
        return None
    required = (
        "allow_consumed", "allow_result", "filesystem_not_exposed",
        "network_not_exposed", "deny_not_consumed", "deny_consequence_unreachable",
        "ambient_credentials_not_exposed", "temporary_state_destroyed",
        "egress_evidence_only",
    )
    if not all(checks.get(key) is True for key in required):
        return None
    return {
        "receipt_sha256": digest,
        "claim_id": claim_id,
        "fencing_token": fence,
        "tvc_source_head": value["tvc_source_head"],
        "denial_probe_ids": sorted(REQUIRED_DENIAL_PROBES),
        "origin": "SAME_RESIDENT_FILESYSTEM_NOT_INDEPENDENT_AUTHORITY_READBACK",
        "master_records_custody_proven": False,
        "organization_ledger_custody_proven": False,
    }


def verified_boundary_receipt_from_terminal(
    runtime: Path, consumption: Mapping[str, Any],
) -> bool:
    """Reject replay of an orphaned/stale terminal consumption marker."""
    path = runtime / BOUNDARY_REL
    if not path.is_file() or path.is_symlink():
        return False
    try:
        boundary = load(path)
    except (ValueError, OSError):
        return False
    claim = boundary.get("claim")
    return bool(
        _boundary_digest(boundary) == consumption.get("boundary_receipt_sha256")
        and isinstance(claim, dict)
        and claim.get("claim_id") == consumption.get("boundary_claim_id")
        and claim.get("fencing_token") == consumption.get("boundary_fencing_token")
    )


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
        and value.get("boundary_receipt_verified") is True
        and isinstance(value.get("boundary_receipt_sha256"), str)
        and verified_boundary_receipt_from_terminal(runtime, value)
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
    existing_boundary = runtime / BOUNDARY_REL
    previous_digest = None
    if existing_boundary.is_file() and not existing_boundary.is_symlink():
        try:
            previous_digest = _boundary_digest(load(existing_boundary))
        except (ValueError, OSError):
            previous_digest = None
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
    boundary = verified_boundary_receipt(
        runtime, worker_result, previous_digest=previous_digest
    ) if bridge_valid and done.returncode == 0 else None
    terminal = bool(
        boundary is not None
        and bridge_valid
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
        "boundary_receipt_verified":boundary is not None,
        "boundary_receipt_sha256":boundary.get("receipt_sha256") if boundary else None,
        "boundary_claim_id":boundary.get("claim_id") if boundary else None,
        "boundary_fencing_token":boundary.get("fencing_token") if boundary else None,
        "boundary_evidence":boundary,
        "organization_ledger_custody_proven":False,
        "master_records_custody_proven":False,
        "runtime_proof_promoted":False,
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
