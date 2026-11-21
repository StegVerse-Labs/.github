#!/usr/bin/env python3
"""ST-019 merge-admission gate (ST019-MERGE-ADMISSION-001; non-authorizing, stdlib only).

Canonical source: StegVerse-Labs/repo-standards templates/merge-gate/stegverse_merge_gate.py.

Runs as the single always-running required check that the org ruleset's
`workflows` rule injects into every pull request on a default branch. It never
mutates anything; it reads the PR event, the checked-out merge candidate and
the current base tip, and emits exactly one disposition:

  ALLOW        every predicate held and evidence was observed
  DENY         a predicate was observed to fail (draft, stale generation, failed task)
  FAIL_CLOSED  a predicate could not be evaluated (missing event, unreadable base,
               declared validation absent where the tier requires it)

Every non-ALLOW carries the six actionable-disposition fields used by
StegVerse-Labs/.github docs/USER_FACING_EXPLANATION_CONTRACT_MIRROR_HANDOFF.md:
failure_code, failed_predicate, required_evidence_or_repair, retry_entrypoint,
owning_existing_goal, next_attempt.

Why this exists: GitHub reports a job skipped by `if:` as success for a
required check, and a workflow skipped by a `paths:` filter never reports at
all. This job has no `if:` and no path filter, so it cannot be skipped, and
it runs the repository's declared validation itself instead of trusting
sibling checks (which would need waiting/polling to observe).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

POLICY_ID = "STEGVERSE-REPOSITORY-PROTECTION-001"
PROFILE_ID = "ST019-MERGE-ADMISSION-001"
OWNING_GOAL = "ST-019 Repository Protection (StegVerse-Labs/repo-standards) / STEGHEALTH-ECOSYSTEM-FAILURE-REMEDIATION-001"

# Copied from repo-standards config/repository-protection-policy.json; the
# repo-standards test suite fails if either copy drifts from the policy.
# merge_admission.generation_fenced_files:
GENERATION_FENCED_FILES = [
    {"repository": "StegVerse-Labs/.github", "path": "data/canonical-task-registry.json", "field": "generation"},
]
# critical_repositories (TIER_2_CRITICAL). The tier comes from this list, not
# from a per-repository setting; ST019_TIER may only raise a repository to
# TIER_2_CRITICAL, never lower one.
CRITICAL_REPOSITORIES = (
    "StegVerse-Labs/.github",
    "StegVerse-Labs/repo-standards",
    "StegVerse-Labs/Continuity",
    "StegVerse-Labs/TV",
    "StegVerse-Labs/TVC",
    "StegVerse-Labs/Governance",
    "StegVerse-Labs/StegCore",
    "StegVerse-org/StegVerse-SDK",
    "master-records/orchestration",
)
GATE_SOURCE_DIRECTORY = ".stegverse-merge-gate-source"


def resolve_tier(repository: str | None, requested: str | None) -> str:
    if repository in CRITICAL_REPOSITORIES or requested == "TIER_2_CRITICAL":
        return "TIER_2_CRITICAL"
    return "TIER_1_STANDARD"


def git(*args: str, check: bool = True) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def read_json_at(rev: str, path: str) -> Any | None:
    r = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)


def disposition(code: str, predicate: str, repair: str, retry: str, nxt: str) -> dict[str, str]:
    return {
        "failure_code": code,
        "failed_predicate": predicate,
        "required_evidence_or_repair": repair,
        "retry_entrypoint": retry,
        "owning_existing_goal": OWNING_GOAL,
        "next_attempt": nxt,
    }


def declared_task_commands(text: str) -> list[tuple[str, str]]:
    """Line-based reader for ST-002 declared-tasks.yaml (same approach as
    repo-standards tools/validate_repo_standards.py; no PyYAML dependency)."""
    tasks: list[tuple[str, str]] = []
    in_tasks = False
    current = None
    for line in text.splitlines():
        if re.match(r"^tasks:\s*$", line):
            in_tasks = True
            continue
        if in_tasks and re.match(r"^\S", line):
            in_tasks = False
        if not in_tasks:
            continue
        m = re.match(r"^  ([A-Za-z0-9_.-]+):\s*$", line)
        if m:
            current = m.group(1)
            continue
        m = re.match(r"^    command:\s*(.+?)\s*$", line)
        if m and current:
            tasks.append((current, m.group(1).strip("'\"")))
    return tasks


def evaluate(event: dict[str, Any], base_ref: str, head_rev: str, tier: str,
             run_tasks: bool) -> dict[str, Any]:
    predicates: list[dict[str, Any]] = []
    pr = event.get("pull_request") or {}
    repository = (event.get("repository") or {}).get("full_name")
    validation = {"declared_validation_present": None, "declared_validation_ran": False,
                  "declared_validation_consequence": "NOT_REACHED"}
    retry = "push to the PR branch or 'Update branch'; the gate re-runs on synchronize/ready_for_review/reopened"

    def done(outcome: str, disp: dict[str, str] | None) -> dict[str, Any]:
        rec = {
            "schema": "stegverse.merge-admission-receipt/v0.1",
            "policy_id": POLICY_ID,
            "profile_id": PROFILE_ID,
            "repository": repository,
            "pull_request": pr.get("number"),
            "head_sha": pr.get("head", {}).get("sha"),
            "base_ref": base_ref,
            "tier": tier,
            "outcome": outcome,
            "predicates": predicates,
            "actionable_disposition": disp,
            **validation,
            "authority_effect": "NONE_VALIDATION_ONLY",
            "github_actions_mutation_authority": False,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        rec["receipt_sha256"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
        return rec

    # P0: event must be a pull_request / merge_group carrying a head.
    if not pr and "merge_group" not in event:
        predicates.append({"id": "P0_EVENT_PRESENT", "held": False})
        return done("FAIL_CLOSED", disposition(
            "EVENT_NOT_PULL_REQUEST", "P0_EVENT_PRESENT",
            "gate must run on pull_request or merge_group", retry, "re-run on a PR event"))
    predicates.append({"id": "P0_EVENT_PRESENT", "held": True})

    # P1: not a draft.  (GitHub already refuses to merge drafts; this makes the
    # required check red while draft so 'Ready for review' forces a fresh run.)
    if pr.get("draft") is True:
        predicates.append({"id": "P1_NOT_DRAFT", "held": False})
        return done("DENY", disposition(
            "PR_IS_DRAFT", "P1_NOT_DRAFT",
            "mark ready for review only when the lane declares it merge-ready",
            "ready_for_review event re-runs this gate", "after ready_for_review"))
    predicates.append({"id": "P1_NOT_DRAFT", "held": True})

    # P2: base tip observable and contained in head (up to date). The ruleset's
    # strict status-check policy enforces this at merge time; the gate also
    # records it so the receipt is self-describing.
    try:
        base_tip = git("rev-parse", f"origin/{base_ref}").strip()
        merge_base = git("merge-base", head_rev, base_tip).strip()
    except RuntimeError as exc:
        predicates.append({"id": "P2_BASE_OBSERVED", "held": False, "error": str(exc)})
        return done("FAIL_CLOSED", disposition(
            "BASE_NOT_OBSERVABLE", "P2_BASE_OBSERVED",
            "checkout must fetch the base branch tip", retry, "re-run"))
    up_to_date = merge_base == base_tip
    predicates.append({"id": "P2_UP_TO_DATE", "held": up_to_date, "base_tip": base_tip, "merge_base": merge_base})
    if not up_to_date:
        return done("DENY", disposition(
            "HEAD_BEHIND_BASE", "P2_UP_TO_DATE",
            f"rebase or merge {base_ref} ({base_tip[:12]}) into the PR branch", retry,
            "after the branch contains the current base tip"))

    # P3: generation fence (only for files that exist on base or head).
    for spec in GENERATION_FENCED_FILES:
        if spec.get("repository") and repository and spec["repository"] != repository:
            continue
        path, field = spec["path"], spec["field"]
        base_doc, head_doc = read_json_at(base_tip, path), read_json_at(head_rev, path)
        if base_doc is None and head_doc is None:
            continue
        try:
            bg = int(base_doc[field]) if base_doc is not None else None
            hg = int(head_doc[field]) if head_doc is not None else None
        except (KeyError, TypeError, ValueError):
            predicates.append({"id": f"P3_GENERATION:{path}", "held": False})
            return done("FAIL_CLOSED", disposition(
                "GENERATION_UNREADABLE", f"P3_GENERATION:{path}",
                f"{path} must carry integer '{field}' on base and head", retry, "re-run after repair"))
        changed = bool(git("diff", "--name-only", base_tip, head_rev, "--", path).strip())
        expected = (bg + 1) if changed else bg
        held = hg == expected
        predicates.append({"id": f"P3_GENERATION:{path}", "held": held, "base_generation": bg,
                           "head_generation": hg, "file_changed": changed, "expected": expected})
        if not held:
            return done("DENY", disposition(
                "GENERATION_NOT_BASE_PLUS_ONE", f"P3_GENERATION:{path}",
                f"set {path}.{field} to {expected} (base {bg}{' + 1' if changed else ', file unchanged'}) on top of current {base_ref}",
                retry, "after rebase and generation renumber"))

    # P4: declared validation (ST-002 declared-tasks.yaml) actually runs and passes.
    dt = Path("declared-tasks.yaml")
    if not dt.exists():
        validation["declared_validation_present"] = False
        if tier == "TIER_2_CRITICAL":
            validation["declared_validation_consequence"] = "FAIL_CLOSED_TIER_2_REQUIRES_VALIDATION"
            predicates.append({"id": "P4_VALIDATION_DECLARED", "held": False})
            return done("FAIL_CLOSED", disposition(
                "VALIDATION_UNDECLARED", "P4_VALIDATION_DECLARED",
                "TIER_2 repositories must declare validation in declared-tasks.yaml (ST-002)",
                retry, "after declared-tasks.yaml is merged via an owner-approved PR"))
        # TIER_1: ALLOW on the structural predicates, and the receipt says in
        # so many words that no validation ran. Never a silent pass.
        validation["declared_validation_consequence"] = "NO_VALIDATION_RAN"
        predicates.append({"id": "P4_VALIDATION_DECLARED", "held": False,
                           "consequence": "ALLOW_RECORDING_NO_VALIDATION_RAN"})
        return done("ALLOW", None)
    validation["declared_validation_present"] = True
    tasks = declared_task_commands(dt.read_text(encoding="utf-8"))
    if not tasks:
        predicates.append({"id": "P4_VALIDATION_DECLARED", "held": False, "reason": "no task commands"})
        return done("FAIL_CLOSED", disposition(
            "DECLARED_TASKS_EMPTY", "P4_VALIDATION_DECLARED",
            "declared-tasks.yaml must declare at least one task command", retry, "after repair"))
    predicates.append({"id": "P4_VALIDATION_DECLARED", "held": True, "task_count": len(tasks)})
    if not run_tasks:
        validation["declared_validation_consequence"] = "DECLARED_NOT_RUN_LOCAL_DRY_RUN"
    if run_tasks:
        validation["declared_validation_ran"] = True
        for name, command in tasks:
            r = subprocess.run(command, shell=True)
            ok = r.returncode == 0
            predicates.append({"id": f"P5_TASK:{name}", "held": ok, "exit_code": r.returncode})
            if not ok:
                return done("DENY", disposition(
                    "DECLARED_TASK_FAILED", f"P5_TASK:{name}",
                    f"make `{command}` exit 0 on the PR head", retry, "after fix pushed"))
        validation["declared_validation_consequence"] = "DECLARED_VALIDATION_PASSED"
    return done("ALLOW", None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", default=os.environ.get("GITHUB_EVENT_PATH", ""))
    ap.add_argument("--base-ref", default=os.environ.get("GITHUB_BASE_REF", ""))
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--tier", default=os.environ.get("ST019_TIER") or None)
    ap.add_argument("--no-run-tasks", action="store_true")
    ap.add_argument("--write", default="merge-admission-receipt.json")
    a = ap.parse_args()
    try:
        event = json.loads(Path(a.event).read_text()) if a.event else {}
    except (OSError, ValueError):
        event = {}
    base_ref = a.base_ref or (event.get("pull_request") or {}).get("base", {}).get("ref", "") \
        or str((event.get("merge_group") or {}).get("base_ref", "")).removeprefix("refs/heads/")
    tier = resolve_tier((event.get("repository") or {}).get("full_name"), a.tier)
    try:
        rec = evaluate(event, base_ref, a.head, tier, not a.no_run_tasks)
    except Exception as exc:  # every error path is a six-field FAIL_CLOSED
        rec = {
            "schema": "stegverse.merge-admission-receipt/v0.1",
            "policy_id": POLICY_ID,
            "profile_id": PROFILE_ID,
            "repository": (event.get("repository") or {}).get("full_name"),
            "outcome": "FAIL_CLOSED",
            "actionable_disposition": disposition(
                "GATE_INTERNAL_ERROR", "P_GATE_EVALUATED",
                f"{type(exc).__name__}: {str(exc)[:300]}",
                "re-run the stegverse-merge-gate check", "after the gate source or repository state is repaired"),
            "authority_effect": "NONE_VALIDATION_ONLY",
            "github_actions_mutation_authority": False,
        }
    Path(a.write).write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
    print(json.dumps(rec, indent=2, sort_keys=True))
    return 0 if rec["outcome"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
