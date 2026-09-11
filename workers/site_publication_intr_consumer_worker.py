#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from consume_site_publication_intr_materialization_request import consume

TASK_ID = "SITE-PUBLICATION-INTR-CONSUMER-001"
MATERIALIZATION_ENV = "STEGVERSE_SITE_PUBLICATION_MATERIALIZATION_ID"


def blocker(problem: str, action: str, release: str) -> dict:
    return {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": False,
        "next_solution_action": action,
        "machine_observable_release_condition": release,
        "physical_additional_machine_required": False,
        "third_party_runtime_required": False,
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_required": False,
        "human_action_required": False,
    }


def response(state: str, transition: str, checkpoint: str, epoch: int, blocked: dict | None = None) -> dict:
    value = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "SITE_PUBLICATION_EVENT_LEASE_EXECUTION",
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 8,
        "checkpoint_ref": checkpoint,
        "evidence_refs": [checkpoint, "docs/SITE_PUBLICATION_INTR_CONSUMER_MIRROR_HANDOFF.md"],
        "cost_observation": {"hb_transition_count": 1, "compute_units": 1, "external_cost_usd": 0, "task_class": "site_publication_intr_consumer"},
    }
    if blocked:
        value["blocker"] = blocked
    return value


def main() -> int:
    invocation = json.load(sys.stdin)
    task = invocation.get("task") or {}
    epoch = invocation.get("heartbeat_epoch")
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1" or task.get("task_id") != TASK_ID or not isinstance(epoch, int):
        return 2
    claim_id = task.get("claim_id")
    fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        return 3
    materialization_id = str(os.environ.get(MATERIALIZATION_ENV) or "").strip()
    if not materialization_id:
        blocked = blocker(
            "Admitted Site publication materialization id is not bound to this fenced invocation.",
            f"Set {MATERIALIZATION_ENV} only from the authentic admitted ingress receipt before targeted execution.",
            "Exact admitted Site publication materialization id is present and bound to the same queued request.",
        )
        json.dump(response("ACTIVE", "SITE_PUBLICATION_EVENT_AWAITING_ADMITTED_MATERIALIZATION", "docs/SITE_PUBLICATION_INTR_CONSUMER_MIRROR_HANDOFF.md", epoch, blocked), sys.stdout)
        print()
        return 0
    receipt = consume(ROOT, materialization_id)
    checkpoint = f"receipts/sovereign-host/site-publication-intr-consumer/{materialization_id}.json"
    blocked = blocker(
        "Candidate request is validated under a fresh WorkerCoordinator claim/fence, but authentic bounded publication lease execution and independent public observation are not yet complete.",
        "Execute the existing canonical EVENT_EPHEMERAL Site publication lease, independently observe /intr/profile and exact HTTP bytes/path hashes, export candidate evidence, and close the lease.",
        "Authentic lease execution, independent HTTPS profile/readback equivalence evidence, and lease closure receipts are observed for this same materialization id and fencing generation.",
    )
    out = response("ACTIVE", "SITE_PUBLICATION_EVENT_CANDIDATE_VALIDATED", checkpoint, epoch, blocked)
    out["candidate_receipt_hash"] = receipt["receipt_hash"]
    out["claim_id"] = claim_id
    out["fencing_token"] = fence
    json.dump(out, sys.stdout)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
