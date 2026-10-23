#!/usr/bin/env python3
"""Recompute an adjacency ruling's consumes-pin and owner-routing conditions (E0: stdlib + local git, no clock, no network).

GITHUB-UNIVERSAL-GOVERNANCE-PRODUCT-001 (Goal StegVerse-org/.github#164), Lane C. Interim companion to
scripts/adjacency_ruling.py (Labs#3327, owned by Lane D), which does not yet recompute these two conditions. Coordination
ruled (class D) that a candidate the finish point relies on may stay a consumes-dependency, not a fold, only if:

  (P) consumed-source pin - every file the finish point reads or executes from that candidate is pinned: the ruling's
      consumes_dependencies entry carries pinned_source {repository, commit (40-hex), files {path: sha256}}; each
      sha256 equals the file at that commit and at the finish-point commit; and the finish-point test file itself
      carries the same commit and sha256s (it verifies them before reading or executing the files).
  (R) owner routing - the ruling's protected_paths name each pinned file with its owner (the consumes-dependency's
      task); a change that modifies a protected path fails closed as an owner-owned edit, routed to that owner.
      Recomputed here between the pinned commit and the finish-point commit, and for any change (check-change).

Any candidate with non-empty finish_point_paths must be covered by (P) and (R). Every refusal is a six-field FAIL_CLOSED.

  verify        --ruling R --finish-point-root DIR [--receipt-out F]
  check-change  --ruling R --root DIR --base REV --head REV [--receipt-out F]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA = "stegverse.adjacency-ruling-conditions-verification/v1"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
ENTRYPOINT = "python scripts/adjacency_ruling_conditions.py verify (canonical-task-registration-transition.yml)"
NEXT_ATTEMPT = "on the next registration plan after the ruling, the pin or the finish-point source is repaired"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class Refusal(Exception):
    def __init__(self, code: str, predicate: str, repair: str, detail: Any = None, owner: str = OWNING_GOAL):
        super().__init__(code)
        self.code, self.predicate, self.repair, self.detail, self.owner = code, predicate, repair, detail, owner

    def six(self) -> dict[str, Any]:
        return {"disposition": "FAIL_CLOSED", "failure_code": self.code, "failed_predicate": self.predicate,
                "required_evidence_or_repair": self.repair, "retry_entrypoint": ENTRYPOINT,
                "owning_existing_goal": self.owner, "next_attempt": NEXT_ATTEMPT, "detail": self.detail}


def _require(ok: bool, code: str, predicate: str, repair: str, detail: Any = None, owner: str = OWNING_GOAL) -> None:
    if not ok:
        raise Refusal(code, predicate, repair, detail, owner)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _blob_sha(root: Path, rev: str, rel: str) -> str | None:
    proc = _git(root, "show", f"{rev}:{rel}")
    return _sha(proc.stdout) if proc.returncode == 0 else None


def _pins(ruling: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pins = {}
    for dep in ruling.get("consumes_dependencies") or []:
        if isinstance(dep, dict) and "pinned_source" in dep:
            pins[dep.get("task_id")] = dep["pinned_source"]
    return pins


def _routes(ruling: dict[str, Any]) -> list[dict[str, Any]]:
    routes = ruling.get("protected_paths")
    _require(routes is None or isinstance(routes, list), "ADJACENCY_RULING_PROTECTED_PATHS_MALFORMED",
             "PROTECTED_PATHS_ARE_A_LIST", "protected_paths must be a list of {repository, owner_task_id, paths, on_modification}")
    return routes or []


def structure(ruling: Any) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    _require(isinstance(ruling, dict) and isinstance(ruling.get("subject"), dict), "ADJACENCY_RULING_SCHEMA_INVALID",
             "ADJACENCY_RULING_IS_WELL_FORMED", "a stegverse.adjacency-ruling/v1 object with a subject")
    fp = ruling["subject"].get("finish_point") or {}
    repository = fp.get("repository")
    pins, routes = _pins(ruling), _routes(ruling)
    for task_id, pin in pins.items():
        ok = (isinstance(pin, dict) and pin.get("repository") == repository and HEX40.match(str(pin.get("commit")))
              and isinstance(pin.get("files"), dict) and pin["files"]
              and all(isinstance(k, str) and HEX64.match(str(v)) for k, v in pin["files"].items()))
        _require(bool(ok), "ADJACENCY_RULING_CONSUMED_PIN_MALFORMED", "CONSUMED_PIN_IS_WELL_FORMED",
                 f"consumes_dependencies[{task_id}].pinned_source needs repository {repository}, a 40-hex commit and "
                 "files {path: 64-hex sha256}", pin)
    for route in routes:
        ok = (isinstance(route, dict) and route.get("repository") == repository
              and isinstance(route.get("paths"), list) and route["paths"] and isinstance(route.get("on_modification"), dict)
              and route["on_modification"].get("disposition") == "FAIL_CLOSED"
              and route["on_modification"].get("routed_to") == route.get("owner_task_id"))
        _require(bool(ok), "ADJACENCY_RULING_PROTECTED_PATHS_MALFORMED", "PROTECTED_PATHS_ARE_WELL_FORMED",
                 "each protected_paths entry needs repository, owner_task_id, paths and on_modification "
                 "{disposition FAIL_CLOSED, failure_code, routed_to = owner_task_id}", route)
        pin = pins.get(route["owner_task_id"])
        _require(pin is not None and sorted(route["paths"]) == sorted(pin["files"]),
                 "ADJACENCY_RULING_PROTECTED_PATHS_UNROUTED", "PROTECTED_PATHS_EQUAL_THE_OWNERS_CONSUMED_PIN",
                 f"protected_paths for {route['owner_task_id']} must list exactly the files of its consumes pin", route)
    routed = {r["owner_task_id"]: set(r["paths"]) for r in routes}
    for cand in ruling.get("candidates") or []:
        relied = set(cand.get("finish_point_paths") or []) if isinstance(cand, dict) else set()
        if relied:
            cid = cand.get("task_id")
            _require(cid in pins and relied <= set(pins[cid]["files"]) and relied <= routed.get(cid, set()),
                     "ADJACENCY_RULING_RELIED_PATHS_UNPINNED", "RELIED_ON_CANDIDATE_PATHS_ARE_PINNED_AND_ROUTED",
                     f"{cid}'s finish_point_paths must be covered by its consumes pin and a protected_paths entry",
                     {"candidate": cid, "relied": sorted(relied)})
    return fp, pins, routes


def change_refusal(routes: list[dict[str, Any]], changed: list[str]) -> Refusal | None:
    for route in routes:
        hit = sorted(set(changed) & set(route["paths"]))
        if hit:
            owner = route["owner_task_id"]
            mod = route["on_modification"]
            return Refusal(mod.get("failure_code") or "OWNER_OWNED_EDIT", "PROTECTED_PATHS_UNMODIFIED_BY_SUBJECT",
                           f"{hit} belong to {owner}: route the change to {owner}; after it publishes, move the consumes "
                           "pin (commit and sha256s) in the ruling and in the finish-point test", {"modified": hit}, owner)
    return None


def verify(ruling: Any, finish_point_root: Path) -> dict[str, Any]:
    try:
        fp, pins, routes = structure(ruling)
        head = _git(finish_point_root, "rev-parse", "HEAD").stdout.decode().strip()
        _require(head == fp.get("source_commit"), "ADJACENCY_RULING_FINISH_POINT_SOURCE_UNAVAILABLE",
                 "FINISH_POINT_SOURCE_AT_PINNED_COMMIT", f"--finish-point-root must be checked out at {fp.get('source_commit')}",
                 {"observed_head": head})
        test_rel = str(fp.get("acceptance_test", "")).partition(":")[2].split("::")[0]
        test_text = (finish_point_root / test_rel).read_text(encoding="utf-8") if (finish_point_root / test_rel).is_file() else ""
        rows = []
        for task_id, pin in pins.items():
            commit = pin["commit"]
            _require(_git(finish_point_root, "cat-file", "-e", f"{commit}^{{commit}}").returncode == 0,
                     "ADJACENCY_RULING_CONSUMED_PIN_COMMIT_UNAVAILABLE", "PINNED_COMMIT_PRESENT_IN_FINISH_POINT_SOURCE",
                     f"fetch {commit} into the finish-point checkout (anonymous, public source)", {"commit": commit})
            for rel, digest in sorted(pin["files"].items()):
                at_pin = _blob_sha(finish_point_root, commit, rel)
                _require(at_pin == digest, "ADJACENCY_RULING_CONSUMED_PIN_DIGEST_DIVERGES",
                         "PINNED_SHA256_EQUALS_FILE_AT_PINNED_COMMIT", f"{rel} sha256 at {commit} must be {digest}",
                         {"path": rel, "at_pin": at_pin})
                at_head = _blob_sha(finish_point_root, head, rel)
                if at_head != digest:  # the subject modified a consumed file: an owner-owned edit when routed
                    raise change_refusal(routes, [rel]) or Refusal(
                        "ADJACENCY_RULING_CONSUMED_PIN_DIGEST_DIVERGES", "PINNED_SHA256_EQUALS_FILE_AT_FINISH_POINT",
                        f"{rel} at {head} differs from its pin {digest}", {"path": rel, "at_head": at_head})
                _require(digest in test_text and commit in test_text, "ADJACENCY_RULING_FINISH_TEST_DOES_NOT_ENFORCE_PIN",
                         "FINISH_TEST_VERIFIES_THE_SAME_PIN",
                         f"{test_rel} must carry {commit} and the sha256 of {rel} and verify them before use", {"path": rel})
            rows.append({"task_id": task_id, "commit": commit, "files": pin["files"], "condition_pin": "HELD"})
        return {"schema": SCHEMA, "disposition": "ALLOW", "finish_point_commit": head, "pins": rows,
                "protected_paths": routes, "condition_routing": "HELD", "lowest_supported_mode": "E0",
                "clock_read": False, "network_used": False}
    except Refusal as refusal:
        return {"schema": SCHEMA, **refusal.six(), "lowest_supported_mode": "E0", "clock_read": False, "network_used": False}


def check_change(ruling: Any, root: Path, base: str, head: str) -> dict[str, Any]:
    try:
        _fp, _pins_, routes = structure(ruling)
        diff = _git(root, "diff", "--name-only", base, head)
        _require(diff.returncode == 0, "ADJACENCY_RULING_CHANGE_UNREADABLE", "CHANGE_DIFF_READABLE",
                 f"both {base} and {head} must be present in {root}", diff.stderr.decode()[:300])
        refusal = change_refusal(routes, diff.stdout.decode().split())
        if refusal is not None:
            raise refusal
        return {"schema": SCHEMA, "disposition": "ALLOW", "base": base, "head": head, "condition_routing": "HELD",
                "lowest_supported_mode": "E0", "clock_read": False, "network_used": False}
    except Refusal as refusal:
        return {"schema": SCHEMA, **refusal.six(), "lowest_supported_mode": "E0", "clock_read": False, "network_used": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--ruling", required=True, type=Path)
    v.add_argument("--finish-point-root", required=True, type=Path)
    v.add_argument("--receipt-out", type=Path)
    c = sub.add_parser("check-change")
    c.add_argument("--ruling", required=True, type=Path)
    c.add_argument("--root", required=True, type=Path)
    c.add_argument("--base", required=True)
    c.add_argument("--head", required=True)
    c.add_argument("--receipt-out", type=Path)
    args = parser.parse_args(argv)
    ruling = json.loads(args.ruling.read_text(encoding="utf-8"))
    body = (verify(ruling, args.finish_point_root.resolve()) if args.cmd == "verify"
            else check_change(ruling, args.root.resolve(), args.base, args.head))
    text = json.dumps(body, indent=2, sort_keys=True) + "\n"
    if args.receipt_out:
        args.receipt_out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if body["disposition"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
