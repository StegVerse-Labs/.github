#!/usr/bin/env python3
"""Restart one StegVerse ephemeral logical heartbeat node.

This helper is local-process supervision. It has no provider, repository-token,
cloud-host, credential, route, wallet, or publication authority. The runtime root
is the complete isolation boundary for one logical node.
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


def start(runtime_root: Path, *, interval_ms: float = 10.0) -> dict[str, Any]:
    runtime_root = runtime_root.expanduser().resolve()
    runner = runtime_root / "scripts" / "run_heartbeat_runtime.py"
    if not runner.is_file():
        raise RuntimeError(f"materialized heartbeat runner missing: {runner}")
    out_path = runtime_root / "receipts" / "sovereign-host" / "ephemeral-heartbeat.stdout.log"
    err_path = runtime_root / "receipts" / "sovereign-host" / "ephemeral-heartbeat.stderr.log"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_handle = out_path.open("ab", buffering=0)
    err_handle = err_path.open("ab", buffering=0)
    command = [
        sys.executable,
        str(runner),
        "--root",
        str(runtime_root),
        "--continuous",
        "--interval-ms",
        str(interval_ms),
    ]
    env = dict(os.environ)
    for name in ("GITHUB_TOKEN", "GH_TOKEN", "STEGVERSE_GITHUB_TOKEN", "TVC_TOKEN"):
        env[name] = ""
    env["STEGVERSE_SOVEREIGN_NODE"] = "1"
    env["STEGVERSE_HEARTBEAT_ROOT"] = str(runtime_root)
    process = subprocess.Popen(
        command,
        cwd=str(runtime_root),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=out_handle,
        stderr=err_handle,
        start_new_session=True,
        close_fds=True,
    )
    receipt = {
        "schema": "stegverse.ephemeral-sovereign-process/v1",
        "runtime_root": str(runtime_root),
        "pid": process.pid,
        "command": command,
        "interval_ms": interval_ms,
        "active": True,
        "supervision_kind": "STEGVERSE_EPHEMERAL_LOCAL_PROCESS",
        "third_party_process_host_required": False,
        "third_party_scheduler_required": False,
        "credential_requirement": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "authority_effect": "LOCAL_RUNTIME_SUPERVISION_ONLY",
    }
    path = runtime_root / PROCESS_RECEIPT
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def restart(runtime_root: Path, *, interval_ms: float = 10.0) -> dict[str, Any]:
    runtime_root = runtime_root.expanduser().resolve()
    previous = _load(runtime_root / PROCESS_RECEIPT)
    previous_pid = previous.get("pid")
    terminated = _terminate(previous_pid)
    fresh = start(runtime_root, interval_ms=interval_ms)
    fresh["previous_pid"] = previous_pid
    fresh["previous_process_terminated"] = terminated
    fresh["restart_observed"] = terminated and fresh["pid"] != previous_pid
    (runtime_root / PROCESS_RECEIPT).write_text(json.dumps(fresh, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return fresh


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--interval-ms", type=float, default=10.0)
    args = parser.parse_args()
    if args.interval_ms < 0:
        raise SystemExit("interval-ms must be >= 0")
    result = restart(args.runtime_root, interval_ms=args.interval_ms)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("restart_observed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
