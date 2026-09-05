#!/usr/bin/env python3
"""Route one runtime-profile governance-review package to the named authority inbox.

Routing is a local coordination projection only. It preserves the exact review-package
hash and names the authority class that must perform its own current-governance review.
It does not invoke that authority, mint claim/fence ownership, grant Interlock/InTr
admission, mutate canonical task state, execute work, or advance HB/oscillator state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ALLOWED_AUTHORITIES = {
    "WORKERCOORDINATOR",
    "INTERLOCK_INTR",
    "MASTER_RECORDS_RECONCILIATION",
    "CANONICAL_COORDINATION",
}
AUTHORITY_INBOX = {
    "WORKERCOORDINATOR": "receipts/runtime-profile-map/authority-review/workercoordinator",
    "INTERLOCK_INTR": "receipts/runtime-profile-map/authority-review/interlock-intr",
    "MASTER_RECORDS_RECONCILIATION": "receipts/runtime-profile-map/authority-review/master-records-reconciliation",
    "CANONICAL_COORDINATION": "receipts/runtime-profile-map/authority-review/canonical-coordination",
}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError("FAIL_CLOSED: " + reason)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"object required:{path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def route(review_path: Path, runtime_root: Path) -> dict[str, Any]:
    review = load(review_path)
    require(review.get("schema") == "stegverse.runtime-profile-map-governance-review/v1", "governance review schema mismatch")
    require(review.get("review_required_before_transition") is True, "review must remain required")
    require(review.get("task_state_changed") is False, "governance review may not mutate task state")
    require(review.get("claim_or_fence_minted") is False, "governance review may not mint claim/fence")
    require(review.get("execution_authority_granted") is False, "governance review may not grant execution authority")
    require(review.get("interlock_intr_admission_granted") is False, "governance review may not grant InTr admission")
    require(review.get("heartbeat_or_oscillator_advanced") is False, "governance review may not advance HB/oscillator")

    task_id = review.get("task_id")
    correlation_id = review.get("correlation_id")
    authority = review.get("review_authority_class")
    require(isinstance(task_id, str) and task_id, "task_id required")
    require(isinstance(correlation_id, str) and correlation_id, "correlation_id required")
    require(authority in ALLOWED_AUTHORITIES, "unsupported review authority class")

    review_hash = sha256(review_path)
    inbox = runtime_root / AUTHORITY_INBOX[authority]
    output = inbox / f"{task_id}.json"
    envelope = {
        "schema": "stegverse.runtime-profile-map-authority-review-envelope/v1",
        "state": "ROUTED_FOR_CURRENT_AUTHORITY_REVIEW",
        "task_id": task_id,
        "correlation_id": correlation_id,
        "review_authority_class": authority,
        "next_governance_review": review.get("next_governance_review"),
        "transition_readiness_disposition": review.get("transition_readiness_disposition"),
        "governance_review_ref": str(review_path),
        "governance_review_sha256": review_hash,
        "authority_inbox_ref": str(inbox),
        "authority_invoked": False,
        "task_state_changed": False,
        "claim_or_fence_minted": False,
        "execution_authority_granted": False,
        "interlock_intr_admission_granted": False,
        "heartbeat_or_oscillator_advanced": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_AUTHORITY_REVIEW_ROUTING_ONLY",
    }
    atomic_json(output, envelope)
    return {**envelope, "envelope_ref": str(output), "envelope_sha256": sha256(output)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = route(args.review.resolve(), args.runtime_root.resolve())
    if args.output:
        atomic_json(args.output, result)
    else:
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
