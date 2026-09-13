#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from consume_site_publication_intr_materialization_request import consume

TASK_ID = "SITE-PUBLICATION-INTR-CONSUMER-001"
MATERIALIZATION_ENV = "STEGVERSE_SITE_PUBLICATION_MATERIALIZATION_ID"
INGRESS_LATEST = Path("receipts/sovereign-network/site-publication-intr-ingress.latest.json")
INGRESS_SCHEMA = "stegverse.site-publication-intr-ingress/v1"
INGRESS_STATE = "INGRESS_ADMITTED_CANDIDATE_ONLY"


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


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("SITE_PUBLICATION_INGRESS_RECEIPT_NOT_OBJECT")
    return value


def resolve_admitted_materialization(root: Path, env_value: str | None = None) -> tuple[str | None, str]:
    latest = root / INGRESS_LATEST
    if not latest.is_file():
        return None, "ADMITTED_INGRESS_RECEIPT_NOT_PRESENT"
    try:
        receipt = _load_object(latest)
    except Exception:
        return None, "ADMITTED_INGRESS_RECEIPT_INVALID"
    required = {
        "schema": INGRESS_SCHEMA,
        "state": INGRESS_STATE,
        "exact_request_validated": True,
        "write_once_persisted": True,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "authority_effect": "NONE_INGRESS_CANDIDATE_ONLY",
    }
    if any(receipt.get(key) != expected for key, expected in required.items()):
        return None, "ADMITTED_INGRESS_RECEIPT_NOT_ELIGIBLE"
    materialization_id = receipt.get("materialization_id")
    if not isinstance(materialization_id, str) or not materialization_id.startswith("INTR-MAT-") or len(materialization_id) != 33:
        return None, "ADMITTED_INGRESS_MATERIALIZATION_ID_INVALID"
    expected_queue = (root / "intr-materialization" / f"{materialization_id}.json").resolve()
    queue_raw = receipt.get("queue_ref")
    if not isinstance(queue_raw, str) or Path(queue_raw).expanduser().resolve() != expected_queue or not expected_queue.is_file():
        return None, "ADMITTED_INGRESS_QUEUE_BINDING_INVALID"
    try:
        request = _load_object(expected_queue)
    except Exception:
        return None, "ADMITTED_INGRESS_QUEUED_REQUEST_INVALID"
    if request.get("materialization_id") != materialization_id:
        return None, "ADMITTED_INGRESS_QUEUE_ID_MISMATCH"
    explicit = str(env_value or "").strip()
    if explicit and explicit != materialization_id:
        return None, "EXPLICIT_MATERIALIZATION_BINDING_CONFLICT"
    return materialization_id, "LOCAL_ADMITTED_INGRESS_RECEIPT"


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

    materialization_id, binding_source = resolve_admitted_materialization(ROOT, os.environ.get(MATERIALIZATION_ENV))
    if not materialization_id:
        blocked = blocker(
            "No uniquely bound authentic Site publication ingress materialization is available to this fenced invocation.",
            "Retain the admitted InTr ingress receipt and exact queued request in the resident runtime; any explicit opaque materialization binding must match that receipt.",
            "A valid write-once admitted ingress receipt and queued request resolve the same materialization id for this WorkerCoordinator invocation.",
        )
        out = response("ACTIVE", "SITE_PUBLICATION_EVENT_AWAITING_ADMITTED_MATERIALIZATION", "docs/SITE_PUBLICATION_INTR_CONSUMER_MIRROR_HANDOFF.md", epoch, blocked)
        out["materialization_binding_resolution"] = binding_source
        json.dump(out, sys.stdout)
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
    out["materialization_id"] = materialization_id
    out["materialization_binding_source"] = binding_source
    json.dump(out, sys.stdout)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
