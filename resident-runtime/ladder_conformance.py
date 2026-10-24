"""Ladder-conformance check over the priority goals (StegVerse-org/.github#163; Coordination relay of Rigel, 2026-10-23).

For every predicate and handoff on a goal's path to its sealed finish point, decide whether it has an E0 (ecosystem-only,
no LLM) path and degrades E3 -> E2 -> E1 -> E0 without stopping or requiring an owner action. The conformance standard is
the operating-modes validator (resident-runtime/sv_operating_modes.py, Labs#3308): its ladder, six fields, provider and
owner-gate patterns, pin form and refusal codes are imported, not restated, and every item that declares an E0 terminal is
also run through its _item_problems. This module adds only what a cross-repository goal needs on top of it:

* an E0 terminal must be bound to an OBSERVED run of the pinned component (observations/<goal>.observations.json, produced
  by scripts/ladder_conformance.py observe against the exact commits), else OPERATING_MODE_E0_WITNESS_UNBOUND;
* every rung E3..E0 names its form (LADDER_RUNG_FORM_MISSING);
* an observed owner action on the path is DENY OPERATING_MODE_OWNER_MUST_ACT, and an observed external machine requirement
  is DENY LADDER_EXTERNAL_MACHINE_REQUIRED;
* an item whose ALLOW is reachable only by editing code (no evidence input or transition binds it) is FAIL_CLOSED
  LADDER_ALLOW_PATH_UNBOUND: at E0 no LLM edits code, so the path would stop there;
* a finish that appends no organization-ledger receipt is FAIL_CLOSED LADDER_FINISH_NOT_LEDGER_BOUND (runtime counts only
  when a manifest-directed transition appends a receipt to refs/stegverse/organization-ledger);
* an access-path CONSTRAINT (e.g. the two credential layers: KV via InTr from a currently admitted healthy node, then the
  SKAP Vault via InTr only from inside KV, in that order) is DENY LADDER_ACCESS_PATH_BYPASSES_LAYER when an observed path
  reaches the protected surface without its gate, DENY LADDER_ACCESS_LAYERS_COLLAPSED when one step mints or skips both
  layers, and FAIL_CLOSED LADDER_CONSTRAINT_NOT_IN_SEALED_SCOPE when the goal's sealed scope does not name it;
* an observed run whose outcome for a named probe differs from what the item requires is OPERATING_MODE_E0_WITNESS_FAILED
  (or LADDER_E0_TERMINAL_NOT_SIX_FIELD when the component raised or returned a non-ALLOW without the six fields);
* every non-ALLOW item is covered by a six-field scoped task naming the owning lane, and every scoped task covers only
  non-ALLOW items carrying its failure code (LADDER_SCOPED_TASK_MISMATCH otherwise); a scoped task may carry an optional
  fixed finish_point (a non-empty string that bounds the task; anything beyond it is a new registered task);
* an item or scoped task may carry an optional failure_class {"class": "A"|"B"|"C", "reason": non-empty} using the
  ecosystem's classes (A: decided by an existing manifest transition or a repair inside the item's own surface; B: a
  missing capability a lane builds; C: waits on a ruling or decision). It is recorded, never changes a verdict, and a
  malformed one is FAIL_CLOSED LADDER_FAILURE_CLASS_MALFORMED (item) or LADDER_SCOPED_TASK_MISMATCH (task);
* an unbound allow_path may name its independent blockers (allow_path.blockers: [{"id", "evidence"}], distinct ids):
  each is its own LADDER_ALLOW_PATH_UNBOUND refusal carrying "blocker", and a scoped task for it names the same
  "blocker", so different owners can each hold one blocker of one item (tasks sharing a failure code cover disjoint
  (item, blocker) pairs); malformed blockers are FAIL_CLOSED LADDER_ALLOW_PATH_BLOCKER_MALFORMED;
* an item may reference a dependency registered elsewhere as its own task (external_dependency_refs: [{"ref", "owner",
  "evidence"}], distinct refs): each is FAIL_CLOSED LADDER_EXTERNAL_DEPENDENCY_PENDING carrying "external_ref"; the
  referenced registered task covers it, so no scoped task here may carry that code; a malformed reference is
  FAIL_CLOSED LADDER_EXTERNAL_DEPENDENCY_REF_MALFORMED.

Pure over the supplied documents: stdlib, no clock, no network, no LLM. Verdicts: ALLOW, DENY, FAIL_CLOSED.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/sv-work-items/ladder-conformance"
SCHEMA = "stegverse.ladder-conformance/v1"
DECL_SCHEMA = "stegverse.ladder-conformance-declaration/v1"
OBS_SCHEMA = "stegverse.ladder-conformance-observations/v1"
TASK_SCHEMA = "stegverse.ladder-conformance-scoped-task/v1"
CHECK_GOAL = "StegVerse-org/.github#163"
ENTRY = "resident-runtime/ladder_conformance.py::evaluate"
RETRY = "python scripts/ladder_conformance.py check (StegVerse-Labs/.github)"
GOALS = ("KV-SKAP-VAULT-FUNCTIONAL-001", "GITHUB-UNIVERSAL-GOVERNANCE-PRODUCT-001")
KINDS = ("PREDICATE", "HANDOFF", "CONSTRAINT")
TASK_SIX = ("failure_code", "failed_check", "required_repair", "retry_point", "owning_goal", "next_attempt")
RANK = {"ALLOW": 0, "FAIL_CLOSED": 1, "DENY": 2}
FAILURE_CLASSES = ("A", "B", "C")


def _failure_class_ok(v: Any) -> bool:
    return (isinstance(v, Mapping) and set(v) == {"class", "reason"} and v.get("class") in FAILURE_CLASSES
            and isinstance(v.get("reason"), str) and bool(v["reason"].strip()))


def _standard():
    mod = sys.modules.get("sv_operating_modes")
    path = ROOT / "resident-runtime/sv_operating_modes.py"
    if mod is None or Path(getattr(mod, "__file__", "")).resolve() != path.resolve():
        spec = importlib.util.spec_from_file_location("sv_operating_modes", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["sv_operating_modes"] = mod
        spec.loader.exec_module(mod)
    return mod


om = _standard()
MODES = om.MODES
LADDER_DOWN = tuple(reversed(MODES))  # E3, E2, E1, E0


def canonical(v: Any) -> bytes:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_uri(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def refusal(disposition: str, code: str, predicate: str, repair: str, owning_goal: str, nxt: str,
            retry: str = RETRY, **detail: Any) -> dict[str, Any]:
    return {"disposition": disposition, "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair, "retry_entrypoint": retry, "owning_existing_goal": owning_goal,
            "next_attempt": nxt, **detail}


def _blockers_ok(v: Any) -> bool:
    return (isinstance(v, list) and bool(v)
            and all(isinstance(b, Mapping) and set(b) == {"id", "evidence"}
                    and all(isinstance(b[k], str) and b[k].strip() for k in ("id", "evidence")) for b in v)
            and len({b["id"] for b in v}) == len(v))


def _external_refs_ok(v: Any) -> bool:
    return (isinstance(v, list) and bool(v)
            and all(isinstance(r, Mapping) and set(r) == {"ref", "owner", "evidence"}
                    and all(isinstance(r[k], str) and r[k].strip() for k in ("ref", "owner", "evidence")) for r in v)
            and len({r["ref"] for r in v}) == len(v))


EXTERNAL_CODE = "LADDER_EXTERNAL_DEPENDENCY_PENDING"


def _strings(v: Any):
    yield from om._strings(v)


def _projection(item: Mapping[str, Any]) -> dict[str, Any]:
    """The item as the standard sees it (its own vocabulary only)."""
    return {k: item.get(k) for k in ("id", "requires_llms", "lowest_supported_mode", "degraded_forms", "e0_terminal",
                                       "source") if k in item}


def _runs(obs: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {r["run_id"]: r for r in obs.get("runs", []) if isinstance(r, Mapping) and isinstance(r.get("run_id"), str)}


def evaluate_item(goal: Mapping[str, Any], item: Any, obs: Mapping[str, Any]) -> dict[str, Any]:
    owning = goal.get("owning_goal", CHECK_GOAL)
    if not isinstance(item, Mapping) or not isinstance(item.get("id"), str) or item.get("kind") not in KINDS:
        return {"id": item.get("id") if isinstance(item, Mapping) else None, "verdict": "FAIL_CLOSED", "refusals": [
            refusal("FAIL_CLOSED", "LADDER_ITEM_MALFORMED", "EVERY_ITEM_HAS_AN_ID_AND_KIND",
                    "give the item a string id and kind PREDICATE, HANDOFF or CONSTRAINT", CHECK_GOAL, "re-run check")]}
    name = "%s:%s" % (goal["task_id"], item["id"])
    bad: list[dict[str, Any]] = []
    e0 = item.get("e0_terminal")
    deg = item.get("degraded_forms") if isinstance(item.get("degraded_forms"), Mapping) else {}
    runs = _runs(obs)

    # 1. the standard itself, for every item that declares an E0 terminal
    if e0 is not None:
        b, _ = om._item_problems(goal["task_id"], _projection(item), [])
        bad += [dict(r, item=name, standard=om.ENTRY) for r in b]
    else:
        cb = item.get("class_b")
        if not (isinstance(cb, Mapping) and all(isinstance(cb.get(k), str) and cb[k].strip() for k in om.SIX)
                and cb.get("disposition") == "FAIL_CLOSED" and cb.get("failure_code") == "OPERATING_MODE_E0_TERMINAL_MISSING"):
            bad.append(refusal("FAIL_CLOSED", "CLASS_B_RECORD_INCOMPLETE", "E0_TERMINAL_OR_CLASS_B",
                               "an item with no E0 terminal carries a six-field class_b record (FAIL_CLOSED "
                               "OPERATING_MODE_E0_TERMINAL_MISSING) naming its owning goal", owning, "re-run check", item=name))
        else:
            bad.append(dict(cb, item=name))
        for s in _strings({k: item.get(k) for k in ("degraded_forms", "requires_llms", "lowest_supported_mode")}):
            if om.PROVIDERS.search(s):
                bad.append(refusal("DENY", "OPERATING_MODE_REQUIRES_SPECIFIC_PROVIDER", "NO_PROVIDER_REQUIREMENT",
                                   "state the requirement as an LLM count", owning, "re-run check", item=name, text=s))
                break

    # 2. every rung names its form
    missing = [m for m in LADDER_DOWN if not (isinstance(deg.get(m), str) and deg[m].strip())]
    if missing:
        bad.append(refusal("FAIL_CLOSED", "LADDER_RUNG_FORM_MISSING", "EVERY_RUNG_E3_TO_E0_NAMES_ITS_FORM",
                           "name the form used at " + ", ".join(missing), owning, "re-run check", item=name, missing=missing))

    # 3. the E0 terminal is bound to an observed run of the pinned component
    if isinstance(e0, Mapping):
        bound = [runs.get(r) for r in item.get("observed_by", [])]
        pins = {p for p in [e0.get("by"), item.get("source")] if isinstance(p, str)}
        pinned = [r for r in bound if r and any(r.get("pin") and r["pin"] in p for p in pins)]
        if not bound or None in bound or not pinned:
            bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_UNBOUND", "E0_TERMINAL_IS_EXERCISED_NOT_FLAGGED",
                               "bind observed_by to a run of the component pinned in by/source (scripts/ladder_conformance.py "
                               "observe at the exact commit)", owning, "on the next observe run", item=name))
        else:
            for r in pinned:
                outs = r.get("outcomes") or []
                if r.get("status") != "OBSERVED" or not outs:
                    bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_FAILED", "E0_TERMINAL_IS_EXERCISED_NOT_FLAGGED",
                                       "the pinned run must complete and record outcomes", owning, "on the next observe run",
                                       item=name, run_id=r.get("run_id")))
                    continue
                for o in outs:
                    if o.get("subject") not in (None, item.get("subject", item["id"])) and item.get("match_subject", True):
                        continue
                    if o.get("disposition") not in e0.get("dispositions", []):
                        bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_FAILED",
                                           "E0_TERMINAL_IS_EXERCISED_NOT_FLAGGED",
                                           "the observed outcome is not one of the declared E0 dispositions", owning,
                                           "on the next observe run", item=name, run_id=r["run_id"], got=o.get("disposition")))
                    elif o["disposition"] != "ALLOW" and not all(isinstance(o.get(k), str) and o[k].strip() for k in om.SIX):
                        bad.append(refusal("FAIL_CLOSED", "LADDER_E0_TERMINAL_NOT_SIX_FIELD", "NON_ALLOW_CARRIES_SIX_FIELDS",
                                           "the component's non-ALLOW must be a returned six-field disposition, not an "
                                           "exception or a bare status", owning, "on the next observe run", item=name,
                                           run_id=r["run_id"], got=o.get("disposition")))

    # 4. observed owner actions and external machines on the path
    for a in item.get("owner_actions", []) or []:
        bad.append(refusal("DENY", "OPERATING_MODE_OWNER_MUST_ACT", "NO_OWNER_MUST_ACT",
                           "convert the human-gated step into a manifest transition with a deterministic default",
                           owning, "on the next record change of the owning goal", item=name, evidence=a))
    for x in item.get("external_requirements", []) or []:
        bad.append(refusal("DENY", "LADDER_EXTERNAL_MACHINE_REQUIRED", "NO_EXTERNAL_MACHINE",
                           "replace the external machine or resident root with an ecosystem state transition",
                           owning, "on the next record change of the owning goal", item=name, evidence=x))

    for x in item.get("bare_status_terminals", []) or []:
        bad.append(refusal("FAIL_CLOSED", "LADDER_E0_TERMINAL_NOT_SIX_FIELD", "NON_ALLOW_CARRIES_SIX_FIELDS",
                           "return a six-field disposition instead of a bare status (a bare BLOCKED is not a finding)",
                           owning, "on the next record change of the owning goal", item=name, evidence=x))

    # 4b. required outcomes of named probes on the pinned runs
    req = item.get("required_outcomes") if isinstance(item.get("required_outcomes"), Mapping) else {}
    if req:
        seen = {}
        for rid in item.get("observed_by", []):
            for o in (runs.get(rid) or {}).get("outcomes") or []:
                if o.get("subject") in req:
                    seen[o["subject"]] = (rid, o)
        for subj, allowed in sorted(req.items()):
            if subj not in seen:
                bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_UNBOUND", "REQUIRED_PROBE_OBSERVED",
                                   "observe the probe " + subj, owning, "on the next observe run", item=name, probe=subj))
                continue
            rid, o = seen[subj]
            got = o.get("disposition")
            six = got == "ALLOW" or all(isinstance(o.get(k), str) and o[k].strip() for k in om.SIX)
            if got == "EXCEPTION" or (got in allowed and not six):
                bad.append(refusal("FAIL_CLOSED", "LADDER_E0_TERMINAL_NOT_SIX_FIELD", "NON_ALLOW_CARRIES_SIX_FIELDS",
                                   "return a six-field %s for %s instead of %s" % ("/".join(allowed), subj,
                                   "raising " + str(o.get("exception")) if got == "EXCEPTION" else "a bare " + str(got)),
                                   owning, "on the next observe run", item=name, run_id=rid, probe=subj, got=got))
            elif got not in allowed:
                bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_FAILED", "E0_TERMINAL_DECIDES_AS_REQUIRED",
                                   "for %s the component must return %s; it returned %s" % (subj, "/".join(allowed), got),
                                   owning, "on the next observe run", item=name, run_id=rid, probe=subj, got=got))

    missing_ev = [r for r in item.get("evidence_runs", []) or [] if r not in runs]
    if missing_ev:
        bad.append(refusal("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_UNBOUND", "EVIDENCE_IS_AN_OBSERVED_RUN",
                           "every evidence_runs entry names a run in the observations", owning,
                           "on the next observe run", item=name, missing=missing_ev))

    # 4c. access-path constraints
    for x in item.get("bypass_paths", []) or []:
        bad.append(refusal("DENY", "LADDER_ACCESS_PATH_BYPASSES_LAYER", "PROTECTED_SURFACE_REACHED_ONLY_THROUGH_ITS_GATE",
                           "remove the path or route it through the layer's InTr gate", owning,
                           "on the next record change of the owning goal", item=name, evidence=x))
    for x in item.get("collapsed_layers", []) or []:
        bad.append(refusal("DENY", "LADDER_ACCESS_LAYERS_COLLAPSED", "TWO_SEQUENTIAL_GATES_EACH_WITH_ITS_OWN_RECEIPT",
                           "split the step so layer 2 consumes a layer-1 receipt minted by a separate, verified gate",
                           owning, "on the next record change of the owning goal", item=name, evidence=x))
    if item.get("kind") == "CONSTRAINT" and item.get("sealed_scope_includes") is not True:
        bad.append(refusal("FAIL_CLOSED", "LADDER_CONSTRAINT_NOT_IN_SEALED_SCOPE", "CONSTRAINT_IS_A_SEALED_PREDICATE",
                           "add the constraint to the goal's sealed expected_evidence_predicates (a re-seal through the "
                           "goal's own request)", owning, "on the next record change of the owning goal", item=name,
                           evidence=item.get("sealed_scope_evidence")))

    # 5. ALLOW is reachable without a code edit
    ap = item.get("allow_path")
    if e0 is not None and not (isinstance(ap, Mapping) and ap.get("state") in ("OBSERVED_ALLOW", "BOUND")
                               and isinstance(ap.get("by"), str) and ap["by"].strip()):
        blockers = ap.get("blockers") if isinstance(ap, Mapping) else None
        if blockers is not None and not _blockers_ok(blockers):
            bad.append(refusal("FAIL_CLOSED", "LADDER_ALLOW_PATH_BLOCKER_MALFORMED", "ALLOW_PATH_BLOCKERS_ARE_ID_AND_EVIDENCE",
                               "allow_path.blockers is a non-empty list of {\"id\", \"evidence\"} with distinct ids",
                               owning, "re-run check", item=name))
            blockers = None
        for b in blockers or [None]:
            extra = {"blocker": b["id"]} if b else {}
            bad.append(refusal("FAIL_CLOSED", "LADDER_ALLOW_PATH_UNBOUND", "ALLOW_REACHABLE_AT_E0_WITHOUT_CODE_EDIT",
                               "give the component an evidence input or transition through which the receipt it waits "
                               "for turns the item ALLOW", owning, "on the next observe run", item=name,
                               evidence=b["evidence"] if b else ((ap or {}).get("evidence") if isinstance(ap, Mapping)
                                                                 else None), **extra))

    # 6. a finish handoff appends an organization-ledger receipt
    if item.get("finish_handoff") and not (isinstance(item.get("ledger_binding"), Mapping)
                                           and item["ledger_binding"].get("state") == "BOUND"):
        bad.append(refusal("FAIL_CLOSED", "LADDER_FINISH_NOT_LEDGER_BOUND", "FINISH_APPENDS_ORGANIZATION_LEDGER_RECEIPT",
                           "bind the finish verdict to a manifest-directed transition that appends a receipt to "
                           "refs/stegverse/organization-ledger", owning, "on the next record change of the owning goal",
                           item=name, evidence=(item.get("ledger_binding") or {}).get("evidence")))

    # 7. a dependency that is not yet admitted (declared, observed draft)
    for d in item.get("unadmitted_dependencies", []) or []:
        bad.append(refusal("FAIL_CLOSED", "LADDER_DEPENDENCY_NOT_ADMITTED", "HANDOFF_SURFACE_ADMITTED",
                           "admit the dependency through its own exact-head admission", owning,
                           "on the dependency's admission event", item=name, evidence=d))

    # 7b. a dependency registered elsewhere as its own task (covered there, not by a scoped task here)
    ext = item.get("external_dependency_refs")
    if ext is not None and not _external_refs_ok(ext):
        bad.append(refusal("FAIL_CLOSED", "LADDER_EXTERNAL_DEPENDENCY_REF_MALFORMED", "EXTERNAL_REF_IS_REF_OWNER_EVIDENCE",
                           "external_dependency_refs is a non-empty list of {\"ref\", \"owner\", \"evidence\"} with "
                           "distinct refs", owning, "re-run check", item=name))
    elif ext:
        for r in ext:
            bad.append(refusal("FAIL_CLOSED", EXTERNAL_CODE, "EXTERNAL_REGISTERED_DEPENDENCY_ADMITTED",
                               "admit " + r["ref"] + " (its own registered task, owned by " + r["owner"] + ")", owning,
                               "on " + r["ref"] + "'s admission event", item=name, external_ref=r["ref"],
                               owner=r["owner"], evidence=r["evidence"]))

    # 8. an optional failure classification is well formed
    if "failure_class" in item and not _failure_class_ok(item["failure_class"]):
        bad.append(refusal("FAIL_CLOSED", "LADDER_FAILURE_CLASS_MALFORMED", "FAILURE_CLASS_IS_A_B_OR_C_WITH_REASON",
                           "failure_class is {\"class\": \"A\"|\"B\"|\"C\", \"reason\": <non-empty>}", owning,
                           "re-run check", item=name))

    verdict = max((r["disposition"] for r in bad), key=lambda d: RANK.get(d, 1), default="ALLOW")
    verdict = verdict if verdict in RANK else "FAIL_CLOSED"
    ladder = {m: {"llms": MODES.index(m), "form": deg.get(m)} for m in LADDER_DOWN}
    out = {"id": item["id"], "kind": item["kind"], "verdict": verdict, "ladder": ladder,
           "lowest_supported_mode": item.get("lowest_supported_mode"), "observed_state": item.get("observed_state"),
           "refusals": bad}
    if _failure_class_ok(item.get("failure_class")):
        out["failure_class"] = dict(item["failure_class"])
    return out


def evaluate(decl: Mapping[str, Any], obs: Mapping[str, Any], tasks: list[Mapping[str, Any]]) -> dict[str, Any]:
    """The conformance document for one goal (without its receipt)."""
    if not (isinstance(decl, Mapping) and decl.get("schema") == DECL_SCHEMA and decl.get("task_id") in GOALS):
        return refusal("FAIL_CLOSED", "LADDER_DECLARATION_MALFORMED", "DECLARATION_HAS_SCHEMA",
                       "schema " + DECL_SCHEMA + " and a priority-goal task_id", CHECK_GOAL, "re-run check")
    if not (isinstance(obs, Mapping) and obs.get("schema") == OBS_SCHEMA and obs.get("task_id") == decl["task_id"]):
        return refusal("FAIL_CLOSED", "LADDER_OBSERVATIONS_UNBOUND", "OBSERVATIONS_MATCH_DECLARATION",
                       "observations/<goal>.observations.json for the same task_id", CHECK_GOAL, "on the next observe run")
    items = decl.get("items") if isinstance(decl.get("items"), list) else []
    ids = [i.get("id") for i in items if isinstance(i, Mapping)]
    results = [evaluate_item(decl, it, obs) for it in items]
    problems: list[dict[str, Any]] = []
    if len(set(ids)) != len(ids) or not items:
        problems.append(refusal("FAIL_CLOSED", "LADDER_ITEM_COVERAGE", "ONE_ENTRY_PER_ITEM", "declare each item once",
                                CHECK_GOAL, "re-run check"))
    sealed = decl.get("sealed_expected_evidence_predicates") or []
    preds = [i["id"] for i in items if isinstance(i, Mapping) and i.get("kind") == "PREDICATE"]
    if sorted(preds) != sorted(sealed):
        problems.append(refusal("FAIL_CLOSED", "LADDER_PREDICATE_COVERAGE", "EVERY_SEALED_PREDICATE_IS_CHECKED",
                                "one PREDICATE item per sealed expected_evidence_predicate", CHECK_GOAL, "re-run check",
                                missing=sorted(set(sealed) - set(preds)), extra=sorted(set(preds) - set(sealed))))
    # scoped tasks <-> non-ALLOW items, both directions
    mine = [t for t in tasks if isinstance(t, Mapping) and t.get("goal") == decl["task_id"]]
    by_code: dict[str, list[Mapping[str, Any]]] = {}
    ids_seen: set[str] = set()
    for t in mine:
        ok = (t.get("schema") == TASK_SCHEMA and all(isinstance(t.get(k), str) and t[k].strip() for k in TASK_SIX)
              and t.get("disposition") in ("DENY", "FAIL_CLOSED") and isinstance(t.get("owning_lane"), str)
              and t["owning_lane"].strip() and isinstance(t.get("items"), list) and t["items"]
              and isinstance(t.get("proposed_resolution"), str) and t["proposed_resolution"].strip()
              and ("finish_point" not in t or (isinstance(t["finish_point"], str) and t["finish_point"].strip()))
              and ("failure_class" not in t or _failure_class_ok(t["failure_class"]))
              and ("blocker" not in t or (isinstance(t["blocker"], str) and t["blocker"].strip()))
              and t.get("task_id") not in ids_seen)
        if ok:
            ids_seen.add(t["task_id"])
            others = {(i, o.get("blocker")) for o in by_code.get(t["failure_code"], []) for i in o["items"]}
            ok = not (others & {(i, t.get("blocker")) for i in t["items"]})
        if not ok:
            problems.append(refusal("FAIL_CLOSED", "LADDER_SCOPED_TASK_MISMATCH", "SCOPED_TASK_HAS_SIX_FIELDS_AND_LANE",
                                    "scoped tasks carry the six fields, owning lane, items and proposed resolution; a "
                                    "finish_point, when present, is a non-empty string; a failure_class, when present, is "
                                    "A, B or C with a reason; a blocker, when present, is a non-empty string; tasks "
                                    "sharing a failure code cover disjoint (item, blocker) pairs", CHECK_GOAL, "re-run check",
                                    task=t.get("task_id")))
            continue
        by_code.setdefault(t["failure_code"], []).append(t)
    need: dict[str, set] = {}
    for r in results:
        for f in r["refusals"]:
            if f["failure_code"] != EXTERNAL_CODE:   # covered by the referenced registered task
                need.setdefault(f["failure_code"], set()).add((r["id"], f.get("blocker")))
        codes = {f["failure_code"] for f in r["refusals"]}
        r["scoped_tasks"] = sorted({t["task_id"] for c in codes for t in by_code.get(c, []) if r["id"] in t["items"]})
    for code, its in sorted(need.items()):
        listed = {(i, t.get("blocker")) for t in by_code.get(code, []) for i in t["items"]}
        if listed != its:
            fmt = lambda xs: sorted(i if b is None else i + " [" + b + "]" for i, b in xs)
            problems.append(refusal("FAIL_CLOSED", "LADDER_SCOPED_TASK_MISMATCH", "EVERY_GAP_HAS_A_SCOPED_TASK",
                                    "scoped tasks for " + code + " listing exactly " + ", ".join(fmt(its)), CHECK_GOAL,
                                    "re-run check", gap_code=code,
                                    task=sorted(t["task_id"] for t in by_code.get(code, [])), listed=fmt(listed)))
    for code in sorted(set(by_code) - set(need)):
        problems.append(refusal("FAIL_CLOSED", "LADDER_SCOPED_TASK_MISMATCH", "SCOPED_TASK_COVERS_A_GAP",
                                "drop the scoped task: no item carries " + code, CHECK_GOAL, "re-run check",
                                task=sorted(t["task_id"] for t in by_code[code])))
    counts = {k: {"checked": sum(1 for r in results if r["kind"] == k),
                  "conformant": sum(1 for r in results if r["kind"] == k and r["verdict"] == "ALLOW")} for k in KINDS}
    nonallow = [r for r in results if r["verdict"] != "ALLOW"]
    verdict = "ALLOW" if not nonallow else max((r["verdict"] for r in nonallow), key=RANK.get)
    doc = {"schema": SCHEMA, "task_id": decl["task_id"], "owning_lane": decl.get("owning_lane"),
           "owning_goal": decl.get("owning_goal"), "finish_point": decl.get("finish_point"), "mode": MODES[0],
           "verdict": verdict, "counts": counts, "gaps": len(nonallow),
           "scoped_tasks": sorted(t["task_id"] for c in by_code for t in by_code[c]), "items": results,
           "consistency": "ALLOW" if not problems else "FAIL_CLOSED", "consistency_refusals": problems,
           "authority_effect": "NONE_CONFORMANCE_RECORD_ONLY", "organization_ledger_appended": False,
           "llm_used": False, "network_used": False, "clock_read": False}
    if verdict != "ALLOW":
        first = next(r for r in nonallow if r["verdict"] == verdict)["refusals"][0]
        doc.update({k: first[k] for k in om.SIX})
        doc["disposition"] = verdict
    return doc
