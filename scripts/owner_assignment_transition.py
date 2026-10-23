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

Candidate owner is kept separate from assigned owner (assigned only on ALLOW).
A per-file candidate_owner, or candidates derived deterministically from Goal-id
references in sealed issue/PR text (derive_candidates_from + `sources`), or the
request candidate_goal is used; excluded_candidates are never selected.  With no
registered candidate the record is a CUSTODY record (record_kind CUSTODY): the
file stays UNOWNED_NOT_OBSERVED, pinned and consumed, edits fail closed, and
custody (not ownership) stays with STEGVERSE-CANONICAL-WORK-COORDINATION-001.

Inputs are files only: a request, a git-history snapshot (made by `history` from
a local clone) and local bare ledger copies.  No network, clock, environment
credential, subprocess outside local `git`, cron or dispatch.  Writes no ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from typing import Any

REQUEST_SCHEMA = "stegverse.owner-assignment-request/v1"
HISTORY_SCHEMA = "stegverse.owner-assignment-git-history/v1"
RECORD_SCHEMA = "stegverse.owner-assignment-record/v1"
RUN_SCHEMA = "stegverse.owner-assignment-run/v1"
SOURCES_SCHEMA = "stegverse.goal-reference-sources/v1"
CUSTODIAN = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
GOAL_ID = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+-[0-9]{3}\b")
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



# ---------------------------------------------------------------- goal-reference sources
def sources_snapshot(exports: list[str], repository: str) -> dict:
    """Seal locally saved issue/PR exports (gh --json number,title,body,comments) as text sources.

    Reads only the given local files; the export itself is made outside this transition."""
    out = []
    for path in sorted(exports):
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        n = d["number"]
        texts = [("body", d.get("body") or "")]
        for c in d.get("comments") or []:
            cid = (c.get("url") or "").rsplit("#issuecomment-", 1)[-1] or c.get("id")
            texts.append((f"comment {cid}", c.get("body") or ""))
        for where, text in texts:
            out.append({"ref": f"{repository}#{n} {where}", "number": n, "text": text,
                        "text_sha256": sha(text.encode())})
    return seal({"schema": SOURCES_SCHEMA, "repository": repository,
                 "evidence_class": "OBSERVED_ISSUE_AND_PR_TEXT_NOT_A_LEDGER_RECEIPT",
                 "sources": sorted(out, key=lambda x: (x["number"], x["ref"]))}, "snapshot_sha256")


def derive_candidates(numbers: list[int], sources: dict | None, registry: dict, records_dir: str) -> dict:
    """Every Goal-id-shaped token in the named sources, each checked against the registry/records."""
    if sources is None:
        return {"sources_read": [], "references": [], "registered": [], "unavailable": True}
    picked = [x for x in sources["sources"] if x["number"] in set(numbers)]
    refs: dict = {}
    for x in picked:
        if sha(x["text"].encode()) != x["text_sha256"]:
            raise SystemExit("goal-reference source text does not hash to its text_sha256: " + x["ref"])
        for gid in sorted(set(GOAL_ID.findall(x["text"]))):
            refs.setdefault(gid, []).append(x["ref"])
    references = [{"goal_id": g, "found_in": sorted(v), "registered": resolve_goal(g, registry, records_dir) is not None}
                  for g, v in sorted(refs.items())]
    return {"sources_read": sorted({x["ref"] for x in picked}), "source_numbers": sorted(set(numbers)),
            "references": references, "registered": [r["goal_id"] for r in references if r["registered"]],
            "unavailable": False}


