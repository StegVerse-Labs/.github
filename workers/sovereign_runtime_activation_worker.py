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
BOOTSTRAP = (ROOT / "scripts" / "bootstrap_sovereign_runtime.py").resolve()
REQUIRED_PREDICATES = (
    "runtime_materialized",
    "native_service_active",
    "continuous_runtime_live",
    "heartbeat_epoch_advanced",
    "worker_coordination_checkpoint_observed",
    "worker_task_capable_cycle_observed",
    "controlled_restart_observed",
    "epoch_and_generation_non_regressing",
    "no_duplicate_claim_or_fence",
    "state_reconstruction_pass",
)
SAFE_EXEC_ENV = {
    "HOME", "USER", "LOGNAME", "SHELL", "PATH", "PYTHONPATH", "LANG", "LC_ALL", "TMPDIR",
    "XDG_CONFIG_HOME", "XDG_STATE_HOME", "LOCALAPPDATA", "UID",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
}
THIRD_PARTY_ENV_VARS = (
    "GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS",
)


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        name = handle.name
    os.replace(name, path)


def load_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def third_party_hosted_environment(env: dict[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return any(truthy(values.get(name)) for name in THIRD_PARTY_ENV_VARS)


def clean_exec_env(env: dict[str, str] | None = None) -> dict[str, str]:
    values = os.environ if env is None else env
    return {name: values[name] for name in SAFE_EXEC_ENV if values.get(name)}


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


def default_node_marker() -> Path:
    return (Path.home() / ".stegverse" / "node.json").resolve()


def default_proof_path() -> Path:
    return (Path.home() / ".stegverse" / "heartbeat" / "activation.latest.json").resolve()


def default_bootstrap_receipt() -> Path:
    return (Path.home() / ".stegverse" / "heartbeat" / "bootstrap.latest.json").resolve()


def all_activation_predicates_pass(proof: dict | None) -> bool:
    return bool(
        proof
        and proof.get("all_predicates_pass") is True
        and all(proof.get(name) is True for name in REQUIRED_PREDICATES)
    )


def execute_v13_self_bootstrap() -> dict:
    runtime_root = default_runtime_root()
    proof_path = default_proof_path()
    bootstrap_receipt = default_bootstrap_receipt()
    result = {
        "attempted": False,
        "entrypoint": "scripts/bootstrap_sovereign_runtime.py",
        "runtime_root": str(runtime_root),
        "proof_path": str(proof_path),
        "bootstrap_receipt_ref": str(bootstrap_receipt),
        "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        "worker_runtime": "heartbeat_runtime.worker_runtime.WorkerCoordinator",
        "continuity_model": "INDEPENDENT_OSCILLATOR_CONTINUITY",
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "heartbeat_dependency": False,
        "physical_additional_machine_required": False,
        "always_on_external_host_required": False,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_forwarded": False,
        "returncode": None,
        "state": None,
        "reason": None,
    }
    if third_party_hosted_environment():
        result["reason"] = "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE"
        return result
    if not BOOTSTRAP.is_file():
        result["reason"] = "CANONICAL_V13_BOOTSTRAP_MISSING"
        return result

    result["attempted"] = True
    command = [
        sys.executable,
        str(BOOTSTRAP),
        "--source-root", str(ROOT),
        "--runtime-root", str(runtime_root),
        "--node-marker", str(default_node_marker()),
        "--proof-path", str(proof_path),
        "--receipt-path", str(bootstrap_receipt),
        "--skip-post-bootstrap-stegfin",
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=480,
        check=False,
        env=clean_exec_env(),
    )
    result["returncode"] = completed.returncode
    bootstrap = load_json(bootstrap_receipt) or {}
    proof = load_json(proof_path) or {}
    result["state"] = bootstrap.get("state")
    result["reason"] = bootstrap.get("reason") or (
        "SOVEREIGN_RUNTIME_SELF_BOOTSTRAP_VERIFIED"
        if completed.returncode == 0 else
        "SOVEREIGN_RUNTIME_SELF_BOOTSTRAP_INCOMPLETE"
    )
    result["node_declaration_ref"] = bootstrap.get("node_declaration_ref")
    result["node_eligibility"] = bootstrap.get("node_eligibility")
    result["activation_proof_observed"] = bool(proof)
    result["activation_all_predicates_pass"] = all_activation_predicates_pass(proof)
    result["missing_predicates"] = [
        name for name in REQUIRED_PREDICATES if proof.get(name) is not True
    ]
    result["proof_schema"] = proof.get("schema")
    return result


def blocker_for(attempt: dict) -> dict:
    reason = attempt.get("reason")
    hosted = reason == "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE"
    return {
        "trigger_type": "CONDITIONAL_CONSTRAINT",
        "dependency_class": "PHYSICAL_RESOURCE_SOVEREIGN_NODE_ELIGIBILITY",
        "problem_statement": (
            "The current execution surface has not produced the canonical deployment-local v13 sovereign-runtime activation proof."
        ),
        "solution_required": True,
        "resolvable_by_current_worker": not hosted,
        "escalation_target": "SOVEREIGN_RUNTIME_OWNER",
        "required_capabilities": [
            "runtime_observation",
            "continuous_process_execution",
            "durable_state_reconstruction",
        ],
        "observed_reason": reason,
        "physical_additional_machine_required": False,
        "always_on_external_host_required": False,
        "heartbeat_activation_blocked": False,
        "workaround_candidates": [
            "Run the existing v13 self-bootstrap on the current non-hosted StegVerse deployment-local surface; it derives the v0.4 node declaration automatically when canonical source and writable durable state are present.",
            "If the current surface cannot satisfy canonical v13 local eligibility, component authority may select another already-admitted StegVerse-owned/federated sovereign surface without treating a second machine as a default requirement.",
        ],
        "next_solution_action": "EXECUTE_CANONICAL_V13_SOVEREIGN_RUNTIME_SELF_BOOTSTRAP",
        "completion_evidence": [
            "stegverse.sovereign-runtime-activation-proof/v1 exists on the deployment-local sovereign surface",
            "all required activation predicates are true, including worker_task_capable_cycle_observed",
            "canonical carrier runtime is heartbeat_runtime.engine_v13.HeartbeatRuntime",
            "WorkerCoordinator task-capable lifecycle evidence is observed",
            "no duplicate claim/fence is introduced",
            "TV/TVC remains sole credential authority",
        ],
    }


def main() -> int:
    invocation = json.load(sys.stdin)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return 2
    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    execution = handoff.get("execution") or {}
    timing = task.get("heartbeat_timing") or {}
    claim_id = task.get("claim_id")
    fence = timing.get("fencing_token")

    if not isinstance(epoch, int) or task.get("task_id") != EXPECTED_TASK:
        return 3
    if not claim_id or not isinstance(fence, int):
        return 4
    required_caps = set(execution.get("required_capabilities") or [])
    if not {
        "runtime_observation",
        "continuous_process_execution",
        "durable_state_reconstruction",
        "bounded_repository_mutation",
    }.issubset(required_caps):
        return 5
    allowed_paths = set(execution.get("allowed_paths") or [])
    if "receipts/sovereign-runtime-activation/**" not in allowed_paths:
        return 6

    attempt = execute_v13_self_bootstrap()
    completed = (
        attempt.get("state") == "COMPLETE"
        and attempt.get("activation_all_predicates_pass") is True
    )

    if completed:
        state = "COMPLETED"
        transition = "SOVEREIGN_RUNTIME_ACTIVATION_VERIFIED"
        expected = None
        blocker = None
    elif attempt.get("state") in {"RETRY", "REVIEW_REQUIRED"}:
        state = "ACTIVE"
        transition = (
            "SOVEREIGN_RUNTIME_INSTALLATION_RETRY_REQUIRED"
            if attempt.get("state") == "RETRY"
            else "SOVEREIGN_RUNTIME_PROOF_REVIEW_REQUIRED"
        )
        expected = "SOVEREIGN_RUNTIME_ACTIVATION_VERIFIED"
        blocker = blocker_for(attempt)
    else:
        state = "BLOCKED"
        transition = "SOVEREIGN_RUNTIME_ELIGIBLE_SURFACE_REQUIRED"
        expected = "EXECUTE_CANONICAL_V13_SOVEREIGN_RUNTIME_SELF_BOOTSTRAP"
        blocker = blocker_for(attempt)

    receipt = {
        "schema": "stegverse.sovereign-runtime-worker-receipt/v0.8",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "heartbeat_epoch_at_invocation": epoch,
        "fencing_token": fence,
        "state": state,
        "transition_id": transition,
        "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        "worker_runtime": "heartbeat_runtime.worker_runtime.WorkerCoordinator",
        "continuity_model": "INDEPENDENT_OSCILLATOR_CONTINUITY",
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "heartbeat_dependency": False,
        "bootstrap_attempt": attempt,
        "physical_additional_machine_required": False,
        "always_on_external_host_required": False,
        "third_party_runtime_required": False,
        "third_party_dependency_is_blocker": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "non_tv_tvc_secret_or_token_forwarded": False,
        "blocker_policy_ref": "control/blocker-resolution-policy.json",
        "blocker": blocker,
        "completed": completed,
        "authority_effect": "bounded_native_runtime_activation_under_existing_g18_handoff",
    }
    receipt_path = RECEIPT_ROOT / f"{EXPECTED_TASK}.json"
    atomic_write(receipt_path, receipt)

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 6,
        "expected_next_transition": expected,
        "expected_next_earliest_epoch": None if completed else epoch + 1,
        "expected_next_latest_epoch": None if completed else epoch + 1,
        "checkpoint_ref": f"receipts/sovereign-runtime-activation/{EXPECTED_TASK}.json",
        "evidence_refs": [
            f"receipts/sovereign-runtime-activation/{EXPECTED_TASK}.json",
            "scripts/bootstrap_sovereign_runtime.py",
            "scripts/verify_sovereign_runtime_activation.py",
            "workers/sovereign_node_repository_resolution_worker.py",
            "heartbeat_runtime/engine_v13.py",
            "heartbeat_runtime/worker_runtime.py",
            "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json",
        ],
        "blocker": blocker,
        "cost_observation": {
            "hb_transition_count": 0,
            "compute_units": 2 if attempt.get("attempted") else 1,
            "external_cost_usd": 0,
            "task_class": "sovereign_runtime_activation",
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
