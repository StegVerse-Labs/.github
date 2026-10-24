"""STAGE_THRESHOLD_DERIVE: the declared transition that derives the NWI-S2 / NWI-S3 exit-gate thresholds from the NWI-S1
corpus's observed baseline (StegVerse-org/.github#163). Thresholds are never hand-written: each metric predicate's
threshold.derivation in data/sv-work-items/stages/<stage>.json declares the rule (rule_id, baseline, formula,
min_observations, the rule text); this module evaluates it and nothing else.

Input   the S1 baseline snapshot (data/sv-work-items/stage-thresholds/s1-baseline-snapshot.json, collected by
        scripts/derive_stage_thresholds.py --collect): the NWI-S1 verifier corpus (SV-LLM/.github evidence/sv-check-receipts
        at a pinned commit, vendored byte-for-byte, corpus digest over the files) plus the organization-ledger admission
        decisions and outcomes at a pinned ledger commit.
Output  ALLOW: the threshold values and a sealed receipt (rule id, rule digest, rule text, corpus digest, observed baseline,
        computed value per target); apply() writes the values into the stage manifests. Otherwise FAIL_CLOSED with six
        fields, nothing written. All-or-nothing: no stage is given a threshold while another's baseline is insufficient.

Baselines (closed set, each computed by the existing E0 producer, so the S1 baseline is held to the same evidence rules as
the stage metric itself):
  S1_CORPUS_VERDICT_AGREEMENT     sv_e0_terminals.verdict_agreement_e0 over the S1 bundles joined by (repository, head
                                  commit) to ledgered admission decisions
  S1_CORPUS_ADMISSION_MISS_RATE   admission_miss_rate.admission_miss_rate_e0 over the ledgered decisions joined to the S1
                                  corpus heads and the ledgered outcomes
No LLM, clock, network or wait (E0).
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]


def _module(name: str, rel: str):
    m = sys.modules.get(name)
    if m is None:
        s = importlib.util.spec_from_file_location(name, ROOT / rel)
        m = importlib.util.module_from_spec(s)
        sys.modules[name] = m
        s.loader.exec_module(m)
    return m


wi = _module("sv_work_items", "resident-runtime/sv_work_items.py")
sg = _module("stage_gate", "resident-runtime/stage_gate.py")
e0 = _module("sv_e0_terminals", "resident-runtime/sv_e0_terminals.py")
amr = _module("admission_miss_rate", "resident-runtime/admission_miss_rate.py")

TRANSITION = "STAGE_THRESHOLD_DERIVE"
OWNING_GOAL = "StegVerse-org/.github#163"
MODE = "E0"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint", "owning_existing_goal",
       "next_attempt")
DIR = ROOT / "data/sv-work-items/stage-thresholds"
SNAPSHOT_FILE = DIR / "s1-baseline-snapshot.json"
OUTCOME_FILE = DIR / "derivation-outcome.json"
CURRENT_MISS_RATE_FILE = DIR / "admission-miss-rate.current.json"
SNAPSHOT_SCHEMA = "stegverse.nwi-s1-baseline-snapshot/v1"
RECEIPT_SCHEMA = "stegverse.nwi-stage-threshold-derivation/v1"
ENTRY = "scripts/derive_stage_thresholds.py"


def _floor4(n: int, d: int) -> float:
    return (n * 10000 // d) / 10000


def _ceil4(n: int, d: int) -> float:
    return (-(-n * 10000 // d)) / 10000


# formula id -> (computes the value from the observed baseline, value is non-vacuous for the comparator)
FORMULAS = {
    "FLOOR_4DP(agreed/evaluated)": (lambda o: _floor4(o["agreed"], o["evaluated"]), lambda v: v > 0),
    "CEIL_4DP((misses+1)/(observed+1))": (lambda o: _ceil4(o["misses"] + 1, o["observed"] + 1), lambda v: v < 1),
}


def file_entry(rel: str, data: bytes) -> dict[str, str]:
    return {"path": rel, "git_blob": hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest(),
            "sha256": "sha256:" + hashlib.sha256(data).hexdigest()}


def corpus_digest(source: Mapping[str, Any], files: list[Mapping[str, str]]) -> str:
    return wi.sha({"source": dict(source), "files": sorted((dict(f) for f in files), key=lambda f: f["path"])})


def targets(stages: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Every metric exit predicate whose threshold declares a derivation."""
    out = []
    for m in stages:
        for g in m.get("exit_gate") or []:
            t = g.get("threshold") or {}
            if g.get("evidence") == "metric" and isinstance(t.get("derivation"), Mapping):
                d = dict(t["derivation"])
                out.append({"stage_id": m["stage_id"], "predicate": g["predicate"], "metric": t.get("metric"),
                            "comparator": t.get("comparator"), "derivation": d, "rule_digest": wi.sha(d)})
    return out


