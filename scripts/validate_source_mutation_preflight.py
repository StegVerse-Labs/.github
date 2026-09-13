#!/usr/bin/env python3
"""Fail closed when StegVerse source mutation precedes canonical-policy reconciliation.

The existing session/build preflight constrains interpretation only when it is actually
invoked. This validator closes the repository-side bypass: a PR that mutates protected
repository state must carry a preflight receipt committed *before* the first protected
mutation. The receipt is bound to the PR base commit, canonical Goal Task, resolved
policy sources, and explicit mutation scope.

This validator grants no runtime, execution, transition, credential, custody, or
publication authority. It is merge-time completeness enforcement only.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_REGISTRY = ROOT / "control" / "canonical-policy-context-registry.json"
TASK_SHARDS = ROOT / "data" / "canonical-task-records"
TASK_REGISTRY = ROOT / "data" / "canonical-task-registry.json"
RECEIPT_PREFIX = "receipts/preflight/"
EXPECTED_SCHEMA = "stegverse.session-build-preflight-receipt/v1"
PASS_STATES = {
    "PASS_FUNCTIONAL_MUTATION_ADMISSIBLE",
    "PASS_NONFUNCTIONAL_RECONCILIATION_ADMISSIBLE",
}


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def merge_base(base_ref: str) -> str:
    candidates = [base_ref]
    if not base_ref.startswith("origin/"):
        candidates.insert(0, f"origin/{base_ref}")
    for candidate in candidates:
        try:
            return git("merge-base", candidate, "HEAD")
        except RuntimeError:
            continue
    raise RuntimeError(f"unable to resolve merge base for {base_ref}")


def changed_paths(base_sha: str) -> list[str]:
    raw = git("diff", "--name-only", f"{base_sha}...HEAD")
    return [line.strip() for line in raw.splitlines() if line.strip()]


def first_change_commit(base_sha: str, path: str) -> str | None:
    raw = git("log", "--reverse", "--format=%H", f"{base_sha}..HEAD", "--", path)
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    return lines[0] if lines else None


def is_ancestor(older: str, newer: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer], cwd=ROOT, check=False
    )
    return proc.returncode == 0


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def task_record(task_id: str) -> dict[str, Any] | None:
    shard = TASK_SHARDS / f"{task_id}.json"
    if shard.is_file():
        record = load_json(shard)
        if record.get("task_id") == task_id:
            return record
    if TASK_REGISTRY.is_file():
        registry = load_json(TASK_REGISTRY)
        for row in registry.get("tasks", []):
            if isinstance(row, dict) and row.get("task_id") == task_id:
                return row
    return None


def required_policy_refs(record: dict[str, Any]) -> set[str]:
    required: set[str] = set()
    if not POLICY_REGISTRY.is_file():
        raise ValueError("canonical policy context registry missing")
    registry = load_json(POLICY_REGISTRY)
    for row in registry.get("required_global_sources", []):
        if isinstance(row, dict) and row.get("required", True) and row.get("ref"):
            required.add(str(row["ref"]))
    for ref in record.get("canonical_policy_refs", []):
        if isinstance(ref, str) and ref.strip():
            required.add(ref.strip())
    return required


def path_authorized(path: str, scope: list[str]) -> bool:
    for item in scope:
        if not isinstance(item, str) or not item:
            continue
        if item.endswith("/") and path.startswith(item):
            return True
        if path == item:
            return True
    return False


def validate_receipt(
    receipt_path: str,
    *,
    base_sha: str,
    protected_paths: list[str],
) -> list[str]:
    findings: list[str] = []
    path = ROOT / receipt_path
    try:
        receipt = load_json(path)
    except Exception as exc:
        return [f"{receipt_path}: invalid receipt: {exc}"]

    if receipt.get("schema") != EXPECTED_SCHEMA:
        findings.append(f"{receipt_path}: schema must be {EXPECTED_SCHEMA}")
    if receipt.get("state") not in PASS_STATES:
        findings.append(f"{receipt_path}: state is not mutation-admissible")
    if receipt.get("preflight_completed_before_source_mutation") is not True:
        findings.append(f"{receipt_path}: preflight-before-mutation assertion missing")
    if receipt.get("base_commit") != base_sha:
        findings.append(
            f"{receipt_path}: base_commit {receipt.get('base_commit')} != PR merge-base {base_sha}"
        )

    task_id = str(receipt.get("goal_task_id") or "").strip()
    record = task_record(task_id) if task_id else None
    if record is None:
        findings.append(f"{receipt_path}: canonical Goal Task not found: {task_id or '<missing>'}")
        return findings

    resolved = {
        str(item).strip()
        for item in receipt.get("canonical_sources_resolved", [])
        if isinstance(item, str) and item.strip()
    }
    missing = sorted(required_policy_refs(record) - resolved)
    if missing:
        findings.append(f"{receipt_path}: required canonical policy sources not resolved: {missing}")

    scope = receipt.get("authorized_mutation_scope", [])
    if not isinstance(scope, list) or not scope:
        findings.append(f"{receipt_path}: authorized_mutation_scope missing")
    else:
        uncovered = [p for p in protected_paths if not path_authorized(p, scope)]
        if uncovered:
            findings.append(f"{receipt_path}: protected paths outside preflight scope: {uncovered}")

    receipt_commit = first_change_commit(base_sha, receipt_path)
    if not receipt_commit:
        findings.append(f"{receipt_path}: receipt is not changed in this PR")
        return findings

    for protected in protected_paths:
        mutation_commit = first_change_commit(base_sha, protected)
        if not mutation_commit:
            continue
        if receipt_commit == mutation_commit:
            findings.append(
                f"{receipt_path}: receipt and protected mutation {protected} first appear in the same commit; preflight must precede mutation"
            )
        elif not is_ancestor(receipt_commit, mutation_commit):
            findings.append(
                f"{receipt_path}: receipt commit {receipt_commit} does not precede first mutation of {protected} ({mutation_commit})"
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-ref",
        default=os.environ.get("GITHUB_BASE_REF") or "main",
        help="PR base branch/ref; defaults to GITHUB_BASE_REF or main",
    )
    args = parser.parse_args()

    try:
        base_sha = merge_base(args.base_ref)
        changed = changed_paths(base_sha)
    except Exception as exc:
        print(f"SOURCE_MUTATION_PREFLIGHT_GUARD_ERROR: {exc}", file=sys.stderr)
        return 2

    receipts = [p for p in changed if p.startswith(RECEIPT_PREFIX) and p.endswith(".json")]
    protected = [p for p in changed if not p.startswith(RECEIPT_PREFIX)]

    if not protected:
        print("SOURCE_MUTATION_PREFLIGHT_GUARD_PASS: no protected mutation")
        return 0
    if not receipts:
        print(
            "SOURCE_MUTATION_PREFLIGHT_GUARD_FAIL: protected mutation exists but no changed receipts/preflight/*.json receipt exists",
            file=sys.stderr,
        )
        return 1

    all_findings: list[str] = []
    for receipt in receipts:
        findings = validate_receipt(receipt, base_sha=base_sha, protected_paths=protected)
        if not findings:
            print(
                f"SOURCE_MUTATION_PREFLIGHT_GUARD_PASS: {receipt} precedes and covers {len(protected)} protected path(s)"
            )
            return 0
        all_findings.extend(findings)

    print("SOURCE_MUTATION_PREFLIGHT_GUARD_FAIL", file=sys.stderr)
    for finding in all_findings:
        print(f"- {finding}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
