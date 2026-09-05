#!/usr/bin/env python3
"""Reconcile one authentically admitted CanonicalWork request against Master Records and WorkerCoordinator projections.

This coordinator is deliberately non-authorizing. It requires an existing
INGRESS_ADMITTED receipt, consumes an explicit Master Records projection, and
returns a coordination decision. It never mints a WorkerCoordinator claim/fence,
never advances HB/oscillator state, and never mutates the canonical registry.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reconcile_task_registry_master_records import find_task, normalize_projection, reconcile
from consume_canonical_work_intr_materialization_request import load, project_worker, validate_request

ROOT = Path(__file__).resolve().parents[1]
INGRESS_SCHEMA = "stegverse.canonical-work-intr-materialization-ingress/v1"


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--materialization-id", required=True)
    parser.add_argument("--master-records-projection", required=True)
    parser.add_argument("--registry", default=str(ROOT / "data" / "canonical-task-registry.json"))
    parser.add_argument("--worker-registry", default=str(ROOT / "control" / "worker-registry.json"))
    parser.add_argument("--output")
    args = parser.parse_args()

    runtime = Path(args.runtime_root).resolve()
    request_path = runtime / "intr-materialization" / f"{args.materialization_id}.json"
    ingress_path = runtime / "receipts" / "sovereign-network" / "canonical-work-intr-ingress" / f"{args.materialization_id}.json"
    payload_path = runtime / "intr-payloads" / "canonical-work" / f"{args.materialization_id}.json"

    request = load(request_path)
    validate_request(request)
    ingress = load(ingress_path)
    require(ingress.get("schema") == INGRESS_SCHEMA and ingress.get("state") == "INGRESS_ADMITTED", "authentic ingress admission receipt required")
    for key in ("materialization_id", "request_hash", "payload_hash", "operation_id", "packet_id"):
        require(ingress.get(key) == request.get(key), "ingress binding mismatch:" + key)
    require(ingress.get("claim_or_fence_minted") is False, "ingress must not mint claim/fence")

    payload = load(payload_path)
    task_id = payload.get("task_id")
    correlation_id = payload.get("correlation_id")
    require(isinstance(task_id, str) and task_id, "task_id required")
    require(isinstance(correlation_id, str) and correlation_id, "correlation_id required")

    registry = load(Path(args.registry))
    task = find_task(registry, task_id)
    require(task.get("correlation_id") == correlation_id, "canonical correlation mismatch")

    master_records_raw: Any = json.loads(Path(args.master_records_projection).read_text(encoding="utf-8"))
    events = normalize_projection(master_records_raw)
    reconciliation = reconcile(task, events)
    worker = project_worker(load(Path(args.worker_registry)), task_id)

    unresolved = [d.get("dependency_id") for d in task.get("dependencies", []) if d.get("state") != "RESOLVED"]
    blocked = bool(task.get("blockers")) or bool(unresolved)
    already_claimed_elsewhere = bool(worker.get("matched") and worker.get("claim_id"))

    if reconciliation.get("state") == "CONFLICT":
        disposition = "RECONCILIATION_CONFLICT_NO_EXECUTION"
    elif blocked:
        disposition = "DEPENDENCY_BLOCKED_NO_EXECUTION"
    elif already_claimed_elsewhere:
        disposition = "EXISTING_WORKERCOORDINATOR_CLAIM_REUSE_OR_WAIT"
    else:
        disposition = "ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW"

    result = {
        "schema": "stegverse.admitted-canonical-work-reconciliation/v1",
        "state": "RECONCILED_NON_AUTHORIZING",
        "materialization_id": args.materialization_id,
        "task_id": task_id,
        "correlation_id": correlation_id,
        "ingress_receipt_ref": str(ingress_path),
        "master_records_reconciliation": reconciliation,
        "worker_claim_projection": worker,
        "unresolved_dependencies": unresolved,
        "blockers": task.get("blockers", []),
        "disposition": disposition,
        "execution_authority_granted": False,
        "claim_or_fence_minted": False,
        "heartbeat_or_oscillator_advanced": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_COORDINATION_RECONCILIATION_ONLY",
    }
    raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
