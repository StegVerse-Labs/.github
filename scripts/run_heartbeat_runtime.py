#!/usr/bin/env python3
"""Run the non-authorizing StegVerse oscillator-produced heartbeat carrier.

The production loop is phase-driven, not event-driven: after one bounded state
sample/bootstrap, the next wake time is derived from the oscillator anchor and
10 ms period. Repository events, workflows, tasks, workers, claims, fences, and
consumer completion never determine when a heartbeat reference exists.

A live carrier may also be observed by the local process-supervision layer as
node-presence evidence. That supervision may restore a missing WorkerCoordinator
process, but the carrier grants no task authority and task execution remains
subject to independent WorkerCoordinator/InTr/TV-TVC admission.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from heartbeat_runtime import CarrierHeartbeatRuntime
from heartbeat_runtime.oscillator_producer import OscillatorProducer
from scripts.repair_resident_worker_presence import ensure_worker_presence

# Deprecated compatibility exports for callers/tests that historically imported
# worker-adapter helpers from this module. The carrier main path never uses them
# for task admission or execution.
from scripts.run_worker_runtime import _read_registry, adapter_entries as _worker_adapter_entries, load_adapters

CARRIER_STATE = Path("control/heartbeat-carrier-runtime-state.json")
WORKER_SUPERVISION_INTERVAL_REFERENCES = 100


def _adapter_entries(root: Path):
    return _worker_adapter_entries(root)


def _sleep_until(deadline_ns: int) -> None:
    """Wait for an oscillator phase deadline without becoming timing authority."""
    remaining_ns = int(deadline_ns) - time.time_ns()
    if remaining_ns > 0:
        time.sleep(remaining_ns / 1_000_000_000)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--cycles", type=int, default=1, help="Finite produced-reference observations when --continuous is not set.")
    parser.add_argument("--continuous", action="store_true", help="Produce oscillator-derived heartbeat observations until locally terminated.")
    parser.add_argument(
        "--interval-ms",
        type=float,
        default=10.0,
        help="Deprecated compatibility argument. It does not control heartbeat cadence; oscillator phase remains fixed at 10 ms.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.cycles < 1 or args.interval_ms < 0:
        raise SystemExit("cycles must be >= 1 and interval-ms must be >= 0")
    if args.continuous and args.dry_run:
        raise SystemExit("continuous dry-run is unsupported")

    root = Path(args.root).resolve()
    runtime = CarrierHeartbeatRuntime(root)
    running = True

    def stop(_signum, _frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    # Dry-run remains an observation-only compatibility surface. Production
    # timing below is oscillator-produced and does not use --interval-ms.
    if args.dry_run:
        for _ in range(args.cycles):
            result = runtime.cycle(write=False, now_ns=time.time_ns())
            print(json.dumps(result, sort_keys=True), flush=True)
        return 0

    # One bounded bootstrap/sample establishes or migrates the persisted
    # oscillator anchor. It does not make this invocation the heartbeat clock.
    bootstrap_ns = time.time_ns()
    bootstrap = runtime.cycle(write=True, now_ns=bootstrap_ns)
    print(json.dumps(bootstrap, sort_keys=True), flush=True)
    produced = 1
    if not args.continuous and produced >= args.cycles:
        return 0

    carrier_path = root / CARRIER_STATE
    carrier = json.loads(carrier_path.read_text(encoding="utf-8"))
    oscillator = carrier.get("oscillator")
    carrier_epoch = carrier.get("epoch")
    if not isinstance(oscillator, dict) or not isinstance(carrier_epoch, int):
        raise SystemExit("oscillator-produced runtime requires persisted oscillator-backed carrier state")

    observed_results: list[dict] = []

    def observe(batch) -> None:
        # The batch already exists by oscillator phase. cycle() only materializes
        # an observation of that reference and cannot cause the reference.
        result = runtime.cycle(write=True, now_ns=batch.produced_unix_ns)
        observed_results.append({
            "pulse_batch": batch.as_dict(),
            "carrier_observation": result,
        })

    producer = OscillatorProducer(
        oscillator,
        initial_emitted_epoch=carrier_epoch,
        clock_ns=time.time_ns,
        sink=observe,
    )

    while running and (args.continuous or produced < args.cycles):
        _sleep_until(producer.next_due_unix_ns)
        if not running:
            break
        batch = producer.run_once()
        if batch is None:
            # Early wake or clock granularity: retry against the same immutable
            # oscillator deadline; no synthetic heartbeat is emitted.
            continue
        payload = observed_results.pop(0)
        produced += 1

        # Process supervision is intentionally downstream of carrier production.
        # The pulse already exists before this check. Every 100 observed references
        # (~1 second at 100 Hz), a live carrier can repair a missing resident worker
        # process. The repair only restores WorkerCoordinator presence; it cannot
        # admit or authorize any task. The restored WorkerCoordinator immediately
        # visits the resident request dispatcher on its own first logical tick.
        if args.continuous and produced % WORKER_SUPERVISION_INTERVAL_REFERENCES == 0:
            payload["resident_worker_presence"] = ensure_worker_presence(
                root,
                carrier_pid=os.getpid(),
                interval_ms=args.interval_ms,
            )

        print(json.dumps(payload, sort_keys=True), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
