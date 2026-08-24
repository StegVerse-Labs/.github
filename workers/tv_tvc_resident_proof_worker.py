#!/usr/bin/env python3
"""Execute the already-admitted TV/TVC resident proof without receiving credential bytes."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
TASK_ID = "SHWP-TV-TVC-RESIDENT-PROOF-001"
TV_SHA = "e0d102a8c187c059754eced9ac017fdb056a0222"
TVC_MIN_SHA = "e4bef703b4d6ccad858459ec502637c598948c42"
RECEIPT_ROOT = (ROOT / "receipts" / "tv-tvc-resident-proof").resolve()
ALLOWED_CAPABILITIES = {
    "runtime_observation",
    "bounded_process_execution",
    "durable_state_reconstruction",
    "tv_tvc_resident_operational_proof_activation",
}
ALLOWED_PATHS = ["receipts/tv-tvc-resident-proof/**"]
ALLOWED_SERVICES = ["stegtvc-tv-artifact-exchange@.service"]


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def _response(state: str, transition_id: str, checkpoint: str, *, next_epoch: int | None = None) -> dict[str, Any]:
    terminal = state == "COMPLETED"
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition_id,
        "transition_sequence": 1,
        "expected_next_transition": None if terminal else "TV_TVC_RESIDENT_PROOF_RECHECK",
        "expected_next_earliest_epoch": None if terminal else next_epoch,
        "expected_next_latest_epoch": None if terminal else next_epoch,
        "checkpoint_ref": checkpoint,
        "evidence_refs": [checkpoint],
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "tv_tvc_resident_operational_proof",
        },
    }


def _git_head(root: Path) -> str:
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return result.stdout.strip().lower()


def _tvc_contains_required_source(root: Path) -> bool:
    result = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", TVC_MIN_SHA, "HEAD"], capture_output=True, text=True)
    return result.returncode == 0


def _parse_dispatcher(stdout: str) -> dict[str, Any]:
    value = json.loads(stdout)
    if not isinstance(value, dict):
        raise ValueError("dispatcher response must be an object")
    return value


def _hosted_runtime_observed() -> bool:
    flags = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES")
    return any(str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes"} for name in flags)


def _blocked_receipt(*, epoch: int, claim_id: str, fence: int, worker_id: str | None, worker_instance_id: str | None, reason: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema": "stegverse.tv-tvc-resident-proof-worker-receipt/v0.1",
        "task_id": TASK_ID,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "worker_id": worker_id,
        "worker_instance_id": worker_instance_id,
        "state": "BLOCKED",
        "reason": reason,
        "evidence": evidence or {},
        "credential_authority": "TV/TVC",
        "credential_value_exposed": False,
        "consumer_secret_received": False,
        "github_token_runtime_authority": False,
        "g18_authority_reused": False,
        "source_fetch_performed": False,
    }


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception as exc:
        print(f"invalid invocation: {exc}", file=sys.stderr)
        return 2
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        print("unsupported invocation schema", file=sys.stderr)
        return 3

    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or epoch < 0 or task.get("task_id") != TASK_ID:
        print("invocation outside admitted TV/TVC task", file=sys.stderr)
        return 4
    execution = handoff.get("execution") or {}
    if set(execution.get("required_capabilities") or []) != ALLOWED_CAPABILITIES:
        print("required capability mismatch", file=sys.stderr)
        return 5
    if execution.get("allowed_paths") != ALLOWED_PATHS or execution.get("allowed_services") != ALLOWED_SERVICES:
        print("execution boundary mismatch", file=sys.stderr)
        return 6
    authority = handoff.get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC" or authority.get("g18_authority_inherited") is not False:
        print("authority boundary mismatch", file=sys.stderr)
        return 7

    claim_id = task.get("claim_id")
    worker_id = task.get("worker_id")
    worker_instance_id = task.get("worker_instance_id")
    fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        print("fresh fenced claim required", file=sys.stderr)
        return 8

    checkpoint = f"receipts/tv-tvc-resident-proof/{TASK_ID}.json"
    receipt_path = (ROOT / checkpoint).resolve()
    if RECEIPT_ROOT not in receipt_path.parents:
        print("receipt path escaped admitted namespace", file=sys.stderr)
        return 9
    if receipt_path.exists():
        prior = json.loads(receipt_path.read_text(encoding="utf-8"))
        if prior.get("claim_id") != claim_id or prior.get("fencing_token") != fence:
            print("existing receipt belongs to a different claim/fence", file=sys.stderr)
            return 10
        if prior.get("state") == "COMPLETED":
            json.dump(_response("COMPLETED", "TV_TVC_RESIDENT_OPERATIONAL_PROOF_ACTIVATED", checkpoint), sys.stdout, sort_keys=True)
            sys.stdout.write("\n")
            return 0

    def block(reason: str, evidence: dict[str, Any] | None = None) -> int:
        receipt = _blocked_receipt(epoch=epoch, claim_id=claim_id, fence=fence, worker_id=worker_id, worker_instance_id=worker_instance_id, reason=reason, evidence=evidence)
        atomic_write(receipt_path, receipt)
        json.dump(_response("BLOCKED", "TV_TVC_RESIDENT_PROOF_BLOCKED", checkpoint, next_epoch=epoch + 1), sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if _hosted_runtime_observed():
        return block("HOSTED_RUNTIME_NOT_AUTHORIZED")

    tv_value = os.environ.get("STEGVERSE_TV_ROOT", "").strip()
    tvc_value = os.environ.get("STEGVERSE_TVC_ROOT", "").strip()
    if not tv_value or not tvc_value:
        return block("LOCAL_TV_TVC_ROOTS_NOT_DECLARED")
    tv_root = Path(tv_value).expanduser().resolve()
    tvc_root = Path(tvc_value).expanduser().resolve()
    required_tv = [tv_root / "scripts/tv_run_resident_operational_proof.py", tv_root / "docs/TV_OPERATIONAL_PROOF_SCHEMA.json"]
    required_tvc = [tvc_root / "tools/task_dispatcher.py", tvc_root / "tv_resident_operational_proof_task.py", tvc_root / "scripts/activate_tv_resident_operational_proof.py"]
    if not all(path.is_file() for path in required_tv):
        return block("LOCAL_TV_SOURCE_INCOMPLETE")
    if not all(path.is_file() for path in required_tvc):
        return block("LOCAL_TVC_SOURCE_INCOMPLETE")
    try:
        tv_head = _git_head(tv_root)
    except Exception as exc:
        return block("LOCAL_TV_GIT_IDENTITY_UNAVAILABLE", {"error_type": type(exc).__name__})
    if tv_head != TV_SHA:
        return block("TV_SOURCE_SHA_MISMATCH", {"expected": TV_SHA, "observed": tv_head})
    if not _tvc_contains_required_source(tvc_root):
        return block("TVC_ROOTLESS_ACTIVATION_SOURCE_NOT_PRESENT", {"required_ancestor": TVC_MIN_SHA})

    child_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(Path.home())),
        "STEGVERSE_TV_SERVICE_MANAGER": "user",
        "STEGTV_TV_CREDENTIAL_MIGRATION_ACTIVATION_AUTHORITY": "TV/TVC",
        "STEGTV_TV_REPO_ROOT": str(tv_root),
    }
    for name in ("XDG_STATE_HOME", "XDG_CONFIG_HOME"):
        value = os.environ.get(name)
        if value:
            child_env[name] = value

    dispatcher = [sys.executable, str(tvc_root / "tools/task_dispatcher.py")]
    preflight = subprocess.run(dispatcher + ["tvc.tv_resident_operational_proof.preflight"], cwd=str(tvc_root), env=child_env, capture_output=True, text=True)
    try:
        preflight_json = _parse_dispatcher(preflight.stdout)
    except Exception as exc:
        return block("TVC_PREFLIGHT_RESPONSE_INVALID", {"returncode": preflight.returncode, "error_type": type(exc).__name__})
    if preflight.returncode == 2 or preflight_json.get("status") == "blocked":
        result = preflight_json.get("result") or {}
        return block("TVC_PREFLIGHT_BLOCKED", {"reason": result.get("reason")})
    if preflight.returncode != 0 or preflight_json.get("status") != "ok":
        return block("TVC_PREFLIGHT_FAILED", {"returncode": preflight.returncode})
    if (preflight_json.get("result") or {}).get("state") != "READY_FOR_TV_TVC_RESIDENT_ACTIVATION":
        return block("TVC_PREFLIGHT_NOT_READY")

    activation = subprocess.run(dispatcher + ["tvc.tv_resident_operational_proof.activate"], cwd=str(tvc_root), env=child_env, capture_output=True, text=True)
    try:
        activation_json = _parse_dispatcher(activation.stdout)
    except Exception as exc:
        return block("TVC_ACTIVATION_RESPONSE_INVALID", {"returncode": activation.returncode, "error_type": type(exc).__name__})
    if activation.returncode == 2 or activation_json.get("status") == "blocked":
        result = activation_json.get("result") or {}
        detail = result.get("evidence") or {}
        activation_result = detail.get("activation_result") or {}
        return block("TVC_ACTIVATION_BLOCKED", {"reason": activation_result.get("reason") or result.get("reason")})
    result = activation_json.get("result") or {}
    safe = (
        activation.returncode == 0
        and activation_json.get("status") == "ok"
        and result.get("state") == "TV_TVC_RESIDENT_OPERATIONAL_PROOF_ACTIVATED"
        and result.get("runtime_execution_observed") is True
        and result.get("credential_value_exposed") is False
        and result.get("consumer_secret_received") is False
        and isinstance(result.get("receipt_path"), str)
        and bool(result.get("receipt_path"))
        and isinstance(result.get("proof_sha256"), str)
        and len(result.get("proof_sha256")) == 64
    )
    if not safe:
        return block("TVC_ACTIVATION_COMPLETION_NOT_PROVEN", {"returncode": activation.returncode, "dispatcher_status": activation_json.get("status"), "result_state": result.get("state")})

    receipt = {
        "schema": "stegverse.tv-tvc-resident-proof-worker-receipt/v0.1",
        "task_id": TASK_ID,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "worker_id": worker_id,
        "worker_instance_id": worker_instance_id,
        "state": "COMPLETED",
        "transition_id": "TV_TVC_RESIDENT_OPERATIONAL_PROOF_ACTIVATED",
        "tv_source_sha": TV_SHA,
        "tvc_required_source_ancestor": TVC_MIN_SHA,
        "service_manager": "systemd-user",
        "runtime_receipt_path": result["receipt_path"],
        "proof_sha256": result["proof_sha256"],
        "runtime_execution_observed": True,
        "credential_authority": "TV/TVC",
        "credential_value_exposed": False,
        "consumer_secret_received": False,
        "github_token_runtime_authority": False,
        "g18_authority_reused": False,
        "source_fetch_performed": False,
    }
    atomic_write(receipt_path, receipt)
    json.dump(_response("COMPLETED", "TV_TVC_RESIDENT_OPERATIONAL_PROOF_ACTIVATED", checkpoint), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
