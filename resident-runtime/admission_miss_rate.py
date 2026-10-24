"""ADMISSION_MISS_RATE producer (NWI-S3 exit gate metric, StegVerse-org/.github#163).

The metric is computed from admission OUTCOMES, never asserted: ledgered admission decisions joined with later observed
results, under the definition declared in data/sv-work-items/stages/NWI-S3.json (metric_definitions.admission_miss_rate,
read here, never restated). Per decision the joined outcome is exactly one of

  FALSE_ADMIT      an ALLOW decision named by a sealed stegverse.admission_miss.v1 record (admission_learning.admission_miss:
                   REVERT / CORRECTION / REFUSAL) whose admission_receipt_ref is the decision's ledger receipt and whose
                   correcting_ref is itself a ledger receipt
  FALSE_REFUSAL    a DENY decision for a change digest at a base, followed later in the ledger by an ALLOW decision for the
                   same change digest at the same base (nothing differed, so the refusal was the miss)
  HELD             a decision named by a sealed stegverse.admission_outcome.v1 HELD record whose evidence_ref is a ledger
                   receipt (a miss record for the same decision wins: the contradiction is kept in the record)
  NOT_APPLICABLE   a FAIL_CLOSED decision (missing evidence; a later ALLOW after the evidence is appended is the designed
                   path, not a miss)
  UNKNOWN          anything else. UNKNOWN is never counted as HELD: no absence of a revert is read as an outcome.

admission_miss_rate = (FALSE_ADMIT + FALSE_REFUSAL) / (FALSE_ADMIT + FALSE_REFUSAL + HELD). Fewer observed outcomes than the
manifest's min_observed_outcomes -> FAIL_CLOSED ADMISSION_MISS_RATE_UNOBSERVED with six fields; no rate is ever defaulted.

Every counted miss is fed to the existing learning path: admission_learning.harvest -> generalize -> generate ->
corpus_append (SCENARIO_CORPUS_APPEND), learn_from_misses() below. No LLM, clock, network or wait (E0).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

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
al = _module("admission_learning", "resident-runtime/admission_learning.py")

OWNING_GOAL = "StegVerse-org/.github#163"
MODE = "E0"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint", "owning_existing_goal",
       "next_attempt")
STAGE_FILE = ROOT / "data/sv-work-items/stages/NWI-S3.json"
METRIC = "admission_miss_rate"
PREDICATE = "ADMISSION_MISS_RATE"
OUTCOME_SCHEMA = "stegverse.admission_outcome.v1"
RECORD_SCHEMA = "stegverse.nwi-s3-admission-miss-rate/v1"
OUTCOMES = ("FALSE_ADMIT", "FALSE_REFUSAL", "HELD", "NOT_APPLICABLE", "UNKNOWN")
ENTRY = "resident-runtime/admission_miss_rate.py::"


def _refusal(code: str, predicate: str, repair: str, entry: str, nxt: str, **d: Any) -> wi.Refusal:
    r = wi.Refusal("FAIL_CLOSED", code, predicate, repair, entry, nxt, **d)
    r.record["retry_entrypoint"] = ENTRY + entry
    return r


def definition(stage: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """The miss definition as declared in the NWI-S3 manifest, with its digest."""
    m = stage if stage is not None else json.loads(STAGE_FILE.read_text(encoding="utf-8"))
    d = ((m.get("metric_definitions") or {}).get(METRIC))
    if not isinstance(d, Mapping):
        raise _refusal("ADMISSION_MISS_DEFINITION_UNDECLARED", "ADMISSION_MISS_IS_DEFINED_IN_THE_MANIFEST",
                       "metric_definitions.admission_miss_rate in data/sv-work-items/stages/NWI-S3.json", "definition",
                         "declare the definition; nothing was computed")
    return {**dict(d), "definition_sha256": wi.sha(dict(d))}


def _terminal(code: str, predicate: str, repair: str, entry: str, nxt: str, **detail: Any) -> dict[str, Any]:
    return {"disposition": "FAIL_CLOSED", "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": ENTRY + entry, "owning_existing_goal": OWNING_GOAL,
            "next_attempt": nxt, "mode": MODE, **detail}


def _ledgered(ref: Any, fixture_mode: bool) -> bool:
    if not isinstance(ref, str):
        return False
    return bool(wi.LEDGER_RECEIPT_REF.match(ref)) or (fixture_mode and wi.FIXTURE_REF_MARK in ref)


def admission_outcome_held(*, admission_receipt_ref: str, evidence_ref: str, observed: str, hb_epoch: Any) -> dict[str, Any]:
    """A sealed HELD observation: the decision's later observed result (evidence_ref, a ledger receipt) shows it held."""
    wi.epoch_check(hb_epoch, "admission_outcome_held")
    if not (wi._str(admission_receipt_ref) and wi._str(evidence_ref) and wi._str(observed)):
        raise _refusal("ADMISSION_OUTCOME_NOT_GROUNDED", "HELD_OUTCOME_NAMES_DECISION_AND_EVIDENCE",
                       "admission_receipt_ref, evidence_ref (a ledger receipt) and what was observed",
                       "admission_outcome_held", "resubmit with the evidence; nothing was recorded")
    return wi.seal({"schema": OUTCOME_SCHEMA, "outcome": "HELD", "admission_receipt_ref": admission_receipt_ref,
                    "evidence_ref": evidence_ref, "observed": observed, "hb_epoch": str(hb_epoch)}, "outcome_sha256")


