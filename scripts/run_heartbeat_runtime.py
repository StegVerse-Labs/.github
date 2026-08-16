#!/usr/bin/env python3
"""Run the non-authorizing StegVerse heartbeat carrier."""
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

from heartbeat_runtime import HeartbeatRuntime


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--cycles", type=int, default=1, help="Finite carrier cycle count when --continuous is not set.")
    parser.add_argument("--continuous", action="store_true", help="Run carrier observations until terminated by the local process manager.")
    parser.add_argument("--interval-ms", type=float, default=10.0, help="Delay between carrier observations; this cadence grants no authority.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.cycles < 1 or args.interval_ms < 0:
        raise SystemExit("cycles must be >= 1 and interval-ms must be >= 0")
    if args.continuous and args.dry_run:
        raise SystemExit("continuous dry-run is unsupported")

    root = Path(args.root).resolve()
    runtime = HeartbeatRuntime(root)
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
