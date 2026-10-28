#!/usr/bin/env python3
"""Run the existing Task Registry collision check-in on every task a PR changes.

Coordination item H48. A pull request that edits data/canonical-task-registry.json
or a shard under data/canonical-task-records/ could register or re-scope a task
that the canonical check-in (scripts/evaluate_task_registry_collision_checkin.py)
would stop, and nothing ran that check-in in CI.

This gate does not sort collisions itself. It loads the evaluator from the head
tree and runs its unmodified main() once per changed task against the head tree
and once against the base tree, so the disposition logic stays in the one
existing engine. Changed tasks are the registry rows and canonical shards whose
JSON differs between base and head.

A changed task is ALLOW when its head disposition is:

* CONTINUE; or
* STOP_INACTIVE / STOP_SUPERSEDED - the PR leaves the task terminal, so no
  session can check in to it; or
* no stronger than its base disposition, with no collision candidate or hard
  collision id the base did not already hold - a pre-existing coordination
  state is reported, not charged to this PR.

Anything else - a newly registered task that is not CONTINUE, a disposition
that got stronger, a new collision candidate, or an evaluator refusal - is
FAIL_CLOSED with the standard six fields. With --strict every non-terminal
non-CONTINUE head disposition fails, whatever the base held.

Each request declares caller_surface CI_PULL_REQUEST_COLLISION_VALIDATION and
observed_registry_generation equal to the tree's own generation; the generation
fence against the live tip is check_registry_generation_fence.py's job. No
session_id is sent and the event ledger is pointed at an empty temporary path,
so no check-in event is appended.

Read-only and non-authorizing: CI here is validation only, never a transition
predicate. It mints no receipt, confers no admission, and writes only the job
summary when GITHUB_STEP_SUMMARY is set. Making it a required check is
owner-only.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile

REGISTRY_PATH = "data/canonical-task-registry.json"
RECORDS_PATH = "data/canonical-task-records"
INVARIANTS_PATH = "data/task-registry-global-invariants.json"
CALLER_SURFACE = "CI_PULL_REQUEST_COLLISION_VALIDATION"
GATE = "REGISTRY_COLLISION_CHECKIN"
OWNING_GOAL = "TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001"
RETRY_ENTRYPOINT = ".github/workflows/task-registry-collision-checkin.yml"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
ALLOW = "ALLOW"
FAIL_CLOSED = "FAIL_CLOSED"
TERMINAL = {"STOP_INACTIVE", "STOP_SUPERSEDED"}


def severity(disposition: str | None) -> int:
    if disposition == "CONTINUE":
        return 0
    if disposition == "COORDINATE_CONVERGENCE":
        return 1
    return 2


def failure(code: str, predicate: str, repair: str, next_attempt: str, **evidence) -> dict:
    return {"disposition": FAIL_CLOSED, "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": RETRY_ENTRYPOINT,
            "owning_existing_goal": OWNING_GOAL, "next_attempt": next_attempt,
            "evidence": evidence}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def registry_rows(root: Path) -> dict:
    registry = _read_json(root / REGISTRY_PATH) or {}
    return {str(r.get("task_id")): r for r in registry.get("tasks") or []
            if isinstance(r, dict) and r.get("task_id")}


def shard_files(root: Path) -> dict:
    directory = root / RECORDS_PATH
    if not directory.is_dir():
        return {}
    return {p.stem: p.read_bytes() for p in sorted(directory.glob("*.json"))}


def changed_task_ids(base: Path, head: Path) -> list[str]:
    changed = set()
    base_rows, head_rows = registry_rows(base), registry_rows(head)
    for tid, row in head_rows.items():
        if base_rows.get(tid) != row:
            changed.add(tid)
    base_shards, head_shards = shard_files(base), shard_files(head)
    for stem, raw in head_shards.items():
        if base_shards.get(stem) == raw:
            continue
        try:
            shard = json.loads(raw)
        except ValueError:
            changed.add(stem)  # the evaluator refuses it; that is the finding
            continue
        # Auxiliary session notes beside the shards carry no task identity.
        if isinstance(shard, dict) and ("task_id" in shard or "checkout_state" in shard
                                        or shard.get("schema") == "stegverse.canonical-task-record/v1"):
            changed.add(stem)
    return sorted(changed)


def load_evaluator(head: Path):
    path = head / "scripts" / "evaluate_task_registry_collision_checkin.py"
    spec = importlib.util.spec_from_file_location("_collision_checkin_for_ci", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def evaluate(module, root: Path, task_id: str) -> dict:
    """Run the evaluator's own main() for one task against one tree."""
    module.REGISTRY = root / REGISTRY_PATH
    module.RECORDS = root / RECORDS_PATH
    module.GLOBAL_INVARIANTS = root / INVARIANTS_PATH
    generation = (_read_json(root / REGISTRY_PATH) or {}).get("generation")
    request = {"task_id": task_id, "caller_surface": CALLER_SURFACE,
               "observed_registry_generation": generation}
    out, saved = io.StringIO(), sys.stdin
    sys.stdin = io.StringIO(json.dumps(request))
    try:
        with contextlib.redirect_stdout(out):
            module.main()
    except SystemExit as exc:
        return {"disposition": "EVALUATOR_REFUSED", "detail": str(exc.code)}
    except Exception as exc:  # an error is never a pass
        return {"disposition": "EVALUATOR_REFUSED", "detail": f"{type(exc).__name__}: {exc}"}
    finally:
        sys.stdin = saved
    return json.loads(out.getvalue())


