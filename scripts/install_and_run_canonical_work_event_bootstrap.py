#!/usr/bin/env python3
"""Install the CanonicalWork route and run one bounded event bootstrap.

This wrapper is intended for an admitted StegVerse resident execution context.
It performs only two repository-local machine steps in sequence:

1. apply/check the fail-closed CanonicalWork route transformation against the
   existing shared Universal InTr router source; and
2. launch the bounded event bootstrap in a fresh Python process so the newly
   installed router is imported from the transformed source.

The selected ``--task-id`` is passed to the existing CanonicalWork bootstrap. The
bootstrap itself resolves that identity exactly once in the canonical task
registry, requires PROPOSED state and an allowed INGRESS_ADMITTED transition, and
preserves WorkerCoordinator / Master Records / Interlock-InTr authority separation.

This wrapper does not define or start a second heartbeat, oscillator, scheduler,
WorkerCoordinator implementation, or ingress implementation. The bootstrap uses
the existing shared Universal InTr Server for exactly one event-triggered request.
Source installation is not itself runtime evidence; only receipts emitted by the
second step may be used as observed execution evidence.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASK_ID = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=str(ROOT), check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--registry", default=str(ROOT / "data" / "canonical-task-registry.json"))
    parser.add_argument("--consumer-timeout-seconds", type=float, default=5.0)
    parser.add_argument("--without-carrier-binding", action="store_true")
    args = parser.parse_args()

    installer = str(ROOT / "scripts" / "install_canonical_work_universal_intr_route.py")
    bootstrap = str(ROOT / "scripts" / "run_canonical_work_event_bootstrap.py")

    run([sys.executable, installer])
    run([sys.executable, installer, "--check"])

    command = [
        sys.executable,
        bootstrap,
        "--task-id",
        args.task_id,
        "--runtime-root",
        str(Path(args.runtime_root).expanduser().resolve()),
        "--registry",
        str(Path(args.registry).expanduser().resolve()),
        "--consumer-timeout-seconds",
        str(args.consumer_timeout_seconds),
    ]
    if args.without_carrier_binding:
        command.append("--without-carrier-binding")
    run(command)

    print(f"PASS: route installation/check completed and bounded CanonicalWork bootstrap returned success for task {args.task_id}")
    print("NONCLAIM: this wrapper does not itself prove WorkerCoordinator claim/fence, governed work, Master Records reconciliation, egress, or closure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
