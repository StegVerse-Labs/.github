#!/usr/bin/env python3
"""Class B owner-assignment transition (E0-terminal, deterministic, no LLM).

Takes files a consumer observed as UNOWNED, verifies a *receipted* lineage
chain from each file to a candidate Goal, and emits an owner-assignment record.

ALLOW only when, for a file:
  1. the file bytes at the pinned commit hash to the declared sha256;
  2. the candidate Goal resolves in the canonical task registry/records and its
     targets cover the file's repository;
  3. every commit in the file's history up to the pin (no rename following) is
     bound by a landing receipt read back from a supplied ledger copy; and
  4. the introducing commit is bound to the candidate Goal by a receipt read back
     from a supplied ledger copy.
A receipt counts only if its body hashes to its address and it lies on the chain
walked from the ledger's HEAD.json via previous_receipt_sha256.  Git commits, PR
bodies and session lines are carried as observed_non_receipted_lineage and never
satisfy a predicate.  Everything else is FAIL_CLOSED with the six fields.

Inputs are files only: a request, a git-history snapshot (made by `history` from
a local clone) and local bare ledger copies.  No network, clock, environment
credential, subprocess outside local `git`, cron or dispatch.  Writes no ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from typing import Any

REQUEST_SCHEMA = "stegverse.owner-assignment-request/v1"
HISTORY_SCHEMA = "stegverse.owner-assignment-git-history/v1"
RECORD_SCHEMA = "stegverse.owner-assignment-record/v1"
RUN_SCHEMA = "stegverse.owner-assignment-run/v1"
LEDGER_REF = "refs/stegverse/organization-ledger"
RETRY = "scripts/owner_assignment_transition.py evaluate"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
COMMIT_KEYS = ("merge_commit", "transfer_commit", "commit", "source_commit")
GOAL_KEYS = ("task_id", "goal_task_id", "owning_goal_task_id")
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")


def canon(v: Any) -> bytes:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(v: Any) -> str:
    return "sha256:" + hashlib.sha256(v if isinstance(v, (bytes, bytearray)) else canon(v)).hexdigest()


def seal(body: dict, key: str) -> dict:
    b = {k: v for k, v in body.items() if k != key}
    return {**b, key: sha(b)}


def _git(git_dir: str, *args: str) -> bytes:
    return subprocess.run(["git", "--git-dir", git_dir, *args], check=True,
                          capture_output=True, env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                                                    "GIT_CONFIG_NOSYSTEM": "1", "HOME": "/nonexistent"}).stdout


def fail(code: str, predicate: str, repair: str, next_attempt: str) -> dict:
    return {"disposition": "FAIL_CLOSED", "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": RETRY,
            "owning_existing_goal": OWNING_GOAL, "next_attempt": next_attempt}


# ---------------------------------------------------------------- history
def history(git_dir: str, repository: str, pinned_commit: str, paths: list[str]) -> dict:
    """Snapshot what local git observes; this is git evidence, not a receipt."""
    files = {}
    for path in sorted(paths):
        raw = _git(git_dir, "log", "--no-renames", "--format=%x00%H", "--name-status",
                   pinned_commit, "--", path).decode()
        commits = []
        for chunk in raw.split("\x00")[1:]:
            lines = [ln for ln in chunk.splitlines() if ln.strip()]
            status = next((ln.split("\t")[0] for ln in lines[1:] if ln.split("\t")[-1] == path), "?")
            commits.append({"commit": lines[0].strip(), "status": status})
        try:
            data = _git(git_dir, "show", f"{pinned_commit}:{path}")
            digest = hashlib.sha256(data).hexdigest()
        except subprocess.CalledProcessError:
            digest = None
        intro = [c["commit"] for c in commits if c["status"] == "A"]
        files[path] = {"sha256_at_pin": digest, "commits_newest_first": commits,
                       "introducing_commit": intro[-1] if intro else None}
    return seal({"schema": HISTORY_SCHEMA, "repository": repository, "pinned_commit": pinned_commit,
                 "evidence_class": "GIT_OBSERVATION_NOT_A_LEDGER_RECEIPT", "files": files}, "snapshot_sha256")


# ---------------------------------------------------------------- ledgers
def read_ledgers(copies_dir: str | None) -> dict:
    """Walk every chain (org + repository-ledger namespaces) in each bare copy."""
    out = {"copies": [], "receipts": []}
    if not copies_dir or not os.path.isdir(copies_dir):
        return out
    for name in sorted(os.listdir(copies_dir)):
        gd = os.path.join(copies_dir, name)
        if not name.endswith(".git"):
            continue
        try:
            tip = _git(gd, "rev-parse", LEDGER_REF).decode().strip()
            tree = _git(gd, "ls-tree", "-r", "--name-only", tip).decode().split()
        except subprocess.CalledProcessError:
            continue
        heads = sorted(p for p in tree if p == "HEAD.json" or (p.startswith("repository-ledger/") and p.endswith("/HEAD.json")))
        chains = []
        for head_path in heads:
            base = head_path[: -len("HEAD.json")]
            head = json.loads(_git(gd, "show", f"{tip}:{head_path}"))
            cursor, seen, n, broken = head.get("receipt_sha256"), set(), 0, None
            while cursor and cursor not in seen:
                seen.add(cursor)
                path = f"{base}receipts/{cursor.split(':', 1)[1]}.json"
                if path not in tree:
                    broken = "receipt_missing:" + cursor
                    break
                r = json.loads(_git(gd, "show", f"{tip}:{path}"))
                if sha({k: v for k, v in r.items() if k != "receipt_sha256"}) != cursor or r.get("receipt_sha256") != cursor:
                    broken = "receipt_does_not_hash_to_address:" + cursor
                    break
                out["receipts"].append({"ledger": name[:-4], "ledger_tip": tip, "path": path, "receipt": r})
                n += 1
                cursor = r.get("previous_receipt_sha256")
            chains.append({"head": head_path, "receipts_on_chain": n, "chain_break": broken})
        out["copies"].append({"ledger": name[:-4], "ref": LEDGER_REF, "tip": tip, "chains": chains})
    return out


def _evidence(r: dict) -> dict:
    e = r.get("evidence")
    return e if isinstance(e, dict) else {}


def landing_receipts(receipts: list, repository: str, commit: str) -> list:
    return [x for x in receipts if _evidence(x["receipt"]).get("repository") == repository
            and any(_evidence(x["receipt"]).get(k) == commit for k in COMMIT_KEYS)]


def goal_receipts(receipts: list, repository: str, commit: str, goal: str) -> list:
    return [x for x in landing_receipts(receipts, repository, commit)
            if any(_evidence(x["receipt"]).get(k) == goal for k in GOAL_KEYS)]


def _ref(x: dict) -> dict:
    return {"ledger": x["ledger"], "ledger_tip": x["ledger_tip"], "path": x["path"],
            "receipt_sha256": x["receipt"]["receipt_sha256"]}


# ---------------------------------------------------------------- goals
def resolve_goal(goal: str, registry: dict, records_dir: str) -> dict | None:
    p = os.path.join(records_dir, goal + ".json")
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    for t in registry.get("tasks", []):
        if t.get("task_id") == goal:
            return t
    return None


# ---------------------------------------------------------------- evaluate
def evaluate_file(req: dict, entry: dict, hist: dict, ledgers: dict, goal_rec: dict | None) -> dict:
    repo, goal, path = req["source_repository"], req["candidate_goal"], entry["path"]
    h = hist["files"].get(path)
    base = {"schema": RECORD_SCHEMA, "repository": repo, "path": path, "pinned_commit": req["pinned_commit"],
            "declared_sha256": entry["sha256"], "candidate_goal": goal,
            "observed_non_receipted_lineage": entry.get("observed_non_receipted_lineage", {}),
            "authority_effect": "NONE_E0_RECORD_ONLY"}
    if hist.get("repository") != repo or hist.get("pinned_commit") != req["pinned_commit"] or h is None:
        return seal({**base, **fail("LINEAGE_INSUFFICIENT", "GIT_HISTORY_SNAPSHOT_MATCHES_REQUEST",
                     "a history snapshot of this repository at the pinned commit that covers the path",
                     "re-run `history` against a local clone holding the pinned commit")}, "record_sha256")
    commits = [c["commit"] for c in h["commits_newest_first"]]
    intro = h["introducing_commit"]
    links = []
    for c in reversed(commits):
        land = landing_receipts(ledgers["receipts"], repo, c)
        bind = goal_receipts(ledgers["receipts"], repo, c, goal) if c == intro else []
        links.append({"commit": c, "introducing": c == intro, "landing_receipts": [_ref(x) for x in land],
                      "goal_binding_receipts": [_ref(x) for x in bind]})
    base["lineage_chain"] = {"introducing_commit": intro, "links_oldest_first": links,
                             "history_snapshot_sha256": hist["snapshot_sha256"]}
    missing = []  # every unmet predicate, in evaluation order; the first is the six-field primary
    if h["sha256_at_pin"] != entry["sha256"].removeprefix("sha256:"):
        missing.append(("FILE_BYTES_AT_PIN_MATCH_DECLARED_SHA256",
                        f"the bytes of {path} at {req['pinned_commit']} hashing to the declared sha256",
                        "correct the declared sha256 or the pinned commit, then re-evaluate"))
    if intro is None:
        missing.append(("INTRODUCING_COMMIT_OBSERVED",
                        f"an introducing (status A, no rename following) commit for {path} reachable from the pin",
                        "pin a commit whose ancestry adds the path"))
    if goal_rec is None:
        missing.append(("CANDIDATE_GOAL_REGISTERED", f"a canonical task record or registry entry for {goal}",
                        "register the Goal through canonical_task_registration_transition.py, then re-evaluate"))
    elif repo not in (goal_rec.get("targets") or {}).get("repositories", []):
        missing.append(("GOAL_TARGETS_COVER_FILE_REPOSITORY",
                        f"{goal} targets.repositories naming {repo} (now "
                        f"{sorted((goal_rec.get('targets') or {}).get('repositories', []))}), changed only by a "
                        "receipted canonical-task registration transition",
                        "a registration transition extending the Goal's targets, read back from the Labs ledger"))
    miss = [l["commit"] for l in links if not l["landing_receipts"]]
    if miss:
        missing.append(("EVERY_HISTORY_COMMIT_HAS_A_READ_BACK_LANDING_RECEIPT",
                        f"ledger receipts (evidence.repository={repo}, evidence.merge_commit|transfer_commit|commit|"
                        f"source_commit=<commit>) on a chain in a supplied ledger copy for: {', '.join(miss)}",
                        "supply ledger copies holding those receipts; a git commit is never accepted in place of one"))
    if intro is not None and not any(l["goal_binding_receipts"] for l in links if l["introducing"]):
        missing.append(("INTRODUCING_COMMIT_BOUND_TO_CANDIDATE_GOAL_BY_RECEIPT",
                        f"a read-back receipt for {intro} in {repo} whose evidence names "
                        f"task_id|goal_task_id|owning_goal_task_id={goal}",
                        "supply the ledger copy holding that receipt, then re-evaluate"))
    if missing:
        r = fail("LINEAGE_INSUFFICIENT", *missing[0])
        r["unmet_predicates"] = [{"failed_predicate": m[0], "required_evidence_or_repair": m[1]} for m in missing]
    else:
        r = {"disposition": "ALLOW", "owner_task_id": goal,
             "basis": "every history commit landing-receipted; introducing commit goal-bound by receipt"}
    if r["disposition"] != "ALLOW":
        contra = entry.get("observed_non_receipted_lineage", {}).get("names_goal")
        if contra and contra != goal:
            r["contradicting_observation"] = (f"non-receipted lineage names {contra}, not {goal}; "
                                              "the candidate assignment is contradicted, not merely unproven")
    return seal({**base, **r}, "record_sha256")


def evaluate(req: dict, hist: dict, ledgers: dict, registry: dict, records_dir: str,
             request_sha: str, registry_sha: str) -> dict:
    if req.get("schema") != REQUEST_SCHEMA or hist.get("schema") != HISTORY_SCHEMA:
        raise SystemExit("unsupported request or history schema")
    if sha({k: v for k, v in hist.items() if k != "snapshot_sha256"}) != hist.get("snapshot_sha256"):
        raise SystemExit("history snapshot does not hash to its snapshot_sha256")
    goal_rec = resolve_goal(req["candidate_goal"], registry, records_dir)
    records = [evaluate_file(req, e, hist, ledgers, goal_rec) for e in sorted(req["files"], key=lambda e: e["path"])]
    tally: dict = {}
    for r in records:
        tally[r["disposition"]] = tally.get(r["disposition"], 0) + 1
    return seal({"schema": RUN_SCHEMA, "request_id": req["request_id"], "request_sha256": request_sha,
                 "registry_sha256": registry_sha, "history_snapshot_sha256": hist["snapshot_sha256"],
                 "ledger_copies": ledgers["copies"], "candidate_goal": req["candidate_goal"],
                 "candidate_goal_resolved": goal_rec is not None, "tally": dict(sorted(tally.items())),
                 "records": records, "e0_terminal": True, "llm_required": False,
                 "authority_effect": "NONE_E0_RECORD_ONLY_NO_LEDGER_WRITE"}, "run_sha256")


def _load(p: str) -> tuple[dict, str]:
    with open(p, "rb") as fh:
        raw = fh.read()
    return json.loads(raw), "sha256:" + hashlib.sha256(raw).hexdigest()


def _dump(obj: dict, out: str | None) -> None:
    text = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("history")
    h.add_argument("--request", required=True)
    h.add_argument("--git-dir", required=True)
    h.add_argument("--out")
    e = sub.add_parser("evaluate")
    e.add_argument("--request", required=True)
    e.add_argument("--history", required=True)
    e.add_argument("--ledger-copies")
    e.add_argument("--registry", default="data/canonical-task-registry.json")
    e.add_argument("--records", default="data/canonical-task-records")
    e.add_argument("--out")
    a = ap.parse_args(argv)
    req, req_sha = _load(a.request)
    if a.cmd == "history":
        _dump(history(a.git_dir, req["source_repository"], req["pinned_commit"], [f["path"] for f in req["files"]]), a.out)
        return 0
    hist, _ = _load(a.history)
    registry, reg_sha = _load(a.registry)
    run = evaluate(req, hist, read_ledgers(a.ledger_copies), registry, a.records, req_sha, reg_sha)
    _dump(run, a.out)
    return 0 if set(run["tally"]) == {"ALLOW"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
