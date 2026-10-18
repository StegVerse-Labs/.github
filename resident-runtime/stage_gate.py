"""STAGE_GATE transition (STAGE_GATES_ARE_ADMITTED_TRANSITIONS), NWI-S0..NWI-S4.

A stage is entered only by its own admitted transition (STAGE_<id>_ADMITTED)
with a ledger receipt. The gate evaluated is the current stage's exit_gate,
read from data/sv-work-items/stages/<stage>.json; thresholds come only from
that manifest (a null threshold FAIL_CLOSES STAGE_THRESHOLD_UNDECLARED, never a
default). No skipping: the target is exactly the next ordinal. An observed
gate failure drops back one stage (FAIL_CLOSED STAGE_REGRESSION, floor
NWI-S0); unobserved evidence is FAIL_CLOSED STAGE_EVIDENCE_UNOBSERVED with no
move (UNKNOWN_NEVER_YIELDS_PASS, but nothing failed). The outcome is recorded
through sv_work_items.record (existing emitter) and can be carried as an
organization transition request (.stegverse/transition-requests/). Stdlib, no clock.

STAGE_GATE_RECEIPT_DERIVES_NATIVE_ISSUE (Q-SV-NATIVE-BOOTSTRAP, decided by invariant): a manifest declares its gate as a
check (exit_gate_check) the NWI-S1 verifier (SV-LLM/.github#46) emits and the org writer (Labs#3255/#3270) appends. A
failing gate receipt is then a ledgered failing check receipt, and sv_work_items.derive_issue_from_check_receipt derives
the NATIVE SV_ISSUE from it unchanged (check id from the manifest, surface = the manifest). This module evaluates the gate;
it never mints or ledgers the receipt.
"""
from __future__ import annotations

import importlib.util
import sys
import json
import operator
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
wi = sys.modules.get("sv_work_items")
if wi is None:  # one module instance, so a Refusal raised anywhere is the same class
    _s = importlib.util.spec_from_file_location("sv_work_items", ROOT / "resident-runtime/sv_work_items.py")
    wi = importlib.util.module_from_spec(_s)
    sys.modules["sv_work_items"] = wi
    _s.loader.exec_module(wi)
STAGES_DIR = ROOT / "data/sv-work-items/stages"
SCHEMA = "stegverse.nwi-stage-manifest/v1"
COMPARATORS = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt, "==": operator.eq}
ENTRY = "resident-runtime/stage_gate.py::evaluate_gate"


def load_stages(directory: Path = STAGES_DIR) -> list[dict[str, Any]]:
    stages = sorted((json.loads(p.read_text()) for p in Path(directory).glob("NWI-S*.json")), key=lambda m: m["ordinal"])
    if [m.get("ordinal") for m in stages] != list(range(len(stages))) or any(m.get("schema") != SCHEMA for m in stages):
        raise wi._fail("STAGE_MANIFESTS_NOT_CONTIGUOUS", "STAGE_MANIFESTS_ARE_ORDERED_FROM_ZERO",
                       "one manifest per ordinal 0..n with schema " + SCHEMA, "load_stages")
    return stages


def gate_check(stage: Mapping[str, Any]) -> dict[str, Any] | None:
    """The check a stage manifest declares for its gate, or None when the manifest declares none. A declaration whose
    minter or verifier_ref is not the NWI-S1 verifier is not a gate check (STAGE_GATE_CHECK_NOT_S1_EMITTED)."""
    c = stage.get("exit_gate_check")
    if c is None:
        return None
    oc = c.get("offline_command") if isinstance(c, Mapping) else None
    if not isinstance(oc, Mapping) or oc.get("verifier_ref") != wi.S1_VERIFIER_REF or wi.S1_VERIFIER_REF not in str(c.get("minter")) \
            or oc.get("verifier_builtin") != c.get("check_id") or c.get("check_id") not in wi.GATE_CHECKS:
        raise _refusal("STAGE_GATE_CHECK_NOT_S1_EMITTED", wi.STAGE_GATE_ISSUE_INVARIANT,
                       "declare exit_gate_check as a built-in of the NWI-S1 verifier (" + wi.S1_VERIFIER_REF + ") appended by the org writer",
                       "re-evaluate once the manifest declares the gate check", stage_id=stage.get("stage_id"))
    return {"check_id": c["check_id"], "verifier_ref": oc["verifier_ref"], "surface": c["surface"],
            "declared_in": wi.GATE_CHECKS[c["check_id"]]["declared_in"]}


def _refusal(code: str, predicate: str, repair: str, nxt: str, **d: Any) -> wi.Refusal:
    r = wi.Refusal("FAIL_CLOSED", code, predicate, repair, "evaluate_gate", nxt, **d)
    r.record["retry_entrypoint"] = ENTRY
    return r


