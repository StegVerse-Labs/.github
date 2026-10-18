"""Merge-admission learning (ADMISSION_SCENARIOS_LEARN_FROM_OBSERVED_OUTCOMES), P1's part.

HARVEST every non-ALLOW outcome (ledger receipts, SV_ISSUEs, ADMISSION_MISS)
as a candidate, GENERALIZE it into a scenario class (predicate, surface,
mutation axes) that generates one mutation-negative per bound field plus
positive controls (TVC#527 pattern), and admit classes and scenarios only
through SCENARIO_CORPUS_APPEND: DENY CLASS_NEVER_FIRES / CLASS_REFUSES_KNOWN_GOOD,
FAIL_CLOSED on an epoch, digest or supersede-chain fault. The corpus binds to
registry/ledger state (sv_work_items.admission_inputs), never GitHub checks.
miss_count is derived from ADMISSION_MISS lines, never stored. Stdlib only, no clock.

Generalization rules (Q-SCENARIO-GENERALIZATION; see the answer file):
  G1 class identity = (failed_predicate, surface kind); failure codes and source
     PRs are members, so Labs#3245 and SDK#533 are one class.
  G2 mutation axes = the observed-input fields the failed predicate reads
     (PREDICATE_BINDINGS); each axis yields exactly one mutation-negative.
  G3 positive controls = the known-good fixture with every axis at its bound value.
  S1 surfaces are typed by sv_work_items.surface_kind.
"""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
wi = sys.modules.get("sv_work_items")
if wi is None:  # one module instance, so a Refusal raised anywhere is the same class
    _s = importlib.util.spec_from_file_location("sv_work_items", ROOT / "resident-runtime/sv_work_items.py")
    wi = importlib.util.module_from_spec(_s)
    sys.modules["sv_work_items"] = wi
    _s.loader.exec_module(wi)

SCENARIO_SCHEMA = "stegverse.admission_scenario.v1"
CLASS_SCHEMA = "stegverse.admission_scenario_class.v1"
MISS_SCHEMA = "stegverse.admission_miss.v1"
ORIGINS = ("SEED", "HARVESTED", "ADMISSION_MISS")
E = "resident-runtime/admission_learning.py::"


def _fail(code, pred, repair, entry, **d):
    r = wi.Refusal("FAIL_CLOSED", code, pred, repair, entry, "resubmit the corrected append; nothing was appended", **d)
    r.record["retry_entrypoint"] = E + entry
    return r


def _deny(code, pred, repair, entry, **d):
    r = wi.Refusal("DENY", code, pred, repair, entry, "derive a corrected class version from the same evidence", **d)
    r.record["retry_entrypoint"] = E + entry
    return r


def _set(obj: dict, field: str, value: Any) -> None:
    obj[field] = value


# predicate -> (failure_code, surface kinds it applies to, [(field, mutation, mutate(obs))])
def _foreign(o):
    o["writer_sessions"] = sorted(set(o["writer_sessions"]) | {"FOREIGN-SESSION"}); o["declared_session_matches_writers"] = False


def _stale_gen(o): o["current_base"] = {**o["current_base"], "registry_generation": o["current_base"]["registry_generation"] + 1}
def _stale_head(o): o["current_base"] = {**o["current_base"], "ledger_head": "f" * 40}
def _drop_first_check(o): o["validation_receipts"] = [v for v in o["validation_receipts"] if v["check_id"] != o["required_check_ids"][0]]
def _unreceipt(o): o["validation_receipts"] = [{**v, "receipt_ref": ""} for v in o["validation_receipts"]]
def _off_head(o): o["validation_receipts"] = [{**v, "change_digest": "sha256:" + "0" * 64} for v in o["validation_receipts"]]
def _req_digest(o): o["bound_request_digest"] = "sha256:" + "1" * 64
def _no_session(o): o["declared_session"] = ""
def _drop_signoff(o): o["signoffs"] = []
def _unreceipt_signoff(o): o["signoffs"] = [{**s, "receipt_ref": ""} for s in o["signoffs"]]
def _fail_check(o): o["validation_receipts"] = [{**v, "disposition": "DENY"} if i == 0 else v for i, v in enumerate(o["validation_receipts"])]


