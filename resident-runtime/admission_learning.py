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
    o["writer_sessions"] = sorted(set(o["writer_sessions"]) | {"FOREIGN-SESSION"})


def _stale_gen(o): o["current_base"] = {**o["current_base"], "registry_generation": o["current_base"]["registry_generation"] + 1}
def _stale_head(o): o["current_base"] = {**o["current_base"], "ledger_head": "f" * 40}
def _drop_first_check(o): o["validation_receipts"] = [v for v in o["validation_receipts"] if v["check_id"] != o["required_check_ids"][0]]
def _unreceipt(o): o["validation_receipts"] = [{**v, "ref": ""} for v in o["validation_receipts"]]
def _artifact_only(o): o["validation_receipts"] = [{**v, "evidence_class": "OBSERVED_ARTIFACT"} for v in o["validation_receipts"]]
def _off_head(o): o["validation_receipts"] = [{**v, "change_digest": "sha256:" + "0" * 64} for v in o["validation_receipts"]]
def _req_digest(o): o["bound_request_digest"] = "sha256:" + "1" * 64
def _declared_label_only(o): o["push_receipts"] = None  # the record still carries declared_session; no push-receipt chain
def _drop_signoff(o): o["signoffs"] = []
def _unreceipt_signoff(o): o["signoffs"] = [{**s, "receipt_ref": ""} for s in o["signoffs"]]
def _fail_check(o): o["validation_receipts"] = [{**v, "disposition": "DENY"} if i == 0 else v for i, v in enumerate(o["validation_receipts"])]
def _writer_evidence_lost(o):  # snapshot restore: every content writer_session UNKNOWN and no sv-push-receipt chain survives
    o["writer_sessions"] = []; o["push_receipts"] = None
def _fail_closed_check(o): o["validation_receipts"] = [{**v, "disposition": "FAIL_CLOSED"} if i == 0 else v for i, v in enumerate(o["validation_receipts"])]
# ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH: the Labs#3266 base-state readback receipt and the supplied epoch
def _reseal_readback(o, **change):
    rb = {k: v for k, v in o["hb_epoch_readback"].items() if k != "result_sha256"}
    for k, v in change.items():
        rb[k] = v
    o["hb_epoch_readback"] = wi.seal(rb, "result_sha256")
def _no_readback(o): o["hb_epoch_readback"] = None
def _unsealed_readback(o): o["hb_epoch_readback"] = {**o["hb_epoch_readback"], "result_sha256": "sha256:" + "0" * 64}
def _clock_epoch(o): _reseal_readback(o, hb_epoch_source={**o["hb_epoch_readback"]["hb_epoch_source"], "derived_from_clock": True})
def _non_int_epoch(o): _reseal_readback(o, hb_epoch=float(o["hb_epoch_readback"]["hb_epoch"]))
def _other_epoch(o): o["supplied_hb_epoch"] = str(int(o["supplied_hb_epoch"]) + 1)
def _unknown_epoch(o): o["supplied_hb_epoch"] = wi.UNKNOWN
# STAGE_GATE_RECEIPT_DERIVES_NATIVE_ISSUE (Q-SV-NATIVE-BOOTSTRAP): what the change resolves (admission_inputs' resolves /
# resolved_issues, the facts sv_work_items.resolved_issue_facts observes from the ledgered receipt)
def _f0(o, **change): o["resolved_issues"] = [{**f, **change} if i == 0 else f for i, f in enumerate(o["resolved_issues"])]
def _no_resolves(o): o["resolves"] = []
def _receipt_not_ledgered(o): o["resolved_issues"] = []
def _extra_unobserved(o): o["resolves"] = sorted(o["resolves"] + ["svi:" + "f" * 64])
def _touches_receipt_path(o): _f0(o, receipt_ledger_paths=sorted(o["resolved_issues"][0]["receipt_ledger_paths"] + [o["touched_paths"][0]]))
def _carries_receipt(o): _f0(o, receipt_file_sha256=sorted(o["resolved_issues"][0]["receipt_file_sha256"] + [o["content_blob_digests"][0]]))
def _writer_is_emitter(o): _f0(o, emitter_session=wi.derive_branch_writer(o["push_receipts"], o["change_commits"],
                                                                         target_repository=o["target_repository"],
                                                                         change_id=o["change_id"])["session"])
