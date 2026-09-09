#!/usr/bin/env python3
"""Reusable-task runner for the canonical native email action monitor.

This is a thin invocation adapter. It does not create a scheduler, mailbox monitor,
WorkerCoordinator, credential route, or execution authority. It only translates the
manifest-bound reusable-task parameters into the existing resident consumer CLI.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RT = "RT-NATIVE-EMAIL-ACTION-MONITOR-001"
EXPECTED_TASK = "STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001"
CONSUMER = ROOT / "scripts" / "consume_native_email_action_monitor_request.py"


def _params() -> dict:
    raw = os.environ.get("STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON", "").strip()
    if not raw:
        raise SystemExit("STEGVERSE_REUSABLE_TASK_PARAMETERS_JSON is required")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise SystemExit("reusable task parameters must be an object")
    return value


def main() -> int:
    if os.environ.get("STEGVERSE_REUSABLE_TASK_ID") != EXPECTED_RT:
        raise SystemExit("reusable task identity mismatch")
    tracking_task = os.environ.get("STEGVERSE_REUSABLE_TASK_TRACKING_TASK_ID", "").strip()
    if tracking_task and tracking_task != EXPECTED_TASK:
        raise SystemExit("tracking task identity mismatch")
    if not CONSUMER.is_file():
        raise SystemExit("native email consumer is not materialized")

    params = _params()
    source_root = Path(str(params.get("source_root") or ROOT)).expanduser().resolve()
    runtime_raw = str(params.get("runtime_root") or "").strip()
    if not runtime_raw:
        raise SystemExit("runtime_root parameter is required")
    runtime_root = Path(runtime_raw).expanduser().resolve()
    if not runtime_root.is_dir():
        raise SystemExit("runtime_root must be an existing directory")

    command = [
        sys.executable,
        str(CONSUMER),
        "--source-root",
        str(source_root),
        "--runtime-root",
        str(runtime_root),
    ]
    completed = subprocess.run(
        command,
        cwd=runtime_root,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
        timeout=1200,
    )
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.stderr:
        print(completed.stderr.rstrip(), file=sys.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
