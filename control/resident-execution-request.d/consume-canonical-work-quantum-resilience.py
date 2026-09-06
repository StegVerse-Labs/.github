#!/usr/bin/env python3
"""Consume the QUANTUM-RESILIENCE-001 Canonical Work ingress request.

This wrapper reuses the canonical resident bootstrap consumer implementation and
supplies only the task/request/receipt identity for QUANTUM-RESILIENCE-001. It
creates no second ingress implementation, scheduler, WorkerCoordinator, credential
path, or authority plane.
"""
from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED = runpy.run_path(str(HERE / "consume-canonical-work-coordination-bootstrap.py"))
consume_for_spec = SHARED["consume_for_spec"]

SPEC = {
    "request_rel": Path("control/resident-execution-request.d/canonical-work-quantum-resilience-001.json"),
    "consumption_rel": Path("receipts/sovereign-host/canonical-work-quantum-resilience-request-consumption.latest.json"),
    "bootstrap_runtime_rel": Path("runtime/canonical-work-quantum-resilience"),
    "task_id": "QUANTUM-RESILIENCE-001",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = consume_for_spec(args.source_root, args.runtime_root, SPEC)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("state") in {"NO_REQUEST", "ALREADY_CONSUMED", "COMPLETED", "ATTEMPT_RECORDED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