def _not_s1(o): _f0(o, verifier_ref="SV-LLM/.github#460")
def _second_issue(o): _f0(o, derived_issue_ids_from_receipt=sorted(o["resolved_issues"][0]["derived_issue_ids_from_receipt"] + ["svi:" + "e" * 64]))
def _already_resolved(o): _f0(o, resolved_by="svc:" + "e" * 64)
def _migrated_change(o): o["record_mode"] = "MIGRATED_HISTORICAL"
# UNKNOWN_IN_NATIVE_RECORD (orchestrator decision): a NATIVE record field holding the sentinel is FAIL_CLOSED, never DENY
def _unknown_owning_goal(o): o["native_unknown_pointers"] = sorted(set(o["native_unknown_pointers"]) | {"/owning_goal"})
def _migrated_issue(o): _f0(o, record_mode="MIGRATED_HISTORICAL")
# NATIVE_RECORD_HB_EPOCH_IS_A_STRING (commit 4): an integer epoch is an observed, malformed value -> DENY HB_EPOCH_MISMATCH
def _int_epoch(o): o["supplied_hb_epoch"] = int(o["supplied_hb_epoch"])
# READBACK_SHAPE_MATCHES_PINNED_PRODUCER (ruling ~17:05Z): the void Labs#3266 2ba0e329 shape (marker under hb_epoch_cross_check)
def _void_2ba0e329_shape(o): _reseal_readback(o, cross_checked=False, hb_epoch_cross_check="HB_EPOCH_NOT_CROSS_CHECKED")
def _strip_cross_checked(o):  # ruling ~17:15Z: cross_checked / detail stripped, then resealed (a self-seal proves no path)
    rb = {k: v for k, v in o["hb_epoch_readback"].items() if k not in ("result_sha256", "cross_checked", "detail", wi.READBACK_SUPPLIED_FIELD)}
    o["hb_epoch_readback"] = wi.seal(rb, "result_sha256")
# GATE_RECEIPT_PAIR_RESOLVES_GATE_DERIVED_ISSUE (commit 4): the resolution_pair fact derive_resolved_issue_facts builds
def _pair(o): return o["resolved_issues"][0]["resolution_pair"]
def _rebind(side):  # the side's receipt keeps binding its (mutated) subject, so the mutation fires its own predicate
    side["subject_digest"] = wi.stage_evaluation_digest(side["subject"])
    side["receipt"] = {**side["receipt"], "change_digest": side["subject_digest"], "head_sha": side["subject"]["evaluated_commit"]}
def _pair_base_unledgered(o): _pair(o)["base"]["receipt"]["ledgered_at_base"] = False
def _pair_no_head(o): _pair(o)["head"] = None
def _pair_head_failing(o): _pair(o)["head"]["receipt"]["disposition"] = "FAIL_CLOSED"
def _pair_head_unbound(o): _pair(o)["head"]["receipt"]["change_digest"] = "sha256:" + "0" * 64
def _pair_head_other_repo(o):
    h = _pair(o)["head"]; h["subject"]["repository"] = "StegVerse-org/.github"; _rebind(h)
def _pair_head_other_manifest(o):
    h = _pair(o)["head"]; h["subject"]["manifest_blob"] = "f" * 40; _rebind(h)
def _pair_read_from_subject(o):  # both subjects bind a blob other than the contract-pinned one (read from the subject)
    for k in ("base", "head"):
        side = _pair(o)[k]; side["subject"]["manifest_blob"] = "e" * 40; _rebind(side)
def _pair_pins_unobserved(o): _pair(o)["pinned_manifest"] = None
def _pair_base_at_head(o):
    b = _pair(o)["base"]; b["subject"]["evaluated_commit"] = _pair(o)["change_commits"]["head_commit"]; _rebind(b)
