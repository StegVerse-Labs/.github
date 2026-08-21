#!/usr/bin/env python3
"""Bootstrap optional resident supervision for the oscillator-produced carrier.

The bootstrap installs a local v13 oscillator carrier and separate
WorkerCoordinator. It never becomes the heartbeat clock: progression remains
OSCILLATOR_ONLY at 10 ms / 100 Hz and hosted environments are validation-only.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

Runner = Callable[..., subprocess.CompletedProcess[Any]]

THIRD_PARTY_ENV_VARS = (
    "GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
CREDENTIAL_ENV_VARS = ("GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN")
REQUIRED_SOURCE_FILES = (
    Path("heartbeat_runtime/engine_v13.py"),
    Path("heartbeat_runtime/independent_oscillator.py"),
    Path("heartbeat_runtime/oscillator_producer.py"),
    Path("heartbeat_runtime/worker_runtime.py"),
    Path("heartbeat_runtime/assignment_timer.py"),
    Path("scripts/install_sovereign_heartbeat_service.py"),
    Path("scripts/verify_sovereign_runtime_activation.py"),
    Path("scripts/run_heartbeat_runtime.py"),
    Path("scripts/run_worker_runtime.py"),
    Path("scripts/advance_heartbeat_transition.py"),
    Path("control/heartbeat-state.json"),
    Path("control/worker-registry.json"),
    Path("management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json"),
)
REQUIRED_PREDICATES = (
    "runtime_materialized", "native_service_active", "continuous_runtime_live",
    "heartbeat_epoch_advanced", "worker_coordination_checkpoint_observed",
    "worker_task_capable_cycle_observed", "controlled_restart_observed",
    "epoch_and_generation_non_regressing", "no_duplicate_claim_or_fence",
    "state_reconstruction_pass",
)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def third_party_hosted_environment(env: dict[str, str] | None = None) -> bool:
    values = dict(os.environ if env is None else env)
    return any(truthy(values.get(name)) for name in THIRD_PARTY_ENV_VARS)


def default_runtime_root(env: dict[str, str] | None = None) -> Path:
    values = dict(os.environ if env is None else env)
    override = values.get("STEGVERSE_HEARTBEAT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    system = platform.system().lower()
    if system == "windows":
        base = Path(values.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    elif system == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(values.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state")))
    return (base / "stegverse" / "heartbeat-runtime").resolve()


def default_node_marker() -> Path:
    return (Path.home() / ".stegverse" / "node.json").resolve()


def default_proof_path() -> Path:
    return (Path.home() / ".stegverse" / "heartbeat" / "activation.latest.json").resolve()


def default_receipt_path() -> Path:
    return (Path.home() / ".stegverse" / "heartbeat" / "bootstrap.latest.json").resolve()


def default_post_bootstrap_receipt() -> Path:
    return (Path.home() / ".stegverse" / "continuity" / "sovereign-post-bootstrap.latest.json").resolve()


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def local_eligibility(source_root: Path, runtime_root: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    source_root = source_root.expanduser().resolve()
    runtime_root = runtime_root.expanduser().resolve()
    values = dict(os.environ if env is None else env)
    hosted = third_party_hosted_environment(values)
    source_files = {str(path): (source_root / path).is_file() for path in REQUIRED_SOURCE_FILES}
    try:
        runtime_root.mkdir(parents=True, exist_ok=True)
        probe = runtime_root / ".bootstrap-write-probe"
        probe.write_text("stegverse\n", encoding="utf-8")
        probe.unlink()
        durable_state_writable = True
    except Exception:
        durable_state_writable = False
    source_complete = all(source_files.values())
    return {
        "source_root": str(source_root),
        "runtime_root": str(runtime_root),
        "required_source_files": source_files,
        "canonical_source_complete": source_complete,
        "durable_state_writable": durable_state_writable,
        "hosted_environment_rejected": hosted,
        "eligible": source_complete and durable_state_writable and not hosted,
        "continuity_model": "INDEPENDENT_OSCILLATOR_CONTINUITY",
        "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        "oscillator_producer_ref": "heartbeat_runtime/oscillator_producer.py",
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "heartbeat_event_trigger_required": False,
        "state_transition_contract_ref": "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json",
        "state_transition_producer_ref": "scripts/advance_heartbeat_transition.py",
        "always_on_external_host_required": False,
        "wall_clock_continuous_process_required": False,
        "resident_native_supervision_optional": True,
        "credential_requirement": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "third_party_runtime_required": False,
        "authority_effect": "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
    }


def existing_declaration(node_marker: Path, env: dict[str, str] | None = None) -> tuple[bool, str | None]:
    values = dict(os.environ if env is None else env)
    if truthy(values.get("STEGVERSE_SOVEREIGN_NODE")):
        return True, "env:STEGVERSE_SOVEREIGN_NODE"
    if node_marker.is_file():
        return True, str(node_marker)
    etc_marker = Path("/etc/stegverse/node.json")
    if etc_marker.is_file():
        return True, str(etc_marker)
    return False, None


def derive_node_declaration(source_root: Path, runtime_root: Path, node_marker: Path, env: dict[str, str] | None = None) -> tuple[bool, str | None, dict[str, Any]]:
    eligibility = local_eligibility(source_root, runtime_root, env)
    declared, ref = existing_declaration(node_marker, env)
    if declared:
        eligibility["declaration_mode"] = "EXISTING"
        return True, ref, eligibility
    if not eligibility["eligible"]:
        eligibility["declaration_mode"] = "NOT_DERIVED"
        return False, None, eligibility
    body = {
        "schema": "stegverse.sovereign-node-declaration/v0.4",
        "declared": True,
        "declaration_source": "SELF_BOOTSTRAP_LOCAL_OSCILLATOR_RUNTIME_ELIGIBILITY",
        "source_root": eligibility["source_root"],
        "state_root": eligibility["runtime_root"],
        "canonical_runtime_complete": True,
        "durable_state_writable": True,
        "hosted_environment_rejected": False,
        "continuity_model": "INDEPENDENT_OSCILLATOR_CONTINUITY",
        "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "heartbeat_event_trigger_required": False,
        "always_on_external_host_required": False,
        "credential_requirement": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "third_party_runtime_required": False,
        "authority_effect": "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
    }
    atomic_write(node_marker, body)
    eligibility["declaration_mode"] = "SELF_BOOTSTRAP_LOCAL_OSCILLATOR_RUNTIME_ELIGIBILITY"
    return True, str(node_marker), eligibility


def scrubbed_child_env(env: dict[str, str] | None, *, source_root: Path, runtime_root: Path, proof_path: Path) -> dict[str, str]:
    child = dict(os.environ if env is None else env)
    for name in CREDENTIAL_ENV_VARS:
        child[name] = ""
    child["STEGVERSE_SOVEREIGN_NODE"] = "1"
    child["STEGVERSE_HEARTBEAT_SOURCE_ROOT"] = str(source_root.resolve())
    child["STEGVERSE_HEARTBEAT_ROOT"] = str(runtime_root.resolve())
    child["STEGVERSE_SOVEREIGN_PROOF_PATH"] = str(proof_path.resolve())
    return child


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def all_predicates_pass(proof: dict[str, Any] | None) -> bool:
    return bool(proof and proof.get("all_predicates_pass") is True and all(proof.get(name) is True for name in REQUIRED_PREDICATES))


def _attempt_post_bootstrap_activation(source_root: Path, *, proof_path: Path, receipt_path: Path, node_marker: Path, env: dict[str, str] | None, runner: Runner) -> dict[str, Any]:
    bridge = source_root / "scripts" / "activate_stegfin_after_sovereign_bootstrap.py"
    integration_receipt = default_post_bootstrap_receipt()
    if not bridge.is_file():
        return {"attempted": False, "state": "NOT_AVAILABLE", "reason": "POST_BOOTSTRAP_STEGFIN_BRIDGE_NOT_PRESENT", "returncode": None, "receipt_ref": str(integration_receipt), "executor_service_active": False}
    persisted = load_json(receipt_path) or {}
    child_env = scrubbed_child_env(env, source_root=source_root, runtime_root=Path(persisted["runtime_root"]), proof_path=proof_path)
    command = [sys.executable, str(bridge), "--root", str(source_root), "--proof-path", str(proof_path), "--bootstrap-receipt", str(receipt_path), "--node-marker", str(node_marker), "--integration-receipt", str(integration_receipt)]
    completed = runner(command, check=False, capture_output=True, text=True, timeout=180, env=child_env)
    receipt = load_json(integration_receipt) or {}
    return {
        "attempted": True,
        "state": receipt.get("state") or ("COMPLETE" if completed.returncode == 0 else "REVIEW_REQUIRED"),
        "reason": receipt.get("reason"),
        "returncode": completed.returncode,
        "receipt_ref": str(integration_receipt),
        "executor_service_active": receipt.get("executor_service_active") is True,
        "credential_authority": receipt.get("credential_authority", "TV/TVC"),
        "non_tv_tvc_secret_or_token_used": receipt.get("non_tv_tvc_secret_or_token_used", False),
        "wallet_handoff_ready_claimed": receipt.get("wallet_handoff_ready_claimed", False),
    }


def bootstrap(source_root: Path, runtime_root: Path, *, node_marker: Path, proof_path: Path, receipt_path: Path, env: dict[str, str] | None = None, runner: Runner = subprocess.run, activate_downstream: bool = True) -> dict[str, Any]:
    source_root = source_root.expanduser().resolve()
    runtime_root = runtime_root.expanduser().resolve()
    node_marker = node_marker.expanduser().resolve()
    proof_path = proof_path.expanduser().resolve()
    receipt_path = receipt_path.expanduser().resolve()
    declared, declaration_ref, eligibility = derive_node_declaration(source_root, runtime_root, node_marker, env)
    body: dict[str, Any] = {
        "schema": "stegverse.sovereign-runtime-self-bootstrap-receipt/v2",
        "task_id": "SHWP-SOVEREIGN-RUNTIME-SELF-BOOTSTRAP-001",
        "source_root": str(source_root),
        "runtime_root": str(runtime_root),
        "node_declaration_ref": declaration_ref,
        "node_eligibility": eligibility,
        "continuity_model": "INDEPENDENT_OSCILLATOR_CONTINUITY",
        "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        "oscillator_producer_ref": "heartbeat_runtime/oscillator_producer.py",
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "heartbeat_event_trigger_required": False,
        "state_transition_contract_ref": "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json",
        "state_transition_producer_ref": "scripts/advance_heartbeat_transition.py",
        "always_on_external_host_required": False,
        "wall_clock_continuous_process_required": False,
        "resident_native_supervision_optional": True,
        "credential_requirement": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "third_party_runtime_required": False,
        "authority_effect": "OPTIONAL_RESIDENT_BOOTSTRAP_ONLY_NO_CREDENTIAL_ROUTE_OR_HEARTBEAT_AUTHORITY",
        "installer_returncode": None,
        "verifier_returncode": None,
        "proof_path": str(proof_path),
        "post_bootstrap_stegfin": {"attempted": False, "state": "NOT_ELIGIBLE", "reason": "SOVEREIGN_BOOTSTRAP_NOT_COMPLETE", "returncode": None, "executor_service_active": False, "wallet_handoff_ready_claimed": False},
        "state": "FAIL_CLOSED",
        "reason": None,
    }
    if third_party_hosted_environment(env):
        body["reason"] = "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_BOOTSTRAP_SURFACE"
        atomic_write(receipt_path, body)
        return body
    if not declared or not eligibility.get("eligible"):
        body["reason"] = "LOCAL_RUNTIME_ELIGIBILITY_NOT_PROVEN"
        atomic_write(receipt_path, body)
        return body
    child_env = scrubbed_child_env(env, source_root=source_root, runtime_root=runtime_root, proof_path=proof_path)
    install = runner([sys.executable, str(source_root / "scripts" / "install_sovereign_heartbeat_service.py"), "--source-root", str(source_root), "--runtime-root", str(runtime_root)], check=False, capture_output=True, text=True, timeout=180, env=child_env)
    body["installer_returncode"] = install.returncode
    if install.returncode != 0:
        body["state"] = "RETRY"
        body["reason"] = "NATIVE_INSTALLATION_RETRY_REQUIRED"
        atomic_write(receipt_path, body)
        return body
    verify = runner([sys.executable, str(source_root / "scripts" / "verify_sovereign_runtime_activation.py"), "--runtime-root", str(runtime_root)], check=False, capture_output=True, text=True, timeout=180, env=child_env)
    body["verifier_returncode"] = verify.returncode
    proof = load_json(proof_path)
    body["activation_proof_observed"] = proof is not None
    body["activation_all_predicates_pass"] = all_predicates_pass(proof)
    body["missing_predicates"] = [name for name in REQUIRED_PREDICATES if not proof or proof.get(name) is not True]
    if verify.returncode == 0 and all_predicates_pass(proof):
        body["state"] = "COMPLETE"
        body["reason"] = "SOVEREIGN_RUNTIME_SELF_BOOTSTRAP_VERIFIED"
        atomic_write(receipt_path, body)
        if activate_downstream:
            body["post_bootstrap_stegfin"] = _attempt_post_bootstrap_activation(source_root, proof_path=proof_path, receipt_path=receipt_path, node_marker=node_marker, env=env, runner=runner)
    else:
        body["state"] = "REVIEW_REQUIRED"
        body["reason"] = "SOVEREIGN_ACTIVATION_PROOF_INCOMPLETE"
    atomic_write(receipt_path, body)
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--node-marker", type=Path, default=None)
    parser.add_argument("--proof-path", type=Path, default=None)
    parser.add_argument("--receipt-path", type=Path, default=None)
    parser.add_argument("--skip-post-bootstrap-stegfin", action="store_true")
    args = parser.parse_args()
    result = bootstrap(
        args.source_root,
        (args.runtime_root or default_runtime_root()).resolve(),
        node_marker=(args.node_marker or default_node_marker()).resolve(),
        proof_path=(args.proof_path or default_proof_path()).resolve(),
        receipt_path=(args.receipt_path or default_receipt_path()).resolve(),
        activate_downstream=not args.skip_post_bootstrap_stegfin,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("state") == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
