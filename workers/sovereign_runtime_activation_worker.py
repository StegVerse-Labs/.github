#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd().resolve()
EXPECTED_TASK = "SHWP-DURABLE-RUNTIME-ACTIVATION"
RECEIPT_ROOT = (ROOT / "receipts" / "sovereign-runtime-activation").resolve()
TRANSITION_RECEIPT = (ROOT / "receipts" / "heartbeat-transition-continuity" / "latest.json").resolve()
TRANSITION_CONTRACT = (ROOT / "management" / "SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json").resolve()
CANDIDATE_RESIDENT_EVIDENCE = [
    Path("/var/lib/stegverse/heartbeat/activation.latest.json"),
    Path.home() / ".stegverse" / "heartbeat" / "activation.latest.json",
    ROOT / "runtime" / "sovereign" / "activation.latest.json",
]
NODE_MARKERS = [Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json"]
THIRD_PARTY_ENV_VARS = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
RESIDENT_PREDICATES = [
    "runtime_materialized", "native_service_active", "continuous_runtime_live",
    "heartbeat_epoch_advanced", "worker_coordination_checkpoint_observed",
    "controlled_restart_observed", "epoch_and_generation_non_regressing",
    "no_duplicate_claim_or_fence", "state_reconstruction_pass",
]
SAFE_EXEC_ENV = {
    "HOME", "USER", "LOGNAME", "SHELL", "PATH", "PYTHONPATH", "LANG", "LC_ALL", "TMPDIR",
    "XDG_CONFIG_HOME", "XDG_STATE_HOME", "LOCALAPPDATA", "UID", "STEGVERSE_HEARTBEAT_ROOT",
}


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def third_party_hosted_environment(env: dict[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return any(truthy(values.get(name)) for name in THIRD_PARTY_ENV_VARS)


def clean_exec_env(env: dict[str, str] | None = None) -> dict[str, str]:
    values = os.environ if env is None else env
    return {name: values[name] for name in SAFE_EXEC_ENV if values.get(name)}


def load_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def _active_leases(control_plane: dict) -> list[dict]:
    rows = (((control_plane.get("worker_coordination") or {}).get("active_leases")) or [])
    return [row for row in rows if isinstance(row, dict)]


def no_duplicate_claim_or_fence(control_plane: dict) -> bool:
    rows = _active_leases(control_plane)
    claims = [row.get("claim_id") for row in rows if row.get("claim_id")]
    fences = [row.get("fencing_token") for row in rows if isinstance(row.get("fencing_token"), int)]
    instances = [row.get("worker_instance_id") for row in rows if row.get("worker_instance_id")]
    return (
        len(claims) == len(set(claims))
        and len(fences) == len(set(fences))
        and len(instances) == len(set(instances))
    )


def state_transition_status() -> dict:
    transition = load_json(TRANSITION_RECEIPT) or {}
    carrier = load_json(ROOT / "control" / "heartbeat-carrier-runtime-state.json") or {}
    worker_state = load_json(ROOT / "control" / "worker-runtime-state.json") or {}
    control_plane = load_json(ROOT / "control" / "worker-control-plane-coordination.json") or {}
    legacy = load_json(ROOT / "control" / "heartbeat-state.json") or {}

    target_epoch = transition.get("carrier_epoch_after")
    observed_epoch = worker_state.get("last_observed_carrier_epoch")
    target_valid = isinstance(target_epoch, int) and target_epoch >= 30
    worker_observed = isinstance(observed_epoch, int) and target_valid and observed_epoch >= target_epoch
    predicates = {
        "carrier_transition_receipt_complete": transition.get("state") == "CARRIER_TRANSITION_COMPLETE",
        "legacy_hb29_unchanged": int(legacy.get("epoch", -1)) == 29 and (transition.get("predicates") or {}).get("legacy_hb29_unchanged") is True,
        "carrier_epoch_at_least_30": target_valid and int(carrier.get("epoch", -1)) >= target_epoch,
        "carrier_generation_non_regressing": (transition.get("predicates") or {}).get("carrier_generation_non_regressing") is True,
        "worker_runtime_checkpoint_observed_at_or_after_carrier_epoch": worker_observed,
        "worker_control_plane_observed": control_plane.get("schema") == "stegverse.worker-control-plane-coordination/v1",
        "no_duplicate_claim_or_fence": bool(control_plane) and no_duplicate_claim_or_fence(control_plane),
        "state_reconstruction_pass": (transition.get("predicates") or {}).get("state_reconstruction_pass") is True and worker_observed,
    }
    return {
        "continuity_model": "STATE_TRANSITION_CONTINUITY",
        "transition_receipt_ref": "receipts/heartbeat-transition-continuity/latest.json",
        "target_carrier_epoch": target_epoch,
        "worker_observed_carrier_epoch": observed_epoch,
        "predicates": predicates,
        "complete": all(predicates.values()),
        "always_on_external_host_required": False,
        "wall_clock_continuous_process_required": False,
        "resident_native_supervision_required": False,
        "physical_additional_machine_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
    }


def execute_state_transition_solution() -> dict:
    result = {
        "attempted": False,
        "entrypoint": "scripts/advance_heartbeat_transition.py",
        "receipt_ref": "receipts/heartbeat-transition-continuity/latest.json",
        "physical_additional_machine_required": False,
        "always_on_external_host_required": False,
        "wall_clock_continuous_process_required": False,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_forwarded": False,
        "returncode": None,
        "reason": None,
    }
    if third_party_hosted_environment():
        result["reason"] = "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_TRANSITION_EVIDENCE"
        return result
    if not TRANSITION_CONTRACT.is_file():
        result["reason"] = "STATE_TRANSITION_CONTINUITY_CONTRACT_MISSING"
        return result
    producer = ROOT / "scripts" / "advance_heartbeat_transition.py"
    if not producer.is_file():
        result["reason"] = "STATE_TRANSITION_PRODUCER_MISSING"
        return result

    result["attempted"] = True
    completed = subprocess.run(
        [sys.executable, str(producer), "--root", str(ROOT), "--receipt-path", str(TRANSITION_RECEIPT)],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
        env=clean_exec_env(),
    )
    result["returncode"] = completed.returncode
    receipt = load_json(TRANSITION_RECEIPT) or {}
    result["state"] = receipt.get("state")
    result["carrier_epoch_before"] = receipt.get("carrier_epoch_before")
    result["carrier_epoch_after"] = receipt.get("carrier_epoch_after")
    result["reason"] = receipt.get("reason") or ("STATE_TRANSITION_COMPLETE" if completed.returncode == 0 else "STATE_TRANSITION_EXECUTION_FAILED")
    return result


def resident_supervision_requested() -> bool:
    return truthy(os.environ.get("STEGVERSE_ENABLE_RESIDENT_HEARTBEAT_SUPERVISION"))


def default_runtime_root(env: dict[str, str] | None = None) -> Path:
    values = os.environ if env is None else env
    override = values.get("STEGVERSE_HEARTBEAT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        base = Path(values.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(values.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state")))
    return (base / "stegverse" / "heartbeat-runtime").resolve()


def optional_resident_supervision() -> dict:
    """Optional stronger evidence; never a heartbeat-continuity prerequisite."""
    result = {
        "attempted": False,
        "required_for_continuity": False,
        "physical_additional_machine_required": False,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_forwarded": False,
    }
    if not resident_supervision_requested():
        result["reason"] = "RESIDENT_SUPERVISION_NOT_REQUESTED"
        return result
    if third_party_hosted_environment():
        result["reason"] = "THIRD_PARTY_HOST_REJECTED"
        return result
    bootstrap = ROOT / "scripts" / "bootstrap_sovereign_runtime.py"
    if not bootstrap.is_file():
        result["reason"] = "OPTIONAL_RESIDENT_BOOTSTRAP_MISSING"
        return result
    result["attempted"] = True
    receipt_path = Path.home() / ".stegverse" / "heartbeat" / "bootstrap.latest.json"
    completed = subprocess.run(
        [sys.executable, str(bootstrap), "--source-root", str(ROOT), "--runtime-root", str(default_runtime_root())],
        capture_output=True,
        text=True,
        timeout=420,
        check=False,
        env=clean_exec_env(),
    )
    receipt = load_json(receipt_path) or {}
    result["returncode"] = completed.returncode
    result["state"] = receipt.get("state")
    result["reason"] = receipt.get("reason")
    proof = None
    for path in CANDIDATE_RESIDENT_EVIDENCE:
        if path.is_file():
            proof = load_json(path)
            if proof:
                result["evidence_path"] = str(path)
                break
    result["all_resident_predicates_pass"] = bool(proof) and all(proof.get(name) is True for name in RESIDENT_PREDICATES)
    return result


def unresolved_transition_contract(solution_attempt: dict | None = None) -> dict:
    return {
        "dependency_class": "EXECUTION_OPPORTUNITY",
        "trigger_type": "CONDITIONAL_CONSTRAINT",
        "problem_statement": "The bounded v12 state-transition producer did not produce a valid successor on this execution opportunity. Another physical machine and an always-on external host are not required.",
        "solution_required": True,
        "resolvable_by_current_worker": True,
        "escalation_target": "SOVEREIGN_RUNTIME_OWNER",
        "required_capabilities": ["bounded_process_execution", "writable_state", "durable_state_reconstruction"],
        "observed_reason": (solution_attempt or {}).get("reason"),
        "physical_additional_machine_required": False,
        "always_on_external_host_required": False,
        "workaround_candidates": [
            "Retry scripts/advance_heartbeat_transition.py on the next admitted StegVerse execution opportunity associated with the current iPhone carrier policy.",
            "Repair any exact repository-local v12 transition defect identified by the fail-closed receipt; do not search for another machine or restore a hosted runtime dependency."
        ],
        "next_solution_action": "EXECUTE_BOUNDED_V12_STATE_TRANSITION",
        "completion_evidence": [
            "receipts/heartbeat-transition-continuity/latest.json is CARRIER_TRANSITION_COMPLETE",
            "control/heartbeat-carrier-runtime-state.json is HB30 or later",
            "legacy control/heartbeat-state.json remains HB29",
            "the independent WorkerCoordinator later observes the successor without duplicate claim/fence"
        ],
    }


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    execution = (invocation.get("handoff") or {}).get("execution") or {}
    timing = task.get("heartbeat_timing") or {}
    claim_id, fence = task.get("claim_id"), timing.get("fencing_token")
    if not isinstance(epoch, int) or task.get("task_id") != EXPECTED_TASK:
        return 3
    if not claim_id or not isinstance(fence, int):
        return 4
    required_caps = set(execution.get("required_capabilities") or [])
    if not {"runtime_observation", "durable_state_reconstruction", "bounded_repository_mutation"}.issubset(required_caps):
        return 5
    allowed_paths = set(execution.get("allowed_paths") or [])
    if "receipts/sovereign-runtime-activation/**" not in allowed_paths or "receipts/heartbeat-transition-continuity/**" not in allowed_paths:
        return 6

    status_before = state_transition_status()
    solution_attempt = {"attempted": False, "reason": "STATE_TRANSITION_ALREADY_COMPLETE"}
    if not status_before["predicates"]["carrier_transition_receipt_complete"]:
        solution_attempt = execute_state_transition_solution()

    status_after = state_transition_status()
    resident = optional_resident_supervision()

    if status_after["complete"]:
        transition = "SOVEREIGN_RUNTIME_STATE_TRANSITION_VERIFIED"
        state = "COMPLETED"
        expected = None
        blocker = None
    elif status_after["predicates"]["carrier_transition_receipt_complete"]:
        transition = "SOVEREIGN_CARRIER_TRANSITION_VERIFIED"
        state = "ACTIVE"
        expected = "SOVEREIGN_WORKER_CHECKPOINT_OBSERVATION"
        blocker = {
            "dependency_class": "INTERNAL_CHECKPOINT",
            "problem_statement": "HB30+ carrier transition is persisted. The independent WorkerCoordinator must observe that successor on a subsequent admitted tick before G18 closes.",
            "solution_required": True,
            "physical_additional_machine_required": False,
            "always_on_external_host_required": False,
            "next_solution_action": "ALLOW_NEXT_WORKER_RUNTIME_TICK_TO_OBSERVE_PERSISTED_CARRIER_SUCCESSOR"
        }
    else:
        transition = "SOVEREIGN_RUNTIME_RESOLUTION_ESCALATION_REQUIRED"
        state = "BLOCKED"
        expected = "EXECUTE_BOUNDED_V12_STATE_TRANSITION"
        blocker = unresolved_transition_contract(solution_attempt)

    receipt = {
        "schema": "stegverse.sovereign-runtime-worker-receipt/v0.7",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "heartbeat_epoch_at_invocation": epoch,
        "fencing_token": fence,
        "transition_id": transition,
        "state": state,
        "continuity_model": "STATE_TRANSITION_CONTINUITY",
        "state_transition_status": status_after,
        "solution_attempt": solution_attempt,
        "resident_supervision": resident,
        "state_transition_entrypoint": "scripts/advance_heartbeat_transition.py",
        "state_transition_contract_ref": "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json",
        "resident_bootstrap_entrypoint": "scripts/bootstrap_sovereign_runtime.py",
        "resident_supervision_required": False,
        "physical_additional_machine_required": False,
        "always_on_external_host_required": False,
        "wall_clock_continuous_process_required": False,
        "third_party_runtime_required": False,
        "third_party_dependency_is_blocker": False,
        "blocker_policy_ref": "control/blocker-resolution-policy.json",
        "blocker": blocker,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "non_tv_tvc_secret_or_token_forwarded": False,
        "authority_effect": "bounded_state_transition_activation_under_existing_handoff",
        "completed": state == "COMPLETED",
    }
    atomic_write(RECEIPT_ROOT / f"{EXPECTED_TASK}.json", receipt)

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 5,
        "expected_next_transition": expected,
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 1,
        "checkpoint_ref": f"receipts/sovereign-runtime-activation/{EXPECTED_TASK}.json",
        "evidence_refs": [
            f"receipts/sovereign-runtime-activation/{EXPECTED_TASK}.json",
            "receipts/heartbeat-transition-continuity/latest.json",
            "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json",
            "management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json",
            "scripts/advance_heartbeat_transition.py",
            "heartbeat_runtime/engine_v12.py",
            "heartbeat_runtime/worker_runtime.py",
            "StegVerse-Labs/.github#12",
            "StegVerse-Labs/.github#59",
            "StegVerse-Labs/.github#65"
        ],
        "blocker": blocker,
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 2 if solution_attempt.get("attempted") else 1,
            "external_cost_usd": 0,
            "task_class": "sovereign_runtime_activation"
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