def judge(task_id: str, head: dict, base: dict | None, strict: bool) -> dict:
    head_disp = head.get("disposition")
    row = {"task_id": task_id, "head_disposition": head_disp,
           "base_disposition": base.get("disposition") if base else None}
    if head_disp == "EVALUATOR_REFUSED":
        return {**row, **failure(
            "REGISTRY_COLLISION_CHECKIN_REFUSED",
            f"the collision check-in evaluates {task_id} at head",
            "repair the task row or shard so the existing evaluator accepts it",
            "after the head evaluates", detail=head.get("detail"))}
    if head_disp == "CONTINUE":
        return {**row, "disposition": ALLOW, "reason": "CONTINUE"}
    if head_disp in TERMINAL:
        return {**row, "disposition": ALLOW, "reason": "TERMINAL_AT_HEAD"}
    head_ids = {c.get("task_id") for c in head.get("collision_candidates") or []}
    head_hard = set(head.get("hard_collision_task_ids") or [])
    new_ids = new_hard = []
    if base and not strict and base.get("disposition") != "EVALUATOR_REFUSED":
        new_ids = sorted(head_ids - {c.get("task_id") for c in base.get("collision_candidates") or []})
        new_hard = sorted(head_hard - set(base.get("hard_collision_task_ids") or []))
        if severity(head_disp) <= severity(base.get("disposition")) and not new_ids and not new_hard:
            return {**row, "disposition": ALLOW, "reason": "PRE_EXISTING_AT_BASE",
                    "collision_candidate_ids": sorted(head_ids)}
    code = "REGISTRY_COLLISION_CHECKIN_STOP_COLLISION" if head_disp == "STOP_COLLISION" \
        else "REGISTRY_COLLISION_CHECKIN_NOT_CONTINUE"
    return {**row, **failure(
        code,
        f"check-in for {task_id} at head is CONTINUE, terminal, or no stronger than at base",
        f"coordinate {task_id} with {sorted(head_hard or head_ids) or 'its owner'} "
        f"({head.get('session_action')}) or narrow its targets before merge",
        "after the head disposition is CONTINUE or no stronger than the base",
        new_collision_candidate_ids=new_ids, new_hard_collision_task_ids=new_hard,
        hard_collision_task_ids=sorted(head_hard), collision_candidate_ids=sorted(head_ids),
        session_action=head.get("session_action"),
        substrate_review_error=head.get("substrate_review_error"))}


def check(base: Path, head: Path, strict: bool = False) -> dict:
    tasks = changed_task_ids(base, head)
    if not tasks:
        return {"disposition": ALLOW, "applicability": "NOT_APPLICABLE",
                "reason": "PR changes no canonical task row or shard", "results": []}
    module = load_evaluator(head)
    base_ids = set(registry_rows(base))
    with tempfile.TemporaryDirectory() as scratch:
        saved = os.environ.get("STEGVERSE_TASK_REGISTRY_EVENT_LEDGER")
        os.environ["STEGVERSE_TASK_REGISTRY_EVENT_LEDGER"] = str(Path(scratch) / "absent.jsonl")
        try:
            results = []
            for tid in tasks:
                head_result = evaluate(module, head, tid)
                base_result = evaluate(module, base, tid) if tid in base_ids else None
                results.append(judge(tid, head_result, base_result, strict))
        finally:
            if saved is None:
                os.environ.pop("STEGVERSE_TASK_REGISTRY_EVENT_LEDGER", None)
            else:
                os.environ["STEGVERSE_TASK_REGISTRY_EVENT_LEDGER"] = saved
    failed = [r for r in results if r["disposition"] == FAIL_CLOSED]
    return {"disposition": FAIL_CLOSED if failed else ALLOW, "strict": strict,
            "changed_task_ids": tasks, "results": results}


def summary_markdown(result: dict) -> str:
    lines = [f"### {GATE}: {result['disposition']}", ""]
    rows = result.get("results") or []
    if rows:
        lines += ["| task | base | head | outcome |", "|---|---|---|---|"]
        lines += [f"| {r['task_id']} | {r.get('base_disposition')} | {r.get('head_disposition')} | "
                  f"{r.get('reason') or r.get('failure_code')} |" for r in rows]
    elif result["disposition"] == FAIL_CLOSED:
        lines += ["| field | value |", "|---|---|"]
        lines += [f"| {k} | {str(result[k]).replace('|', '/')} |" for k in SIX_FIELDS]
    else:
        lines.append(result.get("reason", ""))
    for r in rows:
        if r["disposition"] == FAIL_CLOSED:
            lines += ["", f"#### {r['task_id']}", "", "| field | value |", "|---|---|"]
            lines += [f"| {k} | {str(r[k]).replace('|', '/')} |" for k in SIX_FIELDS]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--base-root", required=True, type=Path)
    parser.add_argument("--head-root", required=True, type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = check(args.base_root.resolve(), args.head_root.resolve(), args.strict)
    except Exception as exc:  # an error is never a pass
        result = failure("REGISTRY_COLLISION_CHECKIN_INTERNAL_ERROR",
                         "the collision check-in gate evaluates without an unexpected error",
                         "fix the gate or its inputs; an error is never a pass",
                         "after the error is fixed, re-run the check",
                         detail=f"{type(exc).__name__}: {exc}")
    print(json.dumps(result, indent=2, sort_keys=True))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(summary_markdown(result))
    return 0 if result["disposition"] == ALLOW else 1


if __name__ == "__main__":
    raise SystemExit(main())
