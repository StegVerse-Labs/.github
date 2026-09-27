#!/usr/bin/env python3
"""Read-only component-010 checkout audit. Not an execution or custody receipt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

TASK_ID = "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001"
SCHEMA = "stegverse.component010-checkout-audit/v1"


def audit(registry: dict, shard: dict) -> dict:
    generation = registry.get("generation")
    rows = registry.get("tasks")
    if not isinstance(generation, int) or isinstance(generation, bool) or not isinstance(rows, list):
        raise ValueError("INVALID_CANONICAL_REGISTRY")
    matches = [row for row in rows if isinstance(row, dict) and row.get("task_id") == TASK_ID]
    if len(matches) != 1 or shard.get("task_id") != TASK_ID:
        raise ValueError("COMPONENT010_CANONICAL_IDENTITY_INVALID")
    row = matches[0]
    for field in ("checkout_state", "coordination_state", "cosv_task_vector"):
        if row.get(field) != shard.get(field):
            raise ValueError("COMPONENT010_SHARD_AGGREGATE_MISMATCH:" + field)
    checked_out = row.get("checkout_state") == "CHECKED_OUT"
    # A GitHub issue, old PR, task status, or caller-supplied string is not a live claim.
    # The canonical task row's worker_claim is a *pointer*, not proof of runtime validity.
    claim = row.get("worker_claim")
    claim_ref = claim.get("receipt_ref") if isinstance(claim, dict) else None
    claim_fence = claim.get("fence") if isinstance(claim, dict) else None
    claim_evidenced = bool(claim_ref and claim_fence)
    unresolved = checked_out and not claim_evidenced
    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "observed_registry_generation": generation,
        "observed_checkout_state": row.get("checkout_state"),
        "observed_coordination_state": row.get("coordination_state"),
        "cosv_task_vector": row.get("cosv_task_vector"),
        "source_projection_disposition": "FAIL_CLOSED_STALE_CHECKOUT_EVIDENCE" if unresolved else "REQUIRES_AUTHENTIC_CLAIM_READBACK" if checked_out else "NO_ACTIVE_CHECKOUT",
        "failing_predicate": "CHECKED_OUT_REQUIRES_AUTHENTIC_CURRENT_CLAIM" if unresolved else None,
        "claim_pointer_present": claim_evidenced,
        "claim_authentically_verified": False,
        "runtime_transition_observed": False,
        "canonical_registry_mutated": False,
        "required_action": "RECONCILE_CHECKOUT_VIA_CANONICAL_OWNER_TRANSITION" if unresolved else "VERIFY_ORIGINAL_CLAIM_AND_FENCE" if checked_out else "ADMIT_VIA_EXISTING_CANONICAL_OWNER",
        "evidence_refs": [
            "data/canonical-task-registry.json",
            "data/canonical-task-records/" + TASK_ID + ".json",
            "StegVerse-Labs/.github#1620",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("data/canonical-task-registry.json"))
    parser.add_argument("--shard", type=Path, default=Path("data/canonical-task-records/" + TASK_ID + ".json"))
    args = parser.parse_args()
    try:
        result = audit(json.loads(args.registry.read_text()), json.loads(args.shard.read_text()))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema": SCHEMA, "source_projection_disposition": "FAIL_CLOSED_INVALID_SOURCE", "failing_predicate": str(exc), "runtime_transition_observed": False}, sort_keys=True))
        raise SystemExit(2)
    print(json.dumps(result, sort_keys=True))
    if result["source_projection_disposition"] == "FAIL_CLOSED_STALE_CHECKOUT_EVIDENCE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
