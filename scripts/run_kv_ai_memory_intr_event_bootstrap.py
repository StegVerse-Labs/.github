#!/usr/bin/env python3
"""CLI wrapper for the resident-native KV AI memory event bootstrap."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from workers.kv_ai_memory_intr_event_bootstrap import ROOT, run_cycle


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one resident-local KV AI memory cycle on the existing shared Universal InTr listener.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    result = run_cycle(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"BOUND_STATE_INPUT_NOT_READY", "EVENT_CYCLE_COMPLETED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
