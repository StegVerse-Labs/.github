#!/usr/bin/env python3
"""Bounded process worker used to prove native SHWP executor semantics.

This worker can mutate only receipts/native-worker-canary/<task_id>.json under
its configured repository checkout. It is intentionally not a general coding
worker and grants no execution authority.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
import sys

ROOT = Path.cwd().resolve()
RECEIPT_ROOT = (ROOT / "receipts" / "native-worker-canary").resolve()


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception as exc:
        print(f"invalid invocation: {exc}", file=sys.stderr)
        return 2

    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        print("unsupported invocation schema", file=sys.stderr)
        return 3

    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    task_id = str(task.get("task_id", ""))
    if not isinstance(epoch, int) or epoch < 0 or task_id != "SHWP-NATIVE-PROCESS-CANARY-001":
        print("invocation outside admitted canary task", file=sys.stderr)
        return 4

    execution = handoff.get("execution") or {}
    required = set(execution.get("required_capabilities") or [])
    allowed_paths = set(execution.get("allowed_paths") or [])
    if "native_receipt_canary" not in required:
        print("required canary capability absent", file=sys.stderr)
        return 5
    if "receipts/native-worker-canary/**" not in allowed_paths:
        print("receipt namespace not admitted", file=sys.stderr)
        return 6

    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") or {}
    fence = timing.get("fencing_token")
    if not claim_id or not isinstance(fence, int):
        print("fenced claim required", file=sys.stderr)
        return 7

    path = (RECEIPT_ROOT / f"{task_id}.json").resolve()
    if RECEIPT_ROOT not in path.parents:
        print("receipt path escaped canary namespace", file=sys.stderr)
        return 8

    prior = None
    if path.exists():
        prior = json.loads(path.read_text(encoding="utf-8"))
        if prior.get("claim_id") != claim_id or prior.get("fencing_token") != fence:
            print("existing receipt belongs to different claim/fence", file=sys.stderr)
            return 9

    sequence = 1 if prior is None else int(prior.get("transition_sequence", 1)) + 1
    completed = sequence >= 2
    transition_id = "CANARY_CHECKPOINT" if not completed else "CANARY_COMPLETE"
    receipt = {
        "schema": "stegverse.native-process-worker-canary/v0.1",
        "task_id": task_id,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "fencing_token": fence,
        "heartbeat_epoch": epoch,
        "transition_id": transition_id,
        "transition_sequence": sequence,
        "completed": completed,
        "authority_effect": "none_beyond_admitted_canary_receipt_namespace",
    }
    atomic_write(path, receipt)

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED" if completed else "ACTIVE",
        "transition_id": transition_id,
        "transition_sequence": sequence,
        "expected_next_transition": None if completed else "CANARY_COMPLETE",
        "expected_next_earliest_epoch": None if completed else epoch + 1,
        "expected_next_latest_epoch": None if completed else epoch + 1,
        "checkpoint_ref": f"receipts/native-worker-canary/{task_id}.json",
        "evidence_refs": [f"receipts/native-worker-canary/{task_id}.json"],
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "native_process_canary"
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
