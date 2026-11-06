"""Operating-mode declaration validator (StegVerse-org/.github#160 issuecomment-6354238464, #163 issuecomment-6354245549).

data/sv-work-items/operating-modes.json declares, for every NWI stage (NWI-S0..NWI-S4), every stage exit-gate predicate and
every SV-LLM path, its lowest supported operating mode on the ladder E0 (ecosystem only, no LLM) < E1 < E2 < E3, the degraded
form at each rung below what it requires, and its E0 terminal state. An item with no E0 terminal is a class B (missing
capability) gap under the owning goal; validate() derives those gaps from the declaration and refuses when the declaration's
own class_b records do not match. Pure over the supplied documents: stdlib, no clock, no network, no LLM.

An e0_terminal is proven, never trusted as a flag (#163 class B closure): an item either declares a witness
{entrypoint: resident-runtime/<module>.py::<function>, cases: data/sv-work-items/e0-witnesses/<file>.json, cases_sha256} that
validate() executes, every case reaching its expected disposition within the declared dispositions at mode E0 with six fields
on every non-ALLOW (and at least one non-ALLOW case), or binds its terminal to an external component pinned as
<org>/<repo>@<40-hex commit> whose own suite exercises it. Every non-final stage's gate is exercised the same way:
resident-runtime/stage_gate.py::evaluate_gate with no evidence must terminate as a six-field non-ALLOW naming every exit
predicate, with a code the stage declares.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
DECLARATION = ROOT / "data/sv-work-items/operating-modes.json"
STAGES_DIR = ROOT / "data/sv-work-items/stages"
SCHEMA = "stegverse.nwi-operating-modes/v1"
OWNING_GOAL = "StegVerse-org/.github#163"
ENTRY = "resident-runtime/sv_operating_modes.py::validate"
MODES = ("E0", "E1", "E2", "E3")
NONE = "NONE"
UNKNOWN = "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"
SIX = ("disposition", "failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
DISPOSITIONS = {"ALLOW", "DENY", "FAIL_CLOSED", "UNDECIDABLE"}
PROVIDERS = re.compile(r"\b(grok|claude|chatgpt|openai|anthropic|xai|gemini|gpt-?[0-9])\b", re.I)
PIN = re.compile(r"\b[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+@[0-9a-f]{40}\b")
WITNESS_ENTRY = re.compile(r"^resident-runtime/(?P<mod>[a-z0-9_]+)\.py::(?P<fn>[a-z_][a-z0-9_]*)$")
WITNESS_CASES = re.compile(r"^data/sv-work-items/e0-witnesses/[a-z0-9][a-z0-9._-]*\.json$")
WITNESS_SCHEMA = "stegverse.nwi-e0-witness-cases/v1"
OWNER_GATE = re.compile(r"owner must act|handoff_ready by owner|human approval|owner merge|independent review", re.I)


def refusal(disposition: str, code: str, predicate: str, repair: str, nxt: str, **detail: Any) -> dict[str, Any]:
    return {"disposition": disposition, "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": ENTRY, "owning_existing_goal": OWNING_GOAL,
            "next_attempt": nxt, **detail}


def _entry(entry: str, root: Path):
    m = WITNESS_ENTRY.match(entry)
    path = root / "resident-runtime" / (m["mod"] + ".py")
    mod = sys.modules.get(m["mod"])
    if mod is None or Path(getattr(mod, "__file__", "")).resolve() != path.resolve():
        spec = importlib.util.spec_from_file_location(m["mod"], path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[m["mod"]] = mod
        spec.loader.exec_module(mod)
    return getattr(mod, m["fn"])


def exercise_witness(name: str, e0: Mapping[str, Any], root: Path = ROOT) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Execute an item's declared witness cases; refusals, and a summary of what was exercised."""
    w = e0.get("witness")

    def unbound(why: str, **d: Any) -> tuple[list[dict[str, Any]], None]:
        return [refusal("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_UNBOUND", "E0_TERMINAL_IS_EXERCISED_NOT_FLAGGED",
                        "witness = {entrypoint: resident-runtime/<module>.py::<function>, cases: "
                        "data/sv-work-items/e0-witnesses/<file>.json, cases_sha256: sha256:<hex of the file bytes>}; " + why,
                        "re-run validate", item=name, **d)], None

    if not (isinstance(w, Mapping) and isinstance(w.get("entrypoint"), str) and WITNESS_ENTRY.match(w["entrypoint"])
            and isinstance(w.get("cases"), str) and WITNESS_CASES.match(w["cases"])):
        return unbound("the witness is malformed")
    path = root / w["cases"]
    if not path.is_file():
        return unbound("the cases file is absent", cases=w["cases"])
    raw = path.read_bytes()
    if w.get("cases_sha256") != "sha256:" + hashlib.sha256(raw).hexdigest():
        return unbound("the cases file does not match cases_sha256", cases=w["cases"])
    try:
        doc = json.loads(raw)
        fn = _entry(w["entrypoint"], root)
    except Exception as exc:  # noqa: BLE001 - any failure to load is an unproven terminal
        return unbound("the cases or entrypoint do not load: " + type(exc).__name__, cases=w["cases"])
    cases = doc.get("cases") if isinstance(doc, Mapping) else None
    if not (doc.get("schema") == WITNESS_SCHEMA and doc.get("item") == name and isinstance(cases, list) and cases):
        return unbound("the cases file declares schema " + WITNESS_SCHEMA + ", item " + name + " and at least one case")
    declared, codes = set(e0["dispositions"]), e0.get("non_allow_codes")
    bad, seen = [], []

    def failed(case_id: Any, why: str, **d: Any) -> None:
        bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_FAILED", "E0_TERMINAL_IS_EXERCISED_NOT_FLAGGED",
                           "the witness case must reach its expected E0 terminal: " + why, "repair the component or the "
                           "declaration, then re-run validate", item=name, case_id=case_id, **d))

    for c in cases:
        cid = c.get("case_id") if isinstance(c, Mapping) else None
        expect = c.get("expect") if isinstance(c, Mapping) else None
        if not (isinstance(cid, str) and isinstance(expect, Mapping) and expect.get("disposition") and isinstance(c.get("input"), Mapping)):
            failed(cid, "a case is {case_id, input, expect: {disposition, ...}}"); continue
        try:
            out = fn(c["input"])
        except Exception as exc:  # noqa: BLE001 - an exception is not a terminal state
            failed(cid, "the entrypoint raised " + type(exc).__name__ + " instead of returning a disposition"); continue
        if not isinstance(out, Mapping) or out.get("disposition") not in declared:
            failed(cid, "the outcome disposition is not one of the declared dispositions",
                   got=out.get("disposition") if isinstance(out, Mapping) else None); continue
        if out.get("mode") != MODES[0]:
            failed(cid, "the outcome was not produced at mode E0", got=out.get("mode")); continue
        if out["disposition"] != "ALLOW":
            if not all(isinstance(out.get(k), str) and out[k].strip() for k in SIX):
                failed(cid, "a non-ALLOW outcome carries six fields"); continue
            if isinstance(codes, list) and out["failure_code"] not in codes:
                failed(cid, "the failure code is not in the declared non_allow_codes", got=out["failure_code"]); continue
        diff = {k: {"expected": v, "got": out.get(k)} for k, v in expect.items() if out.get(k) != v}
        if diff:
            failed(cid, "the outcome differs from the case's expectation", diff=diff); continue
        seen.append((cid, out["disposition"], out.get("failure_code")))
    if not bad and all(d == "ALLOW" for _, d, _ in seen):
        failed(None, "at least one case reaches a non-ALLOW terminal (the FAIL_CLOSED path is exercised, not assumed)")
    if bad:
        return bad, None
    return [], {"item": name, "entrypoint": w["entrypoint"], "cases": len(seen),
                "outcomes": [{"case_id": i, "disposition": d, "failure_code": f} for i, d, f in seen]}


