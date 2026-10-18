#!/usr/bin/env python3
"""Registry admission transition: evaluate one admission-request manifest.

REGISTRY_ADMISSION_TRANSITION_ABSENT (StegVerse-org/.github#164). Admission of
a canonical task row is a manifest-bound state transition. A request
(schema ``stegverse.registry-admission-request/v1``, see
``schemas/registry-admission-request.schema.json``) names the task row, its
shard path, the proposed generation and the live generation it was prepared
against. This evaluator decides ALLOW, DENY or FAIL_CLOSED:

* the row is a ``stegverse.canonical-task-record/v1`` whose ``task_id`` equals
  the request's, and its shard is ``data/canonical-task-records/<task_id>.json``;
* ``task_id`` is absent from the live registry (uniqueness) and the shard path
  is unused;
* ``proposed_generation`` equals the live main generation + 1, the predicate the
  Labs#3220 fence (``scripts/check_registry_generation_fence.py``) enforces on the
  admitting registry PR, decided here with the same codes;
* every ``targets.paths`` entry resolves on the main of a ``targets.repositories``
  entry. For a NEW row this is enforcing. Existing rows are only reported, by
  ``scripts/report_registry_target_paths.py`` (separate, read-only).

Every non-ALLOW carries the six fields. The result is the transition's
decision record, digest-bound (``decision_sha256``) and shaped for the
organization ledger transition (``organization-ledger-transition.yml``). This
script is read-only: it writes no registry, shard or ledger, and the admitting
registry PR and the ledger append stay separate, owner-path transitions. Stdlib
only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
REQUEST_SCHEMA = "stegverse.registry-admission-request/v1"
DECISION_SCHEMA = "stegverse.registry-admission-decision/v1"
RECORD_SCHEMA = "stegverse.canonical-task-record/v1"
SHARD_DIR = "data/canonical-task-records"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
COORDINATION_REF = "StegVerse-org/.github#164"
RETRY_ENTRYPOINT = "python scripts/evaluate_registry_admission_request.py --request <path>"
NOT_TIP_PLUS_ONE = "REGISTRY_GENERATION_NOT_TIP_PLUS_ONE"  # same code as the #3220 fence
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
_TASK_ID = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,127}$")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

# (repository, path) -> True (resolves), False (absent on main), None (not observable)
PathResolver = Callable[[str, str], "bool | None"]


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


class Refusal(Exception):
    def __init__(self, disposition: str, code: str, predicate: str, repair: str, next_attempt: str, **detail: Any):
        super().__init__(code)
        self.record = {"disposition": disposition, "failure_code": code, "failed_predicate": predicate,
                       "required_evidence_or_repair": repair, "retry_entrypoint": RETRY_ENTRYPOINT,
                       "owning_existing_goal": OWNING_GOAL, "next_attempt": next_attempt, **detail}


def _deny(code, predicate, repair, **detail):
    return Refusal("DENY", code, predicate, repair, "commit a corrected successor admission request", **detail)


def _fail(code, predicate, repair, **detail):
    return Refusal("FAIL_CLOSED", code, predicate, repair, "re-evaluate once the predicate is observable", **detail)


def _validate_request(request: Any) -> dict:
    if not isinstance(request, Mapping):
        raise _fail("ADMISSION_REQUEST_UNREADABLE", "ADMISSION_REQUEST_IS_A_JSON_OBJECT", "an admission request JSON object")
    if request.get("schema") != REQUEST_SCHEMA:
        raise _fail("ADMISSION_REQUEST_SCHEMA_INVALID", "REQUEST_SCHEMA_IS_REGISTRY_ADMISSION_REQUEST_V1", f"schema {REQUEST_SCHEMA}")
    for key in ("request_id", "task_id", "shard_path", "owning_existing_goal"):
        if not isinstance(request.get(key), str) or not request[key]:
            raise _fail("ADMISSION_REQUEST_FIELD_MISSING", f"REQUEST_{key.upper()}_PRESENT", f"a non-empty {key}")
    for key in ("proposed_generation", "observed_live_generation"):
        value = request.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise _fail("ADMISSION_REQUEST_FIELD_MISSING", f"REQUEST_{key.upper()}_IS_NON_NEGATIVE_INTEGER", f"a non-negative integer {key}")
    if not isinstance(request.get("task_row"), Mapping):
        raise _fail("ADMISSION_REQUEST_FIELD_MISSING", "REQUEST_TASK_ROW_IS_OBJECT", "the exact canonical task row as an object")
    return dict(request)


def _live_generation(registry: Any) -> tuple[int, set[str]]:
    generation = registry.get("generation") if isinstance(registry, Mapping) else None
    tasks = registry.get("tasks") if isinstance(registry, Mapping) else None
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0 or not isinstance(tasks, list):
        raise _fail("REGISTRY_GENERATION_UNREADABLE", "LIVE_REGISTRY_HAS_GENERATION_AND_TASKS",
                    "a readable data/canonical-task-registry.json at live main")
    return generation, {t.get("task_id") for t in tasks if isinstance(t, Mapping)}


def evaluate(request: Any, registry: Any, existing_shards: set[str], resolve: PathResolver) -> dict:
    """Decide one admission request against the live registry. Pure apart from ``resolve``."""
    try:
        req = _validate_request(request)
        live, task_ids = _live_generation(registry)
        row, task_id = req["task_row"], req["task_id"]
        if row.get("schema") != RECORD_SCHEMA:
            raise _deny("TASK_ROW_SCHEMA_INVALID", "TASK_ROW_IS_CANONICAL_TASK_RECORD_V1", f"a task row with schema {RECORD_SCHEMA}")
        if not _TASK_ID.match(task_id) or row.get("task_id") != task_id:
            raise _deny("TASK_ROW_ID_MISMATCH", "TASK_ROW_TASK_ID_EQUALS_REQUEST_TASK_ID", "a task row whose task_id equals the request's", row_task_id=row.get("task_id"))
        expected_shard = f"{SHARD_DIR}/{task_id}.json"
        if req["shard_path"] != expected_shard:
            raise _deny("SHARD_PATH_INVALID", "SHARD_PATH_IS_CANONICAL_TASK_RECORD_PATH", f"shard_path {expected_shard}", observed=req["shard_path"])
        if task_id in task_ids:
            raise _deny("TASK_ID_NOT_UNIQUE", "TASK_ID_ABSENT_FROM_LIVE_REGISTRY", "a task_id not already in the live registry", task_id=task_id)
        if expected_shard in existing_shards:
            raise _deny("SHARD_ALREADY_EXISTS", "SHARD_PATH_UNUSED_ON_LIVE_MAIN", "a shard path not already present on live main", shard_path=expected_shard)
        if req["proposed_generation"] != live + 1:
            raise _deny(NOT_TIP_PLUS_ONE, "PROPOSED_GENERATION_EQUALS_LIVE_MAIN_PLUS_ONE",
                        f"proposed_generation {live + 1} (live main is {live})",
                        live_generation=live, proposed_generation=req["proposed_generation"],
                        observed_live_generation=req["observed_live_generation"])
        targets = row.get("targets") if isinstance(row.get("targets"), Mapping) else {}
        paths = targets.get("paths") or []
        repos = targets.get("repositories") or []
        resolution = []
        if paths:
            if not isinstance(paths, list) or not all(isinstance(p, str) and p for p in paths):
                raise _deny("TARGET_PATHS_INVALID", "TARGET_PATHS_ARE_NON_EMPTY_STRINGS", "targets.paths as a list of non-empty strings")
            if not isinstance(repos, list) or not repos or not all(isinstance(r, str) and _REPO.match(r) for r in repos):
                raise _deny("TARGET_REPOSITORIES_INVALID", "TARGET_PATHS_HAVE_A_TARGET_REPOSITORY", "targets.repositories naming owner/repo for the paths")
            for path in paths:
                observed = [resolve(repo, path) for repo in repos]
                resolution.append({"path": path, "resolved": any(o is True for o in observed)})
                if not any(o is True for o in observed):
                    if any(o is None for o in observed):
                        raise _fail("TARGET_PATHS_NOT_OBSERVABLE", "TARGET_PATH_RESOLUTION_OBSERVED",
                                    "a readable main of each targets.repositories entry", path=path, repositories=repos)
                    raise _deny("TARGET_PATHS_UNRESOLVED", "EVERY_TARGET_PATH_RESOLVES_ON_TARGET_MAIN",
                                "targets.paths that exist on the main of a targets.repositories entry", path=path, repositories=repos)
        decision = {"disposition": "ALLOW", "live_generation": live, "proposed_generation": req["proposed_generation"],
                    "target_paths": resolution}
    except Refusal as refusal:
        decision = refusal.record
    body = {
        "schema": DECISION_SCHEMA,
        "request_id": request.get("request_id") if isinstance(request, Mapping) else None,
        "task_id": request.get("task_id") if isinstance(request, Mapping) else None,
        "request_sha256": canonical_sha256(request) if isinstance(request, Mapping) else None,
        **decision,
        "registry_written": False,
        "ledger_appended": False,
        "ledger_transition_entrypoint": ".github/workflows/organization-ledger-transition.yml",
        "coordination_ref": COORDINATION_REF,
        "authority_effect": "NONE_ADMISSION_DECISION_ONLY",
    }
    body["decision_sha256"] = canonical_sha256(body)
    return body


def git_resolver(roots: Mapping[str, Path]) -> PathResolver:
    """Resolve against local checkouts of each target repository's main."""
    def resolve(repo: str, path: str):
        root = roots.get(repo)
        if root is None:
            return None
        done = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"HEAD:{path}"], capture_output=True)
        return done.returncode == 0
    return resolve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--request", required=True)
    parser.add_argument("--registry", default=str(ROOT / "data" / "canonical-task-registry.json"))
    parser.add_argument("--repo-root", action="append", default=[], help="OWNER/REPO=PATH of a checkout of that repository's main")
    args = parser.parse_args(argv)
    roots = {}
    for spec in args.repo_root:
        repo, _, path = spec.partition("=")
        roots[repo] = Path(path)
    try:
        request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        request = {"_unreadable": str(exc)}
    try:
        registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        registry = None
    shards = {p.relative_to(ROOT).as_posix() for p in (ROOT / SHARD_DIR).glob("*.json")}
    decision = evaluate(request, registry, shards, git_resolver(roots))
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if decision["disposition"] == "ALLOW" else 1


if __name__ == "__main__":
    sys.exit(main())
