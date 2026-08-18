#!/usr/bin/env python3
"""Project worker control-plane observation for an already-materialized carrier without advancing HB."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from heartbeat_runtime.engine_v12 import HeartbeatRuntime

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    runtime = HeartbeatRuntime(root)
    carrier = runtime._load(runtime.carrier_state_path)
    registry = runtime._load(runtime.registry_path)
    if carrier.get("schema") != "stegverse.heartbeat-carrier-runtime-state/v1":
        raise SystemExit("separated carrier required")
    if int(carrier.get("epoch", -1)) < 30:
        raise SystemExit("HB30+ carrier required")
    control = runtime._control_plane_coordination(carrier, registry)
    runtime._atomic_write(runtime.control_plane_path, control)
    print(json.dumps(control, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
