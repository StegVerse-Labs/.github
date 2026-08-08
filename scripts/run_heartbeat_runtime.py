#!/usr/bin/env python3
"""Run the provider-agnostic StegVerse single-heartbeat runtime."""
from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from heartbeat_runtime import HeartbeatRuntime, ProcessWorkerAdapter


def load_adapters(root: Path) -> dict[str, ProcessWorkerAdapter]:
    registry_path = root / "control" / "process-worker-adapters.json"
    if not registry_path.exists():
        return {}
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if registry.get("schema") != "stegverse.process-worker-adapters/v0.1":
        raise RuntimeError("unsupported process worker adapter registry")
    adapters: dict[str, ProcessWorkerAdapter] = {}
    for entry in registry.get("adapters", []):
        if not entry.get("enabled"):
            continue
        adapter_ref = entry["adapter_ref"]
        if adapter_ref in adapters:
            raise RuntimeError(f"duplicate enabled adapter_ref: {adapter_ref}")
        cwd = Path(entry["cwd"])
        if not cwd.is_absolute():
            cwd = root / cwd
        adapters[adapter_ref] = ProcessWorkerAdapter(
            list(entry["command"]),
            cwd=cwd,
            timeout_seconds=float(entry["timeout_seconds"]),
            env_allowlist=tuple(entry.get("env_allowlist", [])),
        )
    return adapters


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--cycles", type=int, default=1, help="Finite cycle count when --continuous is not set.")
    parser.add_argument("--continuous", action="store_true", help="Run the internal heartbeat loop until terminated by the host/process manager.")
    parser.add_argument("--interval-ms", type=float, default=10.0, help="Internal delay between heartbeat cycles; not a third-party scheduler cadence.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.cycles < 1 or args.interval_ms < 0:
        raise SystemExit("cycles must be >= 1 and interval-ms must be >= 0")
    if args.continuous and args.dry_run:
        raise SystemExit("continuous dry-run is prohibited because non-persistent state cannot prove advancing heartbeat epochs")

    root = Path(args.root).resolve()
    runtime = HeartbeatRuntime(root, adapters=load_adapters(root))
    running = True

    def stop(_signum, _frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    index = 0
    while running and (args.continuous or index < args.cycles):
        result = runtime.cycle(write=not args.dry_run)
        print(json.dumps(result, sort_keys=True), flush=True)
        index += 1
        if running and (args.continuous or index < args.cycles) and args.interval_ms:
            time.sleep(args.interval_ms / 1000.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