def _pair_commits_unobserved(o): _pair(o)["change_commits"] = {"base_commit": None, "head_commit": None}


PREDICATE_BINDINGS: dict[str, tuple[str, list[tuple[str, str, Callable]]]] = {
    "BRANCH_WRITER_IS_BRANCH_OWNER": ("BRANCH_HAS_FOREIGN_WRITER", [
        ("writer_sessions", "add a writer that is not the session derived from the sv-push-receipt chain", _foreign)]),
    "BASE_IS_CURRENT": ("BASE_STALE", [
        ("current_base.registry_generation", "registry generation moved after proposal", _stale_gen),
        ("current_base.ledger_head", "organization-ledger head moved after proposal", _stale_head)]),
    "MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED": ("CHECK_SKIPPED_OR_UNOBSERVED", [
        ("validation_receipts[required_check_ids[0]]", "a required check has no receipt (skipped)", _drop_first_check),
        ("validation_receipts[*].ref", "checks reported but unreceipted", _unreceipt),
        ("validation_receipts[*].evidence_class", "checks evidenced by an observed artifact, not a ledger receipt", _artifact_only)]),
    "RECEIPT_CHANGE_DIGEST_EQUALS_HEAD": ("CHECK_SKIPPED_OR_UNOBSERVED", [
        ("validation_receipts[*].change_digest", "receipts from another head", _off_head)]),
    "AUTHORIZATION_BINDS_FULL_REQUEST": ("REQUEST_DIGEST_MISMATCH", [
        ("bound_request_digest", "decision bound to a different request", _req_digest)]),
    # RETIRED as an admission predicate (Lane C alignment, TVC#531): the PR-body / record author-session declaration grants
    # nothing; the branch writer is derived from the sv-push-receipt chain (sv_work_items.derive_branch_writer). The key stays
    # only so the frozen class id ASC-PR_AUTHOR_SESSION_DECLARED@schema and its scenario ids never move (CORPUS_IS_APPEND_ONLY);
    # its one axis is re-derived: a declared_session label with no push-receipt chain FAIL_CLOSEs BRANCH_WRITER_UNOBSERVED.
    "PR_AUTHOR_SESSION_DECLARED": ("BRANCH_WRITER_UNOBSERVED", [
        ("declared_session", "declared_session present but no sv-push-receipt chain: a declaration is not writer evidence", _declared_label_only)]),
    "REQUIRED_SIGNOFF_RECORDED": ("SIGNOFF_RECEIPT_ABSENT", [
        ("signoffs", "required role sign-off absent", _drop_signoff),
        ("signoffs[*].receipt_ref", "sign-off claimed without receipt", _unreceipt_signoff)]),
    "CHECK_PASSES": ("REQUIRED_CHECK_DENIED", [
        ("validation_receipts[0].disposition", "a required check refused (DENY)", _fail_check)]),
    "CHECK_RECEIPT_DISPOSITION_IS_ALLOW": ("CHECK_SKIPPED_OR_UNOBSERVED", [
        ("validation_receipts[0].disposition", "a required check failed closed", _fail_closed_check)]),
    # an axis may carry a 4th element: its own expected failure code (then its disposition is DISPOSITION_OF[code])
    "ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH": ("HB_EPOCH_SOURCE_UNOBSERVED", [
        ("hb_epoch_readback", "no base-state readback receipt for the bound ledger head", _no_readback),
        ("hb_epoch_readback.result_sha256", "the readback receipt is not sealed (result_sha256 does not verify)", _unsealed_readback),
        ("hb_epoch_readback.hb_epoch_source.derived_from_clock", "the sealed epoch's source reference is derived from a clock",
         _clock_epoch),
        ("hb_epoch_readback.hb_epoch", "the sealed epoch slot is not an integer (a JSON float)", _non_int_epoch),
        ("supplied_hb_epoch", "the SV_CHANGE carries an epoch other than the sealed readback epoch", _other_epoch, "HB_EPOCH_MISMATCH")]),
    # STAGE_GATE_RECEIPT_DERIVES_NATIVE_ISSUE (c): until the receipt is on the ledger the change resolves nothing (#3264)
    "CHANGE_RESOLVES_CLAIMED_SV_ISSUES": ("SV_CHANGE_RESOLVES_NOTHING", [
        ("resolves", "the change cites no SV_ISSUE (#3264 before its gate receipt is ledgered)", _no_resolves),
        ("resolved_issues", "the cited issue's receipt is not on the ledger, so no issue is derived from it", _receipt_not_ledgered),
        ("resolves[+unobserved]", "the change also cites an svi: id no observed issue carries", _extra_unobserved, "RESOLVED_ISSUE_UNOBSERVED")]),
    # (a) emitted by the S1 verifier and appended by the org writer, never minted or ledgered by the resolving change
    "RESOLVING_CHANGE_DID_NOT_SOURCE_ITS_ISSUE": ("SV_CHANGE_SELF_SOURCED_ISSUE", [
        ("resolved_issues[0].receipt_ledger_paths", "the change touches the receipt's ledger path", _touches_receipt_path),
        ("resolved_issues[0].receipt_file_sha256", "the change carries the receipt's bytes", _carries_receipt),
        ("resolved_issues[0].emitter_session", "the change's writer is the receipt's emitter", _writer_is_emitter),
        ("resolved_issues[0].verifier_ref", "the receipt's verifier_ref is not the NWI-S1 verifier (SV-LLM/.github#460)", _not_s1)]),
    # (b) one receipt derives exactly one issue, resolved by exactly one change
    "ONE_RECEIPT_DERIVES_ONE_ISSUE": ("SV_ISSUE_SOURCE_RECEIPT_COLLISION", [
        ("resolved_issues[0].derived_issue_ids_from_receipt", "a second issue names the same source receipt", _second_issue)]),
    "RECEIPT_DERIVED_ISSUE_IS_RESOLVED_ONCE": ("SV_ISSUE_ALREADY_RESOLVED", [
        ("resolved_issues[0].resolved_by", "another change already resolved the receipt-derived issue", _already_resolved)]),
    # (d) migrated records (GitHub issues migrated as MIGRATED_HISTORICAL) are never admissible
    "ADMITTED_RECORDS_ARE_NATIVE": ("HISTORICAL_RECORD_NOT_ADMISSIBLE", [
        ("record_mode", "the SV_CHANGE is MIGRATED_HISTORICAL", _migrated_change),
        ("resolved_issues[0].record_mode", "the cited issue is a migrated (MIGRATED_HISTORICAL) GitHub issue", _migrated_issue)]),
    "NATIVE_RECORD_FIELDS_ARE_OBSERVED": ("UNKNOWN_IN_NATIVE_RECORD", [
        ("owning_goal[UNKNOWN]", "the NATIVE SV_CHANGE's owning_goal is UNKNOWN_NOT_AUTHENTICALLY_OBSERVED (FAIL_CLOSED, never DENY)",
         _unknown_owning_goal)]),
    # the BASE-side failing gate receipt sources the issue, the HEAD-side ALLOW gate receipt resolves it (orchestrator 16:58Z)
    "GATE_RECEIPT_PAIR_RESOLVES_GATE_DERIVED_ISSUE": ("GATE_PAIR_HEAD_RECEIPT_MISSING", [
        ("resolved_issues[0].resolution_pair.head", "no head-side ALLOW gate receipt on the ledger at the change's base ledger_head",
         _pair_no_head),
        ("resolved_issues[0].resolution_pair.base.receipt.ledgered_at_base", "the base-side failing gate receipt is not on the ledger "
         "at the change's base ledger_head", _pair_base_unledgered, "GATE_PAIR_BASE_RECEIPT_MISSING"),
        ("resolved_issues[0].resolution_pair.head.receipt.change_digest", "the head receipt does not bind its stage-evaluation subject",
         _pair_head_unbound, "GATE_PAIR_SUBJECT_NOT_BOUND_BY_RECEIPT"),
        ("resolved_issues[0].resolution_pair.head.receipt.disposition", "the head-side gate receipt failed closed (not ALLOW)",
         _pair_head_failing, "GATE_PAIR_HEAD_RECEIPT_NOT_ALLOW"),
        ("resolved_issues[0].resolution_pair.head.subject.repository", "the head subject is another repository's evaluation",
         _pair_head_other_repo, "GATE_PAIR_REPOSITORY_MISMATCH"),
        ("resolved_issues[0].resolution_pair.head.subject.manifest_blob", "the head subject binds another manifest blob (an exact "
         "match is required)", _pair_head_other_manifest, "GATE_PAIR_MANIFEST_MISMATCH"),
        ("resolved_issues[0].resolution_pair.pinned_manifest", "the gate declaration's contract-pins.json is not supplied",
         _pair_pins_unobserved, "GATE_PAIR_PINNED_MANIFEST_UNOBSERVED"),
        ("resolved_issues[0].resolution_pair.*.subject.manifest_blob", "both subjects' manifest was read from the subject, not the "
         "contract-pinned manifest", _pair_read_from_subject, "GATE_MANIFEST_READ_FROM_SUBJECT"),
        ("resolved_issues[0].resolution_pair.base.subject.evaluated_commit", "the base receipt's subject is at the change's head commit, "
         "not its base commit", _pair_base_at_head, "GATE_PAIR_SUBJECT_COMMIT_WRONG"),
        ("resolved_issues[0].resolution_pair.change_commits", "the change's base and head commits are not observed",
         _pair_commits_unobserved, "GATE_PAIR_CHANGE_COMMITS_UNOBSERVED")]),
}
DENY_CODES = ("BASE_STALE", "REQUIRED_CHECK_DENIED", "HB_EPOCH_MISMATCH", "SV_CHANGE_RESOLVES_NOTHING", "SV_CHANGE_SELF_SOURCED_ISSUE",
              "SV_ISSUE_ALREADY_RESOLVED", "GATE_PAIR_SUBJECT_NOT_BOUND_BY_RECEIPT", "GATE_PAIR_HEAD_RECEIPT_NOT_ALLOW",
              "GATE_PAIR_REPOSITORY_MISMATCH", "GATE_PAIR_MANIFEST_MISMATCH", "GATE_PAIR_SUBJECT_COMMIT_WRONG",
              "GATE_MANIFEST_READ_FROM_SUBJECT")
