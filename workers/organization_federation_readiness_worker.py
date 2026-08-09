#!/usr/bin/env python3
"""Heartbeat-owned organization federation readiness worker.

This worker does not grant authority to any organization. It consumes the
canonical federation/readiness projections, proves every organization has a
machine owner or a fail-closed release condition, and writes only its bounded
receipt namespace.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd().resolve()
FEDERATION = ROOT / "control" / "organization-federation.json"
TASKS = ROOT / "control" / "organization-task-registry.json"
RECEIPT_ROOT = (ROOT / "receipts" / "organization-federation").resolve()
EXPECTED_TASK = "SHWP-ALL-ORG-FEDERATION-001"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def fail(message: str, code: int) -> int:
    print(message, file=sys.stderr)
    return code


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
    except Exception as exc:
        return fail(f"invalid invocation: {exc}", 2)
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        return fail("unsupported invocation schema", 3)

    epoch = invocation.get("heartbeat_epoch")
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    if not isinstance(epoch, int) or epoch < 0 or task.get("task_id") != EXPECTED_TASK:
        return fail("invocation outside admitted federation task", 4)

    execution = handoff.get("execution") or {}
    required = set(execution.get("required_capabilities") or [])
    allowed_paths = set(execution.get("allowed_paths") or [])
    if "bounded_repository_mutation" not in required:
        return fail("bounded_repository_mutation capability not admitted", 5)
    if "receipts/organization-federation/**" not in allowed_paths:
        return fail("federation receipt namespace not admitted", 6)

    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") or {}
    fence = timing.get("fencing_token")
    if not claim_id or not isinstance(fence, int):
        return fail("fenced claim required", 7)

    federation = load(FEDERATION)
    org_tasks = load(TASKS)
    organizations = federation.get("organizations") or []
    task_rows = org_tasks.get("tasks") or []
    if federation.get("schema") != "stegverse.organization-federation/v0.1":
        return fail("unsupported federation schema", 8)
    if org_tasks.get("schema") != "stegverse.organization-task-registry/v0.1":
        return fail("unsupported organization task registry schema", 9)
    if len(organizations) != 14 or len(task_rows) != 14:
        return fail("all-organization denominator must remain 14", 10)

    org_names = {row.get("organization") for row in organizations}
    task_org_names = {row.get("organization") for row in task_rows}
    if len(org_names) != 14 or org_names != task_org_names:
        return fail("federation/task organization sets differ", 11)

    blocked = []
    ready = []
    invalid = []
    for row in task_rows:
        state = row.get("state")
        if state == "READY":
            ready.append(row["organization"])
        elif state == "BLOCKED":
            if not row.get("release_condition") or not row.get("next_action"):
                invalid.append(row["organization"])
            blocked.append({
                "organization": row["organization"],
                "block_class": row.get("block_class"),
                "release_condition": row.get("release_condition"),
                "next_action": row.get("next_action")
            })
        else:
            invalid.append(row.get("organization"))
    if invalid:
        return fail(f"unowned or invalid organization task states: {invalid}", 12)

    receipt_path = (RECEIPT_ROOT / f"{EXPECTED_TASK}.json").resolve()
    if RECEIPT_ROOT not in receipt_path.parents:
        return fail("receipt path escaped federation namespace", 13)
    prior = load(receipt_path) if receipt_path.exists() else None
    if prior and (prior.get("claim_id") != claim_id or prior.get("fencing_token") != fence):
        return fail("existing receipt belongs to different claim/fence", 14)

    sequence = 1 if prior is None else int(prior.get("transition_sequence", 0)) + 1
    complete = len(blocked) == 0
    transition = "ALL_ORGS_READY" if complete else "FEDERATION_READY_WITH_MACHINE_BLOCKERS"
    receipt = {
        "schema": "stegverse.organization-federation-receipt/v0.1",
        "task_id": EXPECTED_TASK,
        "claim_id": claim_id,
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "heartbeat_epoch": epoch,
        "fencing_token": fence,
        "transition_id": transition,
        "transition_sequence": sequence,
        "organization_count": 14,
        "ready_count": len(ready),
        "blocked_count": len(blocked),
        "unassigned_count": 0,
        "ready_organizations": sorted(ready),
        "blocked_organizations": sorted(blocked, key=lambda x: x["organization"]),
        "subsignal_ref": "control/heartbeat-subsignals.json#organization_federation",
        "federation_ref": "control/organization-federation.json",
        "organization_task_registry_ref": "control/organization-task-registry.json",
        "authority_effect": "none_beyond_admitted_federation_receipt_namespace",
        "completed": complete
    }
    atomic_write(receipt_path, receipt)

    response = {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED" if complete else "BLOCKED",
        "transition_id": transition,
        "transition_sequence": sequence,
        "expected_next_transition": None if complete else "FEDERATION_RECHECK",
        "expected_next_earliest_epoch": None if complete else epoch + 1,
        "expected_next_latest_epoch": None if complete else epoch + 1,
        "checkpoint_ref": f"receipts/organization-federation/{EXPECTED_TASK}.json",
        "evidence_refs": [
            "control/organization-federation.json",
            "control/organization-task-registry.json",
            "control/heartbeat-subsignals.json",
            f"receipts/organization-federation/{EXPECTED_TASK}.json"
        ],
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "organization_federation_readiness"
        }
    }
    json.dump(response, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
