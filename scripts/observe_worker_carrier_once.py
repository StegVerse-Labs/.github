#!/usr/bin/env python3
"""Record one independent WorkerCoordinator carrier observation without invoking task adapters."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from heartbeat_runtime.worker_runtime import WorkerCoordinator

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    runtime = WorkerCoordinator(root, adapters={})
    runtime._persist = True
    runtime._acquire()
    try:
        epoch, generation = runtime._carrier_reference()
        if epoch < 30:
            raise RuntimeError("HB30+ carrier required")
        state = runtime._load_runtime_state()
        state["runtime_tick"] = int(state.get("runtime_tick", 0)) + 1
        state["last_observed_carrier_epoch"] = epoch
        state["last_observed_carrier_generation"] = generation
        state["carrier_controls_timer"] = False
        state["observation_mode"] = "CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION"
        state["last_cycle_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        runtime._atomic_write(runtime.worker_runtime_state_path, state)
        runtime.worker_event_path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "event_type": "worker_carrier_reference_observed",
            "carrier_epoch": epoch,
            "carrier_generation": generation,
            "worker_runtime_tick": state["runtime_tick"],
            "task_adapters_invoked": 0,
            "claim_or_fence_mutation": False,
            "carrier_epoch_advanced_by_worker_runtime": False,
            "authority_effect": False,
        }
        with runtime.worker_event_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")
        print(json.dumps({
            "schema": "stegverse.worker-carrier-observation/v1",
            "observed_carrier_epoch": epoch,
            "observed_carrier_generation": generation,
            "worker_runtime_tick": state["runtime_tick"],
            "task_adapters_invoked": 0,
            "claim_or_fence_mutation": False,
            "authority_effect": "OBSERVATION_ONLY",
        }, sort_keys=True))
        return 0
    finally:
        runtime._release_lock()
        runtime._persist = True


if __name__ == "__main__":
    raise SystemExit(main())