def custody_block(entry: dict) -> dict:
    return {"custodian": CUSTODIAN, "owner_status": "UNOWNED_NOT_OBSERVED", "pinned": True, "consumed": True,
            "edit_policy": "EDITS_FAIL_CLOSED_UNTIL_AN_OWNER_IS_ASSIGNED_BY_RECEIPTED_LINEAGE",
            "custody_is_not_ownership": True}

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
def select_candidate(req: dict, entry: dict, sources: dict | None, registry: dict, records_dir: str) -> dict:
    """The candidate owner for one file, kept separate from any assigned owner.

    Precedence: an explicit per-file candidate_owner; else candidates derived from
    goal-reference sources (derive_candidates_from); else the request-level candidate_goal.
    An excluded candidate is never selected."""
    excluded = {x["goal_id"]: x for x in entry.get("excluded_candidates", [])}
    sel = {"excluded_candidates": sorted(entry.get("excluded_candidates", []), key=lambda x: x["goal_id"]),
           "derivation": None, "candidate_owner": None, "conflict": None}
    if entry.get("candidate_owner"):
        c = entry["candidate_owner"]
        if c["goal_id"] in excluded:
            sel["conflict"] = ("CANDIDATE_IS_EXCLUDED", c["goal_id"])
        else:
            sel["candidate_owner"] = {**c, "selected_by": "EXPLICIT_CANDIDATE_OWNER"}
        return sel
    if "derive_candidates_from" in entry:
        d = derive_candidates(entry["derive_candidates_from"], sources, registry, records_dir)
        d["registered_not_excluded"] = [g for g in d["registered"] if g not in excluded]
        sel["derivation"] = d
        if d["unavailable"]:
            sel["conflict"] = ("GOAL_REFERENCE_SOURCES_UNAVAILABLE", None)
        elif len(d["registered_not_excluded"]) > 1:
            sel["conflict"] = ("CANDIDATE_OWNER_AMBIGUOUS", d["registered_not_excluded"])
        elif d["registered_not_excluded"]:
            g = d["registered_not_excluded"][0]
            sel["candidate_owner"] = {"goal_id": g, "selected_by": "DERIVED_FROM_GOAL_REFERENCES",
                                      "basis": [r for r in d["references"] if r["goal_id"] == g][0]["found_in"],
                                      "evidence_class": "OBSERVED_TEXT_NOT_A_LEDGER_RECEIPT"}
        return sel
    if req.get("candidate_goal") and req["candidate_goal"] not in excluded:
        sel["candidate_owner"] = {"goal_id": req["candidate_goal"], "selected_by": "REQUEST_CANDIDATE_GOAL"}
    return sel


def evaluate_file(req: dict, entry: dict, hist: dict, ledgers: dict, registry: dict, records_dir: str,
                  sources: dict | None) -> dict:
    repo, path = req["source_repository"], entry["path"]
    h = hist["files"].get(path)
    sel = select_candidate(req, entry, sources, registry, records_dir)
    cand = sel["candidate_owner"]
    goal = cand["goal_id"] if cand else None
    base = {"schema": RECORD_SCHEMA, "repository": repo, "path": path, "pinned_commit": req["pinned_commit"],
            "declared_sha256": entry["sha256"], "candidate_owner": cand, "assigned_owner": None,
            "excluded_candidates": sel["excluded_candidates"],
            "observed_non_receipted_lineage": entry.get("observed_non_receipted_lineage", {}),
            "authority_effect": "NONE_E0_RECORD_ONLY"}
    if sel["derivation"] is not None:
        base["candidate_derivation"] = sel["derivation"]
    if hist.get("repository") != repo or hist.get("pinned_commit") != req["pinned_commit"] or h is None:
        return seal({**base, "record_kind": "CUSTODY", "custody": custody_block(entry),
                     **fail("LINEAGE_INSUFFICIENT", "GIT_HISTORY_SNAPSHOT_MATCHES_REQUEST",
                            "a history snapshot of this repository at the pinned commit that covers the path",
                            "re-run `history` against a local clone holding the pinned commit")}, "record_sha256")
    commits = [c["commit"] for c in h["commits_newest_first"]]
    intro = h["introducing_commit"]
    links = []
    for c in reversed(commits):
        land = landing_receipts(ledgers["receipts"], repo, c)
        bind = goal_receipts(ledgers["receipts"], repo, c, goal) if (c == intro and goal) else []
        links.append({"commit": c, "introducing": c == intro, "landing_receipts": [_ref(x) for x in land],
                      "goal_binding_receipts": [_ref(x) for x in bind]})
    base["lineage_chain"] = {"introducing_commit": intro, "links_oldest_first": links,
                             "history_snapshot_sha256": hist["snapshot_sha256"]}

    if cand is None:
        # no candidate: a custody record, distinct from ownership
        code, detail = sel["conflict"] or ("NO_REGISTERED_CANDIDATE_OWNER", None)
        if code == "NO_REGISTERED_CANDIDATE_OWNER":
            refs = sel["derivation"]["references"] if sel["derivation"] else []
            seen = ", ".join(f"{r['goal_id']} (registered={r['registered']})" for r in refs) or "none"
            r = fail(code, "A_GOAL_REFERENCE_IN_THE_LINEAGE_SOURCES_NAMES_A_REGISTERED_GOAL",
                     f"a registered Goal named in the lineage sources (Goal-id references observed: {seen}); "
                     "until then custody stays with " + CUSTODIAN,
                     "a canonical-task registration (or a lineage source naming a registered Goal), then re-evaluate")
        elif code == "CANDIDATE_OWNER_AMBIGUOUS":
            r = fail(code, "AT_MOST_ONE_REGISTERED_CANDIDATE_OWNER",
                     f"a Coordination ruling choosing one of {detail} or excluding the others",
                     "add the ruling's excluded_candidates to the request, then re-evaluate")
        elif code == "CANDIDATE_IS_EXCLUDED":
            r = fail(code, "CANDIDATE_OWNER_NOT_EXCLUDED",
                     f"{detail} is excluded for this file by ruling; name a different candidate or none",
                     "correct the request, then re-evaluate")
        else:
            r = fail(code, "GOAL_REFERENCE_SOURCES_SUPPLIED",
                     "the sealed goal-reference sources snapshot the request names",
                     "supply --sources, then re-evaluate")
        return seal({**base, "record_kind": "CUSTODY", "custody": custody_block(entry), **r}, "record_sha256")

    goal_rec = resolve_goal(goal, registry, records_dir)
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
        r["custody"] = custody_block(entry)
        contra = entry.get("observed_non_receipted_lineage", {}).get("names_goal")
        if contra and contra != goal:
            r["contradicting_observation"] = (f"non-receipted lineage names {contra}, not {goal}; "
                                              "the candidate assignment is contradicted, not merely unproven")
    else:
        r = {"disposition": "ALLOW", "assigned_owner": goal,
             "basis": "every history commit landing-receipted; introducing commit goal-bound by receipt"}
    return seal({**base, "record_kind": "OWNER_ASSIGNMENT", **r}, "record_sha256")


