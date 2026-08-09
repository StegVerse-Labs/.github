#!/usr/bin/env python3
"""Bounded worker proving real worker activation from the canonical heartbeat host."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path.cwd().resolve()
RECEIPT_ROOT = (ROOT / "receipts" / "host-self-attest").resolve()
TASK_ID = "SHWP-HOST-SELF-ATTEST-001"


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
    if not isinstance(epoch, int) or epoch < 0 or task.get("task_id") != TASK_ID:
        print("invocation outside admitted self-attestation task", file=sys.stderr)
        return 4

    execution = handoff.get("execution") or {}
    if set(execution.get("required_capabilities") or []) != {"host_runtime_self_attest"}:
        print("required capability mismatch", file=sys.stderr)
        return 5
    if execution.get("allowed_paths") != ["receipts/host-self-attest/**"]:
        print("receipt namespace not admitted", file=sys.stderr)
        return 6
    if execution.get("allowed_services") not in ([], None):
        print("network/service use is not admitted", file=sys.stderr)
        return 7

    claim_id = task.get("claim_id")
    worker_id = task.get("worker_id")
    worker_instance_id = task.get("worker_instance_id")
    timing = task.get("heartbeat_timing") or {}
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        print("current fenced claim required", file=sys.stderr)
        return 8

    path = (RECEIPT_ROOT / f"{TASK_ID}.json").resolve()
    if RECEIPT_ROOT not in path.parents:
        print("receipt path escaped admitted namespace", file=sys.stderr)
        return 9
    if path.exists():
        prior = json.loads(path.read_text(encoding="utf-8"))
        if prior.get("claim_id") != claim_id or prior.get("fencing_token") != fence:
            print("existing receipt belongs to a different claim/fence", file=sys.stderr)
            return 10

    receipt = {
        "schema": "stegverse.host-runtime-self-attestation/v0.1",
        "task_id": TASK_ID,
        "goal_id": handoff.get("goal", {}).get("goal_id"),
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "worker_id": worker_id,
        "worker_instance_id": worker_instance_id,
        "transition_id": "HOST_RUNTIME_SELF_ATTESTED",
        "transition_sequence": 1,
        "provider_is_heartbeat_timing_authority": False,
        "provider_or_host_liveness_grants_execution_authority": False,
        "execution_authority_source": handoff.get("authority", {}).get("authority_source"),
        "completed": True,
    }
    atomic_write(path, receipt)

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED",
        "transition_id": "HOST_RUNTIME_SELF_ATTESTED",
        "transition_sequence": 1,
        "expected_next_transition": None,
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": f"receipts/host-self-attest/{TASK_ID}.json",
        "evidence_refs": [f"receipts/host-self-attest/{TASK_ID}.json"],
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "host_runtime_self_attest"
        },
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
