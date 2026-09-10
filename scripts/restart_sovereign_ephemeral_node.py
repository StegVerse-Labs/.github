#!/usr/bin/env python3
"""Restart one StegVerse ephemeral logical node with separated v13 runtimes.

This helper is local-process supervision. It has no provider, repository-token,
cloud-host, credential, route, wallet, or publication authority. The runtime root
is the complete isolation boundary for one logical node. A valid v13 logical node
runs both the non-authorizing carrier and the separate task-capable worker
coordinator. Merely spawning a worker PID is not sufficient: the worker runtime
state must advance after the spawned run_worker_runtime.py process starts.

Ephemeral child processes never inherit the complete parent environment. Only an
explicit non-secret process/runtime allowlist is forwarded. Teardown verifies both
separated processes are dead and records that observation without deleting governed
durable evidence. A fresh ephemeral instance must use a previously unused/empty
runtime root; intentional same-node continuity uses restart() on the existing root.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping

PROCESS_RECEIPT = Path("receipts/sovereign-host/ephemeral-process.latest.json")
TEARDOWN_RECEIPT = Path("receipts/sovereign-host/ephemeral-process-teardown.latest.json")
WORKER_STATE = Path("control/worker-runtime-state.json")

# Compatibility export retained for existing callers/tests. These names are not
# forwarded with blank values; they are absent from the child environment.
FORBIDDEN_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN")
SAFE_PROCESS_ENV = (
    "PATH", "HOME", "USER", "LOGNAME", "SHELL", "PYTHONPATH", "LANG", "LC_ALL",
    "TMPDIR", "XDG_CONFIG_HOME", "XDG_STATE_HOME", "LOCALAPPDATA", "UID",
)
SAFE_STEGVERSE_ENV = (
    "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_MICRO_NODE_RUNTIME_ROOT",
    "STEGVERSE_TVC_ROOT",
    "STEGVERSE_TV_ROOT",
    "STEGVERSE_STEGOPS_ORCHESTRATOR_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT",
    "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT",
    "STEGVERSE_HIL_STATE_ROOT",
    "STEGVERSE_HIL_RECEIVER_PORT",
    "STEGVERSE_ARA_MAIL_RECIPIENT",
    "STEGVERSE_ARA_MAIL_SENDER",
    "STEGVERSE_SV_DN1_SOURCE_ROOT",
    "STEGVERSE_SOURCE_MATERIALIZATION_ROOT",
    "STEGVERSE_SOURCE_PACKAGE_ROOT",
    "STEGVERSE_SV_DN1_MATERIALIZED_SOURCE_ROOT",
    "STEGVERSE_SV_DN1_RESIDENT_STATE_ROOT",
    "STEGVERSE_SV_DN1_INTR_STATE_ROOT",
    "STEGVERSE_SDK_SOURCE_ROOT",
    "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "STEGVERSE_CORE_LITE_SOURCE_ROOT",
    "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    "STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT",
    "STEGVERSE_BOOTSTRAP_V1_SOURCE_IDENTITY_FREEZE_STATE_ROOT",
    "STEGVERSE_BOOTSTRAP_V1_RELEASE_CANDIDATE_STATE_ROOT",
    "STEGVERSE_BOOTSTRAP_V1_INTR_ROUTE_CONFIG",
    "STEGVERSE_STEGOS_ROOT",
    "STEGVERSE_KV_SOURCE_ROOT",
    "STEGVERSE_KV_ROOT",
    "STEGVERSE_SITE_ROOT",
    "STEGVERSE_STEGINDEX_SOURCE_ROOT",
    "STEGVERSE_REPO_ROOTS_JSON",
    "STEGVERSE_HEALER_ROOT",
    "STEGVERSE_HIL_INTR_ROUTE_CONFIG",
    "STEGVERSE_EVALUATOR_INTR_ROUTE_CONFIG",
    "STEGVERSE_EVALUATOR_INTR_PORT",
    "STEGVERSE_EVALUATOR_INTR_WINDOW_SECONDS",
    "STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG",
    "STEGVERSE_SV002_OBSERVE_PORT",
    "STEGVERSE_RELAY_RUNTIME_BASE",
    "STEGVERSE_TT_ROOT",
    "STEGVERSE_RTG_ROOT",
    "STEGVERSE_GTG_ROOT",
    "STEGVERSE_AE_ROOT",
    "STEGVERSE_SELF_CHAR_MODEL_ENDPOINT",
    "STEGVERSE_SELF_CHAR_MODEL_ID",
    "STEGVERSE_OLLAMA_MODEL",
    "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT",
    "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_DISPATCH_STATE_ROOT",
    "STEGVERSE_TVC_SV_DN1_MERGE_SPOOL_ROOT",
    "STEGVERSE_RESIDENT_SOURCE_MANIFEST",
    "STEGVERSE_MASTER_RECORDS_ROOT",
    "STEGVERSE_ORG_CONTROL_ROOT",
    "STEGVERSE_SV002_ORG_ROOT",
    "STEGVERSE_SV001_AUTONOMY_LEASE",
    "STEGVERSE_SV011_ORG_ROOT",
    "STEGVERSE_SV011_MATERIALIZED_ROOT",
    "STEGVERSE_GLM53_ENDPOINT",
    "STEGVERSE_GLM53_MODEL_PATH",
    "STEGVERSE_GLM53_RUNTIME_IDENTITY",
    "STEGVERSE_GLM53_ENERGY_KWH",
    "STEGVERSE_GLM53_HARDWARE_AMORTIZATION_USD",
    "STEGVERSE_GLM53_ENERGY_COST_USD",
    "STEGVERSE_GLM53_STORAGE_NETWORK_RUNTIME_OVERHEAD_USD",
    "STEGVERSE_RELAY_EGRESS_BINDING",
    "STEGVERSE_RELAY_EGRESS_AUTHORIZATION",
    "STEGVERSE_RELAY_EGRESS_PAYLOAD",
    "STEGVERSE_RESIDENT_RENDEZVOUS_URL",
    "STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF",
    "STEGVERSE_SOVEREIGN_NODE_MARKER",
)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _alive(pid: int | None) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _terminate(pid: int | None, timeout: float = 2.0) -> bool:
    if not _alive(pid):
        return True
    try:
        os.kill(int(pid), signal.SIGTERM)
    except OSError:
        return True
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _alive(pid):
            return True
        time.sleep(0.02)
    try:
        os.kill(int(pid), signal.SIGKILL)
    except (OSError, AttributeError):
        pass
    return not _alive(pid)


def child_env(runtime_root: Path, source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Build a non-secret environment for an ephemeral carrier/worker child."""
    values = dict(os.environ if source is None else source)
    allowed = SAFE_PROCESS_ENV + SAFE_STEGVERSE_ENV
    env = {name: values[name] for name in allowed if values.get(name)}
    env["STEGVERSE_SOVEREIGN_NODE"] = "1"
    env["STEGVERSE_HEARTBEAT_ROOT"] = str(runtime_root.expanduser().resolve())
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    return env


