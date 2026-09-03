#!/usr/bin/env python3
"""Canonical StegVerse session/build pre-work entrypoint backed by StegIndex."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "stegindex_preflight_gate.py"

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

def decide(result: dict):
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
    parser.add_argument(
        "--stegindex-root",
        default=os.environ.get("STEGINDEX_ROOT"),
        help="Already-materialized StegIndex checkout. No network fetch is performed.",
    )
    args = parser.parse_args()

    preflight = run_preflight(args.goal, args.stegindex_root, args.contribution_class)
    disposition, exit_code, task_creation_permitted = decide(preflight)

    result = {
        "schema": "stegverse.session-build-preflight/v1",
        "goal": args.goal,
        "disposition": disposition,
        "task_creation_permitted": task_creation_permitted,
        "preflight": preflight,
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
