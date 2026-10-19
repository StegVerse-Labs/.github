#!/usr/bin/env python3
"""Rehearse the owner's one-command Registry apply in CI, on a throwaway worktree.

Runs the same three commands the owner runs after merge, against a committed data file
whose sha256 the caller declares:

1. the digest check (``sha256sum <data>`` equals ``--sha256``);
2. ``apply_task_record_data.py <data>`` (plan): ALLOW, or NO_CHANGE once applied;
3. ``apply_task_record_data.py <data> --apply`` then a re-run, which must be NO_CHANGE.

Steps 2 and 3 run in a temporary ``git worktree`` of HEAD, so the checkout is never
modified and nothing is committed or pushed. A missing input, a digest mismatch, or any
other disposition is FAIL_CLOSED with the standard six fields. Reads only the repository
and its ``--tip-ref``; no API, network or clock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "stegverse.owner-apply-rehearsal.v1"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
RETRY_ENTRYPOINT = "python scripts/rehearse_owner_apply.py --data <committed data file> --sha256 <digest> [--tip-ref origin/main]"
Runner = Callable[[list[str], Path], dict[str, Any]]


class Refused(Exception):
    def __init__(self, code: str, predicate: str, repair: str, **evidence: Any) -> None:
        super().__init__(code)
        self.result = {"schema": SCHEMA, "disposition": "FAIL_CLOSED", "failure_code": code,
                       "failed_predicate": predicate, "required_evidence_or_repair": repair,
                       "retry_entrypoint": RETRY_ENTRYPOINT, "owning_existing_goal": OWNING_GOAL,
                       "next_attempt": "after the named input or Registry state is corrected", "evidence": evidence}


def run_apply(args: list[str], cwd: Path) -> dict[str, Any]:
    done = subprocess.run([sys.executable, "scripts/apply_task_record_data.py", *args], cwd=cwd,
                          capture_output=True, text=True)
    try:
        return json.loads(done.stdout)
    except ValueError:
        return {"disposition": "UNREADABLE_OUTPUT", "returncode": done.returncode, "stderr": done.stderr[-600:]}


def rehearse(data: Path, sha256: str, tip_ref: str, worktree: Path, runner: Runner = run_apply) -> dict[str, Any]:
    if not sha256 or not data.is_file():
        raise Refused("REHEARSAL_INPUT_NOT_SUPPLIED", "the committed data file exists and its sha256 is declared",
                      "commit the owner data file and declare its sha256 in the workflow", data=str(data))
    digest = hashlib.sha256(data.read_bytes()).hexdigest()
    if digest != sha256.lower():
        raise Refused("REHEARSAL_DIGEST_MISMATCH", "sha256 of the committed data file equals the declared digest",
                      "commit the file the owner will apply, or declare its digest", declared=sha256, actual=digest)
    target = str(data.resolve())  # the digest-checked file itself, applied to the worktree's Registry
    steps = {"plan": runner([target, "--tip-ref", tip_ref], worktree)}
    if steps["plan"].get("disposition") == "ALLOW":
        steps["apply"] = runner([target, "--tip-ref", tip_ref, "--apply"], worktree)
        steps["rerun"] = runner([target, "--tip-ref", tip_ref], worktree)
        ok = steps["apply"].get("disposition") == "ALLOW" and steps["rerun"].get("disposition") == "NO_CHANGE"
    else:
        ok = steps["plan"].get("disposition") == "NO_CHANGE"
    summary = {name: {k: step.get(k) for k in ("disposition", "generation", "tip_generation", "failure_code")}
               for name, step in steps.items()}
    if not ok:
        raise Refused("REHEARSAL_NOT_ALLOW", "plan is ALLOW, apply is ALLOW and the re-run is NO_CHANGE "
                      "(or the plan is NO_CHANGE once applied)", "fix the data or rebase onto the live tip",
                      steps=steps)
    return {"schema": SCHEMA, "disposition": "ALLOW", "sha256": digest, "tip_ref": tip_ref, "steps": summary,
            "authority_effect": "NONE", "files_changed_in_checkout": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path)
    parser.add_argument("--sha256", default="")
    parser.add_argument("--tip-ref", default="origin/main")
    args = parser.parse_args(argv)
    try:
        if args.data is None:
            raise Refused("REHEARSAL_INPUT_NOT_SUPPLIED", "--data names the committed data file", "supply --data")
        with tempfile.TemporaryDirectory() as temp:
            worktree = Path(temp) / "rehearsal"
            subprocess.run(["git", "worktree", "add", "--detach", "--quiet", str(worktree), "HEAD"], cwd=ROOT, check=True)
            try:
                result = rehearse(args.data, args.sha256, args.tip_ref, worktree)
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=ROOT, check=False)
    except Refused as refusal:
        print(json.dumps(refusal.result, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
