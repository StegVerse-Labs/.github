#!/usr/bin/env python3
"""Canonical StegVerse session/build pre-work entrypoint backed by StegIndex and cross-task coordination."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "stegindex_preflight_gate.py"
COORDINATION_LEDGER = ROOT / "control" / "cross-task-coordination.json"
COORDINATION_FRAGMENTS = ROOT / "control" / "cross-task-coordination.d"
EXPECTED_COORDINATION_AUTHORITY = "NONE_INDEX_PROJECTION_ONLY"

EXIT_READY = 0
EXIT_EXACT_DEPENDENCY = 2
EXIT_CONTINUE_MACHINE = 3


def run_preflight(goal: str, stegindex_root: str | None, contribution_class: str | None):
    cmd = [sys.executable, str(GATE), "--query", goal]
    if stegindex_root:
        cmd += ["--stegindex-root", stegindex_root]
    if contribution_class:
        cmd += ["--contribution-class", contribution_class]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "StegIndex gate failed")
    return json.loads(proc.stdout)


def run_coordination_projection(
    stegindex_root: str | None,
    *,
    task_id: str | None = None,
    predicate_id: str | None = None,
) -> dict:
    if not stegindex_root:
        return {
            "state": "STEGINDEX_ROOT_NOT_DECLARED",
            "coordination_consulted": False,
            "exact_dependency": "STEGINDEX_ROOT, STEGVERSE_REPO_ROOTS_JSON, or --stegindex-root",
            "authority_effect": "NONE",
        }
    entry = Path(stegindex_root).expanduser().resolve() / "scripts" / "resolve_cross_task_coordination.py"
    if not entry.is_file():
        return {
            "state": "COORDINATION_RESOLVER_UNAVAILABLE",
            "coordination_consulted": False,
            "exact_dependency": str(entry),
            "authority_effect": "NONE",
        }
    if not COORDINATION_LEDGER.is_file():
        return {
            "state": "COORDINATION_LEDGER_UNAVAILABLE",
            "coordination_consulted": False,
            "exact_dependency": str(COORDINATION_LEDGER),
            "authority_effect": "NONE",
        }

    cmd = [
        sys.executable,
        str(entry),
        "--ledger",
        str(COORDINATION_LEDGER),
        "--fragments-dir",
        str(COORDINATION_FRAGMENTS),
    ]
    if task_id:
        cmd += ["--task-id", task_id]
    if predicate_id:
        cmd += ["--predicate-id", predicate_id]
    proc = subprocess.run(cmd, cwd=Path(stegindex_root), text=True, capture_output=True)
    if proc.returncode != 0:
        return {
            "state": "COORDINATION_RESOLUTION_FAILED",
            "coordination_consulted": False,
            "exact_dependency": proc.stderr.strip() or proc.stdout.strip() or "cross-task coordination projection",
            "authority_effect": "NONE",
        }
    projection = json.loads(proc.stdout)
    if projection.get("authority_effect") != EXPECTED_COORDINATION_AUTHORITY:
        raise RuntimeError("cross-task coordination authority invariant violation")
    return {
        "state": "RESOLVED",
        "coordination_consulted": True,
        "task_filter": task_id,
        "predicate_filter": predicate_id,
        "source_fragment_ids": projection.get("source_fragment_ids", []),
        "related_active_claims": projection.get("related_active_claims", []),
        "foreign_active_claims": projection.get("foreign_active_claims", []),
        "gaps": projection.get("gaps", []),
        "predicate_dependency_relationships": projection.get("predicate_dependency_relationships", []),
        "dependency_readiness_inferred": False,
        "candidate_consumer_execution_admission_inferred": False,
        "runtime_truth_inferred": False,
        "authority_effect": "NONE",
    }


def decide(result: dict, coordination: dict):
    decision = result.get("decision")
    if decision == "CONTINUE_MACHINE_EXECUTION":
        disposition = "CONTINUE_THROUGH_CANONICAL_OWNER"
        exit_code = EXIT_CONTINUE_MACHINE
        task_creation_permitted = False
    elif decision == "REUSE_OR_EXTEND_EXISTING":
        disposition = "REUSE_EXISTING_CAPABILITY"
        exit_code = EXIT_READY
        task_creation_permitted = False
    elif decision == "NO_EXISTING_CAPABILITY_MATCH":
        if not coordination.get("coordination_consulted"):
            disposition = "STOP_AT_COORDINATION_DEPENDENCY"
            exit_code = EXIT_EXACT_DEPENDENCY
            task_creation_permitted = False
        else:
            disposition = "NEW_WORK_MAY_BE_CONSIDERED"
            exit_code = EXIT_READY
            task_creation_permitted = True
    elif decision == "EXACT_BLOCKER_ONLY":
        disposition = "STOP_AT_EXACT_DEPENDENCY"
        exit_code = EXIT_EXACT_DEPENDENCY
        task_creation_permitted = False
    else:
        raise RuntimeError(f"unsupported StegIndex decision: {decision}")
    return disposition, exit_code, task_creation_permitted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--goal", required=True)
    parser.add_argument("--contribution-class")
    parser.add_argument("--coordination-task-id")
    parser.add_argument("--coordination-predicate-id")
    parser.add_argument(
        "--stegindex-root",
        default=os.environ.get("STEGINDEX_ROOT"),
        help="Already-materialized StegIndex checkout. No network fetch is performed.",
    )
    args = parser.parse_args()

    preflight = run_preflight(args.goal, args.stegindex_root, args.contribution_class)
    coordination = run_coordination_projection(
        args.stegindex_root,
        task_id=args.coordination_task_id,
        predicate_id=args.coordination_predicate_id,
    )
    disposition, exit_code, task_creation_permitted = decide(preflight, coordination)

    result = {
        "schema": "stegverse.session-build-preflight/v1",
        "goal": args.goal,
        "disposition": disposition,
        "task_creation_permitted": task_creation_permitted,
        "preflight": preflight,
        "cross_task_coordination": coordination,
        "coordination_required_before_new_work": True,
        "authority_effect": "NONE_PREWORK_DECISION_ONLY",
        "network_fetch_performed": False,
        "runtime_execution_performed": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
