#!/usr/bin/env python3
"""STAGE_THRESHOLD_DERIVE runner (resident-runtime/stage_threshold_derive.py).

  --collect --s1-repo <SV-LLM/.github clone> [--s1-commit <sha>] [--ledger-repo <Labs clone>]
      read the NWI-S1 corpus (evidence/sv-check-receipts at the commit, git objects only) and the organization ledger
      (refs/stegverse/organization-ledger, git objects only) and write the vendored corpus + s1-baseline-snapshot.json
  (default)  derive over the committed snapshot; write derivation-outcome.json, admission-miss-rate.current.json (the
             ADMISSION_MISS_RATE producer over every ledgered decision in the snapshot) and, on ALLOW only, the stage manifests
  --check    exit 1 if a fresh derivation differs from the committed outcome or manifests (reproducibility)
Prints the outcome's disposition summary as JSON. No clock, no network.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
s = importlib.util.spec_from_file_location("stage_threshold_derive", ROOT / "resident-runtime/stage_threshold_derive.py")
td = importlib.util.module_from_spec(s)
sys.modules["stage_threshold_derive"] = td
s.loader.exec_module(td)
wi, sg = td.wi, td.sg

S1_REPOSITORY = "SV-LLM/.github"
S1_PATH = "evidence/sv-check-receipts"
VENDORED = "data/sv-work-items/stage-thresholds/s1-corpus"
LEDGER = "refs/stegverse/organization-ledger"
MERGE = "ORGANIZATION_MAIN_MERGE_TRANSFER"


def dump(obj) -> str:
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout


def collect(s1_repo: Path, s1_commit: str, ledger_repo: Path) -> dict:
    commit = git(s1_repo, "rev-parse", s1_commit + "^{commit}").decode().strip()
    files = []
    for rel in sorted(git(s1_repo, "ls-tree", "-r", "--name-only", commit, S1_PATH).decode().split()):
        data = git(s1_repo, "show", "%s:%s" % (commit, rel))
        sub = rel[len(S1_PATH) + 1:]
        out = ROOT / VENDORED / sub
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        files.append(td.file_entry(sub, data))
    source = {"repository": S1_REPOSITORY, "commit": commit, "path": S1_PATH,
              "producer": "NWI-S1 verifier (SV-LLM/.github#46, sandbox/s1_sv_check_receipts.py)"}
    lc = git(ledger_repo, "rev-parse", LEDGER).decode().strip()
    head = json.loads(git(ledger_repo, "show", lc + ":HEAD.json"))
    org = {}
    for rel in git(ledger_repo, "ls-tree", "-r", "--name-only", lc, "receipts").decode().split():
        r = json.loads(git(ledger_repo, "show", "%s:%s" % (lc, rel)))
        org[r["receipt_sha256"]] = r
    chain, cur = [], head["receipt_sha256"]  # oldest first, by previous_receipt_sha256 from HEAD
    while cur in org:
        chain.append(org[cur]); cur = org[cur].get("previous_receipt_sha256")
    chain.reverse()
    repo_receipts, outcomes = {}, []
    for rel in git(ledger_repo, "ls-tree", "-r", "--name-only", lc).decode().split():
        if not rel.endswith(".json") or rel == "HEAD.json":
            continue
        r = json.loads(git(ledger_repo, "show", "%s:%s" % (lc, rel)))
        if r.get("schema") in ("stegverse.admission_miss.v1", "stegverse.admission_outcome.v1"):
            outcomes.append(r)
        if r.get("transition_class") == MERGE and rel.startswith("repository-ledger/"):
            repo_receipts[r["receipt_sha256"]] = r
    decisions = []
    for seq, o in enumerate(chain):
        rr = repo_receipts.get(o.get("repo_receipt_sha256"))
        if rr is None:
            continue
        ev = rr["evidence"]
        decisions.append({"receipt_ref": "%s@%s:receipts/%s.json" % (LEDGER, lc, o["receipt_sha256"].split(":")[1]),
                          "repo_receipt_sha256": rr["receipt_sha256"], "transition_class": MERGE, "ledger_seq": seq,
                          "disposition": ev["disposition"],
                          "change": {"repository": ev["repository"], "head_commit": ev["parents"][-1],
                                     "merge_commit": ev["merge_commit"], "pull_request": ev.get("pull_request")}})
    ad = ROOT / "data/admission-scenarios"
    miss_lines = [json.loads(l) for f in ("classes.jsonl", "corpus.jsonl") for l in (ad / f).read_text().splitlines()
                  if l.strip() and json.loads(l).get("origin") == "ADMISSION_MISS"]
    return {"schema": td.SNAPSHOT_SCHEMA,
            "s1_corpus": {"source": source, "vendored_dir": VENDORED, "files": files,
                          "corpus_digest": td.corpus_digest(source, files)},
            "ledger": {"ref": LEDGER, "commit": lc, "head_receipt_sha256": head["receipt_sha256"],
                       "hb_epoch": str(org[head["receipt_sha256"]]["hb_reference"]["epoch"]),
                       "org_receipts_in_chain": len(chain)},
            "decisions": decisions, "outcomes": sorted(outcomes, key=wi.canon),
            "admission_learning_corpus": {"files": ["data/admission-scenarios/classes.jsonl", "data/admission-scenarios/corpus.jsonl"],
                                          "admission_miss_origin_lines": len(miss_lines)},
            "collected_by": "scripts/derive_stage_thresholds.py --collect (git objects only; no clock, no network)"}


def generated() -> dict[Path, str]:
    snapshot = json.loads(td.SNAPSHOT_FILE.read_text())
    stages = sg.load_stages()
    outcome = td.derive(snapshot, stages)
    current = td.amr.admission_miss_rate_e0(snapshot.get("decisions") or [], snapshot.get("outcomes") or [])
    out = {td.OUTCOME_FILE: dump(outcome),
           td.CURRENT_MISS_RATE_FILE: dump({"scope": "every ledgered admission decision in the snapshot (ledger %s)"
                                            % snapshot["ledger"]["commit"], "snapshot_sha256": wi.sha(snapshot), **current})}
    for m in td.apply(stages, outcome, td.OUTCOME_FILE.relative_to(ROOT).as_posix()):
        p = sg.STAGES_DIR / (m["stage_id"] + ".json")
        out[p] = json.dumps(m, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--s1-repo", type=Path)
    ap.add_argument("--s1-commit", default="a00a72ec54055e11b23841e3718cfd7352ad8a8c")
    ap.add_argument("--ledger-repo", type=Path, default=ROOT)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.collect:
        td.DIR.mkdir(parents=True, exist_ok=True)
        td.SNAPSHOT_FILE.write_text(dump(collect(a.s1_repo, a.s1_commit, a.ledger_repo)))
    gen = generated()
    stale = sorted(p.relative_to(ROOT).as_posix() for p, t in gen.items() if not p.is_file() or p.read_text() != t)
    outcome = json.loads(gen[td.OUTCOME_FILE])
    summary = {"disposition": outcome["disposition"], "failure_code": outcome.get("failure_code"),
               "thresholds": outcome.get("thresholds"), "corpus_digest": outcome.get("corpus_digest")
               or outcome.get("receipt", {}).get("corpus_digest"), "stale": stale}
    if a.check:
        print(json.dumps(summary, sort_keys=True))
        return 1 if stale else 0
    for p, t in gen.items():
        if not p.is_file() or p.read_text() != t:
            p.write_text(t)
    print(json.dumps({**summary, "stale": []}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
