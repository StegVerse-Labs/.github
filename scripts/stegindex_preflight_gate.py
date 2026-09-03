#!/usr/bin/env python3
"""Consume StegIndex mandatory preflight without granting StegIndex authority."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

EXPECTED_AUTHORITY_EFFECT = "NONE_INDEX_RESOLUTION_ONLY"

def resolve_stegindex_root(explicit: str | None) -> Path | None:
    raw = str(explicit or os.environ.get("STEGINDEX_ROOT") or "").strip()
    if not raw:
        roots_raw = str(os.environ.get("STEGVERSE_REPO_ROOTS_JSON") or "").strip()
        if roots_raw:
            try:
                roots = json.loads(roots_raw)
            except json.JSONDecodeError:
                roots = {}
            if isinstance(roots, dict):
                raw = str(
                    roots.get("StegVerse-Labs/StegIndex")
                    or roots.get("StegIndex")
                    or ""
                ).strip()
    return Path(raw).expanduser().resolve() if raw else None

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

    indexed_truth_usable = result.get("indexed_truth_usable", True)
    duplicate_guard = result.get("duplicate_implementation_guard")
    if not indexed_truth_usable:
        decision = "EXACT_BLOCKER_ONLY"
        exact_dependency = "indexed_truth_reconciled"
    elif duplicate_guard == "REVIEW_DISCOVERED_CANDIDATE_BEFORE_NEW_WORK":
        decision = "EXACT_BLOCKER_ONLY"
        exact_dependency = "candidate_reconciled"
    elif duplicate_guard == "COMPLETE_SOURCE_DISCOVERY_BEFORE_NEW_WORK":
        decision = "EXACT_BLOCKER_ONLY"
        exact_dependency = "source_discovery_complete"
    elif result.get("machine_continuation_required"):
        decision = "CONTINUE_MACHINE_EXECUTION"
        exact_dependency = None
    elif result.get("existing_capability_found"):
        decision = "REUSE_OR_EXTEND_EXISTING"
        exact_dependency = None
    elif duplicate_guard in (None, "NO_EXISTING_CAPABILITY_MATCH"):
        decision = "NO_EXISTING_CAPABILITY_MATCH"
        exact_dependency = None
    else:
        decision = "EXACT_BLOCKER_ONLY"
        exact_dependency = f"unsupported_duplicate_implementation_guard:{duplicate_guard}"

    return {
        "adapter_state": "RESOLVED",
        "decision": decision,
        "query": query,
        "indexed_truth_usable": bool(indexed_truth_usable),
        "truth_reconciliation": result.get("truth_reconciliation"),
        "duplicate_implementation_guard": result.get("duplicate_implementation_guard"),
        "purpose_contributions": result.get("purpose_contributions", []),
        "capability_risk": result.get("capability_risk", {}),
        "first_actionable_predicate": result.get("first_actionable_predicate"),
        "machine_continuation_required": bool(
            indexed_truth_usable and result.get("machine_continuation_required")
        ),
        "generic_blocker_permitted": False if not indexed_truth_usable else bool(result.get("generic_blocker_permitted")),
        "exact_dependency": exact_dependency,
        "authority_effect": "NONE",
        "stegindex_authority_effect": result.get("authority_effect"),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--contribution-class")
    parser.add_argument(
        "--stegindex-root",
        help="Path to an already-materialized StegIndex checkout. Falls back to STEGINDEX_ROOT or STEGVERSE_REPO_ROOTS_JSON. No network fetch is performed.",
    )
    args = parser.parse_args()

    stegindex_root = resolve_stegindex_root(args.stegindex_root)
    if stegindex_root is None:
        result = {
            "adapter_state": "STEGINDEX_ROOT_NOT_DECLARED",
            "decision": "EXACT_BLOCKER_ONLY",
            "generic_blocker_permitted": False,
            "machine_continuation_required": False,
            "exact_dependency": "STEGINDEX_ROOT, STEGVERSE_REPO_ROOTS_JSON, or --stegindex-root",
            "authority_effect": "NONE",
        }
    else:
        result = load_preflight(
            stegindex_root,
            args.query,
            args.contribution_class,
        )

    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
