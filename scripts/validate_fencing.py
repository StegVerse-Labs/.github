#!/usr/bin/env python3
"""Validate merge-time fencing tokens against authoritative counters."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTERS = ROOT / "control" / "fencing-counters.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resource", required=True)
    parser.add_argument("--token", required=True, type=int)
    args = parser.parse_args()
    data = json.loads(COUNTERS.read_text(encoding="utf-8"))
    expected = data.get("resources", {}).get(args.resource)
    if expected is None:
        print(f"ERROR: no authoritative fencing token for {args.resource}", file=sys.stderr)
        raise SystemExit(1)
    if args.token != expected:
        print(f"ERROR: stale fencing token {args.token}; expected {expected}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps({"valid": True, "resource": args.resource, "fencing_token": args.token}, sort_keys=True))

if __name__ == "__main__":
    main()
