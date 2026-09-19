#!/usr/bin/env python3
"""Consume the standing Healer sovereign scheduler resident request."""
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
REQUEST_REL = Path("control/resident-execution-request.d/healer-sovereign-scheduler-001.json")
CONSUMPTION_REL = Path("receipts/sovereign-host/healer-sovereign-scheduler-request-consumption.latest.json")
CHECKPOINT_REL = Path("receipts/healer-sovereign-scheduler/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json")
TARGET_TASK = "SHWP-HEALER-SOVEREIGN-SCHEDULER-001"
TARGET_MODE = "TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
REUSABLE_REFRESH_ENTRYPOINT = Path("scripts/refresh_sovereign_worker_runtime_source_reusable.py")
NEUTRAL_SCHEDULER_REQUIRED = (
    Path("scripts/run_reusable_task_scheduler.py"),
    Path("data/reusable-task-scheduler-contract.json"),
)
NONSECRET_ENV = {
    "PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_HEALER_ROOT", "STEGVERSE_REPO_ROOTS_JSON", "STEGVERSE_TVC_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT", "STEGVERSE_HIL_INTR_ROUTE_CONFIG",
    "STEGVERSE_EVALUATOR_INTR_ROUTE_CONFIG", "STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_env(source: dict[str, str] | None = None) -> dict[str, str]:
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
        "standing_request": True,
        "recurrence": "EACH_ELIGIBLE_RESIDENT_SCHEDULER_CYCLE",
    }
    for key, value in expected.items():
        if request.get(key) != value:
            raise RuntimeError(f"Healer resident request {key} mismatch")
    if not isinstance(request.get("request_id"), str) or not request["request_id"].strip():
        raise RuntimeError("request_id missing")


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([x.strip() for x in stdout.splitlines() if x.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def resolve_source_root(source_root: Path, runtime_root: Path, values: dict[str, str]) -> tuple[Path | None, str]:
    """Keep canonical source distinct from mutable resident runtime."""
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    if source != runtime:
        return (source, "DISPATCHER_DISTINCT_SOURCE") if source.is_dir() else (None, "DISPATCHER_SOURCE_MISSING")

    raw = str(values.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT") or "").strip()
    if not raw:
        return None, "DISTINCT_SOURCE_ROOT_NOT_PROVIDED"
    candidate = Path(raw).expanduser().resolve()
    if candidate == runtime:
        return None, "SOURCE_ROOT_EQUALS_RUNTIME"
    if not candidate.is_dir():
        return None, "SOURCE_ROOT_NOT_MATERIALIZED"
    required = candidate / TARGET_ENTRYPOINT
    if not required.is_file():
        return None, "SOURCE_ROOT_INCOMPLETE"
    return candidate, "STEGVERSE_HEARTBEAT_SOURCE_ROOT"


def synchronize_standing_request(source: Path, runtime: Path) -> dict[str, Any]:
    """Exact-sync the non-authorizing standing request from already-local source.

    This is source transport only. The request cannot mint a claim, fence, credential,
    transition, publication state, or user-verification authority.
    """
    canonical = source / REQUEST_REL
    if not canonical.is_file():
        raise RuntimeError(f"canonical Healer standing request missing: {canonical}")
    canonical_doc = load_json(canonical)
    validate_request(canonical_doc)
    canonical_bytes = canonical.read_bytes()
    canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()

    resident = runtime / REQUEST_REL
    previous_hash = file_sha256(resident) if resident.is_file() else None
    copied = previous_hash != canonical_hash
    if copied:
        resident.parent.mkdir(parents=True, exist_ok=True)
        tmp = resident.with_name("." + resident.name + ".tmp")
        tmp.write_bytes(canonical_bytes)
        os.replace(tmp, resident)
    if not resident.is_file() or resident.read_bytes() != canonical_bytes:
        raise RuntimeError("Healer standing request exact-byte materialization failed")
    validate_request(load_json(resident))
    return {
        "state": "EXACT_CANONICAL_REQUEST_MATERIALIZED" if copied else "EXACT_CANONICAL_REQUEST_ALREADY_PRESENT",
        "request_ref": REQUEST_REL.as_posix(),
        "sha256": canonical_hash,
        "copied": copied,
        "request_granted_authority": False,
        "authority_effect": "NONE_SOURCE_TRANSPORT_ONLY",
    }


def ensure_neutral_scheduler_materialized(
    source: Path,
    runtime: Path,
    *,
    runner=subprocess.run,
    values: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Break the stale-runtime bootstrap loop before Healer delegates scheduling.

    The canonical resident worker refreshes this consumer before dispatch. If the
    resident runtime does not yet contain the neutral scheduler artifacts, invoke
    the already-registered reusable source-refresh adapter directly from the
    already-local canonical source. This grants no execution or transition authority.
    """
    missing_before = [rel.as_posix() for rel in NEUTRAL_SCHEDULER_REQUIRED if not (runtime / rel).is_file()]
    if not missing_before:
        return {
            "state": "NEUTRAL_SCHEDULER_ALREADY_MATERIALIZED",
            "attempted": False,
            "required_paths": [rel.as_posix() for rel in NEUTRAL_SCHEDULER_REQUIRED],
            "missing_before": [],
            "network_source_fetch_performed": False,
            "credential_read_or_acquired": False,
            "authority_effect": "NONE_SOURCE_MATERIALIZATION_ONLY",
        }

    adapter = source / REUSABLE_REFRESH_ENTRYPOINT
    if not adapter.is_file():
        raise RuntimeError(f"canonical reusable source-refresh adapter missing: {adapter}")
    env = clean_env(values)
    env["STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON"] = json.dumps(
        {"source_root": str(source), "runtime_root": str(runtime)},
        sort_keys=True,
        separators=(",", ":"),
    )
    completed = runner(
        [sys.executable, str(adapter)],
        cwd=source,
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=300,
    )
    refresh_receipt = parse_last_json(completed.stdout)
    missing_after = [rel.as_posix() for rel in NEUTRAL_SCHEDULER_REQUIRED if not (runtime / rel).is_file()]
    if completed.returncode != 0 or missing_after:
        raise RuntimeError("neutral reusable scheduler bootstrap materialization failed")
    if not isinstance(refresh_receipt, dict) or refresh_receipt.get("schema") != "stegverse.sovereign-worker-runtime-source-refresh/v1":
        raise RuntimeError("neutral scheduler bootstrap did not emit canonical source-refresh receipt")
    if refresh_receipt.get("network_fetch_performed") is not False or refresh_receipt.get("credential_read_or_acquired") is not False:
        raise RuntimeError("neutral scheduler bootstrap violated local-only source-refresh boundary")
    return {
        "state": "NEUTRAL_SCHEDULER_MATERIALIZED_FROM_LOCAL_CANONICAL_SOURCE",
        "attempted": True,
        "adapter_ref": REUSABLE_REFRESH_ENTRYPOINT.as_posix(),
        "required_paths": [rel.as_posix() for rel in NEUTRAL_SCHEDULER_REQUIRED],
        "missing_before": missing_before,
        "missing_after": missing_after,
        "returncode": completed.returncode,
        "refresh_receipt": refresh_receipt,
        "network_source_fetch_performed": False,
        "credential_read_or_acquired": False,
        "authority_effect": "NONE_SOURCE_MATERIALIZATION_ONLY",
    }



def _identity_observed(value: Any, claim_id: str, fencing_token: int, transition_id: str) -> bool:
    if isinstance(value, dict):
        same_task = value.get("task_id") in (None, TARGET_TASK)
        claim_match = value.get("claim_id") == claim_id
        fence_match = value.get("fencing_token") == fencing_token
        transition_match = value.get("transition_id") == transition_id
        if same_task and claim_match and fence_match:
            return True
        if same_task and transition_match and (claim_match or fence_match):
            return True
        return any(_identity_observed(item, claim_id, fencing_token, transition_id) for item in value.values())
    if isinstance(value, list):
        return any(_identity_observed(item, claim_id, fencing_token, transition_id) for item in value)
    return False


def custody_projected_checkpoint(source: Path, runtime: Path, execution_receipt: dict[str, Any] | None) -> dict[str, Any]:
    """Submit the exact fenced resident checkpoint through existing canonical Master Records custody."""
    path = runtime / CHECKPOINT_REL
    if not path.is_file():
        return {
            "state": "BOUNDARY",
            "reason": "PROJECTED_HEALER_CHECKPOINT_NOT_OBSERVED",
            "checkpoint_ref": CHECKPOINT_REL.as_posix(),
            "authority_effect": "NONE",
        }
    checkpoint = load_json(path)
    transition_id = checkpoint.get("transition_id")
    claim_id = checkpoint.get("claim_id")
    fencing_token = checkpoint.get("fencing_token")
    if (
        checkpoint.get("task_id") != TARGET_TASK
        or not isinstance(transition_id, str)
        or not transition_id
        or not isinstance(claim_id, str)
        or not claim_id
        or not isinstance(fencing_token, int)
    ):
        return {
            "state": "BOUNDARY",
            "reason": "PROJECTED_HEALER_CHECKPOINT_IDENTITY_INVALID",
            "checkpoint_ref": CHECKPOINT_REL.as_posix(),
            "authority_effect": "NONE",
        }
    if not isinstance(execution_receipt, dict) or not _identity_observed(
        execution_receipt, claim_id, fencing_token, transition_id
    ):
        return {
            "state": "BOUNDARY",
            "reason": "PROJECTED_HEALER_CHECKPOINT_FENCE_NOT_BOUND_TO_CURRENT_CYCLE",
            "checkpoint_ref": CHECKPOINT_REL.as_posix(),
            "transition_id": transition_id,
            "claim_id": claim_id,
            "fencing_token": fencing_token,
            "authority_effect": "NONE",
        }

    workers_root = source / "workers"
    if str(workers_root) not in sys.path:
        sys.path.insert(0, str(workers_root))
    from canonical_state_transition_custody import build_state_receipt, canonical_json, submit_state_receipt

    canonical_checkpoint = canonical_json(checkpoint).encode("utf-8")
    checkpoint_sha256 = hashlib.sha256(canonical_checkpoint).hexdigest()
    evidence = {
        "evidence_id": f"healer-fenced-checkpoint:{claim_id}:{fencing_token}",
        "evidence_type": "HEALER_FENCED_CHECKPOINT",
        "origin_transition_id": transition_id,
        "encoding": "canonical-json",
        "sha256": checkpoint_sha256,
        "content": checkpoint,
    }
    state_receipt = build_state_receipt(
        transition_id=transition_id,
        transition_sequence=int(checkpoint.get("transition_sequence") or 1),
        subject_or_correlation_id=TARGET_TASK,
        transition_outcome="OBSERVED",
        prior_state_ref_or_hash=f"worker-claim:{claim_id}:fence:{fencing_token}",
        resulting_state_ref_or_hash="sha256:" + checkpoint_sha256,
        governance_decision_ref_where_applicable=None,
        transition_evidence={
            "checkpoint_ref": CHECKPOINT_REL.as_posix(),
            "checkpoint_sha256": checkpoint_sha256,
            "claim_id": claim_id,
            "fencing_token": fencing_token,
            "worker_state": checkpoint.get("state"),
            "projected_after_fenced_process_adapter_allow": True,
        },
        required_evidence_manifest=[evidence],
        proof_scope="HEALER_FENCED_CHECKPOINT_PROJECTION_ONLY",
        proof_ceiling="OBSERVED_PROJECTED_CHECKPOINT_AND_MASTER_RECORDS_CUSTODY_ONLY",
    )
    result = submit_state_receipt(state_receipt)
    return {
        "state": result.get("state"),
        "reason": result.get("reason"),
        "checkpoint_ref": CHECKPOINT_REL.as_posix(),
        "checkpoint_sha256": checkpoint_sha256,
        "transition_id": transition_id,
        "transition_sequence": state_receipt["transition_sequence"],
        "claim_id": claim_id,
        "fencing_token": fencing_token,
        "required_evidence_validation_status": result.get("required_evidence_validation_status"),
        "reconstruction_status": result.get("reconstruction_status"),
        "receipt_sha256": result.get("receipt_sha256"),
        "reconstructed_receipt_sha256": result.get("reconstructed_receipt_sha256"),
        "master_record_ref": result.get("master_record_ref"),
        "custody_receipt_id": result.get("custody_receipt_id"),
        "authority_effect": "NONE_CUSTODY_RECONSTRUCTION_ONLY",
    }

def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run, env: dict[str, str] | None = None) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    runtime = runtime_root.expanduser().resolve()
    source, source_resolution = resolve_source_root(source_root, runtime_root, values)

    if source is None:
        request_path = runtime / REQUEST_REL
        if not request_path.is_file():
            return {
                "schema": "stegverse.healer-resident-request-consumption/v1",
                "state": "NO_REQUEST",
                "runtime_execution_attempted": False,
                "standing_request": True,
                "source_resolution": source_resolution,
                "retry_allowed": True,
                "authority_effect": "NONE",
            }
        request = load_json(request_path)
        validate_request(request)
        request_hash = stable_hash(request)
        receipt = {
            "schema": "stegverse.healer-resident-request-consumption/v1",
            "state": "ATTEMPT_RECORDED",
            "request_id": request["request_id"],
            "request_sha256": request_hash,
            "task_id": TARGET_TASK,
            "mode": TARGET_MODE,
            "standing_request": True,
            "recurrence": request["recurrence"],
            "source_resolution": source_resolution,
            "runtime_execution_attempted": False,
            "scheduler_cycle_completion_observed": False,
            "terminal_scheduler_completion_observed": False,
            "retry_allowed": True,
            "request_consumed": False,
            "request_granted_authority": False,
            "heartbeat_grants_execution_authority": False,
            "github_token_required": False,
            "github_token_runtime_authority": "NONE",
            "credential_authority": "TV/TVC",
            "credential_requirement": "NONE",
            "second_machine_required": False,
            "network_source_fetch_performed": False,
            "blocker": "DISTINCT_LOCAL_CANONICAL_SOURCE_REQUIRED",
            "authority_effect": "NONE_REQUEST_ONLY",
        }
        path = runtime / CONSUMPTION_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt

    request_materialization = synchronize_standing_request(source, runtime)
    scheduler_materialization = ensure_neutral_scheduler_materialized(source, runtime, runner=runner, values=values)
    request_path = runtime / REQUEST_REL
    request = load_json(request_path)
    validate_request(request)
    request_hash = stable_hash(request)

    # Execute the canonical source refresh bridge directly. Requiring a stale
    # runtime to already contain the current refresh bridge would recreate the
    # same source-refresh circularity this standing request exists to break.
    entrypoint = source / TARGET_ENTRYPOINT
    if not entrypoint.is_file():
        raise RuntimeError(f"canonical Healer resident execution entrypoint missing: {entrypoint}")

    command = [sys.executable, str(entrypoint), "--source-root", str(source), "--runtime-root", str(runtime), "--task-id", TARGET_TASK]
    completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, env=clean_env(values), timeout=1200)
    result = parse_last_json(completed.stdout)
    execution_result = result.get("execution_result") if isinstance(result, dict) else None
    transition = execution_result.get("transition_id") if isinstance(execution_result, dict) else None
    if transition is None and isinstance(result, dict):
        transition = result.get("transition_id")
    cycle_completed = transition == "HEALER_SOVEREIGN_SCHEDULER_COMPLETED"
    master_records = custody_projected_checkpoint(source, runtime, result if isinstance(result, dict) else None)
    custody_complete = (
        master_records.get("state") == "RECORDED"
        and master_records.get("reconstruction_status") == "PASS"
        and master_records.get("required_evidence_validation_status") == "PASS"
        and isinstance(master_records.get("receipt_sha256"), str)
        and master_records.get("receipt_sha256") == master_records.get("reconstructed_receipt_sha256")
    )

    receipt = {
        "schema": "stegverse.healer-resident-request-consumption/v1",
        "state": "CYCLE_COMPLETED" if cycle_completed and custody_complete else ("MASTER_RECORDS_BOUNDARY" if not custody_complete else "ATTEMPT_RECORDED"),
        "request_id": request["request_id"],
        "request_sha256": request_hash,
        "request_materialization": request_materialization,
        "neutral_scheduler_materialization": scheduler_materialization,
        "task_id": TARGET_TASK,
        "mode": TARGET_MODE,
        "standing_request": True,
        "recurrence": request["recurrence"],
        "source_root": str(source),
        "runtime_root": str(runtime),
        "source_resolution": source_resolution,
        "source_runtime_separated": source != runtime,
        "canonical_refresh_entrypoint": str(entrypoint),
        "command": command,
        "execution_returncode": completed.returncode,
        "execution_result_observed": isinstance(result, dict),
        "execution_result": result,
        "master_records_checkpoint_custody": master_records,
        "master_records_checkpoint_identity": {
            "transition_id": master_records.get("transition_id"),
            "receipt_sha256": master_records.get("receipt_sha256"),
            "master_record_ref": master_records.get("master_record_ref"),
        },
        "master_records_checkpoint_custody_complete": custody_complete,
        "runtime_execution_attempted": True,
        "scheduler_cycle_completion_observed": cycle_completed,
        "terminal_scheduler_completion_observed": False,
        "retry_allowed": True,
        "request_consumed": False,
        "request_granted_authority": False,
        "heartbeat_grants_execution_authority": False,
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
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