def _child_env(runtime_root: Path) -> dict[str, str]:
    return child_env(runtime_root)


def assert_fresh_runtime_root(runtime_root: Path) -> None:
    """Fail closed if a new ephemeral instance would reuse an old runtime root."""
    root = runtime_root.expanduser().resolve()
    if not root.exists():
        return
    try:
        next(root.iterdir())
    except StopIteration:
        return
    raise RuntimeError("fresh_ephemeral_runtime_root_required")


def _spawn(command: list[str], runtime_root: Path, stdout_name: str, stderr_name: str, env: dict[str, str]):
    receipt_root = runtime_root / "receipts" / "sovereign-host"
    receipt_root.mkdir(parents=True, exist_ok=True)
    out_handle = (receipt_root / stdout_name).open("ab", buffering=0)
    err_handle = (receipt_root / stderr_name).open("ab", buffering=0)
    return subprocess.Popen(
        command,
        cwd=str(runtime_root),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=out_handle,
        stderr=err_handle,
        start_new_session=True,
        close_fds=True,
    )


def _runtime_tick(runtime_root: Path) -> int:
    value = _load(runtime_root / WORKER_STATE)
    tick = value.get("runtime_tick")
    return int(tick) if isinstance(tick, int) and not isinstance(tick, bool) else -1