def disposition_of(code: str) -> str: return "DENY" if code in DENY_CODES else "FAIL_CLOSED"
PREDICATE_ALIASES: dict[str, str] = {}
# Axes a predicate binds under a second failure code. generalize adds them (each axis names its own expected code)
# only when a harvested candidate carries that code; a seed generalized from the predicate alone does not get them.
SECONDARY_AXES: dict[tuple[str, str], list[tuple[str, str, Callable]]] = {
    ("BRANCH_WRITER_IS_BRANCH_OWNER", "BRANCH_WRITER_UNOBSERVED"): [
        ("content[*].writer_session.evidence_class", "writer evidence lost: every writer_session UNKNOWN_NOT_AUTHENTICALLY_OBSERVED and no sv-push-receipt chain",
         _writer_evidence_lost)]}
# A harvested class name that the class rule (failed predicate + surface kind) maps onto an existing class id is
# recorded as an alias of that class, never as a duplicate class.
CLASS_ALIASES: dict[str, str] = {
    "WRITER_EVIDENCE_LOST_BY_SNAPSHOT_RESTORE": "ASC-BRANCH_WRITER_IS_BRANCH_OWNER@transition"}


# Axes a later ruling adds to an existing class (generalize(ruling=...) -> the next class version, appended through
# SCENARIO_CORPUS_APPEND; earlier versions and their scenarios are never rewritten).
RULING_AXES: dict[tuple[str, str], list[tuple]] = {
    ("ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH", "UNKNOWN_IS_FAIL_CLOSED_NEVER_DENY"): [
        ("supplied_hb_epoch[UNKNOWN]", "the SV_CHANGE's hb_epoch is the UNKNOWN_NOT_AUTHENTICALLY_OBSERVED sentinel (FAIL_CLOSED, "
         "never DENY; precedes c9192134)", _unknown_epoch, "HB_EPOCH_SOURCE_UNOBSERVED")],
    ("ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH", "NATIVE_RECORD_HB_EPOCH_IS_A_STRING"): [
        ("supplied_hb_epoch[int]", "the NATIVE SV_CHANGE's hb_epoch is a JSON integer, not the epoch string (observed, malformed: "
         "DENY, never FAIL_CLOSED)", _int_epoch, "HB_EPOCH_MISMATCH")],
    ("ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH", "READBACK_SHAPE_MATCHES_PINNED_PRODUCER"): [
        ("hb_epoch_readback.hb_epoch_cross_check", "the readback carries hb_epoch_cross_check (the void Labs#3266 2ba0e329 shape): not "
         "produced by the pinned readback, so not authentically observed (FAIL_CLOSED, never DENY)", _void_2ba0e329_shape,
         "HB_EPOCH_SOURCE_UNOBSERVED"),
        ("hb_epoch_readback.cross_checked[stripped]", "the readback's cross_checked (and marker) were stripped and the body resealed: "
         "the producer always emits cross_checked and a self-seal cannot prove which path ran (FAIL_CLOSED, never DENY)",
         _strip_cross_checked, "HB_EPOCH_SOURCE_UNOBSERVED")]}


