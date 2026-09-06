#!/usr/bin/env python3
"""Produce sovereign activation proof for separated oscillator carrier/runtime.

Carrier continuity alone is not runtime activation. The proof requires the
oscillator-produced v13 carrier, the independently executing WorkerCoordinator,
and observable task-capable worker progress. Worker progress is downstream
runtime evidence and never heartbeat timing authority.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

Runner = Callable[..., subprocess.CompletedProcess[Any]]
OBSERVATION_ONLY_MODE = "CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION"
CANONICAL_CARRIER_RUNTIME = "heartbeat_runtime.engine_v13.HeartbeatRuntime"
CANONICAL_WORKER_RUNTIME = "heartbeat_runtime.worker_runtime.WorkerCoordinator"
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
THIRD_PARTY_ENV_VARS = (
    "GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def proof_path(env: dict[str, str] | None = None) -> Path:
    values = dict(os.environ if env is None else env)
    override = values.get("STEGVERSE_SOVEREIGN_PROOF_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".stegverse" / "heartbeat" / "activation.latest.json").resolve()


def third_party_hosted_environment(env: dict[str, str] | None = None) -> bool:
    values = dict(os.environ if env is None else env)
    return any(str(values.get(name, "")).strip().lower() not in ("", "0", "false", "no") for name in THIRD_PARTY_ENV_VARS)


def sovereign_node_declared(env: dict[str, str] | None = None) -> bool:
    values = dict(os.environ if env is None else env)
    if str(values.get("STEGVERSE_SOVEREIGN_NODE", "")).strip().lower() in ("1", "true", "yes"):
        return True
    return any(path.is_file() for path in (Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json"))


def _epoch_generation(state: dict) -> tuple[int, int]:
    return int(state.get("epoch", -1)), int(state.get("generation", -1))


def _runtime_tick(state: dict) -> int:
    value = state.get("runtime_tick")
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else -1


def _worker_task_capable(state: dict) -> bool:
    return (
        state.get("schema") == "stegverse.worker-runtime-state/v1"
        and _runtime_tick(state) >= 0
        and state.get("observation_mode") != OBSERVATION_ONLY_MODE
    )


def _oscillator_carrier(state: dict) -> bool:
    oscillator = state.get("oscillator") or {}
    return (
        state.get("schema") == "stegverse.heartbeat-carrier-runtime-state/v1"
        and state.get("frequency_rule") == "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL"
        and oscillator.get("mechanism") == "INDEPENDENT_PHASE_OSCILLATOR"
        and oscillator.get("period_ns") == 10_000_000
        and oscillator.get("reference_frequency_hz") == 100
        and oscillator.get("progression_dependency") == "OSCILLATOR_ONLY"
        and oscillator.get("downstream_gating") is False
        and oscillator.get("observation_is_causal") is False
        and oscillator.get("snapshot_is_observation_only") is True
        and oscillator.get("sampled_reference_epoch") == state.get("epoch")
    )


def _active_leases(control_plane: dict) -> list[dict]:
    return list((((control_plane.get("worker_coordination") or {}).get("active_leases")) or []))


def no_duplicate_claim_or_fence(control_plane: dict) -> bool:
    leases = _active_leases(control_plane)
    claims = [row.get("claim_id") for row in leases if row.get("claim_id")]
    fences = [row.get("fencing_token") for row in leases if isinstance(row.get("fencing_token"), int)]
    instances = [row.get("worker_instance_id") for row in leases if row.get("worker_instance_id")]
    return len(claims) == len(set(claims)) and len(fences) == len(set(fences)) and len(instances) == len(set(instances))


def worker_coordination_observed(control_plane: dict, runtime_root: Path) -> bool:
    coordination = control_plane.get("worker_coordination") or {}
    if coordination.get("state") not in {"ACTIVE", "IDLE"}:
        return False
    if coordination.get("worker_registry_ref") != "control/worker-registry.json":
        return False
    checkpoint_root = runtime_root / "checkpoints" / "workers"
    worker_runtime_state = runtime_root / "control" / "worker-runtime-state.json"
    return worker_runtime_state.is_file() or (checkpoint_root.is_dir() and any(checkpoint_root.rglob("*.json")))


def restart_commands(*, service_receipt: dict | None = None, system: str | None = None, env: dict[str, str] | None = None) -> list[list[str]]:
    service = service_receipt or {}
    if service.get("registration_kind") == "stegverse-ephemeral-console":
        command = service.get("restart_command")
        if isinstance(command, list) and command and all(isinstance(item, str) and item for item in command):
            return [list(command)]
        raise RuntimeError("ephemeral console service receipt missing restart_command")

    name = (system or platform.system()).lower()
    values = dict(os.environ if env is None else env)
    if name == "linux":
        return [
            ["systemctl", "--user", "restart", "stegverse-heartbeat.service"],
            ["systemctl", "--user", "restart", "stegverse-worker-runtime.service"],
        ]
    if name == "darwin":
        uid = getattr(os, "getuid", lambda: int(values.get("UID", "0")))()
        domain = f"gui/{uid}"
        return [
            ["launchctl", "kickstart", "-k", f"{domain}/org.stegverse.heartbeat"],
            ["launchctl", "kickstart", "-k", f"{domain}/org.stegverse.worker-runtime"],
        ]
    if name == "windows":
        return [
            ["schtasks", "/Run", "/TN", "StegVerse Heartbeat"],
            ["schtasks", "/Run", "/TN", "StegVerse Worker Runtime"],
        ]
    raise RuntimeError(f"unsupported sovereign host platform: {name}")


def _local_supervision_active(service: dict) -> bool:
    if service.get("active") is not True or service.get("third_party_process_host_required") is not False:
        return False
    if service.get("registration_kind") == "stegverse-ephemeral-console":
        return service.get("stegverse_process_supervision") is True
    return (
        service.get("native_process_supervision_only") is True
        and service.get("separate_carrier_and_worker_processes") is True
        and service.get("carrier_active") is True
        and service.get("worker_active") is True
    )


def evaluate_runtime(
    runtime_root: Path,
    *,
    runner: Runner = subprocess.run,
    sleeper: Callable[[float], None] = time.sleep,
    observe_seconds: float = 0.15,
    restart_seconds: float = 0.25,
    system: str | None = None,
    env: dict[str, str] | None = None,
) -> dict:
    root = runtime_root.expanduser().resolve()
    values = dict(os.environ if env is None else env)
    hosted = third_party_hosted_environment(values)
    declared = sovereign_node_declared(values)
    carrier_path = root / "control" / "heartbeat-carrier-runtime-state.json"
    legacy_path = root / "control" / "heartbeat-state.json"
    control_plane_path = root / "control" / "worker-control-plane-coordination.json"
    worker_state_path = root / "control" / "worker-runtime-state.json"
    registry_path = root / "control" / "worker-registry.json"
    materialization_path = root / "receipts" / "sovereign-host" / "materialization.latest.json"
    service_path = root / "receipts" / "sovereign-host" / "activation.latest.json"

    predicates = {name: False for name in REQUIRED_PREDICATES}
    detail: dict[str, Any] = {
        "runtime_root": str(root),
        "third_party_hosted_environment": hosted,
        "sovereign_node_declared": declared,
        "third_party_runtime_required": False,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "non_tv_tvc_secret_or_token_used": False,
        "carrier_state_ref": "control/heartbeat-carrier-runtime-state.json",
        "worker_control_plane_ref": "control/worker-control-plane-coordination.json",
        "worker_state_ref": "control/worker-runtime-state.json",
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "worker_controls_heartbeat_progression": False,
    }
    if hosted or not declared:
        detail["ineligible_reason"] = "THIRD_PARTY_HOSTED_ENVIRONMENT" if hosted else "SOVEREIGN_NODE_DECLARATION_ABSENT"
        return {"predicates": predicates, "detail": detail}

    required_files = (
        root / "heartbeat_runtime" / "engine_v13.py",
        root / "heartbeat_runtime" / "independent_oscillator.py",
        root / "heartbeat_runtime" / "oscillator_producer.py",
        root / "heartbeat_runtime" / "worker_runtime.py",
        root / "scripts" / "run_heartbeat_runtime.py",
        root / "scripts" / "run_worker_runtime.py",
        carrier_path,
        legacy_path,
        control_plane_path,
        registry_path,
        worker_state_path,
        materialization_path,
        service_path,
    )
    predicates["runtime_materialized"] = all(path.is_file() for path in required_files)
    if not predicates["runtime_materialized"]:
        detail["ineligible_reason"] = "RUNTIME_NOT_MATERIALIZED"
        detail["missing_runtime_files"] = [str(path) for path in required_files if not path.is_file()]
        return {"predicates": predicates, "detail": detail}

    materialization = load_json(materialization_path)
    service = load_json(service_path)
    if materialization.get("canonical_carrier_runtime") != CANONICAL_CARRIER_RUNTIME:
        detail["ineligible_reason"] = "CARRIER_RUNTIME_BINDING_MISMATCH"
        return {"predicates": predicates, "detail": detail}
    if materialization.get("worker_runtime") != CANONICAL_WORKER_RUNTIME:
        detail["ineligible_reason"] = "WORKER_RUNTIME_BINDING_MISMATCH"
        return {"predicates": predicates, "detail": detail}
    if materialization.get("heartbeat_production_mode") != "OSCILLATOR_PHASE_DRIVEN":
        detail["ineligible_reason"] = "OSCILLATOR_PRODUCER_BINDING_MISSING"
        return {"predicates": predicates, "detail": detail}
    if materialization.get("heartbeat_interval_argument_controls_progression") is not False:
        detail["ineligible_reason"] = "INTERVAL_ARGUMENT_REGAINED_HEARTBEAT_AUTHORITY"
        return {"predicates": predicates, "detail": detail}
    predicates["native_service_active"] = _local_supervision_active(service)

    legacy_before = legacy_path.read_bytes()
    before = load_json(carrier_path)
    worker_before = load_json(worker_state_path)
    registry_before = load_json(registry_path)
    e0, g0 = _epoch_generation(before)
    wt0 = _runtime_tick(worker_before)
    detail["oscillator_carrier_before"] = _oscillator_carrier(before)

    sleeper(observe_seconds)
    observed = load_json(carrier_path)
    worker_observed_state = load_json(worker_state_path)
    control_observed = load_json(control_plane_path)
    e1, g1 = _epoch_generation(observed)
    wt1 = _runtime_tick(worker_observed_state)
    predicates["heartbeat_epoch_advanced"] = e1 > e0 and _oscillator_carrier(observed)
    predicates["worker_task_capable_cycle_observed"] = _worker_task_capable(worker_observed_state) and wt1 > wt0
    predicates["continuous_runtime_live"] = (
        predicates["native_service_active"]
        and predicates["heartbeat_epoch_advanced"]
        and predicates["worker_task_capable_cycle_observed"]
    )
    predicates["worker_coordination_checkpoint_observed"] = worker_coordination_observed(control_observed, root)

    commands = restart_commands(service_receipt=service, system=system, env=values)
    results = []
    for command in commands:
        completed = runner(command, check=False, capture_output=True, text=True)
        results.append({"command": command, "returncode": completed.returncode})
    predicates["controlled_restart_observed"] = bool(results) and all(row["returncode"] == 0 for row in results)
    detail["restart_results"] = results

    sleeper(restart_seconds)
    after = load_json(carrier_path)
    worker_after = load_json(worker_state_path)
    control_after = load_json(control_plane_path)
    registry_after = load_json(registry_path)
    e2, g2 = _epoch_generation(after)
    wt2 = _runtime_tick(worker_after)
    predicates["epoch_and_generation_non_regressing"] = e2 >= e1 and g2 >= g1 and e1 >= e0 and g1 >= g0
    predicates["no_duplicate_claim_or_fence"] = no_duplicate_claim_or_fence(control_after)
    before_tasks = {row.get("task_id") for row in registry_before.get("tasks", []) if row.get("task_id")}
    after_tasks = {row.get("task_id") for row in registry_after.get("tasks", []) if row.get("task_id")}
    legacy_unchanged = legacy_path.read_bytes() == legacy_before
    worker_progress_after_restart = _worker_task_capable(worker_after) and wt2 > wt1
    predicates["state_reconstruction_pass"] = (
        predicates["controlled_restart_observed"]
        and predicates["epoch_and_generation_non_regressing"]
        and _oscillator_carrier(after)
        and worker_progress_after_restart
        and before_tasks == after_tasks
        and worker_coordination_observed(control_after, root)
        and legacy_unchanged
        and int(load_json(legacy_path).get("epoch", -1)) == 29
    )
    detail.update({
        "registration_kind": service.get("registration_kind"),
        "carrier_active": service.get("carrier_active"),
        "worker_active": service.get("worker_active"),
        "epoch_before": e0,
        "epoch_observed": e1,
        "epoch_after_restart": e2,
        "generation_before": g0,
        "generation_observed": g1,
        "generation_after_restart": g2,
        "worker_runtime_tick_before": wt0,
        "worker_runtime_tick_observed": wt1,
        "worker_runtime_tick_after_restart": wt2,
        "worker_observation_mode": worker_observed_state.get("observation_mode"),
        "worker_progress_after_restart": worker_progress_after_restart,
        "legacy_hb29_unchanged": legacy_unchanged,
        "oscillator_carrier_observed": _oscillator_carrier(observed),
        "oscillator_carrier_after_restart": _oscillator_carrier(after),
        "active_control_lease_count": len(_active_leases(control_after)),
    })
    return {"predicates": predicates, "detail": detail}


def verify(runtime_root: Path, **kwargs: Any) -> dict:
    evaluated = evaluate_runtime(runtime_root, **kwargs)
    predicates = evaluated["predicates"]
    body = {
        "schema": "stegverse.sovereign-runtime-activation-proof/v4",
        **predicates,
        "all_predicates_pass": all(predicates.values()),
        "heartbeat_progression_dependency": "OSCILLATOR_ONLY",
        "third_party_runtime_required": False,
        "physical_additional_machine_required": False,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "non_tv_tvc_secret_or_token_used": False,
        "github_token_runtime_authority": "NONE",
        "render_production_runtime_used": False,
        "detail": evaluated["detail"],
    }
    path = proof_path(kwargs.get("env"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    body["proof_path"] = str(path)
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--observe-seconds", type=float, default=0.15)
    parser.add_argument("--restart-seconds", type=float, default=0.25)
    args = parser.parse_args()
    result = verify(args.runtime_root, observe_seconds=args.observe_seconds, restart_seconds=args.restart_seconds)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_predicates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
