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
from heartbeat_runtime.intr_subsignal_runtime import EVENT_LOG_REL as DERIVED_SUBSIGNAL_EVENT_LOG_REL
from scripts.repair_resident_worker_presence import ensure_worker_presence

# Deprecated compatibility exports for callers/tests that historically imported
# worker-adapter helpers from this module. The carrier main path never uses them
# for task admission or execution.
from scripts.run_worker_runtime import _read_registry, adapter_entries as _worker_adapter_entries, load_adapters

CARRIER_STATE = Path("control/heartbeat-carrier-runtime-state.json")
MATERIALIZATION_RECEIPT = Path("receipts/sovereign-host/materialization.latest.json")
WORKER_SUPERVISION_INTERVAL_REFERENCES = 100
LEGACY_SUBSIGNAL_STATE_REL = Path("control/heartbeat-subsignals.json")


def _subsignal_activity_snapshot(root: Path) -> tuple[tuple[str, int, int], ...]:
    """Observe canonical HB/AU sub-signal persistence surfaces without interpreting them."""
    rows: list[tuple[str, int, int]] = []
    for rel in (DERIVED_SUBSIGNAL_EVENT_LOG_REL, LEGACY_SUBSIGNAL_STATE_REL):
        path = root / rel
        try:
            stat = path.stat()
            rows.append((str(rel), int(stat.st_size), int(stat.st_mtime_ns)))
        except OSError:
            rows.append((str(rel), 0, 0))
    return tuple(rows)


def _observe_hb_subsignal_worker_presence(
    root: Path,
    *,
    previous_snapshot: tuple[tuple[str, int, int], ...],
    carrier_pid: int,
    interval_ms: float,
    supervisor=ensure_worker_presence,
) -> tuple[tuple[tuple[str, int, int], ...], dict | None]:
    """Use any newly persisted HB/AU sub-signal activity only as a supervision cue.

    The canonical denominator includes both the shared exact-byte HB-derived
    carrier event surface and the retained heartbeat-subsignals state surface.
    This does not interpret packet/sub-signal semantics and grants no task,
    claim/fence, admission, transition, credential, routing, custody, or
    execution authority. It merely asks the already-existing carrier-side
    supervision path to ensure the existing WorkerCoordinator process is present.
    """
    current = _subsignal_activity_snapshot(root)
    if current == previous_snapshot:
        return current, None
    result = supervisor(
        root,
        carrier_pid=carrier_pid,
        interval_ms=interval_ms,
    )
    return current, result


def _adapter_entries(root: Path):
    return _worker_adapter_entries(root)


def _restore_local_source_root(root: Path) -> str | None:
    """Recover the non-secret canonical source locator for carrier-side worker repair.

    Native installation already records the canonical source root in the local
    materialization receipt. Carrier-side self-heal must preserve that locator even
    when a service manager did not carry STEGVERSE_HEARTBEAT_SOURCE_ROOT into the
    carrier environment. This restores a locator only; it grants no execution,
    admission, credential, claim, fence, route, or transition authority.
    """
    existing = str(os.environ.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT") or "").strip()
    if existing:
        return str(Path(existing).expanduser().resolve())

    receipt_path = root / MATERIALIZATION_RECEIPT
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    raw = str(receipt.get("source_root") or "").strip() if isinstance(receipt, dict) else ""
    if not raw:
        return None
    source_root = Path(raw).expanduser().resolve()
    if source_root == root or not source_root.is_dir():
        return None
    os.environ["STEGVERSE_HEARTBEAT_SOURCE_ROOT"] = str(source_root)
    return str(source_root)


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
    _restore_local_source_root(root)
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
    subsignal_activity_snapshot = _subsignal_activity_snapshot(root)

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
        # The pulse already exists before this check. Newly persisted HB/AU
        # sub-signal activity can request the same existing supervision check
        # immediately; it grants no authority and does not select a task.
        supervised_this_reference = False
        if args.continuous:
            subsignal_activity_snapshot, subsignal_presence = _observe_hb_subsignal_worker_presence(
                root,
                previous_snapshot=subsignal_activity_snapshot,
                carrier_pid=os.getpid(),
                interval_ms=args.interval_ms,
            )
            if subsignal_presence is not None:
                payload["resident_worker_presence"] = subsignal_presence
                payload["resident_worker_presence_trigger"] = "HB_AU_SUBSIGNAL_ACTIVITY"
                supervised_this_reference = True

        # Preserve the existing periodic supervision as fallback. Every 100
        # observed references (~1 second at 100 Hz), a live carrier can repair
        # a missing resident worker process even when no sub-signal was emitted.
        if (
            args.continuous
            and not supervised_this_reference
            and produced % WORKER_SUPERVISION_INTERVAL_REFERENCES == 0
        ):
            payload["resident_worker_presence"] = ensure_worker_presence(
                root,
                carrier_pid=os.getpid(),
                interval_ms=args.interval_ms,
            )
            payload["resident_worker_presence_trigger"] = "PERIODIC_CARRIER_FALLBACK"

        print(json.dumps(payload, sort_keys=True), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