def _axis_mutator(pred: str, field: str) -> Callable:
    for (p, _), axes in [((pred, None), PREDICATE_BINDINGS[pred][1])] + [(k, v) for k, v in SECONDARY_AXES.items() if k[0] == pred] \
            + [(k, v) for k, v in RULING_AXES.items() if k[0] == pred]:
        for f, _, fn, *_ in axes:
            if f == field:
                return fn
    raise _fail("PREDICATE_BINDING_UNDECLARED", "FAILED_PREDICATE_HAS_DECLARED_BINDINGS", "declare the axis", "generate", axis=field)
# A failure code shared by two predicates (TVC#519: CHECK_SKIPPED_OR_UNOBSERVED under MERGE_READY_... and
# RECEIPT_CHANGE_DIGEST_EQUALS_HEAD) names no single predicate, so it is not a fallback key: such a candidate must
# carry its failed_predicate, else PREDICATE_BINDING_UNDECLARED.
_CODES = [v[0] for v in PREDICATE_BINDINGS.values()]
FAILURE_CODE_TO_PREDICATE = {v[0]: k for k, v in PREDICATE_BINDINGS.items() if _CODES.count(v[0]) == 1}


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
            if r.get("source_receipt_ref") is not None:  # a report locator, not a ledger receipt: carried with its flags
                ref.update({k: r[k] for k in ("source_receipt_ref", "unobserved_fields", "observed_case", "class_name") if k in r})
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
               class_version: int = 1, supersedes: str | None = None, prior: Mapping[str, Any] | None = None,
               provenance_unobserved: list[str] | None = None, ruling: str | None = None) -> dict[str, Any]:
    """Class rule: failed predicate + surface kind. A candidate whose code is a declared secondary code of the predicate
    adds that code's axes; with `prior` (the current version) the axes and provenance are carried forward."""
    pred = candidate.get("failed_predicate")
    pred = PREDICATE_ALIASES.get(candidate.get("failure_code"), pred)
    if pred not in PREDICATE_BINDINGS:
        pred = FAILURE_CODE_TO_PREDICATE.get(candidate.get("failure_code"), pred)
    if pred not in PREDICATE_BINDINGS:
        raise _fail("PREDICATE_BINDING_UNDECLARED", "FAILED_PREDICATE_HAS_DECLARED_BINDINGS",
                    "declare the predicate's bound fields in PREDICATE_BINDINGS (or answer via JDQ Q-SCENARIO-GENERALIZATION)",
                    "generalize", failed_predicate=pred)
    code, axes = PREDICATE_BINDINGS[pred]
    mutation_axes = [{"field": a[0], "bound_value_source": "positive_control", "mutation": a[1],
                      **({"expected_failure_code": a[3], "expected_disposition": disposition_of(a[3])} if len(a) > 3 else {})}
                     for a in axes]
    for a in (prior or {}).get("mutation_axes") or []:
        if a["field"] not in {x["field"] for x in mutation_axes}:
            mutation_axes.append(dict(a))
    for a in RULING_AXES.get((pred, ruling), []) if ruling else []:
        if a[0] not in {x["field"] for x in mutation_axes}:
            mutation_axes.append({"field": a[0], "bound_value_source": "positive_control", "mutation": a[1],
                                  "expected_failure_code": a[3], "expected_disposition": disposition_of(a[3])})
    code2 = candidate.get("failure_code")
    for f, m, _ in SECONDARY_AXES.get((pred, code2), []) if code2 != code else []:
        if f not in {x["field"] for x in mutation_axes}:
            mutation_axes.append({"field": f, "bound_value_source": "positive_control", "mutation": m, "expected_failure_code": code2})
    prov_prior = (prior or {}).get("provenance") or {}
    origin_scenarios = sorted(set(origin_scenarios) | set(prov_prior.get("origin_scenarios") or []))
    aliases = sorted(set(prov_prior.get("class_aliases") or []) | {n for n, c in CLASS_ALIASES.items()
                                                                     if c == class_id_for(pred, surface) and n == candidate.get("class_name")})
    body = {"schema": CLASS_SCHEMA, "class_id": class_id_for(pred, surface), "class_version": class_version,
            "supersedes": supersedes, "predicate": pred, "expected_failure_code": code,
            "expected_disposition": disposition_of(code),
            "surfaces": [{"kind": surface}],
            "mutation_axes": mutation_axes,
            "positive_controls": ["PC-" + surface],
            "provenance": {"origin_scenarios": origin_scenarios, "harvest_receipt_ref": harvest_receipt_ref,
                           "rule_refs": rule_refs, "declared_by_session": declared_by_session, **({"class_aliases": aliases} if aliases else {}),
                           **({"unobserved_fields": sorted(provenance_unobserved)} if provenance_unobserved else {})},
            "hb_epoch": str(hb_epoch)}
    return wi.seal(body, "class_sha256")


