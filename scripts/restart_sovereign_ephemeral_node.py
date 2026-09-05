#!/usr/bin/env python3
"""Restart one StegVerse ephemeral logical node with separated v13 runtimes.

This helper is local-process supervision. It has no provider, repository-token,
cloud-host, credential, route, wallet, or publication authority. The runtime root
is the complete isolation boundary for one logical node. A valid v13 logical node
runs both the non-authorizing carrier and the separate task-capable worker
coordinator. Merely spawning a worker PID is not sufficient: the worker runtime
state must advance after the spawned run_worker_runtime.py process starts.
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
from typing import Any

PROCESS_RECEIPT = Path("receipts/sovereign-host/ephemeral-process.latest.json")
WORKER_STATE = Path("control/worker-runtime-state.json")
FORBIDDEN_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN")


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


def _child_env(runtime_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    for name in FORBIDDEN_ENV:
        env[name] = ""
    env["STEGVERSE_SOVEREIGN_NODE"] = "1"
    env["STEGVERSE_HEARTBEAT_ROOT"] = str(runtime_root)
    return env


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
        "schema": "stegverse.ephemeral-sovereign-process/v3",
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
        "authority_effect": "LOCAL_RUNTIME_SUPERVISION_ONLY",
    }
    path = runtime_root / PROCESS_RECEIPT
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
    fresh = start(runtime_root, interval_ms=interval_ms, worker_tick_timeout=worker_tick_timeout)
    fresh["previous_pid"] = previous_carrier_pid
    fresh["previous_carrier_pid"] = previous_carrier_pid
    fresh["previous_worker_pid"] = previous_worker_pid
    fresh["previous_process_terminated"] = carrier_terminated and worker_terminated
    fresh["carrier_restart_observed"] = carrier_terminated and fresh["carrier_pid"] != previous_carrier_pid
    fresh["worker_restart_observed"] = worker_terminated and fresh["worker_pid"] != previous_worker_pid
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
    args = parser.parse_args()
    if args.interval_ms < 0 or args.worker_tick_timeout <= 0:
        raise SystemExit("interval-ms must be >= 0 and worker-tick-timeout must be > 0")
    result = restart(
        args.runtime_root,
        interval_ms=args.interval_ms,
        worker_tick_timeout=args.worker_tick_timeout,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("restart_observed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