def evaluate_gate(current_stage: str, target_stage: str, evidence: Mapping[str, Any], *, hb_epoch: Any,
                  stages: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Returns {disposition, stage_before, stage_after, entry_transition|failure six fields, record}."""
    out_base = {"transition_class": "STAGE_GATE", "stage_before": current_stage, "stage_after": current_stage}
    try:
        wi.epoch_check(hb_epoch, "evaluate_gate")
        stages = stages if stages is not None else load_stages()
        by = {m["stage_id"]: m for m in stages}
        cur, tgt = by.get(current_stage), by.get(target_stage)
        if cur is not None:
            gc = gate_check(cur)
            out_base["gate_check_id"] = gc["check_id"] if gc else None  # the check id a failing gate receipt carries
        if cur is None or tgt is None:
            raise _refusal("STAGE_MANIFEST_ABSENT", "STAGE_IS_DECLARED_BY_MANIFEST", "declare the stage manifest",
                           "re-evaluate once the manifest is committed", unknown=[s for s in (current_stage, target_stage) if s not in by])
        if tgt["ordinal"] != cur["ordinal"] + 1:
            r = wi.Refusal("DENY", "STAGE_SKIP" if tgt["ordinal"] > cur["ordinal"] else "STAGE_NOT_FORWARD",
                           "STAGES_ARE_NEVER_SKIPPED", "request the next stage only: " + (stages[cur["ordinal"] + 1]["stage_id"]
                           if cur["ordinal"] + 1 < len(stages) else "none (final stage)"), "evaluate_gate",
                           "request the next ordinal")
            r.record["retry_entrypoint"] = ENTRY
            raise r
        failed, unobserved, undeclared = [], [], []
        for g in cur["exit_gate"]:
            ev = evidence.get(g["predicate"]) or {}
            if not wi._str(ev.get("receipt_ref")):
                unobserved.append(g["predicate"]); continue
            if g["evidence"] == "metric":
                t = g.get("threshold") or {}
                if t.get("value") is None or t.get("comparator") not in COMPARATORS:
                    undeclared.append(g["predicate"]); continue
                v = ev.get(t["metric"])
                if not isinstance(v, (int, float)) or isinstance(v, bool):
                    unobserved.append(g["predicate"]); continue
                if not COMPARATORS[t["comparator"]](v, t["value"]):
                    failed.append(g["predicate"])
            elif ev.get("disposition") != "ALLOW":
                failed.append(g["predicate"])
        if not cur["exit_gate"]:
            undeclared.append("EXIT_GATE_EMPTY")
        if failed:
            back = stages[max(cur["ordinal"] - 1, 0)]["stage_id"]
            r = _refusal("STAGE_REGRESSION", "STAGE_GATE_PASSES", "repair the failed gate predicates at " + back + ", then re-enter " + current_stage,
                         "re-run " + stages[max(cur["ordinal"] - 1, 0)]["entry_transition"] + " gate evidence", failed=failed)
            return {**out_base, **r.record, "stage_after": back, "record": {"stage_id": back, "regressed_from": current_stage}}
        if undeclared:
            raise _refusal("STAGE_THRESHOLD_UNDECLARED", "THRESHOLD_IS_DECLARED_IN_STAGE_MANIFEST",
                           "declare the threshold in data/sv-work-items/stages/" + current_stage + ".json (never defaulted here)",
                           "re-evaluate once the manifest declares it", undeclared=undeclared)
        if unobserved:
            raise _refusal("STAGE_EVIDENCE_UNOBSERVED", "UNKNOWN_NEVER_YIELDS_PASS", "a receipted outcome for every exit predicate",
                           "re-evaluate with the receipts; nothing moved", unobserved=unobserved)
        return {**out_base, "disposition": "ALLOW", "stage_after": target_stage, "entry_transition": tgt["entry_transition"],
                "record": {"stage_id": target_stage, "entered_by": tgt["entry_transition"],
                           "evidence": {k: dict(v) for k, v in sorted(evidence.items())}}}
    except wi.Refusal as r:
        return {**out_base, **r.record, "record": {"stage_id": current_stage}}


def transition_request(outcome: Mapping[str, Any], *, owning_goal: str = "StegVerse-org/.github#163") -> dict[str, Any]:
    """The stegverse.organization-transition-request/v1 body that carries the gate outcome to the ledger writer."""
    rid = "NWI-STAGE-GATE-" + outcome["stage_before"] + "-TO-" + str(outcome["record"]["stage_id"])
    return {"schema": "stegverse.organization-transition-request/v1", "request_id": rid, "owning_existing_goal": owning_goal,
            "purpose": "STAGE_GATE outcome (STAGE_GATES_ARE_ADMITTED_TRANSITIONS); records only, no external effect",
            "build_manifest": {"data": {"external_side_effect": False, "request_id": rid, "stage_gate_outcome": dict(outcome)}}}
