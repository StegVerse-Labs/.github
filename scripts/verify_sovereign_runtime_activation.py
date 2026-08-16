#!/usr/bin/env python3
"""Produce the nine-predicate sovereign heartbeat activation proof on a real node.

This verifier is node-local. It never treats GitHub Actions, Render, Cloudflare,
or another hosted platform as production evidence. It observes live heartbeat
advance, performs one controlled local-supervision restart, verifies non-regression
and registry continuity, and writes activation.latest.json for the heartbeat
activation worker to consume.

A StegVerse ephemeral logical node is an allowed local supervision mode when its
service receipt binds an explicit local restart command and no third-party process
host. This removes any physical second/third-machine requirement without weakening
the hosted-environment rejection boundary.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Callable, Any

Runner = Callable[..., subprocess.CompletedProcess[Any]]
REQUIRED_PREDICATES = (
    "runtime_materialized",
    "native_service_active",
    "continuous_runtime_live",
    "heartbeat_epoch_advanced",
    "worker_coordination_checkpoint_observed",
    "controlled_restart_observed",
    "epoch_and_generation_non_regressing",
    "no_duplicate_claim_or_fence",
    "state_reconstruction_pass",
)
THIRD_PARTY_ENV_VARS = (
    "GITHUB_ACTIONS",
    "RENDER",
    "RENDER_SERVICE_ID",
    "VERCEL",
    "CF_PAGES",
    "CLOUDFLARE_WORKERS",
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
    explicit = str(values.get("STEGVERSE_SOVEREIGN_NODE", "")).strip().lower()
    if explicit in ("1", "true", "yes"):
        return True
    markers = (
        Path("/etc/stegverse/node.json"),
        Path.home() / ".stegverse" / "node.json",
    )
    return any(path.is_file() for path in markers)


def _epoch_generation(state: dict) -> tuple[int, int]:
    return int(state.get("epoch", -1)), int(state.get("generation", -1))


def _active_leases(state: dict) -> list[dict]:
    return list((((state.get("subsignals") or {}).get("worker_coordination") or {}).get("active_leases") or []))


def no_duplicate_claim_or_fence(state: dict) -> bool:
    leases = _active_leases(state)
    claims = [row.get("claim_id") for row in leases if row.get("claim_id")]
    fences = [row.get("fencing_token") for row in leases if isinstance(row.get("fencing_token"), int)]
    instances = [row.get("worker_instance_id") for row in leases if row.get("worker_instance_id")]
    return len(claims) == len(set(claims)) and len(fences) == len(set(fences)) and len(instances) == len(set(instances))


def worker_coordination_observed(state: dict, runtime_root: Path) -> bool:
    coordination = ((state.get("subsignals") or {}).get("worker_coordination") or {})
    if coordination.get("state") != "ACTIVE":
        return False
    checkpoint_root = runtime_root / "checkpoints" / "workers"
    return checkpoint_root.is_dir() and any(checkpoint_root.rglob("*.json"))


def restart_command(
    *,
    service_receipt: dict | None = None,
    system: str | None = None,
    env: dict[str, str] | None = None,
) -> list[str]:
    service = service_receipt or {}
    if service.get("registration_kind") == "stegverse-ephemeral-console":
        command = service.get("restart_command")
        if isinstance(command, list) and command and all(isinstance(item, str) and item for item in command):
            return list(command)
        raise RuntimeError("ephemeral console service receipt missing restart_command")

    name = (system or platform.system()).lower()
    values = dict(os.environ if env is None else env)
    if name == "linux":
        return ["systemctl", "--user", "restart", "stegverse-heartbeat.service"]
    if name == "darwin":
        uid = getattr(os, "getuid", lambda: int(values.get("UID", "0")))()
        return ["launchctl", "kickstart", "-k", f"gui/{uid}/org.stegverse.heartbeat"]
    if name == "windows":
        return ["schtasks", "/Run", "/TN", "StegVerse Heartbeat"]
    raise RuntimeError(f"unsupported sovereign host platform: {name}")


def _local_supervision_active(service_receipt: dict) -> bool:
    if service_receipt.get("active") is not True:
        return False
    if service_receipt.get("third_party_process_host_required") is not False:
        return False
    if service_receipt.get("registration_kind") == "stegverse-ephemeral-console":
        return service_receipt.get("stegverse_process_supervision") is True
    return service_receipt.get("native_process_supervision_only") is True


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
    runtime_root = runtime_root.expanduser().resolve()
    values = dict(os.environ if env is None else env)
    hosted = third_party_hosted_environment(values)
    declared = sovereign_node_declared(values)
    state_path = runtime_root / "control" / "heartbeat-state.json"
    registry_path = runtime_root / "control" / "worker-registry.json"
    materialization_path = runtime_root / "receipts" / "sovereign-host" / "materialization.latest.json"
    service_path = runtime_root / "receipts" / "sovereign-host" / "activation.latest.json"

    predicates = {name: False for name in REQUIRED_PREDICATES}
    detail: dict[str, Any] = {
        "runtime_root": str(runtime_root),
        "third_party_hosted_environment": hosted,
        "sovereign_node_declared": declared,
        "third_party_runtime_required": False,
    }

    if hosted or not declared:
        detail["ineligible_reason"] = "THIRD_PARTY_HOSTED_ENVIRONMENT" if hosted else "SOVEREIGN_NODE_DECLARATION_ABSENT"
        return {"predicates": predicates, "detail": detail}

    required_files = (
        runtime_root / "heartbeat_runtime" / "engine_v11.py",
        runtime_root / "scripts" / "run_heartbeat_runtime.py",
        state_path,
        registry_path,
        materialization_path,
        service_path,
    )
    predicates["runtime_materialized"] = all(path.is_file() for path in required_files)
    if not predicates["runtime_materialized"]:
        detail["ineligible_reason"] = "RUNTIME_NOT_MATERIALIZED"
        detail["missing_runtime_files"] = [str(path) for path in required_files if not path.is_file()]
        return {"predicates": predicates, "detail": detail}

    service_receipt = load_json(service_path)
    predicates["native_service_active"] = _local_supervision_active(service_receipt)
    detail["registration_kind"] = service_receipt.get("registration_kind")
    detail["stegverse_process_supervision"] = service_receipt.get("stegverse_process_supervision") is True

    before = load_json(state_path)
    registry_before = load_json(registry_path)
    e0, g0 = _epoch_generation(before)
    sleeper(observe_seconds)
    observed = load_json(state_path)
    e1, g1 = _epoch_generation(observed)
    predicates["heartbeat_epoch_advanced"] = e1 > e0
    predicates["continuous_runtime_live"] = predicates["native_service_active"] and e1 > e0
    predicates["worker_coordination_checkpoint_observed"] = worker_coordination_observed(observed, runtime_root)

    command = restart_command(service_receipt=service_receipt, system=system, env=values)
    completed = runner(command, check=False, capture_output=True, text=True)
    predicates["controlled_restart_observed"] = completed.returncode == 0
    detail["restart_command"] = command
    detail["restart_returncode"] = completed.returncode

    sleeper(restart_seconds)
    after = load_json(state_path)
    registry_after = load_json(registry_path)
    e2, g2 = _epoch_generation(after)
    predicates["epoch_and_generation_non_regressing"] = e2 >= e1 and g2 >= g1 and e1 >= e0 and g1 >= g0
    predicates["no_duplicate_claim_or_fence"] = no_duplicate_claim_or_fence(after)

    before_task_ids = {row.get("task_id") for row in registry_before.get("tasks", []) if row.get("task_id")}
    after_task_ids = {row.get("task_id") for row in registry_after.get("tasks", []) if row.get("task_id")}
    predicates["state_reconstruction_pass"] = (
        predicates["controlled_restart_observed"]
        and predicates["epoch_and_generation_non_regressing"]
        and before_task_ids == after_task_ids
        and worker_coordination_observed(after, runtime_root)
    )
    detail.update({
        "epoch_before": e0,
        "epoch_observed": e1,
        "epoch_after_restart": e2,
        "generation_before": g0,
        "generation_observed": g1,
        "generation_after_restart": g2,
    })
    return {"predicates": predicates, "detail": detail}


def verify(runtime_root: Path, **kwargs: Any) -> dict:
    evaluated = evaluate_runtime(runtime_root, **kwargs)
    predicates = evaluated["predicates"]
    body = {
        "schema": "stegverse.sovereign-runtime-activation-proof/v1",
        **predicates,
        "all_predicates_pass": all(predicates.values()),
        "third_party_runtime_required": False,
        "physical_additional_machine_required": False,
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
