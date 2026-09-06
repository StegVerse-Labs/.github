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
# Compatibility exports retained for direct canonical-source callers/tests.
# Resident refresh execution resolves the equivalent entrypoints from the
# validated canonical source binding instead of mutable resident state.
BOOTSTRAP = (ROOT / "scripts" / "bootstrap_sovereign_runtime.py").resolve()
EPHEMERAL_CONSOLE = (ROOT / "scripts" / "run_sovereign_ephemeral_console.py").resolve()
SOURCE_REFRESH_RECEIPT = ROOT / "receipts" / "sovereign-host" / "worker-source-refresh.latest.json"
REQUIRED_SOURCE_ENTRYPOINTS = (
    Path("scripts/bootstrap_sovereign_runtime.py"),
    Path("scripts/run_sovereign_ephemeral_console.py"),
)
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


def resolve_canonical_source_root(
    runtime_root: Path = ROOT,
    env: dict[str, str] | None = None,
) -> tuple[Path | None, str, str | None]:
    """Resolve the already-local canonical source without network transport.

    Direct canonical-source invocation remains supported when no resident refresh
    receipt or explicit source binding exists. Once a resident refresh receipt is
    present, its source/runtime separation is mandatory and malformed/stale
    binding state fails closed rather than treating mutable resident state as
    canonical source.
    """
    runtime = runtime_root.expanduser().resolve()
    values = os.environ if env is None else env
    explicit = str(values.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT") or "").strip()
    refresh = load_json(runtime / "receipts" / "sovereign-host" / "worker-source-refresh.latest.json")

    source_raw: str | None = explicit or None
    binding_mode = "EXPLICIT_ENV" if explicit else "DIRECT_CANONICAL_SOURCE"
    if refresh is not None:
        if refresh.get("schema") != "stegverse.sovereign-worker-runtime-source-refresh/v1":
            return None, "INVALID_REFRESH_RECEIPT", "SOURCE_REFRESH_SCHEMA_INVALID"
        if refresh.get("network_fetch_performed") is not False:
            return None, "INVALID_REFRESH_RECEIPT", "SOURCE_REFRESH_NETWORK_INVARIANT_INVALID"
        if refresh.get("credential_read_or_acquired") is not False:
            return None, "INVALID_REFRESH_RECEIPT", "SOURCE_REFRESH_CREDENTIAL_INVARIANT_INVALID"
        if refresh.get("authority_effect") != "NONE_LOCAL_SOURCE_REFRESH":
            return None, "INVALID_REFRESH_RECEIPT", "SOURCE_REFRESH_AUTHORITY_EFFECT_INVALID"
        receipt_runtime = str(refresh.get("runtime_root") or "").strip()
        if not receipt_runtime or Path(receipt_runtime).expanduser().resolve() != runtime:
            return None, "INVALID_REFRESH_RECEIPT", "SOURCE_REFRESH_RUNTIME_ROOT_MISMATCH"
        receipt_source = str(refresh.get("source_root") or "").strip()
        if not receipt_source:
            return None, "INVALID_REFRESH_RECEIPT", "SOURCE_REFRESH_SOURCE_ROOT_MISSING"
        if explicit and Path(explicit).expanduser().resolve() != Path(receipt_source).expanduser().resolve():
            return None, "INVALID_REFRESH_RECEIPT", "SOURCE_BINDING_ENV_RECEIPT_MISMATCH"
        source_raw = receipt_source
        binding_mode = "RESIDENT_SOURCE_REFRESH_RECEIPT"

    source = Path(source_raw).expanduser().resolve() if source_raw else runtime
    if binding_mode != "DIRECT_CANONICAL_SOURCE" and source == runtime:
        return None, binding_mode, "CANONICAL_SOURCE_EQUALS_RESIDENT_RUNTIME"
    missing = [rel.as_posix() for rel in REQUIRED_SOURCE_ENTRYPOINTS if not (source / rel).is_file()]
    if missing:
        return None, binding_mode, "CANONICAL_SOURCE_ENTRYPOINTS_MISSING:" + ",".join(missing)
    return source, binding_mode, None


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


def default_ephemeral_console_root(runtime_root: Path | None = None) -> Path:
    runtime = (runtime_root or default_runtime_root()).expanduser().resolve()
    return (runtime.parent / "sovereign-ephemeral-console").resolve()


def all_activation_predicates_pass(proof: dict | None) -> bool:
    return bool(
        proof
        and proof.get("all_predicates_pass") is True
        and all(proof.get(name) is True for name in REQUIRED_PREDICATES)
    )


def execute_same_host_ephemeral_fallback(
    runtime_root: Path,
    proof_path: Path,
    *,
    source_root: Path,
) -> dict:
    console_root = default_ephemeral_console_root(runtime_root)
    receipt_path = console_root / "ephemeral-console.latest.json"
    ephemeral_console = EPHEMERAL_CONSOLE if source_root == ROOT else (
        source_root / "scripts" / "run_sovereign_ephemeral_console.py"
    ).resolve()
    result = {
        "attempted": False,
        "entrypoint": "scripts/run_sovereign_ephemeral_console.py",
        "canonical_source_root": str(source_root),
        "console_root": str(console_root),
        "receipt_ref": str(receipt_path),
        "canonical_proof_path": str(proof_path),
        "same_physical_host_required": True,
        "physical_additional_machine_required": False,
        "third_party_runtime_required": False,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "heartbeat_grants_execution_authority": False,
        "returncode": None,
        "state": None,
        "reason": None,
        "all_nodes_pass": False,
        "all_isolation_predicates_pass": False,
        "primary_retained": False,
        "canonical_proof_promoted": False,
        "activation_all_predicates_pass": False,
    }
    if third_party_hosted_environment():
        result["reason"] = "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE"
        return result
    if not ephemeral_console.is_file():
        result["reason"] = "EXISTING_SAME_HOST_EPHEMERAL_CONSOLE_MISSING"
        return result

    command = [
        sys.executable,
        str(ephemeral_console),
        "--source-root", str(source_root),
        "--console-root", str(console_root),
        "--canonical-proof-path", str(proof_path),
    ]
    result["attempted"] = True
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
        env=clean_exec_env(),
    )
    result["returncode"] = completed.returncode
    console = load_json(receipt_path) or {}
    proof = load_json(proof_path) or {}
    result["state"] = console.get("state")
    result["reason"] = console.get("reason") or (
        "SAME_HOST_EPHEMERAL_RUNTIME_FALLBACK_VERIFIED"
        if completed.returncode == 0 else
        "SAME_HOST_EPHEMERAL_RUNTIME_FALLBACK_INCOMPLETE"
    )
    result["all_nodes_pass"] = console.get("all_nodes_pass") is True
    result["all_isolation_predicates_pass"] = console.get("all_isolation_predicates_pass") is True
    result["primary_retained"] = console.get("primary_retained") is True
    result["canonical_proof_promoted"] = console.get("canonical_proof_promoted") is True
    result["primary_runtime_root"] = console.get("primary_runtime_root")
    result["primary_carrier_pid"] = console.get("primary_carrier_pid")
    result["primary_worker_pid"] = console.get("primary_worker_pid")
    result["activation_all_predicates_pass"] = all_activation_predicates_pass(proof)
    result["proof_schema"] = proof.get("schema")
    result["complete"] = bool(
        completed.returncode == 0
        and console.get("state") == "COMPLETE"
        and result["all_nodes_pass"]
        and result["all_isolation_predicates_pass"]
        and result["primary_retained"]
        and result["canonical_proof_promoted"]
        and result["activation_all_predicates_pass"]
    )
    return result


