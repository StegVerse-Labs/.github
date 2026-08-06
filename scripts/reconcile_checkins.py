#!/usr/bin/env python3
"""Validate check-in proposals and release matching claims after merged delivery."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "control" / "claims-active.json"
PENDING = ROOT / "tasks" / "checkin-pending"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    claims = json.loads(CLAIMS.read_text(encoding="utf-8"))
    active = claims.get("claims", [])
    released = []
    retained = []
    for path in sorted(PENDING.glob("TASK-*.json")) if PENDING.exists() else []:
        proposal = json.loads(path.read_text(encoding="utf-8"))
        task_id = proposal.get("task_id")
        delivery = proposal.get("delivery_state", {})
        result = proposal.get("result")
        if result == "completed" and not delivery.get("merged", False):
            fail(f"{task_id}: completed check-in requires merged=true")
        for claim in active:
            if claim.get("task_id") == task_id and result in {"completed", "abandoned", "transferred", "suspended"}:
                released.append(claim)
            else:
                retained.append(claim)
        active = retained
        retained = []
    print(json.dumps({"valid": True, "releasable_claims": released, "remaining_claims": active}, sort_keys=True))

if __name__ == "__main__":
    main()