PREDICATE_BINDINGS: dict[str, tuple[str, list[tuple[str, str, Callable]]]] = {
    "BRANCH_WRITER_IS_BRANCH_OWNER": ("BRANCH_HAS_FOREIGN_WRITER", [
        ("writer_sessions", "add a writer that is not the declared session", _foreign)]),
    "BASE_IS_CURRENT": ("BASE_STALE", [
        ("current_base.registry_generation", "registry generation moved after proposal", _stale_gen),
        ("current_base.ledger_head", "organization-ledger head moved after proposal", _stale_head)]),
    "MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED": ("CHECK_SKIPPED_OR_UNOBSERVED", [
        ("validation_receipts[required_check_ids[0]]", "a required check has no receipt (skipped)", _drop_first_check),
        ("validation_receipts[*].receipt_ref", "checks reported but unreceipted", _unreceipt)]),
    "VALIDATION_RECEIPT_BINDS_EXACT_HEAD": ("VALIDATION_NOT_AT_EXACT_HEAD", [
        ("validation_receipts[*].change_digest", "receipts from another head", _off_head)]),
    "AUTHORIZATION_BINDS_FULL_REQUEST": ("REQUEST_DIGEST_MISMATCH", [
        ("bound_request_digest", "decision bound to a different request", _req_digest)]),
    "PR_AUTHOR_SESSION_DECLARED": ("AUTHOR_SESSION_NOT_DECLARED", [
        ("declared_session", "author session empty", _no_session)]),
    "REQUIRED_SIGNOFF_RECORDED": ("SIGNOFF_ABSENT", [
        ("signoffs", "required role sign-off absent", _drop_signoff),
        ("signoffs[*].receipt_ref", "sign-off claimed without receipt", _unreceipt_signoff)]),
    "CHECK_PASSES": ("CHECK_NOT_PASSING", [
        ("validation_receipts[0].disposition", "a required check refused", _fail_check)]),
}
PREDICATE_ALIASES = {"CHECK_NOT_PASSING": "CHECK_PASSES"}
FAILURE_CODE_TO_PREDICATE = {v[0]: k for k, v in PREDICATE_BINDINGS.items()}


