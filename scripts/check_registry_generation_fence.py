#!/usr/bin/env python3
"""Fail closed when a canonical Task Registry generation is not main + 1.

Registry generation 317 and then 318 were each taken twice on main on
2026-10-17: #3209 (3da74c7) and #3208 (5b3fc47) both set 317, then #3218
(4683db2) and #3214 (60d90c4) both set 318. Each PR was green because nothing
compared its generation with the live tip of the branch it merged into.

This gate applies the existing session mutation generation fence
(data/task-coordination-policy.json#session_mutation_generation_fence, enforced
by generation_fence_payload() in scripts/evaluate_task_registry_collision_checkin.py)
to the registry file itself, through a read-only path:

* pull_request: when the PR changes data/canonical-task-registry.json relative
  to its merge base with the live base tip, the head generation must equal the
  live base tip generation + 1. The live tip is fetched, never taken from
  github.event.pull_request.base.sha, which is fixed when the event fires.
* push: for every first-parent commit pushed to main that changes the registry
  content, its generation must be exactly its first parent's + 1. A repeat or
  regression is REGISTRY_GENERATION_DUPLICATED; a skip is
  REGISTRY_GENERATION_NOT_TIP_PLUS_ONE.

Outcomes are `disposition: ALLOW` or `disposition: FAIL_CLOSED`. Every failure
path - an unreadable generation, unreadable policy, bad arguments or any
unexpected error - emits the standard six fields (failure_code,
failed_predicate, required_evidence_or_repair, retry_entrypoint,
owning_existing_goal, next_attempt) to stderr and the job summary and exits 1.
It never skips.

Read-only and non-authorizing: it appends no event ledger, mints no receipt,
confers no admission and writes only the job summary when GITHUB_STEP_SUMMARY
is set. It does not prevent a GitHub platform admin bypass.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = "data/canonical-task-registry.json"
POLICY = ROOT / "data" / "task-coordination-policy.json"
GATE = "REGISTRY_GENERATION_FENCE"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
NOT_TIP_PLUS_ONE = "REGISTRY_GENERATION_NOT_TIP_PLUS_ONE"
DUPLICATED = "REGISTRY_GENERATION_DUPLICATED"
UNREADABLE = "REGISTRY_GENERATION_UNREADABLE"
POLICY_UNREADABLE = "REGISTRY_GENERATION_FENCE_POLICY_UNREADABLE"
INTERNAL_ERROR = "REGISTRY_GENERATION_FENCE_INTERNAL_ERROR"
# The standard six-field refusal names (see org-kernel/kernel.py SIX_FIELDS).
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
ALLOW = "ALLOW"
FAIL_CLOSED = "FAIL_CLOSED"
RETRY_ENTRYPOINT = ("Cross-Task Coordination Validation / validate: "
                    "python scripts/check_registry_generation_fence.py")


class GenerationUnreadable(Exception):
    pass


class FencePolicyUnreadable(Exception):
    pass


def _load_collision_gate():
    """Import the existing collision gate for generation_fence_payload().

    Importing it executes no check-in and appends no event; only the pure
    payload function is called.
    """
    spec = importlib.util.spec_from_file_location(
        "_collision_gate_for_generation_fence",
        ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def generation_fence_payload(observed: int | None, current: int) -> dict:
    return _load_collision_gate().generation_fence_payload(observed, current)


def session_fence_policy() -> dict:
    try:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise FencePolicyUnreadable(f"{POLICY.name} is unreadable: {exc}") from None
    fence = policy.get("session_mutation_generation_fence") if isinstance(policy, dict) else None
    if not isinstance(fence, dict) or fence.get("required") is not True:
        raise FencePolicyUnreadable("session_mutation_generation_fence is missing or not required")
    return fence


def parse_generation(raw: bytes | str | None, where: str) -> int:
    if raw is None:
        raise GenerationUnreadable(f"{REGISTRY_PATH} is absent at {where}")
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise GenerationUnreadable(f"{REGISTRY_PATH} at {where} is not JSON: {exc}") from None
    generation = value.get("generation") if isinstance(value, dict) else None
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise GenerationUnreadable(
            f"{REGISTRY_PATH} at {where} has no non-negative integer generation")
    return generation


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True)


def rev(repo: Path, ref: str) -> str:
    done = _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if done.returncode != 0:
        raise GenerationUnreadable(f"cannot resolve {ref}: {done.stderr.decode(errors='replace').strip()}")
    return done.stdout.decode().strip()


def blob(repo: Path, commit: str) -> bytes | None:
    done = _git(repo, "show", f"{commit}:{REGISTRY_PATH}")
    return done.stdout if done.returncode == 0 else None


def generation_at(repo: Path, commit: str) -> int:
    return parse_generation(blob(repo, commit), commit)


def failure(code: str, predicate: str, repair: str, next_attempt: str, **evidence) -> dict:
    return {"disposition": FAIL_CLOSED, "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": RETRY_ENTRYPOINT,
            "owning_existing_goal": OWNING_GOAL, "next_attempt": next_attempt,
            "evidence": evidence}


def policy_unreadable(detail: str) -> dict:
    return failure(POLICY_UNREADABLE,
                   "data/task-coordination-policy.json#session_mutation_generation_fence "
                   "readable with required == true",
                   "restore session_mutation_generation_fence (required: true) in "
                   "data/task-coordination-policy.json; this gate never edits policy data",
                   "after the policy is restored, re-run the check", detail=detail)


def internal_error(exc: BaseException) -> dict:
    return failure(INTERNAL_ERROR, "the generation fence evaluates without an unexpected error",
                   "fix the fence or its inputs so it evaluates; an error is never a pass",
                   "after the error is fixed, re-run the check",
                   detail=f"{type(exc).__name__}: {exc}")


def unreadable(detail: str) -> dict:
    return failure(UNREADABLE, f"{REGISTRY_PATH}#generation readable as a non-negative integer",
                   "restore a readable integer generation in the registry, or make the "
                   "base tip and head fetchable, then rerun", "after the registry is readable",
                   detail=detail)


def evaluate_pull_request(head_generation: int, tip_generation: int, tip_sha: str = "",
                          head_sha: str = "") -> dict:
    """A registry-editing PR must sit exactly one generation above the live tip."""
    fence = generation_fence_payload(head_generation - 1, tip_generation)
    if head_generation == tip_generation + 1 and fence["coordination_generation_current"]:
        return {"disposition": ALLOW, "head_generation": head_generation,
                "tip_generation": tip_generation, "session_mutation_generation_fence": fence}
    stale = "stale" if head_generation <= tip_generation + 1 else "divergent"
    return failure(
        NOT_TIP_PLUS_ONE,
        f"head generation ({head_generation}) == live base tip generation ({tip_generation}) + 1",
        f"rebase onto the live base tip {tip_sha or '(origin/main)'} and set "
        f"{REGISTRY_PATH}#generation to {tip_generation + 1}, keeping every row on the tip",
        f"after the head is rebased to generation {tip_generation + 1} "
        f"({stale} at {head_generation}); re-run if the base tip moves again",
        head_sha=head_sha, head_generation=head_generation, tip_sha=tip_sha,
        tip_generation=tip_generation, session_mutation_generation_fence=fence)


def evaluate_push_step(previous_generation: int, new_generation: int,
                       content_changed: bool, previous_sha: str = "", new_sha: str = "") -> dict:
    """A registry content change on main must advance the generation by exactly one."""
    if not content_changed or new_generation == previous_generation + 1:
        return {"disposition": ALLOW, "previous_generation": previous_generation,
                "new_generation": new_generation, "content_changed": content_changed,
                "commit": new_sha}
    if new_generation > previous_generation + 1:
        return failure(
            NOT_TIP_PLUS_ONE,
            f"registry content changed and new generation ({new_generation}) == "
            f"previous generation ({previous_generation}) + 1",
            f"generations {previous_generation + 1}..{new_generation - 1} were skipped on main; "
            "record the jump in a registry-only owner-merged PR, or confirm it was intended, "
            "keeping the next registry PR at the current main generation + 1",
            "after the owner records the skipped generations; the next registry PR takes "
            "main + 1",
            previous_sha=previous_sha, previous_generation=previous_generation,
            new_sha=new_sha, new_generation=new_generation)
    return failure(
        DUPLICATED,
        f"registry content changed and new generation ({new_generation}) == "
        f"previous generation ({previous_generation}) + 1",
        f"open one registry-only PR that sets {REGISTRY_PATH}#generation to "
        f"{max(new_generation, previous_generation) + 1} on the current main tip, "
        "keeping both colliding changes; it is an owner-only merge",
        "after the repair PR merges; any other registry PR then takes the next generation",
        previous_sha=previous_sha, previous_generation=previous_generation,
        new_sha=new_sha, new_generation=new_generation)


def check_pull_request(repo: Path, base_ref: str, head_ref: str) -> dict:
    try:
        tip, head = rev(repo, base_ref), rev(repo, head_ref)
        done = _git(repo, "merge-base", tip, head)
        if done.returncode != 0:
            raise GenerationUnreadable(f"no merge base between {tip} and {head}")
        fork = done.stdout.decode().strip()
        head_blob = blob(repo, head)
        if head_blob is not None and head_blob == blob(repo, fork):
            return {"disposition": ALLOW, "applicability": "NOT_APPLICABLE", "reason": "PR does not change the registry",
                    "tip_sha": tip, "head_sha": head}
        return evaluate_pull_request(parse_generation(head_blob, head),
                                     generation_at(repo, tip), tip, head)
    except GenerationUnreadable as exc:
        return unreadable(str(exc))


def check_push(repo: Path, before: str, after: str) -> dict:
    try:
        after_sha = rev(repo, after)
        zero = not before or set(before) == {"0"}
        start = rev(repo, f"{after_sha}^1") if zero else rev(repo, before)
        done = _git(repo, "rev-list", "--first-parent", "--reverse", f"{start}..{after_sha}")
        if done.returncode != 0:
            raise GenerationUnreadable(f"cannot list {start}..{after_sha}")
        steps, previous = [], start
        for commit in done.stdout.decode().split():
            prev_blob, new_blob = blob(repo, previous), blob(repo, commit)
            result = evaluate_push_step(parse_generation(prev_blob, previous),
                                        parse_generation(new_blob, commit),
                                        prev_blob != new_blob, previous, commit)
            if result["disposition"] != ALLOW:
                return result
            steps.append(result)
            previous = commit
        return {"disposition": ALLOW, "steps": steps}
    except GenerationUnreadable as exc:
        return unreadable(str(exc))


def summary_markdown(result: dict) -> str:
    lines = [f"### {GATE}: {result['disposition']}", ""]
    if result["disposition"] == FAIL_CLOSED:
        lines += ["| field | value |", "|---|---|"]
        lines += [f"| {k} | {str(result[k]).replace('|', '/')} |" for k in SIX_FIELDS]
    return "\n".join(lines) + "\n"


def evaluate(args: argparse.Namespace) -> dict:
    try:
        fence_policy = session_fence_policy()
    except FencePolicyUnreadable as exc:
        return policy_unreadable(str(exc))
    repo = Path(args.repo)
    result = (check_pull_request(repo, args.base_ref, args.head_ref) if args.mode == "pull_request"
              else check_push(repo, args.before, args.after))
    result["reconciliation_action"] = fence_policy.get("reconciliation_action")
    return result


def emit(result: dict, mode: str | None) -> int:
    """Print, summarize and exit; every non-ALLOW outcome carries the six fields."""
    if result.get("disposition") != ALLOW:
        result = result if result.get("disposition") == FAIL_CLOSED else internal_error(
            ValueError(f"unexpected disposition {result.get('disposition')!r}"))
    result.update(gate=GATE, mode=mode, authority_effect="NONE_READ_ONLY",
                  event_ledger_written=False,
                  policy_ref="data/task-coordination-policy.json#session_mutation_generation_fence")
    failed = result["disposition"] == FAIL_CLOSED
    try:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as handle:
                handle.write(summary_markdown(result))
    except Exception as exc:  # reporting must not turn a failure into a pass
        print(f"{GATE}: could not write the report: {type(exc).__name__}: {exc}", file=sys.stderr)
        failed = True
    if failed:
        for key in SIX_FIELDS:
            print(f"{key}={result.get(key, INTERNAL_ERROR if key == 'failure_code' else '')}",
                  file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mode", choices=("pull_request", "push"), required=True)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument("--before", default="")
    parser.add_argument("--after", default="HEAD")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code in (0, None):
            raise
        return emit(internal_error(ValueError(f"invalid arguments (argparse exit {exc.code})")), None)
    try:
        result = evaluate(args)
    except Exception as exc:  # fail closed on anything unexpected, with the six fields
        result = internal_error(exc)
    return emit(result, args.mode)


if __name__ == "__main__":
    sys.exit(main())
