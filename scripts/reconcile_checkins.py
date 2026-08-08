#!/usr/bin/env python3
"""Validate check-in proposals and identify claims releasable after terminal delivery."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "control" / "claims-active.json"
PENDING = ROOT / "tasks" / "checkin-pending"
TERMINAL_DELIVERY_STATES = {"merged", "released", "deployed"}
TERMINAL_RESULTS = {"completed", "abandoned", "transferred", "suspended"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_completed_delivery(task_id: str, proposal: dict) -> None:
    rows = proposal.get("repository_results")
    if not isinstance(rows, list) or not rows:
        fail(f"{task_id}: completed check-in requires at least one repository result")
    for row in rows:
        repository = row.get("repository") or "<unknown>"
        state = row.get("delivery_state")
        if state not in TERMINAL_DELIVERY_STATES:
            fail(f"{task_id}: completed check-in repository {repository} requires terminal delivery state; got {state!r}")
        if state == "merged" and not row.get("commit"):
            fail(f"{task_id}: merged repository result {repository} requires commit evidence")


def main() -> None:
    claims = json.loads(CLAIMS.read_text(encoding="utf-8"))
    active = list(claims.get("claims", []))
    released = []

    for path in sorted(PENDING.glob("TASK-*.json")) if PENDING.exists() else []:
        proposal = json.loads(path.read_text(encoding="utf-8"))
        task_id = proposal.get("task_id")
        result = proposal.get("result")
        if result == "completed":
            validate_completed_delivery(task_id, proposal)

        next_active = []
        for claim in active:
            if claim.get("task_id") == task_id and result in TERMINAL_RESULTS:
                released.append(claim)
            else:
                next_active.append(claim)
        active = next_active

    print(json.dumps({"valid": True, "releasable_claims": released, "remaining_claims": active}, sort_keys=True))


if __name__ == "__main__":
    main()
