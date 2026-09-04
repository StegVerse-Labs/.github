#!/usr/bin/env python3
"""Classify whether an exact proposed entity transition is machine- or human-owned.

This classifier grants no authority. It prevents machine-owned transitions from being
routed into the human interaction queue merely because they execute on the user's
current device. The exact transition still requires contemporaneous Interlock/InTr
(and TV/TVC where applicable) governance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "stegverse.entity-transition-ownership-evaluation/v1"
HUMAN_CLASSES = {
    "HUMAN_ONLY",
    "USER_ONLY",
    "LEGAL_PERSON_SIGNATURE",
    "OWNER_EXPLICIT_CONSENT",
}


def fail(reason: str) -> None:
    raise SystemExit(f"FAIL_CLOSED: {reason}")


def evaluate(proposal: dict[str, Any]) -> dict[str, Any]:
    transition_id = str(proposal.get("transition_id") or "").strip()
    authority_class = str(proposal.get("authority_class") or "").strip().upper()
    execution_surface = str(proposal.get("execution_surface") or "").strip()
    if not transition_id:
        fail("transition_id required")
    if not authority_class:
        fail("authority_class required; do not infer authority")

    human_required = authority_class in HUMAN_CLASSES
    if proposal.get("human_approval_required") is True and not human_required:
        fail("machine-owned transition may not be promoted to human approval")
    if proposal.get("human_approval_required") is False and human_required:
        fail("human-authority transition may not bypass explicit human action")

    route = "CURRENT_USER_IOS_INTERACTION_QUEUE" if human_required else "ENTITY_MACHINE_GOVERNANCE_LOOP"
    return {
        "schema": SCHEMA,
        "transition_id": transition_id,
        "authority_class": authority_class,
        "execution_surface": execution_surface or None,
        "human_interaction_required": human_required,
        "route": route,
        "current_governance_required": True,
        "authority_inferred": False,
        "authority_reused": False,
        "prior_receipt_authorizes_transition": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_CLASSIFICATION_ONLY",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("proposal", type=Path)
    args = p.parse_args()
    proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
    print(json.dumps(evaluate(proposal), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
