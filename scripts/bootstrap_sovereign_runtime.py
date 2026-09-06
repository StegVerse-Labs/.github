#!/usr/bin/env python3
"""Bootstrap the canonical carrier-first sovereign runtime.

The independent engine_v13 oscillator carrier is started first through the
existing carrier-only native installer. WorkerCoordinator startup is not a
carrier prerequisite. After oscillator references exist, the existing
carrier-side self-heal path must establish/observe the independent task-capable
WorkerCoordinator before full runtime activation is verified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

Runner = Callable[..., subprocess.CompletedProcess[Any]]
THIRD_PARTY_ENV_VARS = (
    "GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
CREDENTIAL_ENV_VARS = ("GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN")
CARRIER_ACTIVATION_REL = Path("receipts/sovereign-host/carrier-activation.latest.json")
RUNTIME_PRESENCE_REL = Path("receipts/sovereign-host/runtime-presence.latest.json")
SELF_HEAL_REL = Path("receipts/sovereign-host/ephemeral-process.latest.json")
WORKER_STATE_REL = Path("control/worker-runtime-state.json")
REQUIRED_SOURCE_FILES = (
    Path("heartbeat_runtime/engine_v13.py"),
    Path("heartbeat_runtime/independent_oscillator.py"),
    Path("heartbeat_runtime/intr_derived_carrier.py"),
    Path("heartbeat_runtime/runtime_presence_projection.py"),
    Path("heartbeat_runtime/oscillator_producer.py"),
    Path("heartbeat_runtime/worker_runtime.py"),
    Path("heartbeat_runtime/assignment_timer.py"),
    Path("scripts/install_sovereign_heartbeat_service.py"),
    Path("scripts/install_sovereign_heartbeat_carrier.py"),
    Path("scripts/install_sovereign_worker_source_refresh_service.py"),
    Path("scripts/verify_sovereign_runtime_activation.py"),
    Path("scripts/verify_stegindex_resident_operational_proof.py"),
    Path("scripts/run_heartbeat_runtime.py"),
    Path("scripts/repair_resident_worker_presence.py"),
    Path("scripts/run_worker_runtime.py"),
    Path("scripts/project_hb_runtime_presence.py"),
    Path("scripts/project_de006_runtime_observability.py"),
    Path("scripts/verify_stegos_parent_evidence_candidate.py"),
    Path("control/runtime-observability-consumers/decision-envelope-de006.json"),
    Path("scripts/dispatch_resident_execution_requests.py"),
    Path("scripts/consume_org_claim_allocator_request.py"),
    Path("scripts/allocate_claims.py"),
    Path("control/resident-execution-request.d/org-claim-allocator-001.json"),
    Path("scripts/consume_resident_execution_request.py"),
    Path("scripts/consume_g18_resident_execution_request.py"),
    Path("scripts/consume_hil_resident_execution_request.py"),
    Path("scripts/consume_evaluator_intr_resident_execution_request.py"),
    Path("scripts/materialize_evaluator_intr_route_config.py"),
    Path("scripts/consume_sv002_public_observation_request.py"),
    Path("scripts/materialize_sv002_observation_route_config.py"),
    Path("scripts/serve_sv002_observation_intr_runtime.py"),
    Path("scripts/consume_hil_intr_materialization_request.py"),
    Path("scripts/consume_device_kv_intr_materialization_request.py"),
    Path("scripts/consume_device_kv_intr_materialization_request_base.py"),
    Path("scripts/workspace_device_kv_query_extension.py"),
    Path("scripts/personal_profile_device_kv_extension.py"),
    Path("scripts/materialize_personal_kv_provider_root.py"),
    Path("scripts/consume_publisher_intr_materialization_request.py"),
    Path("scripts/consume_kv_publisher_return_materialization_request.py"),
    Path("scripts/consume_hil_tvc_lifecycle_outbox.py"),
    Path("scripts/watch_hil_tvc_lifecycle_outbox.py"),
    Path("scripts/consume_ara_graph_resident_execution_request.py"),
    Path("scripts/consume_cmc028_resident_execution_request.py"),
    Path("scripts/consume_sv_dn1_resident_execution_request.py"),
    Path("scripts/consume_stegos_kv_intr_chain_request.py"),
    Path("scripts/consume_resident_rendezvous.py"),
    Path("scripts/consume_bootstrap_v1_intr_bundle_delivery_request.py"),
    Path("scripts/consume_tvc_broker_validation_request.py"),
    Path("scripts/consume_sv002_self_characterization_request.py"),
    Path("scripts/consume_sv002_org_runtime_activation_request.py"),
    Path("scripts/consume_healer_sovereign_scheduler_request.py"),
    Path("scripts/consume_universal_governance_enforced_reference_request.py"),
    Path("scripts/consume_cross_framework_current_basis_v04_request.py"),
    Path("scripts/consume_stegverse001_bounded_autonomy_request.py"),
    Path("scripts/consume_one_shot_resident_stack_activation_request.py"),
    Path("scripts/activate_resident_stack.py"),
    Path("scripts/continue_stegverse001_evidence_chain.py"),
    Path("scripts/refresh_and_dispatch_resident_requests.py"),
    Path("scripts/run_stegverse001_activation_progression.py"),
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


def default_runtime_locator_path(env: dict[str, str] | None = None) -> Path | None:
    if platform.system().lower() != "linux":
        return None
    values = dict(os.environ if env is None else env)
    raw = str(values.get("XDG_RUNTIME_DIR") or "").strip()
    base = Path(raw) if raw else Path("/run/user") / str(os.getuid())
    return base / "stegverse" / "sovereign-runtime.json" if base.is_absolute() else None


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def publish_runtime_locator(source_root: Path, runtime_root: Path, *, env: dict[str, str] | None = None) -> dict[str, Any]:
    path = default_runtime_locator_path(env)
    if path is None:
        return {"state": "NOT_APPLICABLE", "published": False, "reason": "RUNTIME_LOCATOR_LINUX_ONLY", "authority_effect": "NONE"}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.parent.stat().st_uid != os.getuid():
            return {"state": "HANDOFF_READY", "published": False, "reason": "RUNTIME_LOCATOR_PARENT_OWNER_MISMATCH", "path": str(path), "authority_effect": "NONE_LOCATOR_ONLY"}
        body = {
            "schema": "stegverse.sovereign-runtime-locator/v1", "uid": os.getuid(),
            "runtime_root": str(runtime_root.expanduser().resolve()), "source_root": str(source_root.expanduser().resolve()),
            "credential_material_present": False, "request_grants_authority": False,
            "heartbeat_grants_authority": False, "github_token_runtime_authority": "NONE",
            "credential_authority": "TV/TVC", "authority_effect": "NONE_LOCATOR_ONLY",
        }
        atomic_write(path, body)
        os.chmod(path, 0o600)
        return {"state": "PUBLISHED", "published": True, "path": str(path), "uid": os.getuid(), "runtime_root": body["runtime_root"], "credential_material_present": False, "authority_effect": "NONE_LOCATOR_ONLY"}
    except Exception as exc:
        return {"state": "HANDOFF_READY", "published": False, "reason": f"RUNTIME_LOCATOR_PUBLICATION_FAILED:{type(exc).__name__}", "path": str(path), "authority_effect": "NONE_LOCATOR_ONLY"}


def derived_node_id(source_root: Path, state_root: Path) -> str:
    basis = {
        "schema": "stegverse.sovereign-node-declaration/v0.4",
        "source_root": str(source_root.expanduser().resolve()),
        "state_root": str(state_root.expanduser().resolve()),
        "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        "continuity_model": "INDEPENDENT_OSCILLATOR_CONTINUITY", "credential_authority": "TV/TVC",
    }
    canonical = json.dumps(basis, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "SV-NODE-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def local_eligibility(source_root: Path, runtime_root: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    source_root = source_root.expanduser().resolve()
    runtime_root = runtime_root.expanduser().resolve()
    hosted = third_party_hosted_environment(env)
    source_files = {str(path): (source_root / path).is_file() for path in REQUIRED_SOURCE_FILES}
    try:
        runtime_root.mkdir(parents=True, exist_ok=True)
        probe = runtime_root / ".bootstrap-write-probe"
        probe.write_text("stegverse\n", encoding="utf-8")
        probe.unlink()
        writable = True
    except Exception:
        writable = False
    complete = all(source_files.values())
    return {
        "source_root": str(source_root), "runtime_root": str(runtime_root), "required_source_files": source_files,
        "canonical_source_complete": complete, "durable_state_writable": writable, "hosted_environment_rejected": hosted,
        "eligible": complete and writable and not hosted, "continuity_model": "INDEPENDENT_OSCILLATOR_CONTINUITY",
        "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime", "oscillator_producer_ref": "heartbeat_runtime/oscillator_producer.py",
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY", "heartbeat_event_trigger_required": False,
        "always_on_external_host_required": False, "wall_clock_continuous_process_required": False,
        "resident_native_supervision_optional": True, "credential_requirement": "NONE", "credential_authority": "TV/TVC",
        "github_token_required": False, "third_party_runtime_required": False,
        "authority_effect": "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
    }


def existing_declaration(node_marker: Path, env: dict[str, str] | None = None) -> tuple[bool, str | None]:
    values = dict(os.environ if env is None else env)
    if truthy(values.get("STEGVERSE_SOVEREIGN_NODE")):
        return True, "env:STEGVERSE_SOVEREIGN_NODE"
    if node_marker.is_file():
        return True, str(node_marker)
    etc_marker = Path("/etc/stegverse/node.json")
    return (True, str(etc_marker)) if etc_marker.is_file() else (False, None)


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
        "schema": "stegverse.sovereign-node-declaration/v0.4", "declared": True,
        "node_id": derived_node_id(source_root, runtime_root), "declaration_source": "SELF_BOOTSTRAP_LOCAL_OSCILLATOR_RUNTIME_ELIGIBILITY",
        "source_root": eligibility["source_root"], "state_root": eligibility["runtime_root"], "canonical_runtime_complete": True,
        "durable_state_writable": True, "hosted_environment_rejected": False, "continuity_model": "INDEPENDENT_OSCILLATOR_CONTINUITY",
        "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime", "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "heartbeat_event_trigger_required": False, "always_on_external_host_required": False, "credential_requirement": "NONE",
        "credential_authority": "TV/TVC", "github_token_required": False, "third_party_runtime_required": False,
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


def all_predicates_pass(proof: dict[str, Any] | None) -> bool:
    return bool(proof and proof.get("all_predicates_pass") is True and all(proof.get(name) is True for name in REQUIRED_PREDICATES))


def _carrier_activation_valid(receipt: dict[str, Any] | None) -> bool:
    r = receipt or {}
    return (
        r.get("schema") == "stegverse.sovereign-heartbeat-carrier-activation/v1"
        and r.get("activation_scope") == "CARRIER_ONLY"
        and r.get("carrier_active") is True
        and r.get("worker_start_attempted") is False
        and r.get("worker_runtime_dependency_for_carrier_start") is False
        and r.get("network_fetch_required") is False
        and r.get("third_party_process_host_required") is False
        and r.get("github_runtime_dependency") is False
        and r.get("credential_authority") == "TV/TVC"
        and r.get("credential_requirement") == "NONE"
        and r.get("heartbeat_progression_dependency") == "OSCILLATOR_ONLY"
        and r.get("heartbeat_period_ms") == 10.0
        and r.get("heartbeat_reference_frequency_hz") == 100.0
        and r.get("heartbeat_production_mode") == "OSCILLATOR_PHASE_DRIVEN"
        and r.get("canonical_runtime") == "heartbeat_runtime.engine_v13.HeartbeatRuntime"
    )


def _worker_presence_valid(runtime_root: Path) -> bool:
    presence = load_json(runtime_root / RUNTIME_PRESENCE_REL) or {}
    healed = load_json(runtime_root / SELF_HEAL_REL) or {}
    worker = load_json(runtime_root / WORKER_STATE_REL) or {}
    task_capable = (
        worker.get("schema") == "stegverse.worker-runtime-state/v1"
        and isinstance(worker.get("runtime_tick"), int)
        and worker.get("observation_mode") != "CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION"
    )
    projected = (presence.get("resident") or {}).get("present_worker_runtime_observed") is True
    self_heal = (
        healed.get("active") is True
        and healed.get("worker_task_capable_cycle_observed") is True
        and healed.get("carrier_active") is True
        and healed.get("worker_active") is True
    )
    return task_capable and (projected or self_heal)


def _wait_for_worker_presence(runtime_root: Path, *, timeout_seconds: float = 3.0, sleeper=time.sleep) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if _worker_presence_valid(runtime_root):
            worker = load_json(runtime_root / WORKER_STATE_REL) or {}
            return {"observed": True, "state": "INDEPENDENT_WORKER_PRESENCE_OBSERVED", "runtime_tick": worker.get("runtime_tick"), "authority_effect": "NONE_OBSERVATION_ONLY"}
        sleeper(0.05)
    worker = load_json(runtime_root / WORKER_STATE_REL) or {}
    return {"observed": False, "state": "INDEPENDENT_WORKER_PRESENCE_NOT_YET_OBSERVED", "runtime_tick": worker.get("runtime_tick"), "authority_effect": "NONE_OBSERVATION_ONLY"}


def _install_source_refresh_watcher(source_root: Path, runtime_root: Path, *, proof_path: Path, env: dict[str, str] | None, runner: Runner) -> dict[str, Any]:
    if platform.system().lower() != "linux":
        return {"attempted": False, "state": "NOT_APPLICABLE_NON_LINUX", "activated": False, "authority_effect": "NONE"}
    script = source_root / "scripts/install_sovereign_worker_source_refresh_service.py"
    if not script.is_file():
        return {"attempted": False, "state": "NOT_AVAILABLE", "reason": "SOURCE_REFRESH_WATCHER_INSTALLER_NOT_PRESENT", "activated": False, "authority_effect": "NONE"}
    child_env = scrubbed_child_env(env, source_root=source_root, runtime_root=runtime_root, proof_path=proof_path)
    completed = runner([sys.executable, str(script), "--source-root", str(source_root), "--runtime-root", str(runtime_root)], cwd=source_root, check=False, capture_output=True, text=True, timeout=180, env=child_env)
    receipt = load_json(runtime_root / "receipts/sovereign-host/worker-source-refresh-installation.latest.json") or {}
    return {"attempted": True, "state": "ACTIVE" if completed.returncode == 0 and receipt.get("activated") is True else "INCOMPLETE", "returncode": completed.returncode, "activated": receipt.get("activated") is True, "authority_effect": "NONE_LOCAL_SOURCE_REFRESH_INSTALLATION"}


def _dispatch_resident_requests(source_root: Path, runtime_root: Path, *, proof_path: Path, env: dict[str, str] | None, runner: Runner) -> dict[str, Any]:
    dispatcher = runtime_root / "scripts/dispatch_resident_execution_requests.py"
    if not dispatcher.is_file():
        return {"attempted": False, "state": "NOT_AVAILABLE", "reason": "RESIDENT_REQUEST_DISPATCHER_NOT_MATERIALIZED", "returncode": None, "authority_effect": "NONE"}
    child_env = scrubbed_child_env(env, source_root=source_root, runtime_root=runtime_root, proof_path=proof_path)
    completed = runner([sys.executable, str(dispatcher), "--source-root", str(source_root), "--runtime-root", str(runtime_root)], cwd=runtime_root, check=False, capture_output=True, text=True, timeout=3600, env=child_env)
    receipt = load_json(runtime_root / "receipts/sovereign-host/resident-request-dispatch.latest.json") or {}
    return {"attempted": True, "state": receipt.get("state") or ("DISPATCH_COMPLETE" if completed.returncode == 0 else "DISPATCH_INCOMPLETE"), "returncode": completed.returncode, "receipt_ref": "receipts/sovereign-host/resident-request-dispatch.latest.json", "request_failures": receipt.get("request_failures", []), "request_dispatch_grants_authority": receipt.get("request_dispatch_grants_authority", False), "authority_effect": "NONE"}


def _advance_tvc_skap_successor(source_root: Path, runtime_root: Path, *, proof_path: Path, env: dict[str, str] | None, runner: Runner) -> dict[str, Any]:
    worker_runner = runtime_root / "scripts/run_worker_runtime.py"
    task_id = "TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001"
    if not worker_runner.is_file():
        return {"attempted": False, "state": "NOT_AVAILABLE", "reason": "WORKER_RUNTIME_RUNNER_NOT_MATERIALIZED", "task_id": task_id, "authority_effect": "NONE"}
    child_env = scrubbed_child_env(env, source_root=source_root, runtime_root=runtime_root, proof_path=proof_path)
    completed = runner([sys.executable, str(worker_runner), "--root", str(runtime_root), "--task-id", task_id], cwd=runtime_root, check=False, capture_output=True, text=True, timeout=1800, env=child_env)
    result = None
    for line in reversed([line.strip() for line in (completed.stdout or "").splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            result = value
            break
    state = result.get("state") if isinstance(result, dict) and isinstance(result.get("state"), str) else ("SUCCESSOR_CYCLE_COMPLETE" if completed.returncode == 0 else "SUCCESSOR_CYCLE_INCOMPLETE")
    return {"attempted": True, "state": state, "task_id": task_id, "returncode": completed.returncode, "worker_result": result, "fresh_independent_claim_required": True, "parent_claim_reuse_prohibited": True, "heartbeat_grants_execution_authority": False, "credential_authority": "TV/TVC", "github_token_required": False, "authority_effect": "NONE_SUCCESSOR_DISPATCH_ONLY"}


def _attempt_post_bootstrap_activation(source_root: Path, *, proof_path: Path, receipt_path: Path, node_marker: Path, env: dict[str, str] | None, runner: Runner) -> dict[str, Any]:
    bridge = source_root / "scripts/activate_stegfin_after_sovereign_bootstrap.py"
    integration_receipt = default_post_bootstrap_receipt()
    if not bridge.is_file():
        return {"attempted": False, "state": "NOT_AVAILABLE", "reason": "POST_BOOTSTRAP_STEGFIN_BRIDGE_NOT_PRESENT", "returncode": None, "receipt_ref": str(integration_receipt), "executor_service_active": False}
    persisted = load_json(receipt_path) or {}
    child_env = scrubbed_child_env(env, source_root=source_root, runtime_root=Path(persisted["runtime_root"]), proof_path=proof_path)
    command = [sys.executable, str(bridge), "--root", str(source_root), "--proof-path", str(proof_path), "--bootstrap-receipt", str(receipt_path), "--node-marker", str(node_marker), "--integration-receipt", str(integration_receipt)]
    completed = runner(command, check=False, capture_output=True, text=True, timeout=180, env=child_env)
    receipt = load_json(integration_receipt) or {}
    return {"attempted": True, "state": receipt.get("state") or ("COMPLETE" if completed.returncode == 0 else "REVIEW_REQUIRED"), "reason": receipt.get("reason"), "returncode": completed.returncode, "receipt_ref": str(integration_receipt), "executor_service_active": receipt.get("executor_service_active") is True, "credential_authority": receipt.get("credential_authority", "TV/TVC"), "non_tv_tvc_secret_or_token_used": receipt.get("non_tv_tvc_secret_or_token_used", False), "wallet_handoff_ready_claimed": receipt.get("wallet_handoff_ready_claimed", False)}


def bootstrap(source_root: Path, runtime_root: Path, *, node_marker: Path, proof_path: Path, receipt_path: Path, env: dict[str, str] | None = None, runner: Runner = subprocess.run, activate_downstream: bool = True) -> dict[str, Any]:
    source_root = source_root.expanduser().resolve()
    runtime_root = runtime_root.expanduser().resolve()
    node_marker = node_marker.expanduser().resolve()
    proof_path = proof_path.expanduser().resolve()
    receipt_path = receipt_path.expanduser().resolve()
    declared, declaration_ref, eligibility = derive_node_declaration(source_root, runtime_root, node_marker, env)
    body: dict[str, Any] = {
        "schema": "stegverse.sovereign-runtime-self-bootstrap-receipt/v2", "task_id": "SHWP-SOVEREIGN-RUNTIME-SELF-BOOTSTRAP-001",
        "source_root": str(source_root), "runtime_root": str(runtime_root), "node_declaration_ref": declaration_ref, "node_eligibility": eligibility,
        "continuity_model": "INDEPENDENT_OSCILLATOR_CONTINUITY", "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        "oscillator_producer_ref": "heartbeat_runtime/oscillator_producer.py", "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "heartbeat_event_trigger_required": False, "carrier_start_mode": "DIRECT_CARRIER_ONLY_NATIVE_INSTALLER",
        "workercoordinator_required_for_carrier_start": False, "worker_start_attempted_by_carrier_installer": False,
        "credential_requirement": "NONE", "credential_authority": "TV/TVC", "github_token_required": False, "third_party_runtime_required": False,
        "authority_effect": "OPTIONAL_RESIDENT_BOOTSTRAP_ONLY_NO_CREDENTIAL_ROUTE_OR_HEARTBEAT_AUTHORITY",
        "installer_returncode": None, "carrier_only_installer_returncode": None, "carrier_activation_receipt_ref": str(CARRIER_ACTIVATION_REL),
        "carrier_activation_valid": False, "worker_presence_after_carrier_start": {"observed": False, "state": "NOT_ELIGIBLE", "authority_effect": "NONE"},
        "verifier_returncode": None, "proof_path": str(proof_path),
        "runtime_locator": {"state": "NOT_ELIGIBLE", "published": False, "authority_effect": "NONE"},
        "post_install_source_refresh_watcher": {"attempted": False, "state": "NOT_ELIGIBLE", "activated": False, "authority_effect": "NONE"},
        "post_bootstrap_resident_request_dispatch": {"attempted": False, "state": "NOT_ELIGIBLE", "returncode": None, "authority_effect": "NONE"},
        "post_bootstrap_tvc_skap_successor": {"attempted": False, "state": "NOT_ELIGIBLE", "task_id": "TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001", "authority_effect": "NONE"},
        "post_bootstrap_stegfin": {"attempted": False, "state": "NOT_ELIGIBLE", "reason": "SOVEREIGN_BOOTSTRAP_NOT_COMPLETE", "returncode": None, "executor_service_active": False, "wallet_handoff_ready_claimed": False},
        "state": "FAIL_CLOSED", "reason": None,
    }
    if third_party_hosted_environment(env):
        body["reason"] = "THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_BOOTSTRAP_SURFACE"
        atomic_write(receipt_path, body)
        return body
    if not declared or not eligibility.get("eligible"):
        body["reason"] = "LOCAL_RUNTIME_ELIGIBILITY_NOT_PROVEN"
        atomic_write(receipt_path, body)
        return body

    body["runtime_locator"] = publish_runtime_locator(source_root, runtime_root, env=env)
    child_env = scrubbed_child_env(env, source_root=source_root, runtime_root=runtime_root, proof_path=proof_path)
    install = runner([sys.executable, str(source_root / "scripts/install_sovereign_heartbeat_carrier.py"), "--source-root", str(source_root), "--runtime-root", str(runtime_root)], check=False, capture_output=True, text=True, timeout=180, env=child_env)
    body["installer_returncode"] = install.returncode
    body["carrier_only_installer_returncode"] = install.returncode
    carrier_receipt = load_json(runtime_root / CARRIER_ACTIVATION_REL)
    body["carrier_activation_valid"] = _carrier_activation_valid(carrier_receipt)
    if install.returncode != 0 or not body["carrier_activation_valid"]:
        body["state"] = "RETRY"
        body["reason"] = "CARRIER_ONLY_ACTIVATION_RETRY_REQUIRED"
        atomic_write(receipt_path, body)
        return body

    body["post_install_source_refresh_watcher"] = _install_source_refresh_watcher(source_root, runtime_root, proof_path=proof_path, env=env, runner=runner)
    if platform.system().lower() == "linux" and body["post_install_source_refresh_watcher"].get("attempted") is True and body["post_install_source_refresh_watcher"].get("activated") is not True:
        body["state"] = "RETRY"
        body["reason"] = "SOURCE_REFRESH_WATCHER_ACTIVATION_RETRY_REQUIRED"
        atomic_write(receipt_path, body)
        return body

    body["worker_presence_after_carrier_start"] = _wait_for_worker_presence(runtime_root)
    if body["worker_presence_after_carrier_start"].get("observed") is not True:
        body["state"] = "RETRY"
        body["reason"] = "INDEPENDENT_WORKER_SELF_HEAL_NOT_YET_OBSERVED"
        atomic_write(receipt_path, body)
        return body

    body["post_bootstrap_resident_request_dispatch"] = _dispatch_resident_requests(source_root, runtime_root, proof_path=proof_path, env=env, runner=runner)
    body["post_bootstrap_tvc_skap_successor"] = _advance_tvc_skap_successor(source_root, runtime_root, proof_path=proof_path, env=env, runner=runner)

    verify = runner([sys.executable, str(source_root / "scripts/verify_sovereign_runtime_activation.py"), "--runtime-root", str(runtime_root)], check=False, capture_output=True, text=True, timeout=180, env=child_env)
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