def execute_v13_self_bootstrap() -> dict:
    runtime_root = default_runtime_root()
    proof_path = default_proof_path()
    bootstrap_receipt = default_bootstrap_receipt()
    source_root, source_binding_mode, source_binding_error = resolve_canonical_source_root(ROOT)
    result = {
        "attempted": False,
        "entrypoint": "scripts/bootstrap_sovereign_runtime.py",
        "runtime_root": str(runtime_root),
        "canonical_source_root": str(source_root) if source_root is not None else None,
        "canonical_source_binding_mode": source_binding_mode,
        "canonical_source_binding_error": source_binding_error,
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
        "same_host_ephemeral_fallback": {
            "attempted": False,
            "reason": "NATIVE_BOOTSTRAP_NOT_YET_EVALUATED",
        },
    }
    if third_party_hosted_environment():
        result["reason"] = "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE"
        result["same_host_ephemeral_fallback"]["reason"] = "HOSTED_RUNTIME_FALLBACK_PROHIBITED"
        return result
    if source_root is None:
        result["reason"] = f"CANONICAL_LOCAL_SOURCE_BINDING_INVALID:{source_binding_error or 'UNKNOWN'}"
        result["same_host_ephemeral_fallback"]["reason"] = "CANONICAL_LOCAL_SOURCE_REQUIRED_FIRST"
        return result
    bootstrap = BOOTSTRAP if source_root == ROOT else (
        source_root / "scripts" / "bootstrap_sovereign_runtime.py"
    ).resolve()
    if not bootstrap.is_file():
        result["reason"] = "CANONICAL_V13_BOOTSTRAP_MISSING"
        result["same_host_ephemeral_fallback"]["reason"] = "CANONICAL_BOOTSTRAP_SOURCE_REQUIRED_FIRST"
        return result

    result["attempted"] = True
    command = [
        sys.executable,
        str(bootstrap),
        "--source-root", str(source_root),
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
    bootstrap_result = load_json(bootstrap_receipt) or {}
    proof = load_json(proof_path) or {}
    result["state"] = bootstrap_result.get("state")
    result["reason"] = bootstrap_result.get("reason") or (
        "SOVEREIGN_RUNTIME_SELF_BOOTSTRAP_VERIFIED"
        if completed.returncode == 0 else
        "SOVEREIGN_RUNTIME_SELF_BOOTSTRAP_INCOMPLETE"
    )
    result["node_declaration_ref"] = bootstrap_result.get("node_declaration_ref")
    result["node_eligibility"] = bootstrap_result.get("node_eligibility")
    result["activation_proof_observed"] = bool(proof)
    result["activation_all_predicates_pass"] = all_activation_predicates_pass(proof)
    result["missing_predicates"] = [
        name for name in REQUIRED_PREDICATES if proof.get(name) is not True
    ]
    result["proof_schema"] = proof.get("schema")

    native_complete = (
        result.get("state") == "COMPLETE"
        and result.get("activation_all_predicates_pass") is True
    )
    if native_complete:
        result["same_host_ephemeral_fallback"] = {
            "attempted": False,
            "reason": "NATIVE_BOOTSTRAP_COMPLETE_FALLBACK_NOT_REQUIRED",
            "physical_additional_machine_required": False,
            "third_party_runtime_required": False,
        }
        return result

    fallback = execute_same_host_ephemeral_fallback(
        runtime_root,
        proof_path,
        source_root=source_root,
    )
    result["same_host_ephemeral_fallback"] = fallback
    if fallback.get("complete") is True:
        proof = load_json(proof_path) or {}
        result["state"] = "COMPLETE"
        result["reason"] = "SOVEREIGN_RUNTIME_SAME_HOST_EPHEMERAL_FALLBACK_VERIFIED"
        result["activation_proof_observed"] = bool(proof)
        result["activation_all_predicates_pass"] = all_activation_predicates_pass(proof)
        result["missing_predicates"] = [
            name for name in REQUIRED_PREDICATES if proof.get(name) is not True
        ]
        result["proof_schema"] = proof.get("schema")
    else:
        fallback_reason = str(fallback.get("reason") or "UNKNOWN")
        result["reason"] = f"NATIVE_BOOTSTRAP_INCOMPLETE_AND_EPHEMERAL_FALLBACK_INCOMPLETE:{fallback_reason}"
    return result


def blocker_for(attempt: dict) -> dict:
    reason = attempt.get("reason")
    hosted = reason == "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE"
    fallback = attempt.get("same_host_ephemeral_fallback") if isinstance(attempt.get("same_host_ephemeral_fallback"), dict) else {}
    return {
        "trigger_type": "CONDITIONAL_CONSTRAINT",
        "dependency_class": "PHYSICAL_RESOURCE_SOVEREIGN_NODE_ELIGIBILITY",
        "problem_statement": (
            "The current execution surface has not produced the canonical deployment-local v13 sovereign-runtime activation proof after the existing native bootstrap and same-host logical-isolation recovery paths were evaluated."
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
        "canonical_source_root": attempt.get("canonical_source_root"),
        "canonical_source_binding_mode": attempt.get("canonical_source_binding_mode"),
        "canonical_source_binding_error": attempt.get("canonical_source_binding_error"),
        "same_host_ephemeral_fallback_attempted": fallback.get("attempted") is True,
        "same_host_ephemeral_fallback_reason": fallback.get("reason"),
        "physical_additional_machine_required": False,
        "always_on_external_host_required": False,
        "heartbeat_activation_blocked": False,
        "workaround_candidates": [
            "Retry the existing v13 self-bootstrap on the current non-hosted StegVerse deployment-local surface using the already-local canonical source binding; G18 automatically exercises the existing same-host ephemeral-console fallback when native proof remains incomplete.",
            "If both existing local recovery paths cannot satisfy canonical v13 eligibility/proof, component authority may select another already-admitted StegVerse-owned/federated sovereign surface without treating a second machine as a default requirement.",
        ],
        "next_solution_action": "RETRY_EXISTING_G18_NATIVE_THEN_SAME_HOST_EPHEMERAL_RECOVERY",
        "completion_evidence": [
            "stegverse.sovereign-runtime-activation-proof/v1 exists on the deployment-local sovereign surface",
            "all required activation predicates are true, including worker_task_capable_cycle_observed",
            "canonical carrier runtime is heartbeat_runtime.engine_v13.HeartbeatRuntime",
            "WorkerCoordinator task-capable lifecycle evidence is observed",
            "same-host ephemeral fallback, when used, proves all logical nodes and isolation predicates and retains the primary local carrier/worker",
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
        expected = "RETRY_EXISTING_G18_NATIVE_THEN_SAME_HOST_EPHEMERAL_RECOVERY"
        blocker = blocker_for(attempt)

    receipt = {
        "schema": "stegverse.sovereign-runtime-worker-receipt/v0.9",
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
        "authority_effect": "bounded_native_or_same_host_logical_runtime_activation_under_existing_g18_handoff",
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
            "scripts/run_sovereign_ephemeral_console.py",
            "scripts/verify_sovereign_runtime_activation.py",
            "workers/sovereign_node_repository_resolution_worker.py",
            "heartbeat_runtime/engine_v13.py",
            "heartbeat_runtime/worker_runtime.py",
            "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json",
        ],
        "blocker": blocker,
        "cost_observation": {
            "hb_transition_count": 0,
            "compute_units": 3 if attempt.get("same_host_ephemeral_fallback", {}).get("attempted") else (2 if attempt.get("attempted") else 1),
            "external_cost_usd": 0,
            "task_class": "sovereign_runtime_activation",
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())