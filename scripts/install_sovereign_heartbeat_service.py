#!/usr/bin/env python3
"""Materialize and activate separated StegVerse oscillator carrier/worker runtimes.

The carrier cadence is immutable: 10 ms / 100 Hz from the independent oscillator.
``interval_ms`` remains only as the WorkerCoordinator scheduling interval for
backward-compatible callers. It cannot change heartbeat phase progression.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

Runner = Callable[..., subprocess.CompletedProcess[Any]]
MUTABLE_RUNTIME_DIRS = ("checkpoints", "events", "receipts", "heartbeats")
MUTABLE_CONTROL_FILES = (
    "heartbeat-carrier-runtime-state.json",
    "worker-runtime-state.json",
    "worker-control-plane-coordination.json",
    "worker-status.json",
)
COPY_DIRS = (
    "heartbeat_runtime",
    "control",
    "handoffs",
    "authorizations",
    "workers",
    "schemas",
    "cost-basis",
    "management",
    "state_language",
)
COPY_FILES = (
    "scripts/run_heartbeat_runtime.py",
    "scripts/run_worker_runtime.py",
    "scripts/project_hb_runtime_presence.py",
    "scripts/project_de006_runtime_observability.py",
    "scripts/verify_stegos_parent_evidence_candidate.py",
    "control/runtime-observability-consumers/decision-envelope-de006.json",
    "scripts/refresh_and_execute_resident_task.py",
    "scripts/refresh_sovereign_worker_runtime_source.py",
    "scripts/run_independent_ecosystem_chat_parent.py",
    "scripts/consume_resident_execution_request.py",
    "scripts/consume_g18_resident_execution_request.py",
    "scripts/consume_hil_resident_execution_request.py",
    "scripts/consume_evaluator_intr_resident_execution_request.py",
    "scripts/materialize_evaluator_intr_route_config.py",
    "scripts/consume_sv002_public_observation_request.py",
    "scripts/materialize_sv002_observation_route_config.py",
    "scripts/serve_sv002_observation_intr_runtime.py",
    "scripts/consume_hil_intr_materialization_request.py",
    "scripts/consume_device_kv_intr_materialization_request.py",
    "scripts/consume_device_kv_intr_materialization_request_base.py",
    "scripts/workspace_device_kv_query_extension.py",
    "scripts/personal_profile_device_kv_extension.py",
    "scripts/materialize_personal_kv_provider_root.py",
    "scripts/consume_publisher_intr_materialization_request.py",
    "scripts/consume_kv_publisher_return_materialization_request.py",
    "scripts/consume_hil_tvc_lifecycle_outbox.py",
    "scripts/watch_hil_tvc_lifecycle_outbox.py",
    "scripts/consume_ara_graph_resident_execution_request.py",
    "scripts/consume_cmc028_resident_execution_request.py",
    "scripts/run_sv_dn1_first_round_chain.py",
    "scripts/consume_sv_dn1_resident_execution_request.py",
    "scripts/consume_stegos_kv_intr_chain_request.py",
    "scripts/consume_resident_rendezvous.py",
    "scripts/consume_bootstrap_v1_intr_bundle_delivery_request.py",
    "scripts/consume_tvc_broker_validation_request.py",
    "scripts/bootstrap_tvc_pr92_validation_source.py",
    "scripts/consume_sv002_self_characterization_request.py",
    "scripts/consume_healer_sovereign_scheduler_request.py",
    "scripts/consume_universal_governance_enforced_reference_request.py",
    "scripts/consume_cross_framework_current_basis_v04_request.py",
    "scripts/consume_stegverse001_bounded_autonomy_request.py",
    "scripts/consume_one_shot_resident_stack_activation_request.py",
    "scripts/activate_resident_stack.py",
    "scripts/continue_stegverse001_evidence_chain.py",
    "scripts/dispatch_resident_execution_requests.py",
    "scripts/consume_org_claim_allocator_request.py",
    "scripts/allocate_claims.py",
    "control/resident-execution-request.d/org-claim-allocator-001.json",
    "scripts/refresh_and_dispatch_resident_requests.py",
    "scripts/run_stegverse001_activation_progression.py",
    "scripts/materialize_live_cosv_packet.py",
    "scripts/cosv.py",
    "scripts/cosv_state_packet.py",
    "scripts/project_worker_control_plane_from_carrier.py",
    "scripts/verify_iphone_heartbeat_transition_receipt.py",
    "scripts/advance_heartbeat_transition.py",
    "scripts/refresh_heartbeat_transition_receipt.py",
    "scripts/verify_sovereign_runtime_activation.py",
    "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json",
)
CANONICAL_RUNTIME = "heartbeat_runtime.engine_v13.HeartbeatRuntime"
CANONICAL_CARRIER_RUNTIME = CANONICAL_RUNTIME
WORKER_RUNTIME = "heartbeat_runtime.worker_runtime.WorkerCoordinator"
OSCILLATOR_PERIOD_MS = 10.0
OSCILLATOR_FREQUENCY_HZ = 100.0
DEFAULT_WORKER_INTERVAL_MS = 10.0
# Compatibility export. This is NOT heartbeat timing authority.
DEFAULT_INTERVAL_MS = DEFAULT_WORKER_INTERVAL_MS

WORKER_SAFE_LOCAL_BINDINGS = (
    "STEGVERSE_HEALER_ROOT",
    "STEGVERSE_REPO_ROOTS_JSON",
    "STEGVERSE_STEGINDEX_SOURCE_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT",
    "STEGVERSE_TVC_ROOT",
    "STEGVERSE_TV_ROOT",
    "STEGVERSE_MICRO_NODE_RUNTIME_ROOT",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT",
    "STEGVERSE_MASTER_RECORDS_ROOT",
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "STEGVERSE_STEGOS_ROOT",
    "STEGVERSE_KV_SOURCE_ROOT",
    "STEGVERSE_KV_ROOT",
    "STEGVERSE_KV_PROVIDER_BINDING_PATH",
    "STEGVERSE_KV_PROVIDER_MATERIALIZED_ROOT",
    "STEGVERSE_TVC_PROVIDER_SESSION_FILE",
    "STEGVERSE_SITE_ROOT",
    "STEGVERSE_TT_ROOT",
    "STEGVERSE_RTG_ROOT",
    "STEGVERSE_GTG_ROOT",
    "STEGVERSE_AE_ROOT",
    "STEGVERSE_RESIDENT_SOURCE_MANIFEST",
    "STEGVERSE_SV001_AUTONOMY_LEASE",
)


def default_runtime_root(env=None):
    values = dict(os.environ if env is None else env)
    override = values.get("STEGVERSE_HEARTBEAT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    name = platform.system().lower()
    if name == "windows":
        base = Path(values.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif name == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(values.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return (base / "stegverse" / "heartbeat-runtime").resolve()


def _nominal_ticks_per_second(interval_ms: float) -> float | None:
    return None if interval_ms <= 0 else 1000.0 / interval_ms


def materialize(source_root: Path, target_root: Path, *, interval_ms: float = DEFAULT_WORKER_INTERVAL_MS):
    """Copy the sovereign runtime without network access or hosted authority."""
    source_root = source_root.resolve()
    target_root = target_root.resolve()
    target_root.mkdir(parents=True, exist_ok=True)
    for rel in COPY_DIRS:
        src = source_root / rel
        if src.exists():
            ignore = shutil.ignore_patterns(*MUTABLE_CONTROL_FILES) if rel == "control" else None
            shutil.copytree(src, target_root / rel, dirs_exist_ok=True, ignore=ignore)
    for rel in COPY_FILES:
        src = source_root / rel
        if not src.is_file():
            raise RuntimeError(f"missing canonical runtime file: {rel}")
        dst = target_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    required = (
        target_root / "heartbeat_runtime" / "__init__.py",
        target_root / "heartbeat_runtime" / "engine_v13.py",
        target_root / "heartbeat_runtime" / "independent_oscillator.py",
        target_root / "heartbeat_runtime" / "intr_derived_carrier.py",
        target_root / "heartbeat_runtime" / "oscillator_producer.py",
        target_root / "heartbeat_runtime" / "worker_runtime.py",
        target_root / "heartbeat_runtime" / "assignment_timer.py",
        target_root / "schemas" / "heartbeat-carrier-runtime-state.schema.json",
        target_root / "control" / "heartbeat-state.json",
        target_root / "control" / "worker-registry.json",
        target_root / "scripts" / "run_heartbeat_runtime.py",
        target_root / "scripts" / "run_worker_runtime.py",
        target_root / "scripts" / "dispatch_resident_execution_requests.py",
        target_root / "scripts" / "consume_resident_execution_request.py",
        target_root / "scripts" / "consume_g18_resident_execution_request.py",
        target_root / "scripts" / "consume_hil_resident_execution_request.py",
        target_root / "scripts" / "consume_evaluator_intr_resident_execution_request.py",
        target_root / "scripts" / "materialize_evaluator_intr_route_config.py",
        target_root / "scripts" / "consume_hil_intr_materialization_request.py",
        target_root / "scripts" / "consume_device_kv_intr_materialization_request.py",
        target_root / "scripts" / "consume_publisher_intr_materialization_request.py",
        target_root / "scripts" / "consume_kv_publisher_return_materialization_request.py",
        target_root / "scripts" / "consume_hil_tvc_lifecycle_outbox.py",
        target_root / "scripts" / "watch_hil_tvc_lifecycle_outbox.py",
        target_root / "scripts" / "consume_sv002_self_characterization_request.py",
        target_root / "scripts" / "consume_healer_sovereign_scheduler_request.py",
        target_root / "scripts" / "consume_universal_governance_enforced_reference_request.py",
        target_root / "scripts" / "consume_cross_framework_current_basis_v04_request.py",
        target_root / "scripts" / "consume_stegos_kv_intr_chain_request.py",
        target_root / "scripts" / "consume_resident_rendezvous.py",
        target_root / "scripts" / "consume_bootstrap_v1_intr_bundle_delivery_request.py",
        target_root / "scripts" / "bootstrap_tvc_pr92_validation_source.py",
        target_root / "scripts" / "refresh_and_dispatch_resident_requests.py",
        target_root / "management" / "SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json",
    )
    if not all(path.is_file() for path in required):
        raise RuntimeError("materialized oscillator-separated runtime is incomplete")

    init_text = (target_root / "heartbeat_runtime" / "__init__.py").read_text(encoding="utf-8")
    if "CarrierHeartbeatRuntime" not in init_text or "WorkerCoordinator" not in init_text:
        raise RuntimeError("materialized package does not expose separated carrier and worker runtimes")

    receipt = {
        "schema": "stegverse.sovereign-heartbeat-materialization/v4",
        "source_root": str(source_root),
        "runtime_root": str(target_root),
        "canonical_runtime": CANONICAL_RUNTIME,
        "canonical_carrier_runtime": CANONICAL_CARRIER_RUNTIME,
        "worker_runtime": WORKER_RUNTIME,
        "carrier_producer_ref": "heartbeat_runtime/oscillator_producer.py",
        "carrier_runtime_entrypoint": "scripts/run_heartbeat_runtime.py",
        "worker_runtime_entrypoint": "scripts/run_worker_runtime.py",
        "state_transition_producer_ref": "scripts/advance_heartbeat_transition.py",
        "state_transition_contract_ref": "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json",
        "initial_carrier_bootstrap_ready": True,
        "legacy_combined_runtime_is_production_target": False,
        "heartbeat_production_mode": "OSCILLATOR_PHASE_DRIVEN",
        "heartbeat_period_ms": OSCILLATOR_PERIOD_MS,
        "heartbeat_reference_frequency_hz": OSCILLATOR_FREQUENCY_HZ,
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "heartbeat_event_trigger_required": False,
        "heartbeat_interval_argument_controls_progression": False,
        "worker_default_interval_ms": float(interval_ms),
        "nominal_carrier_references_per_second": OSCILLATOR_FREQUENCY_HZ,
        "nominal_worker_ticks_per_second": _nominal_ticks_per_second(float(interval_ms)),
        "carrier_state_ref": "control/heartbeat-carrier-runtime-state.json",
        "legacy_hb29_source_ref": "control/heartbeat-state.json",
        "worker_registry_ref": "control/worker-registry.json",
        "worker_control_plane_ref": "control/worker-control-plane-coordination.json",
        "worker_lease_clock": "WORKER_RUNTIME_INTERNAL_HB_UNIT",
        "carrier_epoch_controls_worker_expiry": False,
        "carrier_presence_controls_worker_expiry": False,
        "wall_clock_worker_expiry_authority": False,
        "network_fetch_required": False,
        "third_party_process_host_required": False,
        "third_party_scheduler_required": False,
        "third_party_deployment_required": False,
        "github_runtime_dependency": False,
        "render_runtime_dependency": False,
        "cloudflare_runtime_dependency": False,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "non_tv_tvc_secret_or_token_used": False,
        "heartbeat_timing_authority": "INDEPENDENT_OSCILLATOR_ONLY",
        "worker_timer_authority": WORKER_RUNTIME,
        "heartbeat_grants_execution_authority": False,
        "execution_authority_effect": "NONE_FROM_CARRIER",
        "manual_action_required": False,
        "source_mutable_runtime_state_copied": False,
        "mutable_runtime_dirs_excluded_from_source": list(MUTABLE_RUNTIME_DIRS),
        "source_mutable_control_state_copied": False,
        "mutable_control_files_excluded_from_source": list(MUTABLE_CONTROL_FILES),
    }
    path = target_root / "receipts" / "sovereign-host" / "materialization.latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def _carrier_command(root: Path) -> list[str]:
    # No interval argument: the public carrier runner wakes from oscillator phase.
    return [
        sys.executable,
        str(root / "scripts" / "run_heartbeat_runtime.py"),
        "--root",
        str(root),
        "--continuous",
    ]


def _worker_command(root: Path, interval_ms: float) -> list[str]:
    return [
        sys.executable,
        str(root / "scripts" / "run_worker_runtime.py"),
        "--root",
        str(root),
        "--continuous",
        "--interval-ms",
        str(interval_ms),
    ]


_CANONICAL_NODE_REF = re.compile(r"^SV-NODE-[0-9a-f]{24}$")


def _load_declared_node_ref(values: dict[str, str]) -> str | None:
    candidates = []
    explicit_marker = str(values.get("STEGVERSE_SOVEREIGN_NODE_MARKER") or "").strip()
    if explicit_marker:
        candidates.append(Path(explicit_marker).expanduser())
    candidates.extend([
        Path.home() / ".stegverse" / "node.json",
        Path("/etc/stegverse/node.json"),
    ])
    for path in candidates:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        node_id = str(value.get("node_id") or "")
        if (
            value.get("schema") == "stegverse.sovereign-node-declaration/v0.4"
            and value.get("declared") is True
            and _CANONICAL_NODE_REF.fullmatch(node_id)
            and value.get("credential_authority") == "TV/TVC"
            and str(value.get("authority_effect") or "").endswith("NO_CREDENTIAL_OR_ROUTE_AUTHORITY")
        ):
            return node_id
    return None


def _resident_rendezvous_env(values: dict[str, str]) -> dict[str, str]:
    url = str(values.get("STEGVERSE_RESIDENT_RENDEZVOUS_URL") or "").strip()
    node_ref = str(values.get("STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF") or "").strip()
    if not url and not node_ref:
        return {}
    if url and not node_ref:
        node_ref = _load_declared_node_ref(values) or ""
    if not url.startswith("https://"):
        raise RuntimeError("resident rendezvous URL must use https")
    if any(ch in url for ch in "\r\n\"") or any(ch in node_ref for ch in "\r\n\""):
        raise RuntimeError("resident rendezvous configuration contains unsafe characters")
    if not node_ref or len(node_ref) > 256:
        raise RuntimeError("resident rendezvous node ref required")
    return {
        "STEGVERSE_RESIDENT_RENDEZVOUS_URL": url.rstrip("/"),
        "STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF": node_ref,
    }


def _systemd_unit(description: str, command: list[str], root: Path, extra_env: dict[str, str] | None = None) -> str:
    env_lines = [f"Environment=STEGVERSE_HEARTBEAT_ROOT={root}"]
    for key, value in sorted((extra_env or {}).items()):
        env_lines.append(f"Environment={key}={value}")
    return "\n".join([
        "[Unit]",
        f"Description={description}",
        "After=local-fs.target",
        "",
        "[Service]",
        "Type=simple",
        "ExecStart=" + " ".join(f'\"{part}\"' for part in command),
        "Restart=always",
        "RestartSec=2",
        *env_lines,
        "",
        "[Install]",
        "WantedBy=default.target",
        "",
    ])


def materialize_service(root: Path, *, interval_ms=DEFAULT_WORKER_INTERVAL_MS, system=None, env=None):
    name = (system or platform.system()).lower()
    values = dict(os.environ if env is None else env)
    carrier_command = _carrier_command(root)
    worker_command = _worker_command(root, interval_ms)
    rendezvous_env = _resident_rendezvous_env(values)
    worker_env = dict(rendezvous_env)
    source_root = str(values.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT") or "").strip()
    if source_root:
        source_path = Path(source_root).expanduser().resolve()
        if source_path == root.resolve():
            raise RuntimeError("canonical source root must remain distinct from resident runtime root")
        worker_env["STEGVERSE_HEARTBEAT_SOURCE_ROOT"] = str(source_path)
    for key in WORKER_SAFE_LOCAL_BINDINGS:
        value = str(values.get(key) or "").strip()
        if value:
            worker_env[key] = value

    if name == "linux":
        base = Path(values.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "systemd" / "user"
        carrier_path = base / "stegverse-heartbeat.service"
        worker_path = base / "stegverse-worker-runtime.service"
        carrier_content = _systemd_unit("StegVerse oscillator-produced non-authorizing heartbeat carrier", carrier_command, root)
        worker_content = _systemd_unit("StegVerse worker control-plane runtime", worker_command, root, worker_env)
        activation_commands = [
            ["systemctl", "--user", "daemon-reload"],
            ["systemctl", "--user", "enable", "--now", carrier_path.name],
            ["systemctl", "--user", "enable", "--now", worker_path.name],
        ]
        carrier_success_index, worker_success_index = 1, 2
        kind = "systemd-user-separated"
    elif name == "darwin":
        base = Path.home() / "Library" / "LaunchAgents"
        carrier_path = base / "org.stegverse.heartbeat.plist"
        worker_path = base / "org.stegverse.worker-runtime.plist"
        uid = getattr(os, "getuid", lambda: int(values.get("UID", "0")))()
        domain = f"gui/{uid}"
        carrier_content = plistlib.dumps({
            "Label": "org.stegverse.heartbeat",
            "ProgramArguments": carrier_command,
            "RunAtLoad": True,
            "KeepAlive": True,
            "EnvironmentVariables": {"STEGVERSE_HEARTBEAT_ROOT": str(root)},
            "StandardOutPath": str(root / "receipts" / "sovereign-host" / "carrier.stdout.log"),
            "StandardErrorPath": str(root / "receipts" / "sovereign-host" / "carrier.stderr.log"),
        }).decode()
        worker_content = plistlib.dumps({
            "Label": "org.stegverse.worker-runtime",
            "ProgramArguments": worker_command,
            "RunAtLoad": True,
            "KeepAlive": True,
            "EnvironmentVariables": {"STEGVERSE_HEARTBEAT_ROOT": str(root), **worker_env},
            "StandardOutPath": str(root / "receipts" / "sovereign-host" / "worker.stdout.log"),
            "StandardErrorPath": str(root / "receipts" / "sovereign-host" / "worker.stderr.log"),
        }).decode()
        activation_commands = [
            ["launchctl", "bootout", domain, str(carrier_path)],
            ["launchctl", "bootstrap", domain, str(carrier_path)],
            ["launchctl", "bootout", domain, str(worker_path)],
            ["launchctl", "bootstrap", domain, str(worker_path)],
        ]
        carrier_success_index, worker_success_index = 1, 3
        kind = "launch-agent-separated"
    elif name == "windows":
        base = Path(values.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "StegVerse"
        carrier_path = base / "heartbeat-start.cmd"
        worker_path = base / "worker-runtime-start.cmd"
        carrier_content = "@echo off\r\n" + subprocess.list2cmdline(carrier_command) + "\r\n"
        worker_prefix = "".join(f"set {key}={value}\r\n" for key, value in sorted(worker_env.items()))
        worker_content = "@echo off\r\n" + worker_prefix + subprocess.list2cmdline(worker_command) + "\r\n"
        activation_commands = [
            ["schtasks", "/Create", "/F", "/SC", "ONLOGON", "/TN", "StegVerse Heartbeat", "/TR", str(carrier_path)],
            ["schtasks", "/Create", "/F", "/SC", "ONLOGON", "/TN", "StegVerse Worker Runtime", "/TR", str(worker_path)],
        ]
        carrier_success_index, worker_success_index = 0, 1
        kind = "scheduled-task-separated"
    else:
        raise RuntimeError(f"unsupported sovereign host platform: {name}")

    carrier_path.parent.mkdir(parents=True, exist_ok=True)
    carrier_path.write_text(carrier_content, encoding="utf-8")
    worker_path.parent.mkdir(parents=True, exist_ok=True)
    worker_path.write_text(worker_content, encoding="utf-8")
    return {
        "schema": "stegverse.sovereign-heartbeat-service/v4",
        "platform": name,
        "registration_kind": kind,
        "registration_path": str(carrier_path),
        "carrier_registration_path": str(carrier_path),
        "worker_registration_path": str(worker_path),
        "carrier_command": carrier_command,
        "worker_command": worker_command,
        "activation_commands": activation_commands,
        "carrier_success_index": carrier_success_index,
        "worker_success_index": worker_success_index,
        "runtime_root": str(root),
        "canonical_runtime": CANONICAL_RUNTIME,
        "canonical_carrier_runtime": CANONICAL_CARRIER_RUNTIME,
        "worker_runtime": WORKER_RUNTIME,
        "heartbeat_production_mode": "OSCILLATOR_PHASE_DRIVEN",
        "heartbeat_period_ms": OSCILLATOR_PERIOD_MS,
        "heartbeat_reference_frequency_hz": OSCILLATOR_FREQUENCY_HZ,
        "heartbeat_interval_argument_controls_progression": False,
        "worker_interval_ms": float(interval_ms),
        "nominal_carrier_references_per_second": OSCILLATOR_FREQUENCY_HZ,
        "nominal_worker_ticks_per_second": _nominal_ticks_per_second(float(interval_ms)),
        "native_process_supervision_only": True,
        "separate_carrier_and_worker_processes": True,
        "heartbeat_grants_execution_authority": False,
        "carrier_epoch_controls_worker_expiry": False,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "non_tv_tvc_secret_or_token_used": False,
        "third_party_process_host_required": False,
        "third_party_deployment_required": False,
        "third_party_scheduler_required": False,
        "render_production_runtime_used": False,
        "manual_action_required": False,
        "resident_rendezvous_configured": bool(rendezvous_env),
        "native_local_source_refresh_configured": bool(worker_env.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT")),
        "canonical_local_source_root": worker_env.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT"),
        "safe_local_worker_bindings": sorted(key for key in WORKER_SAFE_LOCAL_BINDINGS if worker_env.get(key)),
        "resident_rendezvous_url": rendezvous_env.get("STEGVERSE_RESIDENT_RENDEZVOUS_URL"),
        "resident_rendezvous_node_ref": rendezvous_env.get("STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF"),
        "resident_rendezvous_grants_execution_authority": False,
    }


def install(source_root, target_root, runner=subprocess.run, *, interval_ms=DEFAULT_WORKER_INTERVAL_MS, system=None, env=None):
    materialization = materialize(source_root, target_root, interval_ms=interval_ms)
    service = materialize_service(target_root, interval_ms=interval_ms, system=system, env=env)
    results = []
    for command in service["activation_commands"]:
        completed = runner(command, check=False, capture_output=True, text=True)
        results.append({"command": command, "returncode": completed.returncode})
    carrier_index = int(service["carrier_success_index"])
    worker_index = int(service["worker_success_index"])
    carrier_active = len(results) > carrier_index and results[carrier_index]["returncode"] == 0
    worker_active = len(results) > worker_index and results[worker_index]["returncode"] == 0
    receipt = {
        **materialization,
        **service,
        "activation_results": results,
        "carrier_active": carrier_active,
        "worker_active": worker_active,
        "active": carrier_active and worker_active,
    }
    path = target_root / "receipts" / "sovereign-host" / "activation.latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--interval-ms", type=float, default=DEFAULT_WORKER_INTERVAL_MS, help="WorkerCoordinator interval only; heartbeat remains fixed at 10 ms oscillator phase.")
    parser.add_argument("--materialize-only", action="store_true")
    args = parser.parse_args()
    root = (args.runtime_root or default_runtime_root()).resolve()
    if args.interval_ms < 0:
        raise SystemExit("interval-ms must be >= 0")
    if args.materialize_only:
        result = materialize(args.source_root, root, interval_ms=args.interval_ms)
        result["service"] = materialize_service(root, interval_ms=args.interval_ms)
    else:
        result = install(args.source_root, root, interval_ms=args.interval_ms)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("active", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