def generate(cls: Mapping[str, Any], known_good: Mapping[str, Any], *, hb_epoch: Any) -> list[dict[str, Any]]:
    """One mutation-negative per bound field plus the positive control."""
    base = {"schema": SCENARIO_SCHEMA, "scenario_class": cls["class_id"], "origin": "SEED",
            "source": {"class_sha256": cls["class_sha256"]}, "hb_epoch": str(hb_epoch)}
    out = [wi.seal({**base, "scenario_id": cls["positive_controls"][0] + "/" + cls["class_id"], "observed_inputs": copy.deepcopy(dict(known_good)),
                    "expected_disposition": "ALLOW", "expected_failure_code": None,
                    "generated_from": {"class_id": cls["class_id"], "axis": None}}, "scenario_sha256")]
    for axis in cls["mutation_axes"]:
        field = axis["field"]
        obs = copy.deepcopy(dict(known_good)); _axis_mutator(cls["predicate"], field)(obs)
        out.append(wi.seal({**base, "scenario_id": cls["class_id"] + "/" + field, "observed_inputs": obs,
                            "expected_disposition": axis.get("expected_disposition", cls["expected_disposition"]),
                            "expected_failure_code": axis.get("expected_failure_code", cls["expected_failure_code"]),
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
                  evaluator: Callable[..., dict] | None = None) -> dict[str, Any]:
    """SCENARIO_CORPUS_APPEND. ALLOW returns the lines to append and the six-field-ready outcome. The corpus is a
    fixture context (positive controls carry fixture receipts), so the default evaluator runs in fixture_mode."""
    evaluator = evaluator or (lambda obs, **kw: wi.evaluate_admission(obs, fixture_mode=True, **kw))
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
        # a superseding version is covered by the class's lines already in the corpus plus the appended ones; every
        # one of them is re-evaluated against the new version below
        mine = [s for s in (corpus_lines if prev is not None else []) + scenarios if s["scenario_class"] == new_class["class_id"]]
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
