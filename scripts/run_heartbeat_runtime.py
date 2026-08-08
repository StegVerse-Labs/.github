#!/usr/bin/env python3
"""Run one or more StegVerse heartbeat cycles from the native runtime engine."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from heartbeat_runtime import HeartbeatRuntime


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--interval-ms", type=float, default=10.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.cycles < 1 or args.interval_ms < 0:
        raise SystemExit("cycles must be >= 1 and interval-ms must be >= 0")

    runtime = HeartbeatRuntime(Path(args.root))
    for index in range(args.cycles):
        result = runtime.cycle(write=not args.dry_run)
        print(json.dumps(result, sort_keys=True))
        if index + 1 < args.cycles and args.interval_ms:
            time.sleep(args.interval_ms / 1000.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
