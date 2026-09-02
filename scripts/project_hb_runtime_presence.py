#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from heartbeat_runtime.runtime_presence_projection import project  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Project canonical HB/runtime resident observability from existing evidence.")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--request-ref")
    parser.add_argument("--consumption-ref")
    parser.add_argument("--execution-ref")
    parser.add_argument("--reconstruction-ref")
    args = parser.parse_args()
    refs = {
        name: value
        for name, value in {
            "request": args.request_ref,
            "consumption": args.consumption_ref,
            "execution": args.execution_ref,
            "reconstruction": args.reconstruction_ref,
        }.items()
        if value
    }
    result = project(args.runtime_root, refs)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