def evaluate(req: dict, hist: dict, ledgers: dict, registry: dict, records_dir: str,
             request_sha: str, registry_sha: str, sources: dict | None = None) -> dict:
    if req.get("schema") != REQUEST_SCHEMA or hist.get("schema") != HISTORY_SCHEMA:
        raise SystemExit("unsupported request or history schema")
    if sha({k: v for k, v in hist.items() if k != "snapshot_sha256"}) != hist.get("snapshot_sha256"):
        raise SystemExit("history snapshot does not hash to its snapshot_sha256")
    if sources is not None:
        if sources.get("schema") != SOURCES_SCHEMA or \
                sha({k: v for k, v in sources.items() if k != "snapshot_sha256"}) != sources.get("snapshot_sha256"):
            raise SystemExit("goal-reference sources snapshot does not hash to its snapshot_sha256")
        if req.get("goal_reference_sources_sha256") not in (None, sources["snapshot_sha256"]):
            raise SystemExit("goal-reference sources snapshot is not the one the request pins")
    records = [evaluate_file(req, e, hist, ledgers, registry, records_dir, sources)
               for e in sorted(req["files"], key=lambda e: e["path"])]
    tally: dict = {}
    kinds: dict = {}
    for r in records:
        tally[r["disposition"]] = tally.get(r["disposition"], 0) + 1
        kinds[r["record_kind"]] = kinds.get(r["record_kind"], 0) + 1
    return seal({"schema": RUN_SCHEMA, "request_id": req["request_id"], "request_sha256": request_sha,
                 "registry_sha256": registry_sha, "history_snapshot_sha256": hist["snapshot_sha256"],
                 "goal_reference_sources_sha256": sources["snapshot_sha256"] if sources else None,
                 "ledger_copies": ledgers["copies"], "tally": dict(sorted(tally.items())),
                 "record_kinds": dict(sorted(kinds.items())), "records": records,
                 "e0_terminal": True, "llm_required": False,
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
    so = sub.add_parser("sources")
    so.add_argument("--repository", required=True)
    so.add_argument("--export", action="append", required=True)
    so.add_argument("--out")
    e = sub.add_parser("evaluate")
    e.add_argument("--request", required=True)
    e.add_argument("--history", required=True)
    e.add_argument("--ledger-copies")
    e.add_argument("--sources")
    e.add_argument("--registry", default="data/canonical-task-registry.json")
    e.add_argument("--records", default="data/canonical-task-records")
    e.add_argument("--out")
    a = ap.parse_args(argv)
    if a.cmd == "sources":
        _dump(sources_snapshot(a.export, a.repository), a.out)
        return 0
    req, req_sha = _load(a.request)
    if a.cmd == "history":
        _dump(history(a.git_dir, req["source_repository"], req["pinned_commit"], [f["path"] for f in req["files"]]), a.out)
        return 0
    hist, _ = _load(a.history)
    registry, reg_sha = _load(a.registry)
    sources = _load(a.sources)[0] if a.sources else None
    run = evaluate(req, hist, read_ledgers(a.ledger_copies), registry, a.records, req_sha, reg_sha, sources)
    _dump(run, a.out)
    return 0 if set(run["tally"]) == {"ALLOW"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
