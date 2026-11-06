#!/usr/bin/env python3
"""Goal scope seal: GOAL_SCOPE_SEALED (registration) and the read-only scope-freeze PR check.

A Goal's scope is the canonical JSON of four fields:

    {"goal", "targets", "expected_evidence_predicates", "finish_point"}

``scope_digest`` is ``"sha256:" + sha256(canonical JSON)`` with sorted keys, no
whitespace and UTF-8 (the same ``canon`` the registration transition uses).
The first three fields must equal the canonical record; ``finish_point`` names a
concrete acceptance test and the predicate it verifies, so "done" is something a
test can decide rather than something a Goal can keep growing toward.

* Registration (scripts/canonical_task_registration_transition.py): a
  NEW_IDENTITY request must carry ``sealed_scope``; the transition checks the
  digest and the record equality and derives ``control/goal-scope-seals/<task_id>.json``.
* Scope freeze (``check`` below, run by the existing read-only registration
  workflow on pull_request): every seal on the head must re-hash to its digest and
  equal its record and Registry row; a seal on the base may change only when the
  head seal names the base digest in ``supersedes_scope_digest`` and a committed
  ``control/goal-scope-supersede-requests/*.json`` request binds base -> head
  digests. A sealed Goal whose record scope changes without that is refused.

Every refusal is six-field FAIL_CLOSED with ``failed_predicate`` GOAL_SCOPE_SEALED.
Lowest supported mode: E0 (ecosystem only, no LLM): stdlib, committed files, no
clock, no network. Authority: NONE_SCOPE_SEAL_ONLY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

SEAL_SCHEMA = "stegverse.goal-scope-seal/v1"
SUPERSEDE_SCHEMA = "stegverse.goal-scope-supersede-request/v1"
PREDICATE = "GOAL_SCOPE_SEALED"
SEALS = "control/goal-scope-seals"
SUPERSEDE_REQUESTS = "control/goal-scope-supersede-requests"
REGISTRY = "data/canonical-task-registry.json"
RECORDS = "data/canonical-task-records"
RECORD_SCOPE_FIELDS = ("goal", "targets", "expected_evidence_predicates")
FINISH_POINT_FIELDS = ("acceptance_test", "predicate", "verifier_entrypoint", "lowest_supported_mode")
AUTHORITY_EFFECT = "NONE_SCOPE_SEAL_ONLY"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
ENTRYPOINT = "scripts/goal_scope_seal.py"
WORKFLOW = ".github/workflows/canonical-task-registration-transition.yml"
NEXT_ATTEMPT = "on the next pull_request event that carries the repair"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(scope: Any) -> str:
    return "sha256:" + hashlib.sha256(canon(scope)).hexdigest()


def scope_of(record: dict[str, Any], finish_point: Any) -> dict[str, Any]:
    scope = {field: record.get(field) for field in RECORD_SCOPE_FIELDS}
    scope["finish_point"] = finish_point
    return scope


def dump(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


class ScopeRefusal(Exception):
    def __init__(self, code: str, detail: str, repair: str):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.repair = code, detail, repair


def _require(ok: bool, code: str, detail: str, repair: str) -> None:
    if not ok:
        raise ScopeRefusal(code, detail, repair)


def validate_sealed_scope(sealed: Any, task_id: str, record: dict[str, Any], *, new_identity: bool) -> dict[str, Any]:
    """Registration-side GOAL_SCOPE_SEALED. Returns the seal file body."""
    fix = (f"carry sealed_scope {{schema {SEAL_SCHEMA}, scope {{goal, targets, expected_evidence_predicates, "
           f"finish_point}}, scope_digest sha256 over canonical scope JSON, supersedes_scope_digest}} ({ENTRYPOINT})")
    _require(isinstance(sealed, dict), "GOAL_SCOPE_NOT_SEALED", "the request carries no sealed_scope", fix)
    _require(sealed.get("schema") == SEAL_SCHEMA, "GOAL_SCOPE_NOT_SEALED", f"sealed_scope.schema {sealed.get('schema')!r}", fix)
    scope = sealed.get("scope")
    _require(isinstance(scope, dict) and set(scope) == set(RECORD_SCOPE_FIELDS) | {"finish_point"},
             "GOAL_SCOPE_NOT_SEALED", "sealed_scope.scope must hold exactly goal, targets, expected_evidence_predicates, finish_point", fix)
    finish = scope["finish_point"]
    _require(isinstance(finish, dict) and all(isinstance(finish.get(k), str) and finish.get(k) for k in FINISH_POINT_FIELDS),
             "GOAL_FINISH_POINT_NOT_TESTABLE", f"finish_point must name non-empty {list(FINISH_POINT_FIELDS)}",
             "name the acceptance test, the predicate it decides, its verifier entrypoint and the lowest supported mode")
    _require(sealed.get("scope_digest") == digest(scope), "GOAL_SCOPE_DIGEST_MISMATCH",
             f"scope_digest {sealed.get('scope_digest')!r} != {digest(scope)}",
             "recompute scope_digest as sha256 over the canonical scope JSON (sorted keys, no whitespace, UTF-8)")
    for field in RECORD_SCOPE_FIELDS:
        _require(scope[field] == record.get(field), "GOAL_SCOPE_DIVERGES_FROM_RECORD",
                 f"sealed scope.{field} differs from the record's {field}", f"seal exactly the record's {field}")
    if new_identity:
        _require(sealed.get("supersedes_scope_digest") is None, "GOAL_SCOPE_SUPERSEDE_ON_NEW_IDENTITY",
                 "a new identity has no prior scope to supersede", "set supersedes_scope_digest null")
    return {
        "schema": SEAL_SCHEMA,
        "task_id": task_id,
        "scope": scope,
        "scope_digest": sealed["scope_digest"],
        "supersedes_scope_digest": sealed.get("supersedes_scope_digest"),
        "authority_effect": AUTHORITY_EFFECT,
    }


# --- scope freeze over predecessor -> successor trees (the PR check)
def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _seals(root: Path) -> dict[str, tuple[str, Any]]:
    out: dict[str, tuple[str, Any]] = {}
    folder = root / SEALS
    if folder.is_dir():
        for path in sorted(folder.glob("*.json")):
            out[path.stem] = (f"{SEALS}/{path.name}", _load(path))
    return out


def _supersede_requests(root: Path) -> list[dict[str, Any]]:
    folder = root / SUPERSEDE_REQUESTS
    if not folder.is_dir():
        return []
    found = []
    for path in sorted(folder.glob("*.json")):
        body = _load(path)
        if isinstance(body, dict) and body.get("schema") == SUPERSEDE_SCHEMA:
            found.append(body)
    return found


def _registry_rows(root: Path) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    path = root / REGISTRY
    if path.is_file():
        for row in _load(path).get("tasks", []):
            if isinstance(row, dict):
                rows.setdefault(row.get("task_id"), []).append(row)
    return rows


def check(base: Path, head: Path) -> dict[str, Any]:
    """Return the scope-freeze receipt for base -> head. Reads files only; writes nothing."""
    base_seals, head_seals = _seals(base), _seals(head)
    supersedes = _supersede_requests(head)
    rows = _registry_rows(head)
    failures: list[dict[str, Any]] = []

    def refuse(task_id: str, code: str, detail: str, repair: str) -> None:
        failures.append({"task_id": task_id, "failure_code": code, "failed_predicate": PREDICATE, "class": "B",
                         "detail": detail, "required_evidence_or_repair": repair,
                         "retry_entrypoint": f"{WORKFLOW} / python {ENTRYPOINT} check --base <base> --head <head>",
                         "owning_existing_goal": OWNING_GOAL, "next_attempt": NEXT_ATTEMPT})

    for task_id, (rel, base_seal) in base_seals.items():
        if task_id not in head_seals:
            refuse(task_id, "GOAL_SCOPE_SEAL_REMOVED", f"{rel} exists on the base and not on the head",
                   "restore the seal; a sealed scope is replaced only by a superseding seal")
    for task_id, (rel, seal) in head_seals.items():
        if not isinstance(seal, dict) or seal.get("schema") != SEAL_SCHEMA or seal.get("task_id") != task_id \
                or not isinstance(seal.get("scope"), dict):
            refuse(task_id, "GOAL_SCOPE_SEAL_SCHEMA_INVALID", f"{rel} is not a {SEAL_SCHEMA} seal for {task_id}",
                   f"derive {rel} through the registration transition")
            continue
        scope = seal["scope"]
        if seal.get("scope_digest") != digest(scope):
            refuse(task_id, "GOAL_SCOPE_DIGEST_MISMATCH", f"{rel} scope re-hashes to {digest(scope)}, seal says {seal.get('scope_digest')}",
                   "a changed scope needs a new scope_digest and a supersede request")
            continue
        base_entry = base_seals.get(task_id)
        if base_entry is not None and base_entry[1].get("scope_digest") != seal["scope_digest"]:
            prior = base_entry[1].get("scope_digest")
            bound = seal.get("supersedes_scope_digest") == prior and any(
                r.get("task_id") == task_id and r.get("prior_scope_digest") == prior
                and r.get("successor_scope_digest") == seal["scope_digest"] for r in supersedes)
            if not bound:
                refuse(task_id, "GOAL_SCOPE_CHANGED_WITHOUT_SUPERSEDE",
                       f"sealed scope {prior} -> {seal['scope_digest']} without supersedes_scope_digest and a "
                       f"{SUPERSEDE_SCHEMA} request under {SUPERSEDE_REQUESTS}/",
                       f"file a {SUPERSEDE_SCHEMA} request binding prior_scope_digest -> successor_scope_digest "
                       "and set the seal's supersedes_scope_digest, or revert the scope change")
                continue
        record_path = head / RECORDS / f"{task_id}.json"
        holders = [(f"{RECORDS}/{task_id}.json", _load(record_path))] if record_path.is_file() else []
        holders += [(f"{REGISTRY}#tasks[{task_id}]", row) for row in rows.get(task_id, [])]
        for where, record in holders:
            drift = [f for f in RECORD_SCOPE_FIELDS if record.get(f) != scope.get(f)]
            if drift:
                refuse(task_id, "GOAL_SCOPE_EXPANDED_WITHOUT_SUPERSEDE",
                       f"{where} {drift} differ from sealed scope {seal['scope_digest']}",
                       "revert the record's scope fields, or seal the new scope (new scope_digest) with a supersede request")
    body: dict[str, Any] = {
        "schema": "stegverse.goal-scope-freeze-receipt/v1",
        "predicate": PREDICATE,
        "disposition": "ALLOW" if not failures else "FAIL_CLOSED",
        "sealed_goals_on_head": sorted(head_seals),
        "authority_effect": AUTHORITY_EFFECT,
        "clock_read": False,
        "lowest_supported_mode": "E0",
    }
    if failures:
        first = failures[0]
        body.update({k: first[k] for k in SIX_FIELDS})
        body["failures"] = failures
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="scope freeze over predecessor -> successor trees")
    c.add_argument("--base", type=Path, required=True)
    c.add_argument("--head", type=Path, required=True)
    c.add_argument("--receipt-out", type=Path)
    d = sub.add_parser("digest", help="print the scope_digest of a sealed_scope.scope JSON file")
    d.add_argument("scope", type=Path)
    args = parser.parse_args(argv)
    if args.cmd == "digest":
        print(digest(_load(args.scope)))
        return 0
    body = check(args.base.resolve(), args.head.resolve())
    text = json.dumps(body, indent=2, sort_keys=True) + "\n"
    if args.receipt_out:
        args.receipt_out.write_text(text, encoding="utf-8")
    (sys.stdout if body["disposition"] == "ALLOW" else sys.stderr).write(text)
    return 0 if body["disposition"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
