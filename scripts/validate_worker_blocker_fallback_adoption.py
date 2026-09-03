#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADOPTION = ROOT / "control" / "worker-blocker-fallback-adoption.json"

ALLOWED = {
    "ADOPTED",
    "ADOPTED_REFERENCE_IMPLEMENTATION",
    "ALREADY_CONFORMANT",
    "ALREADY_PARTIALLY_CONFORMANT",
    "FOLLOWUP_TASK_CREATED",
    "FOLLOWUP_TASK_REQUIRED",
    "NOT_APPLICABLE",
}

def fail(message: str):
    raise SystemExit(f"WORKER_BLOCKER_FALLBACK_ADOPTION_FAIL: {message}")

def main():
    doc = json.loads(ADOPTION.read_text(encoding="utf-8"))
    families = doc.get("worker_families")
    if not isinstance(families, list) or not families:
        fail("worker_families missing")

    seen = set()
    for row in families:
        family = row.get("family")
        state = row.get("state")
        if not family:
            fail("family missing")
        if family in seen:
            fail(f"duplicate family {family}")
        seen.add(family)
        if state not in ALLOWED:
            fail(f"{family}: invalid state {state}")
        if not row.get("owner"):
            fail(f"{family}: owner missing")
        if state in {"ADOPTED","ADOPTED_REFERENCE_IMPLEMENTATION","ALREADY_CONFORMANT"}:
            if not row.get("evidence") and family == "validation_reconciliation":
                fail(f"{family}: adopted state requires evidence")

    target = next((r for r in families if r.get("family") == "validation_reconciliation"), None)
    if target is None:
        fail("validation_reconciliation family missing")
    if target.get("state") != "ADOPTED":
        fail("validation_reconciliation must remain ADOPTED unless its evidence is explicitly superseded")
    evidence = target.get("evidence") or []
    required_fragments = [
        "StegVerse-Labs/StegIndex#3",
        "StegVerse-Labs/.github#881",
        "StegVerse-Labs/.github#885",
        "33713433913 SUCCESS",
        "33713434257 SUCCESS",
    ]
    joined = "\n".join(evidence)
    for fragment in required_fragments:
        if fragment not in joined:
            fail(f"validation_reconciliation missing evidence fragment: {fragment}")
    if target.get("authority_effect") != "NONE":
        fail("validation_reconciliation adoption must grant no authority")

    print(f"WORKER_BLOCKER_FALLBACK_ADOPTION_PASS families={len(families)}")

if __name__ == "__main__":
    main()
