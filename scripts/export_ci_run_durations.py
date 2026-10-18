#!/usr/bin/env python3
"""Convert saved GitHub Actions workflow-run records into a CI run-duration export.

Input: one or more JSON files holding the response of
``GET /repos/{owner}/{repo}/actions/runs`` (an object with ``workflow_runs``, or a list
of such objects as written by ``gh api --paginate --slurp``). The caller saves the
records; this script reads files only and never calls an API, so measured E comes from
the ecosystem's own run records instead of a lane's report.

Output: ``stegverse.ci-run-duration-export.v1`` (the input of
``compute_ecosystem_offload_ratio.py --ci-runs``), keeping only completed runs on the
named head branches, optionally for one UTC date. ``completed_at`` is the run record's
``updated_at``, the time GitHub last changed the completed run. Runs are de-duplicated by
repo and run id and sorted, so the output is deterministic.

A missing or malformed input is FAIL_CLOSED with the standard six fields.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

EXPORT_SCHEMA = "stegverse.ci-run-duration-export.v1"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
RETRY_ENTRYPOINT = ("python scripts/export_ci_run_durations.py --runs <actions-runs.json> ... --branch <head_branch> "
                    "[--date YYYY-MM-DD] --source <text>")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Refused(Exception):
    def __init__(self, code: str, predicate: str, repair: str, **evidence: Any) -> None:
        super().__init__(code)
        self.result = {"schema": EXPORT_SCHEMA, "disposition": "FAIL_CLOSED", "failure_code": code,
                       "failed_predicate": predicate, "required_evidence_or_repair": repair,
                       "retry_entrypoint": RETRY_ENTRYPOINT, "owning_existing_goal": OWNING_GOAL,
                       "next_attempt": "after the named input is supplied or corrected", "evidence": evidence}


def _pages(document: Any, name: str) -> list[dict[str, Any]]:
    pages = document if isinstance(document, list) else [document]
    runs: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, dict) or not isinstance(page.get("workflow_runs"), list):
            raise Refused("INPUT_SCHEMA", f"{name} is an Actions runs response with a workflow_runs list",
                          "save the response of GET /repos/{owner}/{repo}/actions/runs", input=name)
        runs.extend(page["workflow_runs"])
    return runs


def convert(documents: dict[str, Any], branches: set[str], day: str | None, source: str) -> dict[str, Any]:
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for name, document in documents.items():
        for index, run in enumerate(_pages(document, name)):
            repo = (run.get("repository") or {}).get("full_name") if isinstance(run, dict) else None
            if not (isinstance(run, dict) and isinstance(repo, str) and isinstance(run.get("id"), int)
                    and isinstance(run.get("head_branch"), str) and isinstance(run.get("path"), str)
                    and isinstance(run.get("run_started_at"), str) and isinstance(run.get("status"), str)):
                raise Refused("INPUT_VALUE_INVALID",
                              f"{name} run {index} carries repository.full_name, id, head_branch, path, status and "
                              "run_started_at", "save the unmodified API response", input=name, index=index)
            if run["head_branch"] not in branches or run["status"] != "completed":
                continue
            if day is not None and not run["run_started_at"].startswith(day):
                continue
            seen[(repo, str(run["id"]))] = {
                "repo": repo, "run_id": run["id"], "workflow": run["path"].rsplit("/", 1)[-1],
                "head_branch": run["head_branch"], "head_sha": run.get("head_sha"),
                "run_started_at": run["run_started_at"], "completed_at": run.get("updated_at"),
                "conclusion": run.get("conclusion"),
            }
    runs = sorted(seen.values(), key=lambda r: (r["repo"], r["run_started_at"], r["run_id"]))
    return {"schema": EXPORT_SCHEMA, "source": source, "runs": runs}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=Path, action="append", default=[])
    parser.add_argument("--branch", action="append", default=[])
    parser.add_argument("--date")
    parser.add_argument("--source")
    args = parser.parse_args(argv)
    try:
        for flag, value in (("--runs", args.runs), ("--branch", args.branch), ("--source", args.source)):
            if not value:
                raise Refused("INPUT_NOT_SUPPLIED", f"{flag} is supplied", f"supply {flag}", input=flag)
        if args.date is not None and not DATE.match(args.date):
            raise Refused("INPUT_VALUE_INVALID", "--date is YYYY-MM-DD", "pass a UTC date", input="--date")
        try:
            documents = {str(path): json.loads(path.read_text(encoding="utf-8")) for path in args.runs}
        except (OSError, ValueError) as exc:
            raise Refused("INPUT_UNREADABLE", "every --runs file is readable JSON", "supply readable files",
                          detail=f"{type(exc).__name__}: {exc}") from None
        result = convert(documents, set(args.branch), args.date, args.source)
    except Refused as refusal:
        print(json.dumps(refusal.result, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