def _load_corpus(snapshot: Mapping[str, Any], root: Path) -> tuple[dict[str, bytes], str | None]:
    s1 = snapshot.get("s1_corpus") or {}
    files, data = s1.get("files") or [], {}
    for f in files:
        p = root / s1["vendored_dir"] / f["path"]
        b = p.read_bytes() if p.is_file() else b""
        if file_entry(f["path"], b) != dict(f):
            return {}, "S1 corpus file %s differs from the snapshot's git blob / sha256" % f["path"]
        data[f["path"]] = b
    if not files or corpus_digest(s1.get("source") or {}, files) != s1.get("corpus_digest"):
        return {}, "S1 corpus digest does not recompute over the vendored files"
    return data, None


def s1_bundles(corpus: Mapping[str, bytes]) -> list[dict[str, Any]]:
    out = []
    for path in sorted(p for p in corpus if p.endswith("/bundle.json")):
        b = json.loads(corpus[path])
        d = path.rsplit("/", 1)[0]
        receipts = []
        for cid, digest in sorted((b.get("receipts") or {}).items()):
            rp = d + "/" + cid + ".json"
            receipts.append({"receipt": json.loads(corpus[rp]) if rp in corpus else None,
                             "receipt_ref": b.get("ledger_receipt_ref") if b.get("authentic_ledger_receipt") is True else None})
        out.append({"bundle": path, "repository": b.get("repository"), "head_sha": b.get("head_sha"),
                    "change_digest": b.get("change_digest"), "disposition": b.get("disposition"),
                    "failure_code": b.get("failure_code"), "authentic_ledger_receipt": b.get("authentic_ledger_receipt"),
                    "check_receipts": receipts})
    return out


def _joined(bundles: list[Mapping[str, Any]], decisions: list[Mapping[str, Any]]) -> list[tuple[dict, dict | None]]:
    by = {(d["change"].get("repository"), d["change"].get("head_commit")): d for d in decisions}
    return [(dict(b), by.get((b["repository"], b["head_sha"]))) for b in bundles]


def baseline_verdict_agreement(bundles, decisions) -> dict[str, Any]:
    evals = []
    for b, dec in _joined(bundles, decisions):
        evals.append({"change_digest": b["change_digest"], "check_receipts": b["check_receipts"],
                      "admission": None if dec is None else {"change_digest": b["change_digest"],
                                                             "disposition": dec["disposition"], "receipt_ref": dec["receipt_ref"]}})
    out = e0.verdict_agreement_e0(evals)
    joined = [{"bundle": b["bundle"], "s1_verdict": b["disposition"], "s1_failure_code": b["failure_code"],
               "authentic_ledger_receipt": b["authentic_ledger_receipt"],
               "admission": None if dec is None else {"disposition": dec["disposition"], "receipt_ref": dec["receipt_ref"]}}
              for b, dec in _joined(bundles, decisions)]
    if out["disposition"] != "ALLOW":
        return {"observed": False, "producer": {k: out[k] for k in ("disposition", *SIX)}, "excluded": out.get("excluded"),
                "joined": joined}
    return {"observed": True, "agreed": out["agreed"], "evaluated": out["evaluated"], "n": out["evaluated"],
            "record_digest": out["record"]["record_digest"], "joined": joined}