def _sealed(rec: Mapping[str, Any], field: str) -> bool:
    try:
        al.verify_line(rec, field, "admission_miss_rate")
        return True
    except wi.Refusal:
        return False


def admission_miss_rate_e0(decisions: Any, outcomes: Any = (), *, fixture_mode: bool = False,
                           stage: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """decisions: [{receipt_ref, disposition, ledger_seq, change: {repository, head_commit, change_digest?, base?}}] read
    from the organization ledger; outcomes: stegverse.admission_miss.v1 and stegverse.admission_outcome.v1 records.
    ALLOW returns the sealed rate record, the gate evidence and the misses to learn from; otherwise six-field FAIL_CLOSED."""
    e = "admission_miss_rate_e0"
    try:
        d = definition(stage)
    except wi.Refusal as r:
        return {**dict(r.record), "mode": MODE}
    min_obs = d.get("min_observed_outcomes")
    kinds = tuple(d.get("false_admit_miss_kinds") or ())
    excluded, decs = [], []
    for i, dec in enumerate(decisions if isinstance(decisions, list) else []):
        ch = dec.get("change") if isinstance(dec, Mapping) else None
        if not (isinstance(dec, Mapping) and dec.get("disposition") in ("ALLOW", "DENY", "FAIL_CLOSED")
                and isinstance(dec.get("ledger_seq"), int) and isinstance(ch, Mapping)):
            excluded.append({"index": i, "reason": "DECISION_MALFORMED"}); continue
        if not _ledgered(dec.get("receipt_ref"), fixture_mode):
            excluded.append({"index": i, "reason": "DECISION_NOT_LEDGERED"}); continue
        decs.append(dec)
    misses, held, bad_outcomes = {}, {}, []
    for j, o in enumerate(outcomes if isinstance(outcomes, list) else []):
        schema = o.get("schema") if isinstance(o, Mapping) else None
        if schema == al.MISS_SCHEMA and _sealed(o, "miss_sha256") and o.get("miss_kind") in kinds \
                and _ledgered(o.get("correcting_ref"), fixture_mode):
            misses.setdefault(o["admission_receipt_ref"], []).append(o)
        elif schema == OUTCOME_SCHEMA and _sealed(o, "outcome_sha256") and o.get("outcome") == "HELD" \
                and _ledgered(o.get("evidence_ref"), fixture_mode):
            held.setdefault(o["admission_receipt_ref"], []).append(o)
        else:
            bad_outcomes.append({"index": j, "schema": schema, "reason": "OUTCOME_NOT_GROUNDED"})
    joined, counted_misses = [], []
    for dec in sorted(decs, key=lambda x: (x["ledger_seq"], x["receipt_ref"])):
        ref, disp, ch = dec["receipt_ref"], dec["disposition"], dec["change"]
        later_allow = [x["receipt_ref"] for x in decs if x["ledger_seq"] > dec["ledger_seq"] and x["disposition"] == "ALLOW"
                       and ch.get("change_digest") and x["change"].get("change_digest") == ch.get("change_digest")
                       and x["change"].get("base") == ch.get("base")]
        if disp == "FAIL_CLOSED":
            out, by = "NOT_APPLICABLE", []
        elif disp == "ALLOW" and ref in misses:
            out, by = "FALSE_ADMIT", [m["miss_sha256"] for m in misses[ref]]
            counted_misses += misses[ref]
        elif disp == "DENY" and later_allow:
            out, by = "FALSE_REFUSAL", later_allow
        elif ref in held:
            out, by = "HELD", [h["outcome_sha256"] for h in held[ref]]
        else:
            out, by = "UNKNOWN", []
        joined.append({"receipt_ref": ref, "disposition": disp, "outcome": out, "by": by,
                       "contradicted_held": out in ("FALSE_ADMIT", "FALSE_REFUSAL") and ref in held})
    counts = {k: sum(1 for j in joined if j["outcome"] == k) for k in OUTCOMES}
    miss_n = counts["FALSE_ADMIT"] + counts["FALSE_REFUSAL"]
    observed = miss_n + counts["HELD"]
    common = {"definition_id": d.get("definition_id"), "definition_sha256": d["definition_sha256"], "counts": counts,
              "decisions_considered": len(decs), "excluded": excluded, "outcomes_not_grounded": bad_outcomes}
    if not isinstance(min_obs, int) or min_obs < 1 or observed < min_obs:
        return _terminal("ADMISSION_MISS_RATE_UNOBSERVED", "ADMISSION_MISS_RATE_IS_COMPUTED_FROM_OBSERVED_OUTCOMES",
                         "at least %s admission decision(s) with an observed outcome: a ledgered stegverse.admission_miss.v1 "
                         "record (correcting_ref a ledger receipt), a ledgered DENY later contradicted by an ALLOW of the same "
                         "change digest at the same base, or a stegverse.admission_outcome.v1 HELD record whose evidence_ref is "
                         "a ledger receipt" % min_obs, e,
                         "re-run on the next organization-ledger append of an admission decision or outcome; the NWI-S3 "
                         "ADMISSION_MISS_RATE predicate stays unobserved meanwhile (no rate is defaulted) and nothing waits",
                         admission_miss_rate="UNKNOWN", **common)
    rate = miss_n / observed
    record = wi.seal({"schema": RECORD_SCHEMA, "mode": MODE, **common, "observed": observed, "misses": miss_n,
                      METRIC: rate, "joined": joined}, "record_digest")
    return {"disposition": "ALLOW", "mode": MODE, METRIC: rate, "observed": observed, "misses": miss_n, "counts": counts,
            "record": record,
            "learning_candidates": al.harvest(sorted(counted_misses, key=lambda m: m["miss_sha256"])),
            "miss_records": sorted(counted_misses, key=lambda m: m["miss_sha256"]),
            "gate_evidence": {PREDICATE: {METRIC: rate, "miss_rate_record_digest": record["record_digest"]}}}


def learn_from_misses(miss_records: Iterable[Mapping[str, Any]], classes: list[dict], scenarios: list[dict], *,
                      known_good: Callable[[str], Mapping[str, Any]], rule_refs: list[dict], declared_by_session: str,
                      hb_epoch: Any) -> dict[str, Any]:
    """Each counted miss -> harvest -> generalize (class rule: predicate gap + surface kind, superseding the current version)
    -> generate -> corpus_append (SCENARIO_CORPUS_APPEND). Per miss: the transition's own outcome (ALLOW with corpus_head, or
    its six-field DENY / FAIL_CLOSED). classes / scenarios are extended in place on ALLOW only."""
    results = []
    for m in miss_records:
        cand = al.harvest([m])[0]
        surface = (cand["surfaces"] or [None])[0]
        try:
            if surface is None:
                raise _refusal("ADMISSION_MISS_SURFACE_UNOBSERVED", "MISS_NAMES_A_TOUCHED_SURFACE_KIND",
                               "the admitted change's touched_surface_kinds", "learn_from_misses",
                                 "re-run with a miss record that names its surface")
            cid = al.class_id_for(cand["failed_predicate"], surface)
            prior = al.latest_classes(classes).get(cid)
            cls = al.generalize(cand, surface=surface, origin_scenarios=["ADMISSION_MISS %s (%s)" % (m["miss_sha256"], m["correcting_ref"])],
                                rule_refs=rule_refs, declared_by_session=declared_by_session,
                                harvest_receipt_ref=m["correcting_ref"], hb_epoch=hb_epoch, prior=prior,
                                class_version=(prior or {}).get("class_version", 0) + 1,
                                supersedes=(prior or {}).get("class_sha256"))
        except wi.Refusal as r:
            results.append({**{k: r.record[k] for k in ("disposition", *SIX)}, "miss_sha256": m["miss_sha256"]}); continue
        have = {s["scenario_id"] for s in scenarios}
        generated = al.generate(cls, known_good(surface), hb_epoch=hb_epoch)
        gen = [s for s in generated if s["scenario_id"] not in have]
        # the observed miss itself, as the class's primary-axis negative carrying the miss as its source
        primary = next((a["field"] for a in cls["mutation_axes"]
                        if a.get("expected_failure_code", cls["expected_failure_code"]) == cls["expected_failure_code"]),
                       cls["mutation_axes"][0]["field"])
        neg = next(s for s in generated if s["generated_from"]["axis"] == primary)
        gen.append(wi.seal({**{k: v for k, v in neg.items() if k != "scenario_sha256"},
                            "scenario_id": "%s/admission-miss/%s" % (cid, m["miss_sha256"].split(":")[1][:16]),
                            "origin": "ADMISSION_MISS",
                            "source": {"class_sha256": cls["class_sha256"], "miss_sha256": m["miss_sha256"],
                                       "admitted_change": m["admitted_change"], "admission_receipt_ref": m["admission_receipt_ref"],
                                       "correcting_ref": m["correcting_ref"], "miss_kind": m["miss_kind"]}}, "scenario_sha256"))
        out = al.corpus_append(classes, scenarios, cls, gen, hb_epoch=hb_epoch)
        if out["disposition"] == "ALLOW":
            classes += out["append_classes"]; scenarios += out["append_scenarios"]
        results.append({**{k: out.get(k) for k in ("disposition", "transition_class", "corpus_head", *SIX) if k in out},
                        "class_id": cid, "miss_sha256": m["miss_sha256"]})
    return {"transition_class": "SCENARIO_CORPUS_APPEND", "results": results}


def witness_admission_miss_rate(case: Mapping[str, Any]) -> dict[str, Any]:
    """Witness entrypoint (operating-modes.json NWI-S3:ADMISSION_MISS_RATE). With through_gate, the produced evidence (bound
    to the case's receipt_ref for the rate record) is evaluated by the NWI-S3 gate, which must itself terminate."""
    out = admission_miss_rate_e0(case.get("decisions"), case.get("outcomes", []), fixture_mode=bool(case.get("fixture_mode")))
    if not case.get("through_gate"):
        return out
    evidence = dict(case.get("other_evidence") or {})
    if out["disposition"] == "ALLOW":
        evidence.update({k: {**v, "receipt_ref": case["rate_record_receipt_ref"]} for k, v in out["gate_evidence"].items()})
    gate = sg.evaluate_gate("NWI-S3", "NWI-S4", evidence, hb_epoch=case.get("hb_epoch"))
    return {**{k: gate[k] for k in gate if k in ("disposition", *SIX)}, "mode": MODE, "producer": out, "gate": gate}