# ------------------------------------------------------------------ harvest
def harvest(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Every non-ALLOW outcome is a candidate; no curation. Deterministic order."""
    out = []
    for r in records:
        schema = r.get("schema")
        if schema == wi.ISSUE_SCHEMA:
            d, origin, ref = r["disposition"], "HARVESTED", {"issue_id": r["issue_id"], "source_receipt": r["source_receipt"]}
        elif schema == MISS_SCHEMA:
            d = {"disposition": "FAIL_CLOSED", "failure_code": "ADMISSION_MISS", "failed_predicate": r.get("predicate_gap") or "UNKNOWN"}
            origin, ref = "ADMISSION_MISS", {"admitted_change": r["admitted_change"], "correcting_ref": r["correcting_ref"]}
        else:  # ledger receipt or transition outcome carrying a disposition
            ev = r.get("evidence") if isinstance(r.get("evidence"), Mapping) else r
            if ev.get("disposition") in (None, "ALLOW"):
                continue
            d, origin, ref = ev, "HARVESTED", {"receipt_sha256": r.get("receipt_sha256")}
        if d.get("disposition") == "ALLOW":
            continue
        out.append({"failure_code": d.get("failure_code"), "failed_predicate": d.get("failed_predicate"),
                    "origin": origin, "source": ref, "surfaces": sorted(r.get("touched_surface_kinds") or r.get("surfaces") or [])})
    return sorted(out, key=lambda c: wi.canon(c))


# ------------------------------------------------------------------ generalize
def class_id_for(predicate: str, surface: str) -> str:
    return "ASC-" + predicate + "@" + surface


def generalize(candidate: Mapping[str, Any], *, surface: str, origin_scenarios: list[str], rule_refs: list[dict],
               declared_by_session: str, harvest_receipt_ref: str | None, hb_epoch: Any,
               class_version: int = 1, supersedes: str | None = None) -> dict[str, Any]:
    pred = candidate.get("failed_predicate")
    pred = PREDICATE_ALIASES.get(candidate.get("failure_code"), pred)
    if pred not in PREDICATE_BINDINGS:
        pred = FAILURE_CODE_TO_PREDICATE.get(candidate.get("failure_code"), pred)
    if pred not in PREDICATE_BINDINGS:
        raise _fail("PREDICATE_BINDING_UNDECLARED", "FAILED_PREDICATE_HAS_DECLARED_BINDINGS",
                    "declare the predicate's bound fields in PREDICATE_BINDINGS (or answer via JDQ Q-SCENARIO-GENERALIZATION)",
                    "generalize", failed_predicate=pred)
    code, axes = PREDICATE_BINDINGS[pred]
    body = {"schema": CLASS_SCHEMA, "class_id": class_id_for(pred, surface), "class_version": class_version,
            "supersedes": supersedes, "predicate": pred, "expected_failure_code": code,
            "expected_disposition": "DENY" if code in ("BASE_STALE", "CHECK_NOT_PASSING") else "FAIL_CLOSED",
            "surfaces": [{"kind": surface}],
            "mutation_axes": [{"field": f, "bound_value_source": "positive_control", "mutation": m} for f, m, _ in axes],
            "positive_controls": ["PC-" + surface],
            "provenance": {"origin_scenarios": sorted(origin_scenarios), "harvest_receipt_ref": harvest_receipt_ref,
                           "rule_refs": rule_refs, "declared_by_session": declared_by_session},
            "hb_epoch": str(hb_epoch)}
    return wi.seal(body, "class_sha256")


def generate(cls: Mapping[str, Any], known_good: Mapping[str, Any], *, hb_epoch: Any) -> list[dict[str, Any]]:
    """One mutation-negative per bound field plus the positive control."""
    _, axes = PREDICATE_BINDINGS[cls["predicate"]]
    base = {"schema": SCENARIO_SCHEMA, "scenario_class": cls["class_id"], "origin": "SEED",
            "source": {"class_sha256": cls["class_sha256"]}, "hb_epoch": str(hb_epoch)}
    out = [wi.seal({**base, "scenario_id": cls["positive_controls"][0] + "/" + cls["class_id"], "observed_inputs": copy.deepcopy(dict(known_good)),
                    "expected_disposition": "ALLOW", "expected_failure_code": None,
                    "generated_from": {"class_id": cls["class_id"], "axis": None}}, "scenario_sha256")]
    for field, _, mutate in axes:
        obs = copy.deepcopy(dict(known_good)); mutate(obs)
        out.append(wi.seal({**base, "scenario_id": cls["class_id"] + "/" + field, "observed_inputs": obs,
                            "expected_disposition": cls["expected_disposition"], "expected_failure_code": cls["expected_failure_code"],
                            "generated_from": {"class_id": cls["class_id"], "axis": field}}, "scenario_sha256"))
    return out


# ------------------------------------------------------------------ corpus
def verify_line(line: Mapping[str, Any], field: str, entry: str) -> None:
    wi.epoch_check(line.get("hb_epoch"), entry)
    if line.get(field) != wi.sha({k: v for k, v in line.items() if k != field}):
        raise _fail("CORPUS_LINE_DIGEST_MISMATCH", "CORPUS_LINE_DIGEST_VERIFIES", "re-derive the line; corpus lines are never edited", entry)


def latest_classes(class_lines: Iterable[Mapping[str, Any]]) -> dict[str, dict]:
    """Latest version per class_id; FAIL_CLOSED on a broken or forked supersede chain."""
    by: dict[str, list[dict]] = {}
    for c in class_lines:
        verify_line(c, "class_sha256", "latest_classes")
        by.setdefault(c["class_id"], []).append(dict(c))
    out = {}
    for cid, versions in by.items():
        versions.sort(key=lambda c: c["class_version"])
        for i, v in enumerate(versions):
            want = None if i == 0 else versions[i - 1]["class_sha256"]
            if v["class_version"] != i + 1 or v.get("supersedes") != want:
                code = "CLASS_SUPERSEDE_CHAIN_FORKED" if v["class_version"] <= i else "CLASS_SUPERSEDE_CHAIN_BROKEN"
                raise _fail(code, "CLASS_SUPERSEDE_CHAIN_LINEAR", "each version supersedes exactly the previous one", "latest_classes", class_id=cid)
        out[cid] = versions[-1]
    return out


def covered_kinds(classes: Mapping[str, Mapping]) -> list[str]:
    return sorted({s["kind"] for c in classes.values() for s in c["surfaces"]})


def corpus_append(class_lines: list[dict], corpus_lines: list[dict], new_class: Mapping[str, Any], scenarios: list[dict],
                  *, hb_epoch: Any, known_good: Iterable[Mapping[str, Any]] = (),
                  evaluator: Callable[..., dict] = wi.evaluate_admission) -> dict[str, Any]:
    """SCENARIO_CORPUS_APPEND. ALLOW returns the lines to append and the six-field-ready outcome."""
    entry = "corpus_append"
    try:
        wi.epoch_check(hb_epoch, entry)
        verify_line(new_class, "class_sha256", entry)
        for s in scenarios:
            verify_line(s, "scenario_sha256", entry)
        for s in corpus_lines:
            verify_line(s, "scenario_sha256", entry)
        prov = new_class.get("provenance") or {}
        if not prov.get("origin_scenarios") or not prov.get("rule_refs") or not prov.get("declared_by_session"):
            raise _fail("CLASS_PROVENANCE_ABSENT", "CLASS_NAMES_PROVENANCE", "origin_scenarios, rule_refs and declared_by_session", entry)
        current = latest_classes(class_lines)
        latest_classes(list(class_lines) + [dict(new_class)])
        prev = current.get(new_class["class_id"])
        if prev is not None and wi.canon({k: v for k, v in prev.items() if k not in ("class_sha256", "class_version", "supersedes", "hb_epoch")}) \
                == wi.canon({k: v for k, v in new_class.items() if k not in ("class_sha256", "class_version", "supersedes", "hb_epoch")}):
            raise _deny("CLASS_VERSION_UNCHANGED", "CLASS_VERSION_CHANGES_CONTENT", "a new version must change the class", entry)
        known = list(current) + [new_class["class_id"]]
        for s in scenarios:
            if s["scenario_class"] not in known or (s.get("generated_from") or {}).get("class_id") not in (None, *known):
                raise _fail("SCENARIO_CLASS_UNKNOWN", "SCENARIO_NAMES_A_CORPUS_CLASS", "append the class first", entry, scenario=s["scenario_id"])
        ids = {s["scenario_id"] for s in corpus_lines}
        dup = sorted(s["scenario_id"] for s in scenarios if s["scenario_id"] in ids and not s.get("supersedes"))
        if dup:
            raise _deny("SCENARIO_ID_EXISTS", "CORPUS_IS_APPEND_ONLY", "a changed scenario names what it supersedes", entry, duplicates=dup)
        mine = [s for s in scenarios if s["scenario_class"] == new_class["class_id"]]
        axes = {a["field"] for a in new_class["mutation_axes"]}
        if {(s.get("generated_from") or {}).get("axis") for s in mine if s["expected_disposition"] != "ALLOW"} != axes:
            raise _deny("CLASS_AXIS_WITHOUT_NEGATIVE", "ONE_MUTATION_NEGATIVE_PER_BOUND_FIELD", "generate one negative per axis", entry)
        for s in mine:
            if s["expected_disposition"] == "ALLOW":
                continue
            out = wi.admit(s["observed_inputs"], evaluator)
            if out["disposition"] != s["expected_disposition"] or out.get("failure_code") != s["expected_failure_code"]:
                raise _deny("CLASS_NEVER_FIRES", "CLASS_FIRES_ON_EVERY_MUTATION_NEGATIVE",
                            "the evaluator must refuse every mutation-negative with the class's code", entry,
                            scenario=s["scenario_id"], observed=out.get("failure_code") or out["disposition"])
        good = [s["observed_inputs"] for s in mine if s["expected_disposition"] == "ALLOW"] + [dict(k) for k in known_good] \
            + [s["observed_inputs"] for s in corpus_lines if s["expected_disposition"] == "ALLOW"]
        if not [s for s in mine if s["expected_disposition"] == "ALLOW"]:
            raise _deny("CLASS_POSITIVE_CONTROL_ABSENT", "CLASS_ALLOWS_EVERY_KNOWN_GOOD_FIXTURE", "include a positive control", entry)
        for g in good:
            out = wi.admit(g, evaluator)
            if out["disposition"] != "ALLOW":
                raise _deny("CLASS_REFUSES_KNOWN_GOOD", "CLASS_ALLOWS_EVERY_KNOWN_GOOD_FIXTURE",
                            "the class must not refuse a known-good fixture", entry, observed=out.get("failure_code"))
        return {"disposition": "ALLOW", "transition_class": "SCENARIO_CORPUS_APPEND", "append_classes": [dict(new_class)],
                "append_scenarios": [dict(s) for s in scenarios], "record": dict(new_class),
                "corpus_head": wi.sha([s["scenario_sha256"] for s in corpus_lines + scenarios])}
    except wi.Refusal as r:
        return {**r.record, "transition_class": "SCENARIO_CORPUS_APPEND", "record": dict(new_class)}


# ------------------------------------------------------------------ miss feedback
def admission_miss(change: Mapping[str, Any], *, admission_receipt_ref: str, correcting_ref: str, miss_kind: str,
                   predicate_gap: str | None, class_ids: list[str], hb_epoch: Any) -> dict[str, Any]:
    wi.epoch_check(hb_epoch, "admission_miss")
    if miss_kind not in ("REVERT", "CORRECTION", "REFUSAL"):
        raise _fail("MISS_KIND_INVALID", "MISS_KIND_IS_REVERT_CORRECTION_OR_REFUSAL", "REVERT, CORRECTION or REFUSAL", "admission_miss")
    if change.get("lifecycle_state") != "APPLIED" or not wi._str(correcting_ref):
        raise _fail("ADMISSION_MISS_NOT_GROUNDED", "CORRECTING_REF_IS_RECEIPTED", "an APPLIED change and a receipted correcting ref", "admission_miss")
    return wi.seal({"schema": MISS_SCHEMA, "admitted_change": change["change_id"], "admitted_change_digest": change["head"]["change_digest"],
                    "admission_receipt_ref": admission_receipt_ref, "correcting_ref": correcting_ref, "miss_kind": miss_kind,
                    "predicate_gap": predicate_gap, "class_ids": sorted(class_ids),
                    "touched_surface_kinds": sorted({wi.surface_kind(p) for p in change["touched_paths"]}),
                    "hb_epoch": str(hb_epoch)}, "miss_sha256")


def miss_counts(miss_lines: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Derived per class from ADMISSION_MISS lines only; never stored."""
    counts: dict[str, int] = {}
    for m in miss_lines:
        verify_line(m, "miss_sha256", "miss_counts")
        for c in m["class_ids"]:
            counts[c] = counts.get(c, 0) + 1
    return counts