def baseline_admission_miss_rate(bundles, decisions, outcomes) -> dict[str, Any]:
    s1_decisions = [dec for _, dec in _joined(bundles, decisions) if dec is not None]
    out = amr.admission_miss_rate_e0(s1_decisions, list(outcomes))
    if out["disposition"] != "ALLOW":
        return {"observed": False, "producer": {k: out[k] for k in ("disposition", *SIX)}, "counts": out.get("counts"),
                "decisions": [d["receipt_ref"] for d in s1_decisions]}
    return {"observed": True, "misses": out["misses"], "observed_outcomes": out["observed"], "observed_n": out["observed"],
            "n": out["observed"], "record_digest": out["record"]["record_digest"],
            "decisions": [d["receipt_ref"] for d in s1_decisions]}


def _fail(code: str, predicate: str, repair: str, nxt: str, **d: Any) -> dict[str, Any]:
    return {"disposition": "FAIL_CLOSED", "transition_class": TRANSITION, "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": ENTRY, "owning_existing_goal": OWNING_GOAL,
            "next_attempt": nxt, "mode": MODE, **d}


def derive(snapshot: Mapping[str, Any], stages: list[Mapping[str, Any]] | None = None, *, root: Path = ROOT) -> dict[str, Any]:
    stages = stages if stages is not None else sg.load_stages()
    if not isinstance(snapshot, Mapping) or snapshot.get("schema") != SNAPSHOT_SCHEMA:
        return _fail("S1_BASELINE_SNAPSHOT_UNOBSERVED", "STAGE_THRESHOLD_INPUT_IS_THE_S1_BASELINE_SNAPSHOT",
                     "a %s snapshot (scripts/derive_stage_thresholds.py --collect)" % SNAPSHOT_SCHEMA,
                     "collect the snapshot, then re-run; nothing was written")
    try:
        hb = wi.epoch_check((snapshot.get("ledger") or {}).get("hb_epoch"), "stage_threshold_derive")
    except wi.Refusal as r:
        return {**dict(r.record), "transition_class": TRANSITION, "retry_entrypoint": ENTRY, "mode": MODE}
    corpus, bad = _load_corpus(snapshot, root)
    if bad:
        return _fail("S1_CORPUS_DIGEST_MISMATCH", "STAGE_THRESHOLD_INPUT_IS_THE_PINNED_S1_CORPUS", bad,
                     "re-collect the S1 corpus at its pinned commit; nothing was written")
    tg = targets(stages)
    if not tg:
        return _fail("STAGE_THRESHOLD_RULE_UNDECLARED", "THRESHOLD_DERIVATION_IS_DECLARED_IN_STAGE_MANIFEST",
                     "a threshold.derivation on each metric exit predicate", "declare the rule; nothing was written")
    bundles, decisions = s1_bundles(corpus), list(snapshot.get("decisions") or [])
    outcomes = list(snapshot.get("outcomes") or [])
    computed, insufficient = [], []
    for t in tg:
        d = t["derivation"]
        f = FORMULAS.get(d.get("formula"))
        base = {"S1_CORPUS_VERDICT_AGREEMENT": lambda: baseline_verdict_agreement(bundles, decisions),
                "S1_CORPUS_ADMISSION_MISS_RATE": lambda: baseline_admission_miss_rate(bundles, decisions, outcomes)
                }.get(d.get("baseline"))
        row = {k: t[k] for k in ("stage_id", "predicate", "metric", "comparator", "rule_digest")} | {
            "rule_id": d.get("rule_id"), "rule": d.get("rule")}
        if d.get("transition") != TRANSITION or f is None or base is None or t["comparator"] not in sg.COMPARATORS \
                or not isinstance(d.get("min_observations"), int) or d["min_observations"] < 1:
            insufficient.append({**row, "reason": "STAGE_THRESHOLD_RULE_UNDECLARED"}); continue
        observed = base()
        row["baseline"] = observed
        if not observed["observed"]:
            insufficient.append({**row, "reason": "BASELINE_UNOBSERVED"}); continue
        if observed["n"] < d["min_observations"]:
            insufficient.append({**row, "reason": "BASELINE_BELOW_MIN_OBSERVATIONS"}); continue
        o = {"agreed": observed.get("agreed"), "evaluated": observed.get("evaluated"), "misses": observed.get("misses"),
             "observed": observed.get("observed_n")}
        value = f[0](o)
        if not f[1](value):
            insufficient.append({**row, "value": value, "reason": "DERIVED_THRESHOLD_VACUOUS"}); continue
        computed.append({**row, "value": value})
    common = {"corpus_digest": snapshot["s1_corpus"]["corpus_digest"], "corpus_source": snapshot["s1_corpus"]["source"],
              "ledger": snapshot.get("ledger"), "snapshot_sha256": wi.sha(dict(snapshot)), "hb_epoch": hb}
    if insufficient:
        return _fail("STAGE_THRESHOLD_BASELINE_INSUFFICIENT", "STAGE_THRESHOLD_IS_DERIVED_FROM_OBSERVED_S1_BASELINE",
                     "; ".join("%s %s: %s" % (i["stage_id"], i["predicate"], i["reason"]) for i in insufficient)
                     + " -- the S1 baseline needs NWI-S1 verifier check receipts appended to the organization ledger "
                       "(authentic_ledger_receipt true) for changes with ledgered admission decisions, and ledgered admission "
                       "outcomes (stegverse.admission_miss.v1 / stegverse.admission_outcome.v1), at least each rule's "
                       "min_observations", "re-run %s --collect then %s on the next organization-ledger append of an S1 "
                       "verifier receipt or admission outcome; thresholds stay null (STAGE_THRESHOLD_UNDECLARED) meanwhile "
                       "and nothing waits" % (ENTRY, ENTRY), **common, insufficient=insufficient, computed=computed)
    receipt = wi.seal({"schema": RECEIPT_SCHEMA, "transition_class": TRANSITION, "mode": MODE, **common,
                       "targets": computed}, "receipt_sha256")
    return {"disposition": "ALLOW", "transition_class": TRANSITION, "mode": MODE, "receipt": receipt,
            "thresholds": {t["stage_id"] + ":" + t["predicate"]: t["value"] for t in computed}}


def apply(stages: list[Mapping[str, Any]], outcome: Mapping[str, Any], receipt_file: str) -> list[dict[str, Any]]:
    """The stage manifests after the transition: on ALLOW each derived threshold's value and derived_by; otherwise unchanged."""
    out = copy.deepcopy([dict(m) for m in stages])
    if outcome.get("disposition") != "ALLOW":
        return out
    vals = {(t["stage_id"], t["predicate"]): t for t in outcome["receipt"]["targets"]}
    for m in out:
        for g in m.get("exit_gate") or []:
            t = vals.get((m["stage_id"], g["predicate"]))
            if t is not None:
                g["threshold"]["value"] = t["value"]
                g["threshold"]["derived_by"] = {"transition": TRANSITION, "receipt_file": receipt_file,
                                                "receipt_sha256": outcome["receipt"]["receipt_sha256"]}
    return out


def witness_threshold_derive(case: Mapping[str, Any]) -> dict[str, Any]:
    """Witness / test entrypoint: derive over a supplied snapshot (vendored corpus under the case's root)."""
    return derive(case.get("snapshot"), case.get("stages"), root=Path(case.get("root") or ROOT))
