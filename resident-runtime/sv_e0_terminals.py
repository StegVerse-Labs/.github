"""E0 (ecosystem-only, no LLM) terminal forms for the operating-mode ladder (StegVerse-org/.github#160
issuecomment-6354238464; #163 issuecomment-6354245549, class B items in #163 issuecomment-6354429866).

Each form reaches a defined, receipt-bound terminal disposition (ALLOW / DENY / FAIL_CLOSED, six fields on every
non-ALLOW) from deterministic components, ledger receipts and manifests only: no LLM, no clock, no network, no external
machine, nothing waits and nothing polls. LLM layers (E1..E3) stay optional and additive; they never gate these forms.

  verdict_agreement_e0     NWI-S2 SV_LLM_VERDICT_AGREEMENT_RATE: the verdict producer at E0 is the NWI-S1 verifier's
                           six-field check receipts per evaluated change (SV-LLM/.github#46); agreement = that verdict
                           equals the ledgered admission disposition for the same change digest. LLM verdicts are
                           counted separately and never move the E0 metric.
  bounded_solve_e0         NWI-S3 W05_TV_TVC_HELD_INVOCATION_ADMITTED, degraded to E0: a work item of a class the
                           ecosystem resolves deterministically (E0_SOLVERS, each an existing component) is resolved at
                           E0; any other item terminates as FAIL_CLOSED PROVIDER_LAYER_NOT_ADMITTED with a deferral record
                           re-evaluated on the next PROVIDER_LAYER_TRANSITION receipt (an append, not a poll).
  verify_respond_terminal  sv_llm_paths ENTITY_RESPOND: re-verifies, from the SV-LLM/sandbox repository-ledger receipts
                           themselves, that a request whose entity surface the pass did not supply terminated in that
                           pass as UNAVAILABLE ENTITY_SURFACE_NOT_SUPPLIED with a six-field FAIL_CLOSED, and that the work
                           completed: hashes, chain links, entity-set digest, contribution id and content digest are all
                           recomputed here, nothing is taken from a flag.
  stage_gate_witness       runs resident-runtime/stage_gate.py::evaluate_gate on a supplied case.

resident-runtime/sv_operating_modes.py::validate exercises these through each item's declared witness cases.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]


def _module(name: str, rel: str):
    m = sys.modules.get(name)
    if m is None:  # one module instance, so a Refusal raised anywhere is the same class
        s = importlib.util.spec_from_file_location(name, ROOT / rel)
        m = importlib.util.module_from_spec(s)
        sys.modules[name] = m
        s.loader.exec_module(m)
    return m


wi = _module("sv_work_items", "resident-runtime/sv_work_items.py")
sg = _module("stage_gate", "resident-runtime/stage_gate.py")

OWNING_GOAL = "StegVerse-org/.github#163"
MODE = "E0"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint", "owning_existing_goal",
       "next_attempt")
DISPOSITIONS = ("ALLOW", "DENY", "FAIL_CLOSED")
VERDICT_SCHEMA = "stegverse.nwi-s2-verdict-agreement/v1"
SOLVE_SCHEMA = "stegverse.nwi-s3-bounded-solving/v1"
LLM_MODES = ("E1", "E2", "E3")
PROVIDER_TRANSITION = "PROVIDER_LAYER_TRANSITION receipt (Labs#3291 / SV-LLM/sandbox#39)"
SANDBOX_REPOSITORY = "SV-LLM/sandbox"
SURFACE_NOT_SUPPLIED = "ENTITY_SURFACE_NOT_SUPPLIED"
CONTRIBUTION_SCHEMA = "sv-llm.contribution/v0.1"


def _terminal(disposition: str, code: str, predicate: str, repair: str, entry: str, nxt: str, **detail: Any) -> dict[str, Any]:
    return {"disposition": disposition, "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": "resident-runtime/sv_e0_terminals.py::" + entry,
            "owning_existing_goal": OWNING_GOAL, "next_attempt": nxt, "mode": MODE, **detail}


def _ledgered(ref: Any, fixture_mode: bool) -> bool:
    """A receipt counts as ledgered only by an organization-ledger receipt ref; a fixture ref counts only in fixture_mode."""
    if not isinstance(ref, str):
        return False
    if wi.LEDGER_RECEIPT_REF.match(ref):
        return True
    return fixture_mode and wi.FIXTURE_REF_MARK in ref


# -- NWI-S2: verdict agreement at E0 ------------------------------------------------------------------------------------
def ecosystem_verdict(dispositions: Iterable[str]) -> str:
    """The single ecosystem verdict over a change's verifier check receipts: FAIL_CLOSED if any check failed closed,
    else DENY if any denied, else ALLOW."""
    ds = list(dispositions)
    return "FAIL_CLOSED" if "FAIL_CLOSED" in ds else "DENY" if "DENY" in ds else "ALLOW"


def verdict_agreement_e0(evaluations: Any, *, llm_verdicts: Any = (), fixture_mode: bool = False) -> dict[str, Any]:
    """evaluations: [{change_digest, check_receipts: [{receipt: <stegverse.sv_check_receipt.v1>, receipt_ref}],
    admission: {change_digest, disposition, receipt_ref}}]. Returns ALLOW with the verdict record (agreed, evaluated,
    agreement_rate and the gate evidence for NWI-S2) when at least one change has both a ledgered verifier verdict and a
    ledgered admission disposition; otherwise FAIL_CLOSED VERDICT_AGREEMENT_EVIDENCE_UNOBSERVED. Never waits."""
    e = "verdict_agreement_e0"
    verdicts, excluded = [], []
    for i, ev in enumerate(evaluations if isinstance(evaluations, list) else []):
        cd = ev.get("change_digest") if isinstance(ev, Mapping) else None
        if not isinstance(cd, str) or not wi.DIGEST.match(cd):
            excluded.append({"index": i, "reason": "CHANGE_DIGEST_MALFORMED"}); continue
        receipts = ev.get("check_receipts")
        if not isinstance(receipts, list) or not receipts:
            excluded.append({"index": i, "change_digest": cd, "reason": "VERIFIER_VERDICT_UNOBSERVED"}); continue
        dispositions, bad = [], None
        for cr in receipts:
            if not isinstance(cr, Mapping) or not _ledgered(cr.get("receipt_ref"), fixture_mode):
                bad = {"reason": "VERIFIER_RECEIPT_NOT_LEDGERED"}; break
            try:
                r = wi.validate_check_receipt(cr.get("receipt"), change={"head": {"change_digest": cd}})
            except wi.Refusal as ref:
                bad = {"reason": "VERIFIER_RECEIPT_REFUSED", "refusal": {k: ref.record[k] for k in ("disposition", *SIX)}}
                break
            dispositions.append(r["disposition"])
        if bad:
            excluded.append({"index": i, "change_digest": cd, **bad}); continue
        adm = ev.get("admission")
        if not (isinstance(adm, Mapping) and adm.get("change_digest") == cd and adm.get("disposition") in DISPOSITIONS
                and _ledgered(adm.get("receipt_ref"), fixture_mode)):
            excluded.append({"index": i, "change_digest": cd, "reason": "ADMISSION_DISPOSITION_UNOBSERVED"}); continue
        v = ecosystem_verdict(dispositions)
        verdicts.append({"change_digest": cd, "verifier_verdict": v, "admission_disposition": adm["disposition"],
                         "agrees": v == adm["disposition"], "check_receipt_refs": [c["receipt_ref"] for c in receipts],
                         "admission_receipt_ref": adm["receipt_ref"]})
    additive = {"llm_verdicts": 0, "llm_agreed_with_admission": 0, "by_mode": {}}
    by_change = {v["change_digest"]: v for v in verdicts}
    for lv in llm_verdicts if isinstance(llm_verdicts, list) else []:
        if isinstance(lv, Mapping) and lv.get("mode") in LLM_MODES and lv.get("change_digest") in by_change \
                and lv.get("disposition") in DISPOSITIONS:
            additive["llm_verdicts"] += 1
            additive["by_mode"][lv["mode"]] = additive["by_mode"].get(lv["mode"], 0) + 1
            additive["llm_agreed_with_admission"] += lv["disposition"] == by_change[lv["change_digest"]]["admission_disposition"]
    if not verdicts:
        return _terminal("FAIL_CLOSED", "VERDICT_AGREEMENT_EVIDENCE_UNOBSERVED", "VERIFY_ONLY_VERDICT_HAS_E0_PRODUCER",
                         "a change with ledgered NWI-S1 verifier check receipts (SV-LLM/.github#46) and a ledgered admission "
                         "disposition for the same change digest", e,
                         "re-run on the next organization-ledger append of a verifier receipt or admission outcome; the "
                         "NWI-S2 gate stays at FAIL_CLOSED STAGE_EVIDENCE_UNOBSERVED meanwhile and nothing waits",
                         excluded=excluded, additive=additive)
    agreed = sum(1 for v in verdicts if v["agrees"])
    record = wi.seal({"schema": VERDICT_SCHEMA, "producer": "NWI-S1 verifier check receipts (SV-LLM/.github#46)",
                      "mode": MODE, "verdicts": sorted(verdicts, key=lambda v: v["change_digest"]), "agreed": agreed,
                      "evaluated": len(verdicts), "excluded": excluded, "additive_llm_layers": additive}, "record_digest")
    return {"disposition": "ALLOW", "mode": MODE, "record": record, "agreed": agreed, "evaluated": len(verdicts),
            "agreement_rate": agreed / len(verdicts),
            "gate_evidence": {"SV_LLM_VERDICT_AGREEMENT_RATE": {"agreement_rate": agreed / len(verdicts),
                                                                "verdict_record_digest": record["record_digest"]}}}


def witness_verdict_agreement(case: Mapping[str, Any]) -> dict[str, Any]:
    """Witness entrypoint. With through_gate, the produced evidence (bound to the case's receipt_ref for the verdict
    record) is evaluated by the NWI-S2 gate, which must itself terminate."""
    out = verdict_agreement_e0(case.get("evaluations"), llm_verdicts=case.get("llm_verdicts", []),
                               fixture_mode=bool(case.get("fixture_mode")))
    if not case.get("through_gate"):
        return out
    evidence = {}
    if out["disposition"] == "ALLOW":
        evidence = {k: {**v, "receipt_ref": case["verdict_record_receipt_ref"]} for k, v in out["gate_evidence"].items()}
    gate = sg.evaluate_gate("NWI-S2", "NWI-S3", evidence, hb_epoch=case.get("hb_epoch"))
    return {**{k: gate[k] for k in gate if k in ("disposition", *SIX)}, "mode": MODE, "producer": out, "gate": gate}


# -- NWI-S3: bounded solving at E0 --------------------------------------------------------------------------------------
def _solve_stage_gate(inp: Mapping[str, Any]) -> dict[str, Any]:
    return sg.evaluate_gate(inp.get("stage"), inp.get("target"), inp.get("evidence") or {}, hb_epoch=inp.get("hb_epoch"))


def _solve_check_receipt(inp: Mapping[str, Any]) -> dict[str, Any]:
    try:
        cd = inp.get("change_digest")
        return {"disposition": "ALLOW", "receipt": wi.validate_check_receipt(
            inp.get("receipt"), change={"head": {"change_digest": cd}} if cd else None)}
    except wi.Refusal as r:
        return dict(r.record)


def _solve_verdict_agreement(inp: Mapping[str, Any]) -> dict[str, Any]:
    return verdict_agreement_e0(inp.get("evaluations"), fixture_mode=bool(inp.get("fixture_mode")))


# problem class -> the existing deterministic component that resolves it at E0
E0_SOLVERS: dict[str, Callable[[Mapping[str, Any]], dict[str, Any]]] = {
    "STAGE_GATE_EVALUATION": _solve_stage_gate,
    "SV_CHECK_RECEIPT_VALIDATION": _solve_check_receipt,
    "VERDICT_AGREEMENT": _solve_verdict_agreement,
}


def bounded_solve_e0(item: Any) -> dict[str, Any]:
    """item: {work_item_id, problem_class, input}. Resolved at E0 by the class's deterministic component, whose own
    disposition (six fields on non-ALLOW) is the item's terminal; any other class terminates as FAIL_CLOSED
    PROVIDER_LAYER_NOT_ADMITTED with a deferral record for the E1 form (W05). Never waits for a provider."""
    e = "bounded_solve_e0"
    if not (isinstance(item, Mapping) and wi._str(item.get("work_item_id")) and wi._str(item.get("problem_class"))
            and isinstance(item.get("input"), Mapping)):
        return _terminal("FAIL_CLOSED", "BOUNDED_SOLVING_ITEM_MALFORMED", "WORK_ITEM_DECLARES_ID_CLASS_AND_INPUT",
                         "{work_item_id, problem_class, input}", e, "resubmit the corrected work item; nothing was solved")
    digest = wi.sha({k: item[k] for k in ("work_item_id", "problem_class", "input")})
    solver = E0_SOLVERS.get(item["problem_class"])
    if solver is None:
        deferral = wi.seal({"schema": SOLVE_SCHEMA, "work_item_id": item["work_item_id"], "work_item_digest": digest,
                            "problem_class": item["problem_class"], "deferred_to_mode": "E1",
                            "e1_form": "W05_TV_TVC_HELD_INVOCATION_ADMITTED", "resume_on": PROVIDER_TRANSITION},
                           "deferral_digest")
        return _terminal("FAIL_CLOSED", "PROVIDER_LAYER_NOT_ADMITTED", "BOUNDED_SOLVING_HAS_E0_DEGRADED_FORM",
                         "no deterministic component resolves problem class " + item["problem_class"] + " (E0 solvers: "
                         + ", ".join(sorted(E0_SOLVERS)) + ") and no provider layer is admitted", e,
                         "re-evaluated when the next " + PROVIDER_TRANSITION + " is appended (event, not poll); the item is "
                         "terminal at E0 meanwhile", work_item_digest=digest, deferral=deferral)
    out = solver(item["input"])
    disposition = out.get("disposition") if isinstance(out, Mapping) else None
    if disposition not in DISPOSITIONS or (disposition != "ALLOW" and not all(wi._str(out.get(k)) for k in SIX)):
        return _terminal("FAIL_CLOSED", "E0_SOLVER_OUTCOME_NOT_TERMINAL", "BOUNDED_SOLVING_HAS_E0_DEGRADED_FORM",
                         "the E0 solver returns ALLOW, or DENY/FAIL_CLOSED with six fields", e,
                         "repair the solver for " + item["problem_class"], work_item_digest=digest)
    result = {"disposition": disposition, "mode": MODE, "resolved_at_mode": MODE, "work_item_id": item["work_item_id"],
              "work_item_digest": digest, "problem_class": item["problem_class"], "solution": out,
              "solution_digest": wi.sha(out)}
    if disposition != "ALLOW":
        result.update({k: out[k] for k in SIX})
    return result


def witness_bounded_solving(case: Mapping[str, Any]) -> dict[str, Any]:
    return bounded_solve_e0(case.get("item"))


# -- SV-LLM/sandbox respond(): unsupplied entity surface ----------------------------------------------------------------
def entity_set_digest(names: Iterable[str]) -> str:
    """Mirror of SV-LLM/sandbox runtime/work_cycle.py::entity_set_digest (recomputed, not trusted)."""
    return wi.sha(sorted(names))


def unsupplied_contribution_id(work_id: str, entity: str, capability: str, set_digest: str) -> str:
    """Mirror of SV-LLM/sandbox runtime/work_cycle.py::unsupplied_contribution_id."""
    return "surface-not-supplied:" + hashlib.sha256("\0".join((work_id, entity, capability, set_digest)).encode("utf-8")).hexdigest()


def verify_respond_terminal(case: Mapping[str, Any]) -> dict[str, Any]:
    """case: {supplied_entities, receipts: the SV-LLM/sandbox repository-ledger receipts of one work item}. Returns the
    recorded six-field FAIL_CLOSED ENTITY_SURFACE_NOT_SUPPLIED terminal (mode E0) once every derivation is recomputed and
    the work is completed; FAIL_CLOSED RESPOND_E0_TERMINAL_NOT_EVIDENCED naming the failed check otherwise."""
    e = "verify_respond_terminal"

    def no(check: str, **d: Any) -> dict[str, Any]:
        return _terminal("FAIL_CLOSED", "RESPOND_E0_TERMINAL_NOT_EVIDENCED", "EVERY_CONTRIBUTION_REQUEST_REACHES_A_TERMINAL_STATE_AT_E0",
                         "SV-LLM/sandbox receipts showing every unsupplied request recorded as UNAVAILABLE "
                         + SURFACE_NOT_SUPPLIED + " with a six-field FAIL_CLOSED and the work completed", e,
                         "re-run with the receipts of a pass at the pinned SV-LLM/sandbox source", failed_check=check, **d)

    receipts, supplied = case.get("receipts"), case.get("supplied_entities")
    if not (isinstance(receipts, list) and receipts and isinstance(supplied, list) and all(isinstance(s, str) for s in supplied)):
        return no("CASE_SHAPE")
    prev = receipts[0].get("previous_receipt_sha256") if isinstance(receipts[0], Mapping) else None
    for i, r in enumerate(receipts):
        if not isinstance(r, Mapping) or r.get("repository") != SANDBOX_REPOSITORY or r.get("schema") != wi.REPO_RECEIPT_SCHEMA:
            return no("RECEIPT_IS_A_SANDBOX_REPO_RECEIPT", index=i)
        if r.get("receipt_sha256") != wi.sha({k: v for k, v in r.items() if k != "receipt_sha256"}):
            return no("RECEIPT_HASH_RECOMPUTES", index=i)
        if i and r.get("previous_receipt_sha256") != prev:
            return no("RECEIPT_CHAIN_LINKS", index=i)
        prev = r["receipt_sha256"]
    ok = [r for r in receipts if (r.get("evidence") or {}).get("disposition") == "ALLOW"]
    work_ids = {r["evidence"].get("work_id") for r in ok}
    if len(work_ids) != 1:
        return no("ONE_WORK_ITEM")
    work_id = work_ids.pop()
    requested = [(r["evidence"]["entity"], r["evidence"]["capability"]) for r in ok if r["transition_class"] == "CONTRIBUTION_REQUESTED"]
    recorded = {(r["evidence"]["entity"], r["evidence"]["envelope"]["capability"]): r for r in ok
                if r["transition_class"] in ("ENTITY_CONTRIBUTION_RECORDED", "ENTITY_CONTRIBUTION_REFUSED")}
    missing = [p for p in requested if p not in recorded]
    if missing:
        return no("NO_REQUEST_LEFT_OUTSTANDING", outstanding=[list(p) for p in missing])
    set_digest = entity_set_digest(supplied)
    terminals = []
    for entity, capability in requested:
        if entity in supplied:
            continue
        ev = recorded[(entity, capability)]["evidence"]
        env = ev["envelope"]
        rec = env.get("non_success_status_record") or {}
        expect_refs = ["entity-set:" + set_digest]
        if not (env.get("schema") == CONTRIBUTION_SCHEMA and env.get("status") == "UNAVAILABLE" == ev.get("status")
                and env.get("entity") == entity and env.get("work_id") == work_id
                and rec.get("reason_or_failed_predicate") == SURFACE_NOT_SUPPLIED and rec.get("status") == "UNAVAILABLE"
                and env.get("evidence_refs") == expect_refs == rec.get("evidence_refs")
                and env.get("provenance") == rec.get("provenance") and env.get("uncertainty") == rec.get("uncertainty")):
            return no("UNSUPPLIED_ENVELOPE_SHAPE", entity=entity)
        if env.get("contribution_id") != unsupplied_contribution_id(work_id, entity, capability, set_digest) \
                or ev.get("contribution_id") != env["contribution_id"]:
            return no("CONTRIBUTION_ID_RECOMPUTES", entity=entity)
        if env.get("content_digest") != wi.sha(rec) or ev.get("content_digest") != env["content_digest"]:
            return no("CONTENT_DIGEST_RECOMPUTES", entity=entity)
        t = ev.get("e0_terminal") or {}
        if not (t.get("disposition") == "FAIL_CLOSED" and t.get("failure_code") == SURFACE_NOT_SUPPLIED
                and t.get("mode") == MODE and all(wi._str(t.get(k)) for k in SIX)):
            return no("SIX_FIELD_FAIL_CLOSED_RECORDED", entity=entity)
        terminals.append({"entity": entity, "capability": capability, "terminal": dict(t),
                          "repo_receipt_sha256": recorded[(entity, capability)]["receipt_sha256"]})
    if not terminals:
        return no("A_REQUEST_WITH_NO_SUPPLIED_SURFACE")
    classes = [r["transition_class"] for r in ok]
    last_contribution = max(i for i, r in enumerate(ok) if r["transition_class"].startswith("ENTITY_CONTRIBUTION_"))
    if "SANDBOX_WORK_COMPLETED" not in classes[last_contribution:]:
        return no("WORK_COMPLETED_AFTER_THE_TERMINALS")
    first = terminals[0]["terminal"]
    return {"disposition": "FAIL_CLOSED", **{k: first[k] for k in SIX}, "mode": MODE, "work_id": work_id,
            "entity_set_digest": set_digest, "terminals": terminals, "work_completed": True}


# -- stage gate -------------------------------------------------------------------------------------------------------
def stage_gate_witness(case: Mapping[str, Any]) -> dict[str, Any]:
    """case: {stage, target, evidence, hb_epoch}; the gate's own outcome (deterministic, no LLM input) at mode E0."""
    return {**sg.evaluate_gate(case.get("stage"), case.get("target"), case.get("evidence") or {}, hb_epoch=case.get("hb_epoch")),
            "mode": MODE}