def _wait_for_worker_tick(runtime_root: Path, baseline_tick: int, worker_pid: int, timeout: float = 3.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _alive(worker_pid):
            return {
                "observed": False,
                "reason": "WORKER_PROCESS_EXITED_BEFORE_TASK_CAPABLE_TICK",
                "baseline_tick": baseline_tick,
                "observed_tick": _runtime_tick(runtime_root),
            }
        current = _runtime_tick(runtime_root)
        if current > baseline_tick:
            state = _load(runtime_root / WORKER_STATE)
            return {
                "observed": True,
                "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_OBSERVED",
                "baseline_tick": baseline_tick,
                "observed_tick": current,
                "observed_carrier_epoch": state.get("last_observed_carrier_epoch"),
                "observed_carrier_generation": state.get("last_observed_carrier_generation"),
            }
        time.sleep(0.02)
    return {
        "observed": False,
        "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_TIMEOUT",
        "baseline_tick": baseline_tick,
        "observed_tick": _runtime_tick(runtime_root),
    }


def start(runtime_root: Path, *, interval_ms: float = 10.0, worker_tick_timeout: float = 3.0) -> dict[str, Any]:
    runtime_root = runtime_root.expanduser().resolve()
    carrier_runner = runtime_root / "scripts" / "run_heartbeat_runtime.py"
    worker_runner = runtime_root / "scripts" / "run_worker_runtime.py"
    if not carrier_runner.is_file():
        raise RuntimeError(f"materialized heartbeat carrier runner missing: {carrier_runner}")
    if not worker_runner.is_file():
        raise RuntimeError(f"materialized worker runtime runner missing: {worker_runner}")

    baseline_tick = _runtime_tick(runtime_root)
    carrier_command = [
        sys.executable,
        str(carrier_runner),
        "--root",
        str(runtime_root),
        "--continuous",
        "--interval-ms",
        str(interval_ms),
    ]
    worker_command = [
        sys.executable,
        str(worker_runner),
        "--root",
        str(runtime_root),
        "--continuous",
        "--interval-ms",
        str(interval_ms),
    ]
    env = _child_env(runtime_root)
    carrier = _spawn(
        carrier_command,
        runtime_root,
        "ephemeral-heartbeat.stdout.log",
        "ephemeral-heartbeat.stderr.log",
        env,
    )
    try:
        worker = _spawn(
            worker_command,
            runtime_root,
            "ephemeral-worker.stdout.log",
            "ephemeral-worker.stderr.log",
            env,
        )
    except Exception:
        _terminate(carrier.pid)
        raise

    worker_tick = _wait_for_worker_tick(runtime_root, baseline_tick, worker.pid, timeout=worker_tick_timeout)
    if not worker_tick.get("observed"):
        _terminate(worker.pid)
        _terminate(carrier.pid)
        raise RuntimeError(str(worker_tick.get("reason") or "TASK_CAPABLE_WORKER_RUNTIME_TICK_NOT_OBSERVED"))

    receipt = {
        "schema": "stegverse.ephemeral-sovereign-process/v4",
        "runtime_root": str(runtime_root),
        "pid": carrier.pid,
        "carrier_pid": carrier.pid,
        "worker_pid": worker.pid,
        "command": carrier_command,
        "carrier_command": carrier_command,
        "worker_command": worker_command,
        "interval_ms": interval_ms,
        "carrier_active": _alive(carrier.pid),
        "worker_active": _alive(worker.pid),
        "worker_task_capable_cycle_observed": True,
        "worker_tick_evidence": worker_tick,
        "active": _alive(carrier.pid) and _alive(worker.pid),
        "separate_carrier_and_worker_processes": True,
        "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        "worker_runtime": "heartbeat_runtime.worker_runtime.WorkerCoordinator",
        "supervision_kind": "STEGVERSE_EPHEMERAL_LOCAL_PROCESS",
        "third_party_process_host_required": False,
        "third_party_scheduler_required": False,
        "credential_requirement": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_used": False,
        "parent_environment_inherited": False,
        "child_environment_allowlist_enforced": True,
        "authority_effect": "LOCAL_RUNTIME_SUPERVISION_ONLY",
    }
    path = runtime_root / PROCESS_RECEIPT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def teardown(runtime_root: Path) -> dict[str, Any]:
    """Stop an ephemeral node and verify no supervised process survives.

    Governed durable evidence/state is intentionally retained. A successor ephemeral
    instance must use a fresh runtime root; restart() is the only same-root continuity
    operation.
    """
    runtime_root = runtime_root.expanduser().resolve()
    previous = _load(runtime_root / PROCESS_RECEIPT)
    previous_carrier_pid = previous.get("carrier_pid", previous.get("pid"))
    previous_worker_pid = previous.get("worker_pid")
    carrier_terminated = _terminate(previous_carrier_pid)
    worker_terminated = _terminate(previous_worker_pid)
    carrier_dead = not _alive(previous_carrier_pid)
    worker_dead = not _alive(previous_worker_pid)
    complete = carrier_terminated and worker_terminated and carrier_dead and worker_dead
    receipt = {
        "schema": "stegverse.ephemeral-sovereign-process-teardown/v1",
        "state": "TEARDOWN_COMPLETE" if complete else "TEARDOWN_INCOMPLETE",
        "runtime_root": str(runtime_root),
        "previous_carrier_pid": previous_carrier_pid,
        "previous_worker_pid": previous_worker_pid,
        "carrier_terminated": carrier_terminated,
        "worker_terminated": worker_terminated,
        "carrier_dead_verified": carrier_dead,
        "worker_dead_verified": worker_dead,
        "no_supervised_process_residue": complete,
        "durable_evidence_deleted": False,
        "same_root_reinstantiation_allowed": False,
        "same_root_continuation_requires_restart": True,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_TEARDOWN_OBSERVATION_ONLY",
    }
    path = runtime_root / TEARDOWN_RECEIPT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def restart(runtime_root: Path, *, interval_ms: float = 10.0, worker_tick_timeout: float = 3.0) -> dict[str, Any]:
    runtime_root = runtime_root.expanduser().resolve()
    previous = _load(runtime_root / PROCESS_RECEIPT)
    previous_carrier_pid = previous.get("carrier_pid", previous.get("pid"))
    previous_worker_pid = previous.get("worker_pid")
    carrier_terminated = _terminate(previous_carrier_pid)
    worker_terminated = _terminate(previous_worker_pid)
    if not (carrier_terminated and worker_terminated):
        raise RuntimeError("previous_ephemeral_process_teardown_incomplete")
    fresh = start(runtime_root, interval_ms=interval_ms, worker_tick_timeout=worker_tick_timeout)
    fresh["previous_pid"] = previous_carrier_pid
    fresh["previous_carrier_pid"] = previous_carrier_pid
    fresh["previous_worker_pid"] = previous_worker_pid
    fresh["previous_process_terminated"] = True
    fresh["carrier_restart_observed"] = fresh["carrier_pid"] != previous_carrier_pid
    fresh["worker_restart_observed"] = fresh["worker_pid"] != previous_worker_pid
    fresh["restart_observed"] = (
        fresh["carrier_restart_observed"]
        and fresh["worker_restart_observed"]
        and fresh.get("worker_task_capable_cycle_observed") is True
    )
    (runtime_root / PROCESS_RECEIPT).write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return fresh


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--interval-ms", type=float, default=10.0)
    parser.add_argument("--worker-tick-timeout", type=float, default=3.0)
    parser.add_argument("--teardown", action="store_true")
    args = parser.parse_args()
    if args.interval_ms < 0 or args.worker_tick_timeout <= 0:
        raise SystemExit("interval-ms must be >= 0 and worker-tick-timeout must be > 0")
    if args.teardown:
        result = teardown(args.runtime_root)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("state") == "TEARDOWN_COMPLETE" else 1
    result = restart(
        args.runtime_root,
        interval_ms=args.interval_ms,
        worker_tick_timeout=args.worker_tick_timeout,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("restart_observed") else 1


if __name__ == "__main__":
    raise SystemExit(main())