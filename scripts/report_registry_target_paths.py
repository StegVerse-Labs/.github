#!/usr/bin/env python3
"""Report-only check: every registry row's targets.paths must resolve (Q-J4 feedback).

Strictly read-only. It reads data/canonical-task-registry.json and the shards
under data/canonical-task-records/, and resolves each targets.paths entry
against the default branch of every repository in targets.repositories using
an anonymous, blob-less, depth-1 git fetch (no credential). It never edits the
registry, a shard or a row, and it never appends to the ledger.

Report mode (the default) always exits 0 and prints the report, so the drift
is visible without gating anything. A row whose paths do not all resolve gets a
six-field FAIL_CLOSED record in the report. --enforce exits 1 on any
non-RESOLVED row; CI does not use it until Q-J4 is answered.
Stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
SHARDS = ROOT / "data" / "canonical-task-records"
SCHEMA = "stegverse.registry-target-paths-report/v1"
OWNING_EXISTING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
QUESTION_REF = "Q-J4 (JOINT DISCOVERY QUEUE, StegVerse-org/.github#164)"
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

# resolve(repository) -> (default_head_sha | None, set_of_paths | None, error | None)
Resolver = Callable[[str], tuple]


def _sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _rows(registry: dict, shards: Iterable[tuple[str, dict]]) -> list[tuple[str, dict]]:
    found: dict[str, tuple[str, dict]] = {}
    for row in registry.get("tasks") or []:
        if isinstance(row, dict) and isinstance(row.get("targets"), dict) and row["targets"].get("paths"):
            found[f"registry:{row.get('task_id')}"] = ("data/canonical-task-registry.json", row)
    for name, row in shards:
        if isinstance(row, dict) and isinstance(row.get("targets"), dict) and row["targets"].get("paths"):
            found[f"shard:{name}"] = (f"data/canonical-task-records/{name}", row)
    return [found[k] for k in sorted(found)]


def git_resolver(workdir: Path) -> Resolver:
    cache: dict[str, tuple] = {}
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "/bin/false",
           "HOME": str(workdir), "GIT_CONFIG_NOSYSTEM": "1"}

    def run(args: list[str], cwd: Path) -> str:
        done = subprocess.run(["git", *args], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=120, check=False)
        if done.returncode != 0:
            raise RuntimeError((done.stderr or done.stdout).strip()[:200])
        return done.stdout

    def resolve(repository: str) -> tuple:
        if repository in cache:
            return cache[repository]
        target = workdir / repository.replace("/", "__")
        try:
            target.mkdir(parents=True, exist_ok=False)
            run(["init", "--quiet"], target)
            run(["fetch", "--quiet", "--depth=1", "--filter=blob:none", f"https://github.com/{repository}.git", "HEAD"], target)
            head = run(["rev-parse", "FETCH_HEAD"], target).strip()
            paths = set(run(["ls-tree", "-r", "--name-only", "FETCH_HEAD"], target).splitlines())
            cache[repository] = (head, paths, None)
        except Exception as exc:  # private, missing, or network failure: not observable anonymously
            cache[repository] = (None, None, f"{type(exc).__name__}: {exc}")
        return cache[repository]

    return resolve


def evaluate_row(source: str, row: dict, resolve: Resolver) -> dict[str, Any]:
    targets = row["targets"]
    task_id = row.get("task_id")
    paths = targets.get("paths")
    repos = targets.get("repositories")
    base = {"task_id": task_id, "source": source, "paths": paths, "repositories": repos}
    if not isinstance(paths, list) or not all(isinstance(p, str) and p and not p.startswith("/") and ".." not in p.split("/") for p in paths):
        return {**base, "state": "TARGET_PATHS_INVALID", **_six("TARGET_PATHS_INVALID", "TARGETS_PATHS_ARE_RELATIVE_REPOSITORY_PATHS", task_id)}
    if not isinstance(repos, list) or not repos or not all(isinstance(r, str) and _REPO.match(r) for r in repos):
        return {**base, "state": "TARGET_REPOSITORIES_INVALID", **_six("TARGET_REPOSITORIES_INVALID", "TARGETS_REPOSITORIES_ARE_OWNER_SLASH_REPO", task_id)}
    observed, unresolved, unobservable = {}, [], []
    for repository in repos:
        head, tree, error = resolve(repository)
        observed[repository] = {"default_head_sha": head, "error": error}
        if tree is None:
            unobservable.append(repository)
    if len(unobservable) == len(repos):
        return {**base, "observed": observed, "state": "TARGET_PATHS_NOT_OBSERVABLE",
                **_six("TARGET_PATHS_NOT_OBSERVABLE", "TARGET_REPOSITORY_DEFAULT_BRANCH_IS_ANONYMOUSLY_READABLE", task_id)}
    trees = [resolve(r)[1] for r in repos if resolve(r)[1] is not None]
    for path in paths:
        if not any(path in tree for tree in trees):
            unresolved.append(path)
    if unresolved:
        return {**base, "observed": observed, "unresolved_paths": unresolved, "state": "TARGET_PATHS_UNRESOLVED",
                **_six("TARGET_PATHS_UNRESOLVED", "EVERY_TARGETS_PATH_EXISTS_ON_A_TARGET_REPOSITORY_DEFAULT_BRANCH", task_id, unresolved)}
    return {**base, "observed": observed, "state": "RESOLVED", "disposition": "ALLOW"}


def _six(code: str, predicate: str, task_id: Any, unresolved: list | None = None) -> dict[str, Any]:
    return {
        "disposition": "FAIL_CLOSED",
        "failure_code": code,
        "failed_predicate": predicate,
        "required_evidence_or_repair": (f"answer {QUESTION_REF}: either the target files are created at the declared paths or the row's "
                                        f"targets.paths are corrected through the registry admission transition (no edit by this report)"
                                        + (f"; unresolved: {unresolved}" if unresolved else "")),
        "retry_entrypoint": "python scripts/report_registry_target_paths.py",
        "owning_existing_goal": f"{task_id} (registry coordination: {OWNING_EXISTING_GOAL})",
        "next_attempt": "rerun after the Q-J4 answer lands on the target repository default branch or in an admitted registry generation",
    }


def build_report(registry: dict, shards: Iterable[tuple[str, dict]], resolve: Resolver) -> dict[str, Any]:
    shards = list(shards)
    rows = [evaluate_row(src, row, resolve) for src, row in _rows(registry, shards)]
    by_shard = {row.get("task_id"): row["targets"].get("paths") for _, row in shards
                if isinstance(row, dict) and isinstance(row.get("targets"), dict)}
    drift = [{"task_id": row.get("task_id"), "registry_paths": row["targets"].get("paths"), "shard_paths": by_shard[row.get("task_id")]}
             for row in registry.get("tasks") or []
             if isinstance(row, dict) and isinstance(row.get("targets"), dict) and row.get("task_id") in by_shard
             and row["targets"].get("paths") != by_shard[row.get("task_id")]]
    report = {
        "schema": SCHEMA,
        "mode": "REPORT_ONLY",
        "registry_generation": registry.get("generation"),
        "rows_with_target_paths": len(rows),
        "resolved": sum(1 for r in rows if r["state"] == "RESOLVED"),
        "rows": rows,
        "registry_shard_target_paths_drift": drift,
        "registry_written": False,
        "shard_written": False,
        "ledger_appended": False,
        "credential_used": False,
    }
    report["report_sha256"] = _sha256(report)
    return report


def load_shards(directory: Path) -> list[tuple[str, dict]]:
    out = []
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else []:
        try:
            out.append((path.name, json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, ValueError):
            continue
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--shards", type=Path, default=SHARDS)
    parser.add_argument("--enforce", action="store_true", help="exit 1 on any non-RESOLVED row (not used in CI until Q-J4 is answered)")
    args = parser.parse_args(argv)
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="target-paths-") as work:
        report = build_report(registry, load_shards(args.shards), git_resolver(Path(work)))
    print(json.dumps(report, indent=2, sort_keys=True))
    for row in report["rows"]:
        if row["state"] != "RESOLVED":
            print(f"::warning::REPORT_ONLY {row['failure_code']} {row['task_id']} {row.get('unresolved_paths', '')}", file=sys.stderr)
    return 1 if args.enforce and report["resolved"] != report["rows_with_target_paths"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
