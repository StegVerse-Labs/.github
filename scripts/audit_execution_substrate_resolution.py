#!/usr/bin/env python3
"""Repo-wide conformance audit for execution_substrate_resolution.

scripts/validate_task_registration_substrate_resolution.py scopes itself to
records `git diff --diff-filter=AM` reports as changed, which is correct for a
PR gate but means a non-conforming record that nobody touches is never seen.

scripts/evaluate_task_registry_collision_checkin.py calls the SAME
validate_resolution and returns STOP_SUBSTRATE_REVIEW_REQUIRED before any
coordination logic, so a record that fails it cannot pass check-in at all.

This audit runs that predicate across every record, so the standing backlog is
visible without waiting for someone to edit each file. Reporting only; it
changes nothing and grants no authority.

Exit 0 always unless --strict, which exits 1 when any record fails.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_task_registration_substrate_resolution import (  # noqa: E402
    runtime_capable,
    validate_resolution,
)

RECORDS = ROOT / "data" / "canonical-task-records"


def audit() -> dict:
    conforming, missing, invalid = [], [], []
    for path in sorted(RECORDS.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            invalid.append({"task_id": path.stem, "error": f"unreadable: {exc}"})
            continue
        if not runtime_capable(record):
            continue
        try:
            validate_resolution(record)
        except ValueError as exc:
            row = {
                "task_id": path.stem,
                "coordination_state": record.get("coordination_state"),
                "error": str(exc),
            }
            if "requires execution_substrate_resolution" in str(exc):
                missing.append(row)
            else:
                invalid.append(row)
        else:
            conforming.append(path.stem)
    return {"conforming": conforming, "missing": missing, "invalid": invalid}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="exit 1 if any record fails")
    args = parser.parse_args(argv)

    result = audit()
    blocked = result["missing"] + result["invalid"]
    total = len(result["conforming"]) + len(blocked)

    if args.json:
        print(json.dumps({
            "schema": "stegverse.execution-substrate-resolution-audit/v1",
            "authority_effect": "NONE",
            "runtime_capable_records": total,
            "conforming": len(result["conforming"]),
            "missing_block": result["missing"],
            "invalid_block": result["invalid"],
        }, indent=2))
    else:
        print(f"EXECUTION_SUBSTRATE_RESOLUTION_AUDIT runtime_capable={total} "
              f"conforming={len(result['conforming'])} blocked={len(blocked)}")
        if blocked:
            print("\nBlocked at check-in (STOP_SUBSTRATE_REVIEW_REQUIRED):")
            for state, n in Counter(r["coordination_state"] for r in blocked).most_common():
                print(f"  {str(state):16s} {n}")
            print("\nRecords with a present but non-conforming block:")
            for row in result["invalid"]:
                print(f"  {row['task_id']}\n      {row['error']}")

    return 1 if (args.strict and blocked) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
