#!/usr/bin/env python3
"""Consume StegIndex mandatory preflight without granting StegIndex authority."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

EXPECTED_AUTHORITY_EFFECT = "NONE_INDEX_RESOLUTION_ONLY"

def load_preflight(stegindex_root: Path, query: str, contribution_class: str | None):
    entry = stegindex_root / "scripts" / "preflight.py"
    if not entry.is_file():
        return {
            "adapter_state": "STEGINDEX_SOURCE_UNAVAILABLE",
            "decision": "EXACT_BLOCKER_ONLY",
            "generic_blocker_permitted": False,
            "machine_continuation_required": False,
            "exact_dependency": str(entry),
            "authority_effect": "NONE",
        }

    cmd = [sys.executable, str(entry), "--query", query]
    if contribution_class:
        cmd += ["--contribution-class", contribution_class]

    proc = subprocess.run(
        cmd,
        cwd=stegindex_root,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return {
            "adapter_state": "STEGINDEX_PREFLIGHT_FAILED",
            "decision": "EXACT_BLOCKER_ONLY",
            "generic_blocker_permitted": False,
            "machine_continuation_required": False,
            "exact_dependency": proc.stderr.strip() or proc.stdout.strip(),
            "authority_effect": "NONE",
        }

    result = json.loads(proc.stdout)
    if result.get("authority_effect") != EXPECTED_AUTHORITY_EFFECT:
        raise SystemExit("StegIndex authority invariant violation")

    if result.get("machine_continuation_required"):
        decision = "CONTINUE_MACHINE_EXECUTION"
    elif result.get("existing_capability_found"):
        decision = "REUSE_OR_EXTEND_EXISTING"
    else:
        decision = "NO_EXISTING_CAPABILITY_MATCH"

    return {
        "adapter_state": "RESOLVED",
        "decision": decision,
        "query": query,
        "duplicate_implementation_guard": result.get("duplicate_implementation_guard"),
        "purpose_contributions": result.get("purpose_contributions", []),
        "first_actionable_predicate": result.get("first_actionable_predicate"),
        "machine_continuation_required": bool(result.get("machine_continuation_required")),
        "generic_blocker_permitted": bool(result.get("generic_blocker_permitted")),
        "authority_effect": "NONE",
        "stegindex_authority_effect": result.get("authority_effect"),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--contribution-class")
    parser.add_argument(
        "--stegindex-root",
        default=os.environ.get("STEGINDEX_ROOT"),
        help="Path to an already-materialized StegIndex checkout. No network fetch is performed.",
    )
    args = parser.parse_args()

    if not args.stegindex_root:
        result = {
            "adapter_state": "STEGINDEX_ROOT_NOT_DECLARED",
            "decision": "EXACT_BLOCKER_ONLY",
            "generic_blocker_permitted": False,
            "machine_continuation_required": False,
            "exact_dependency": "STEGINDEX_ROOT or --stegindex-root",
            "authority_effect": "NONE",
        }
    else:
        result = load_preflight(
            Path(args.stegindex_root).expanduser().resolve(),
            args.query,
            args.contribution_class,
        )

    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