def exercise_stage_gate(sid: str, target: str, predicates: list[str], e0: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The stage's gate evaluation with no evidence terminates as a six-field non-ALLOW naming every exit predicate."""
    try:
        sg = sys.modules.get("stage_gate") or _load_stage_gate()
        out = sg.evaluate_gate(sid, target, {}, hb_epoch="32")
    except Exception as exc:  # noqa: BLE001
        out = {"exception": type(exc).__name__}
    codes = e0.get("non_allow_codes") if isinstance(e0.get("non_allow_codes"), list) else []
    ok = (out.get("disposition") in ("DENY", "FAIL_CLOSED") and all(isinstance(out.get(k), str) and out[k] for k in SIX)
          and out.get("failure_code") in codes and sorted(out.get("unobserved") or []) == sorted(predicates))
    if ok:
        return []
    return [refusal("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_FAILED", "E0_TERMINAL_IS_EXERCISED_NOT_FLAGGED",
                    "resident-runtime/stage_gate.py::evaluate_gate(" + sid + ", " + target + ", {}) must terminate as a "
                    "six-field non-ALLOW with a declared non_allow_code naming every exit predicate", "re-run validate",
                    stage=sid, got={k: out.get(k) for k in ("disposition", "failure_code", "unobserved", "exception")})]


def _load_stage_gate():
    spec = importlib.util.spec_from_file_location("stage_gate", ROOT / "resident-runtime/stage_gate.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["stage_gate"] = mod
    spec.loader.exec_module(mod)
    return mod


def load_stage_predicates(directory: Path = STAGES_DIR) -> dict[str, list[str]]:
    out = {}
    for p in sorted(Path(directory).glob("NWI-S*.json")):
        m = json.loads(p.read_text())
        out[m["stage_id"]] = [g["predicate"] for g in m.get("exit_gate", [])]
    return out


def _strings(v: Any):
    if isinstance(v, str):
        yield v
    elif isinstance(v, Mapping):
        for k, x in v.items():
            yield str(k)
            yield from _strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from _strings(x)


def _item_problems(where: str, it: Any, witnesses: list | None = None) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Structural refusals for one item, and its derived class B gap (or None). With `witnesses` (a list), the item's E0
    terminal is also proven: its witness is executed (summary appended) or its component is pinned externally."""
    bad: list[dict[str, Any]] = []
    if not isinstance(it, Mapping) or not isinstance(it.get("id"), str):
        return [refusal("FAIL_CLOSED", "OPERATING_MODE_ITEM_MALFORMED", "EVERY_ITEM_HAS_AN_ID", "give the item a string id",
                        "re-run validate", item=where)], None
    name = "%s:%s" % (where, it["id"])
    req, low, deg, e0 = it.get("requires_llms"), it.get("lowest_supported_mode"), it.get("degraded_forms"), it.get("e0_terminal")
    if not (req == UNKNOWN or (isinstance(req, int) and not isinstance(req, bool) and 0 <= req <= 3)):
        bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_REQUIREMENT_MALFORMED", "REQUIRES_LLMS_IS_A_LADDER_COUNT",
                           "requires_llms is 0..3 or " + UNKNOWN, "re-run validate", item=name))
    elif isinstance(req, int) and req > 1:
        bad.append(refusal("DENY", "OPERATING_MODE_REQUIRES_MORE_THAN_ONE_LLM", "AT_MOST_ONE_LLM",
                           "name a form that needs at most one LLM; deterministic verifiers plus ledger receipts stand in for the rest",
                           "re-run validate", item=name, requires_llms=req))
    if low not in MODES + (NONE,):
        bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_UNDECLARED", "LOWEST_SUPPORTED_MODE_DECLARED",
                           "declare lowest_supported_mode as one of E0..E3 (or NONE with a class_b record)", "re-run validate", item=name))
    if not isinstance(deg, Mapping) or any(k not in MODES for k in deg):
        bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_DEGRADED_FORMS_MALFORMED", "DEGRADED_FORM_PER_RUNG",
                           "degraded_forms maps ladder modes to the form used at that rung", "re-run validate", item=name))
        deg = {}
    for s in _strings({k: it.get(k) for k in ("degraded_forms", "e0_terminal", "lowest_supported_mode", "requires_llms")}):
        if PROVIDERS.search(s):
            bad.append(refusal("DENY", "OPERATING_MODE_REQUIRES_SPECIFIC_PROVIDER", "NO_PROVIDER_REQUIREMENT",
                               "state the requirement as an LLM count; providers are optional manifest-declared layers",
                               "re-run validate", item=name, text=s))
            break
    for s in _strings(it):
        if OWNER_GATE.search(s):
            bad.append(refusal("DENY", "OPERATING_MODE_OWNER_MUST_ACT", "NO_OWNER_MUST_ACT",
                               "convert the human-gated phrasing into a manifest transition", "re-run validate", item=name, text=s))
            break
    if isinstance(req, int) and isinstance(low, str) and low in MODES:
        need = MODES.index(low)
        if need > req:
            bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_INCONSISTENT", "LOWEST_MODE_NOT_ABOVE_REQUIREMENT",
                               "lowest_supported_mode needs no more LLMs than requires_llms", "re-run validate", item=name))
        missing = [m for m in MODES[:need] if m not in deg]
        if missing:
            bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_DEGRADED_FORM_MISSING", "DEGRADED_FORM_PER_RUNG",
                               "name the degraded form at " + ", ".join(missing), "re-run validate", item=name, missing=missing))
    if e0 is not None:
        disp = e0.get("dispositions") if isinstance(e0, Mapping) else None
        if not (isinstance(disp, list) and disp and set(disp) <= DISPOSITIONS and isinstance(e0.get("by"), str) and e0["by"].strip()):
            bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_E0_TERMINAL_MALFORMED", "E0_TERMINAL_IS_A_DISPOSITION",
                               "e0_terminal = {dispositions: [ALLOW|DENY|FAIL_CLOSED|UNDECIDABLE...], by: <deterministic component>}",
                               "re-run validate", item=name))
    if witnesses is not None and isinstance(e0, Mapping) and low in MODES and not bad:
        if "witness" in e0:
            b, summary = exercise_witness(name, e0)
            bad += b
            if summary:
                witnesses.append(summary)
        elif not any(isinstance(x, str) and PIN.search(x) for x in (e0.get("by"), it.get("source"))):
            bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_E0_TERMINAL_UNPROVEN", "E0_TERMINAL_IS_EXERCISED_NOT_FLAGGED",
                               "declare an executed witness for the E0 terminal, or pin the component that produces it as "
                               "<org>/<repo>@<40-hex commit> in by or source", "re-run validate", item=name))
    gap = None
    if e0 is None or low == NONE:
        gap = {"item": name, "failure_code": "OPERATING_MODE_E0_TERMINAL_MISSING"}
        cb = it.get("class_b")
        if not (isinstance(cb, Mapping) and all(isinstance(cb.get(k), str) and cb[k].strip() for k in SIX)
                and cb["disposition"] == "FAIL_CLOSED" and cb["owning_existing_goal"] == OWNING_GOAL
                and cb["failure_code"] == "OPERATING_MODE_E0_TERMINAL_MISSING"):
            bad.append(refusal("FAIL_CLOSED", "CLASS_B_RECORD_INCOMPLETE", "E0_TERMINAL_OR_CLASS_B",
                               "an item with no E0 terminal carries a six-field class_b record (FAIL_CLOSED "
                               "OPERATING_MODE_E0_TERMINAL_MISSING, owning goal " + OWNING_GOAL + ") with a conforming resolution",
                               "re-run validate", item=name))
        if e0 is not None or low != NONE:
            bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_INCONSISTENT", "E0_TERMINAL_OR_CLASS_B",
                               "an item without an E0 terminal declares lowest_supported_mode NONE, and vice versa",
                               "re-run validate", item=name))
        if isinstance(cb, Mapping):
            gap["class_b"] = dict(cb)
    elif it.get("class_b") is not None:
        bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_INCONSISTENT", "E0_TERMINAL_OR_CLASS_B",
                           "drop the class_b record: the item declares an E0 terminal", "re-run validate", item=name))
    return bad, gap


def validate(doc: Any, stage_predicates: Mapping[str, list[str]] | None = None, *, exercise: bool = True) -> dict[str, Any]:
    """ALLOW when every item has an E0 terminal, proven by exercising it (exercise=True: witnesses run, stage gates
    evaluated); FAIL_CLOSED OPERATING_MODE_E0_TERMINAL_MISSING listing the class B gaps when the declaration is well-formed
    but some item has none; the first structural refusal otherwise. exercise=False checks the declaration shape only."""
    stage_predicates = load_stage_predicates() if stage_predicates is None else stage_predicates
    if not isinstance(doc, Mapping) or doc.get("schema") != SCHEMA or doc.get("owning_goal") != OWNING_GOAL:
        return refusal("FAIL_CLOSED", "OPERATING_MODE_DECLARATION_MALFORMED", "DECLARATION_HAS_SCHEMA",
                       "schema " + SCHEMA + " and owning_goal " + OWNING_GOAL, "re-run validate")
    ladder = doc.get("ladder")
    if not (isinstance(ladder, list) and [(r.get("mode"), r.get("llms")) for r in ladder if isinstance(r, Mapping)]
            == [(m, i) for i, m in enumerate(MODES)]):
        return refusal("FAIL_CLOSED", "OPERATING_MODE_LADDER_MALFORMED", "LADDER_IS_E0_TO_E3",
                       "ladder = E0 (0 LLMs), E1 (1), E2 (2), E3 (3) in that order", "re-run validate")
    bad: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    witnesses: list[dict[str, Any]] | None = [] if exercise else None
    stage_order = sorted(stage_predicates)
    stages = doc.get("stages") if isinstance(doc.get("stages"), list) else []
    ids = [s.get("stage_id") for s in stages if isinstance(s, Mapping)]
    if sorted(ids) != sorted(stage_predicates) or len(set(ids)) != len(ids):
        bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_STAGE_COVERAGE", "EVERY_STAGE_DECLARES_ITS_LOWEST_MODE",
                           "one entry per stage manifest", "re-run validate",
                           missing=sorted(set(stage_predicates) - set(ids)), extra=sorted(set(ids) - set(stage_predicates))))
    for s in stages:
        if not isinstance(s, Mapping) or s.get("stage_id") not in stage_predicates:
            continue
        sid = s["stage_id"]
        preds = s.get("predicates") if isinstance(s.get("predicates"), list) else []
        got = [p.get("id") for p in preds if isinstance(p, Mapping)]
        if sorted(got) != sorted(stage_predicates[sid]) or len(set(got)) != len(got):
            bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_PREDICATE_COVERAGE", "EVERY_GATE_PREDICATE_DECLARES_ITS_LOWEST_MODE",
                               "one entry per exit_gate predicate of " + sid, "re-run validate", stage=sid,
                               missing=sorted(set(stage_predicates[sid]) - set(got)), extra=sorted(set(got) - set(stage_predicates[sid]))))
        stage_gaps = []
        for p in preds:
            b, g = _item_problems(sid, p, witnesses)
            bad += b
            if g:
                stage_gaps.append(g)
        gaps += stage_gaps
        if s.get("lowest_supported_mode") not in MODES or not isinstance(s.get("e0_terminal"), Mapping):
            bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_UNDECLARED", "EVERY_STAGE_DECLARES_ITS_LOWEST_MODE",
                               "declare the stage's lowest_supported_mode and its gate's e0_terminal", "re-run validate", stage=sid))
        elif exercise and stage_order.index(sid) + 1 < len(stage_order):
            b = exercise_stage_gate(sid, stage_order[stage_order.index(sid) + 1], stage_predicates[sid], s["e0_terminal"])
            bad += b
            if not b:
                witnesses.append({"item": sid + ":STAGE_GATE", "entrypoint": "resident-runtime/stage_gate.py::evaluate_gate",
                                  "cases": 1})
        if s.get("exit_passable_at_e0") is not (not stage_gaps):
            bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_INCONSISTENT", "STAGE_EVALUATION_VS_EXIT",
                               "exit_passable_at_e0 is true exactly when every exit predicate has an E0 terminal", "re-run validate",
                               stage=sid, derived=not stage_gaps))
    paths = doc.get("sv_llm_paths")
    if not (isinstance(paths, list) and paths):
        bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_PATHS_UNDECLARED", "EVERY_SV_LLM_PATH_DECLARES_ITS_LOWEST_MODE",
                           "declare sv_llm_paths", "re-run validate"))
        paths = []
    seen = set()
    for p in paths:
        b, g = _item_problems("sv_llm_paths", p, witnesses)
        if isinstance(p, Mapping):
            if p.get("id") in seen:
                b.append(refusal("FAIL_CLOSED", "OPERATING_MODE_PATH_DUPLICATE", "ONE_ENTRY_PER_PATH", "drop the duplicate",
                                 "re-run validate", item=p.get("id")))
            seen.add(p.get("id"))
            if not (isinstance(p.get("source"), str) and p["source"].strip()):
                b.append(refusal("FAIL_CLOSED", "OPERATING_MODE_PATH_SOURCE_UNBOUND", "PATH_NAMES_ITS_SOURCE",
                                 "name the path's source as <repo>@<commit>:<path> or its PR", "re-run validate", item=p.get("id")))
        bad += b
        if g:
            gaps.append(g)
    if bad:
        first = dict(bad[0])
        first["refusals"] = bad
        return first
    if gaps:
        return refusal("FAIL_CLOSED", "OPERATING_MODE_E0_TERMINAL_MISSING", "E0_TERMINAL_OR_CLASS_B",
                       "build each listed item's E0 terminal (its class_b record names the conforming resolution)",
                       "re-run validate after each class B item lands", class_b=gaps)
    out = {"disposition": "ALLOW", "schema": SCHEMA, "mode": MODES[0],
           "items_checked": sum(len(s.get("predicates", [])) for s in stages) + len(paths)}
    if exercise:
        out["exercised"] = witnesses
    return out


def main() -> int:
    out = validate(json.loads(DECLARATION.read_text()))
    print(json.dumps(out, indent=1, sort_keys=True))
    # class B gaps are declared, reported state, not a structural failure of the declaration
    return 0 if out["disposition"] == "ALLOW" or out["failure_code"] == "OPERATING_MODE_E0_TERMINAL_MISSING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
