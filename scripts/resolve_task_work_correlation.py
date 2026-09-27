#!/usr/bin/env python3
"""Read-only Task Registry correlation for source work, without fabricating runtime admission.

Canonical task_id is the unique work identity. COSV may be reused across related
Goals as a lineage coordinate, never as an exclusive ownership or execution token.
An AI_SESSION_GATE disposition is consulted only at an actual governed runtime
transition; its absence does not suppress approved source edits/tests/PR merges.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "data" / "canonical-task-registry.json"


def resolve(task_id: str, registry: dict) -> dict:
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("canonical task_id required")
    rows = registry.get("tasks")
    if not isinstance(rows, list):
        raise ValueError("registry tasks must be a list")
    hits = [row for row in rows if row.get("task_id") == task_id]
    if len(hits) != 1:
        raise ValueError("canonical task_id absent or nonunique")
    row = hits[0]
    correlation_id = row.get("correlation_id")
    root_id = row.get("root_correlation_id")
    if correlation_id != task_id or not isinstance(root_id, str) or not root_id:
        raise ValueError("canonical correlation_id or root_correlation_id inconsistent")
    work = row.get("work_correlation") or {}
    if work and (work.get("primary_key") != task_id
                 or work.get("correlation_id") != correlation_id
                 or work.get("root_correlation_id") != root_id):
        raise ValueError("work correlation disagrees with canonical task record")
    cosv = row.get("cosv_task_vector")
    if cosv is not None and not isinstance(cosv, str):
        raise ValueError("COSV lineage must be a string or null")
    if work and work.get("existing_cosv_lineage") != cosv:
        raise ValueError("COSV lineage differs from canonical task")
    # This digest is a reproducible lookup key, not a signing, admission or
    # WorkerCoordinator authority claim. Registry generation is reported
    # separately so source consumers can detect stale projections.
    identity = {"task_id": task_id, "correlation_id": correlation_id,
                "root_correlation_id": root_id}
    digest = "sha256:" + hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    return {
        "schema": "stegverse.task-registry-work-correlation-resolution/v1",
        "registry_generation": registry["generation"],
        "task_id": task_id,
        "correlation_id": correlation_id,
        "root_correlation_id": root_id,
        "work_identity_digest": digest,
        "cosv_lineage": cosv,
        "cosv_is_exclusive_task_identity": False,
        "source_work_allowed_without_runtime_disposition":
            bool(row.get("registration", {}).get("source_work_approved_by_owner_request")),
        "worker_claim_issued": False,
        "intr_admission_issued": False,
        "master_records_closure_claimed": False,
        "authority_effect": "NONE_CORRELATION_ONLY",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    args = parser.parse_args()
    print(json.dumps(resolve(args.task_id, json.loads(
        args.registry.read_text(encoding="utf-8")
    )), sort_keys=True))


if __name__ == "__main__":
    main()
