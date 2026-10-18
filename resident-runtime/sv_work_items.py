"""StegVerse-native work items: SV_ISSUE and SV_CHANGE (WORK_ITEMS_ARE_TASK_REGISTRY_NATIVE).

An SV_ISSUE is a Task Registry work record whose body is a six-field non-ALLOW
disposition, the invariant it violates and the receipt it was observed in. An
SV_CHANGE is the PR analogue: a content-addressed proposed transition bound to
its base (registry generation plus organization-ledger head), its declared
author session and the SV_ISSUEs it resolves. GitHub is a one-way projection.

Every lifecycle step is a transition declared in
data/sv-work-items/lifecycle-transitions.json. `transition()` evaluates it and
returns ALLOW/DENY/FAIL_CLOSED (six fields on every non-ALLOW); `record()`
hands the outcome, refusals included, to the existing repository emitter
(.stegverse/transition-ledger/emit.py::append) with the supplied epoch, whose
receipt the organization ledger aggregates. The supplied-epoch rule is
org-kernel/kernel.py::supplied_epoch_failure. Stdlib only, no clock, no
network, no environment read.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("sv_work_items_kernel", ROOT / "org-kernel/kernel.py")
kernel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kernel)

ISSUE_SCHEMA = "stegverse.sv_issue.v1"
CHANGE_SCHEMA = "stegverse.sv_change.v1"
LIFECYCLE = json.loads((ROOT / "data/sv-work-items/lifecycle-transitions.json").read_text())
REQUIRED_CHECKS = json.loads((ROOT / "data/sv-work-items/required-checks.json").read_text())
OWNING_GOAL = "StegVerse-org/.github#163 (WORK_ITEMS_ARE_TASK_REGISTRY_NATIVE)"
EPOCH_PREDICATE = "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
DISPOSITIONS = ("ALLOW", "DENY", "FAIL_CLOSED")
ISSUE_STATES = ("OPENED", "CLAIMED", "RESOLVED", "CLOSED_BY_INVARIANT", "SUPERSEDED")
CHANGE_STATES = ("PROPOSED", "VERIFIED", "ADMITTED", "DENIED", "FAIL_CLOSED", "APPLIED", "SUPERSEDED", "WITHDRAWN")
RESOLUTION_CLASSES = ("A", "B", "C", "D")
SOURCE_KINDS = ("ORGANIZATION_LEDGER_RECEIPT", "REPOSITORY_LEDGER_RECEIPT", "MIGRATION_EVIDENCE")
SURFACE_KINDS = ("workflow", "transition", "schema", "ledger_writer", "registry", "doc")
# Record mode. A MIGRATED_HISTORICAL record carries history that predates the
# native path; it may hold UNKNOWN only at the pointers listed below (and must
# list each one in unknown_fields), and it is never admissible. It becomes NATIVE
# only through a superseding record whose values are observed.
UNKNOWN = "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"
RECORD_MODES = ("NATIVE", "MIGRATED_HISTORICAL")
MIGRATED_UNKNOWN_ALLOWED = {
    "SV_ISSUE": ("/hb_epoch", "/resolution_class", "/owning_goal", "/disposition/owning_existing_goal", "/surface",
                 "/restatements/*/owning_existing_goal"),
    "SV_CHANGE": ("/hb_epoch", "/owning_goal"),
}
MIGRATION_FLAG_RESOLVES = "RESOLVES_NOT_RECORDED"
WRITER_EVIDENCE = ("DECLARED", "OBSERVED_COMMIT_TRAILER", UNKNOWN)
VALIDATION_EVIDENCE = ("LEDGER_RECEIPT", "OBSERVED_ARTIFACT")  # only LEDGER_RECEIPT counts toward VERIFIED
# Fields outside the full-request digest (TVC#527 pattern: everything else,
# including any field added later, is bound by default).
CHANGE_NON_REQUEST_FIELDS = frozenset({"_note", "request_digest", "lifecycle_state", "validation_receipts",
                                       "signoffs", "governance_decision_ref", "projection", "hb_epoch", "superseded_by"})
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
LEDGER_REF = "refs/stegverse/organization-ledger"


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(value: Any) -> str:
    raw = value if isinstance(value, (bytes, bytearray)) else canon(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def seal(body: Mapping[str, Any], field: str) -> dict[str, Any]:
    clean = {k: v for k, v in body.items() if k != field}
    return {**clean, field: sha(clean)}


class Refusal(Exception):
    def __init__(self, disposition: str, code: str, predicate: str, repair: str, entry: str, nxt: str, **detail: Any):
        super().__init__(code)
        self.record = {"disposition": disposition, "failure_code": code, "failed_predicate": predicate,
                       "required_evidence_or_repair": repair, "retry_entrypoint": "resident-runtime/sv_work_items.py::" + entry,
                       "owning_existing_goal": OWNING_GOAL, "next_attempt": nxt, **detail}


def _fail(code, predicate, repair, entry, nxt="resubmit the corrected record; nothing was recorded as ALLOW", **d):
    return Refusal("FAIL_CLOSED", code, predicate, repair, entry, nxt, **d)


def _deny(code, predicate, repair, entry, nxt="propose a successor record bound to the observed state", **d):
    return Refusal("DENY", code, predicate, repair, entry, nxt, **d)


def epoch_check(hb_epoch: Any, entry: str) -> str:
    failure = kernel.supplied_epoch_failure(hb_epoch)
    if failure is not None:
        code, detail = failure
        raise _fail(code, EPOCH_PREDICATE, "supply hb_epoch as ASCII digits with value >= 32; it is never derived from a clock",
                    entry, "resubmit with the supplied epoch; nothing was written", detail=detail)
    return str(hb_epoch)


def _str(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _base_ok(base: Any) -> bool:
    return (isinstance(base, Mapping) and isinstance(base.get("registry_generation"), int)
            and not isinstance(base.get("registry_generation"), bool) and base["registry_generation"] >= 0
            and isinstance(base.get("ledger_head"), str) and GIT_SHA.match(base["ledger_head"]) is not None)


# ------------------------------------------------------------------ SV_ISSUE
def source_receipt_ref(src: Mapping[str, Any]) -> str:
    """The receipt (or migration evidence) an issue was observed in, as one normalized reference."""
    if src.get("kind") == "MIGRATION_EVIDENCE":
        return "migration:%s@%s" % (src.get("evidence_path"), src.get("evidence_sha256"))
    return "%s@%s" % (src.get("ledger_ref"), src.get("receipt_sha256"))


def issue_identity_inputs(rec: Mapping[str, Any]) -> dict[str, Any]:
    inv = rec.get("violated_invariant") or {}
    return {"violated_invariant": {k: inv.get(k) for k in ("repository", "file", "rule_id")},
            "failed_predicate": (rec.get("disposition") or {}).get("failed_predicate"),
            "surface": rec.get("surface"),
            "source_receipt_ref": source_receipt_ref(rec.get("source_receipt") or {})}


def issue_identity(rec: Mapping[str, Any]) -> str:
    """issue_id = "svi:" + sha256(canon({violated_invariant{repository,file,rule_id}, failed_predicate, surface,
    source_receipt_ref})). No free text: a reworded restatement of the same failure is the same issue."""
    return "svi:" + sha(issue_identity_inputs(rec))[7:]


def sentinel_pointers(rec: Any, path: str = "") -> list[str]:
    """JSON pointers holding UNKNOWN (exact or embedded). /projection is a non-authority view and is not scanned;
    writer_session.evidence_class is an enum whose value happens to be the sentinel."""
    out: list[str] = []
    if isinstance(rec, Mapping):
        for k, v in rec.items():
            p = path + "/" + str(k)
            if p == "/projection" or (k == "evidence_class" and "/writer_session" in path):
                continue
            out += sentinel_pointers(v, p)
    elif isinstance(rec, list):
        for i, v in enumerate(rec):
            out += sentinel_pointers(v, path + "/" + str(i))
    elif isinstance(rec, str) and UNKNOWN in rec:
        out.append(path or "/")
    return out


def _pointer_match(pointer: str, allowed: str) -> bool:
    a, b = pointer.split("/"), allowed.split("/")
    return len(a) == len(b) and all(y == x or (y == "*" and x.isdigit()) for x, y in zip(a, b))


def mode_check(rec: Mapping[str, Any], kind: str, base_field: str, e: str) -> str:
    mode = rec.get("record_mode")
    if mode not in RECORD_MODES:
        raise _deny("RECORD_MODE_INVALID", "RECORD_MODE_DECLARED", "record_mode NATIVE or MIGRATED_HISTORICAL", e)
    found = sentinel_pointers(rec)
    if mode == "NATIVE":
        if found:
            raise _deny("UNKNOWN_IN_NATIVE_RECORD", "NATIVE_RECORD_FIELDS_ARE_OBSERVED",
                        "observe every field, or record the history as MIGRATED_HISTORICAL", e, unknown=found)
        extra = [k for k in ("unknown_fields", "migration_provenance", "migration_flags") if k in rec]
        if extra:
            raise _deny("MIGRATION_FIELDS_ON_NATIVE_RECORD", "NATIVE_RECORD_FIELDS_ARE_OBSERVED",
                        "a NATIVE record carries no migration fields", e, fields=extra)
        return mode
    listed = rec.get("unknown_fields")
    if not isinstance(listed, list) or sorted(set(listed)) != sorted(found) or len(listed) != len(found):
        raise _deny("UNKNOWN_FIELDS_NOT_DECLARED", "MIGRATED_UNKNOWN_ONLY_WHERE_LISTED",
                    "unknown_fields lists exactly the pointers that hold " + UNKNOWN, e, found=sorted(found), listed=listed)
    bad = sorted(p for p in found if not any(_pointer_match(p, allowed) for allowed in MIGRATED_UNKNOWN_ALLOWED[kind]))
    if bad:
        raise _deny("UNKNOWN_FIELD_NOT_PERMITTED", "MIGRATED_UNKNOWN_ONLY_WHERE_LISTED",
                    "observe these fields; UNKNOWN is permitted only at " + ", ".join(MIGRATED_UNKNOWN_ALLOWED[kind]), e, fields=bad)
    mp = rec.get("migration_provenance")
    if not isinstance(mp, Mapping) or set(mp) != {"original_base_observed", "original_base_ref", "migrated_at_base"} \
            or not isinstance(mp["original_base_observed"], bool) or not _base_ok(mp["migrated_at_base"]) \
            or mp["migrated_at_base"] != rec.get(base_field) \
            or (mp["original_base_observed"] and not _base_ok(mp["original_base_ref"])) \
            or (not mp["original_base_observed"] and mp["original_base_ref"] is not None):
        raise _deny("MIGRATION_PROVENANCE_INVALID", "MIGRATED_RECORD_NAMES_ITS_BASES",
                    "migration_provenance{original_base_observed bool, original_base_ref base|null (null iff not observed), "
                    "migrated_at_base == " + base_field + "}", e)
    return mode


def _epoch_or_unknown(rec: Mapping[str, Any], e: str) -> None:
    if rec.get("hb_epoch") == UNKNOWN and rec.get("record_mode") == "MIGRATED_HISTORICAL":
        return  # listed and permitted by mode_check; such a record is never admissible
    epoch_check(rec.get("hb_epoch"), e)


def validate_issue(rec: Any) -> dict[str, Any]:
    e = "validate_issue"
    if not isinstance(rec, Mapping) or rec.get("schema") != ISSUE_SCHEMA:
        raise _deny("SV_ISSUE_SCHEMA_MISMATCH", "RECORD_SCHEMA_IS_" + ISSUE_SCHEMA, "supply a stegverse.sv_issue.v1 record", e)
    d = rec.get("disposition")
    if not isinstance(d, Mapping) or d.get("disposition") not in ("DENY", "FAIL_CLOSED"):
        raise _deny("SV_ISSUE_BODY_NOT_NON_ALLOW", "ISSUE_BODY_IS_SIX_FIELD_NON_ALLOW",
                    "the issue body is a DENY or FAIL_CLOSED disposition", e)
    missing = [f for f in SIX_FIELDS if not _str(d.get(f))]
    if missing:
        raise _deny("SV_ISSUE_SIX_FIELDS_INCOMPLETE", "ISSUE_BODY_IS_SIX_FIELD_NON_ALLOW", "fill every one of the six fields", e, missing=missing)
    inv = rec.get("violated_invariant")
    if not isinstance(inv, Mapping) or not _str(inv.get("rule_id")) or not _str(inv.get("file")):
        raise _deny("SV_ISSUE_INVARIANT_UNNAMED", "ISSUE_NAMES_VIOLATED_INVARIANT",
                    "name the violated invariant by rule_id and file (blob_sha when the file is in a repository)", e)
    src = rec.get("source_receipt")
    if not isinstance(src, Mapping) or src.get("kind") not in SOURCE_KINDS:
        raise _deny("SV_ISSUE_SOURCE_RECEIPT_ABSENT", "ISSUE_NAMES_SOURCE_RECEIPT", "name the receipt the failure was observed in", e)
    if src["kind"] == "MIGRATION_EVIDENCE":
        if not _str(src.get("evidence_path")) or not isinstance(src.get("evidence_sha256"), str) or not DIGEST.match(src["evidence_sha256"]):
            raise _deny("SV_ISSUE_SOURCE_RECEIPT_ABSENT", "ISSUE_NAMES_SOURCE_RECEIPT",
                        "migration evidence names its path and sha256; the OPEN receipt becomes its ledger receipt", e)
    elif not isinstance(src.get("receipt_sha256"), str) or not DIGEST.match(src["receipt_sha256"]) or not str(src.get("ledger_ref", "")).startswith("refs/"):
        raise _deny("SV_ISSUE_SOURCE_RECEIPT_ABSENT", "ISSUE_NAMES_SOURCE_RECEIPT", "a ledger source names ledger_ref and receipt_sha256", e)
    mode_check(rec, "SV_ISSUE", "observed_base", e)
    if rec.get("resolution_class") not in RESOLUTION_CLASSES + (UNKNOWN,):
        raise _deny("SV_ISSUE_CLASS_INVALID", "ISSUE_RESOLUTION_CLASS_IS_A_B_C_OR_D", "classify the issue A, B, C or D", e)
    sf = rec.get("surface")
    if sf != UNKNOWN and not (isinstance(sf, Mapping) and set(sf) == {"kind", "path"} and sf.get("kind") in SURFACE_KINDS and _str(sf.get("path"))):
        raise _deny("SV_ISSUE_SURFACE_INVALID", "ISSUE_NAMES_SURFACE", "surface{kind in " + "/".join(SURFACE_KINDS) + ", path}", e)
    if not _str(rec.get("owning_goal")):
        raise _deny("SV_ISSUE_GOAL_ABSENT", "ISSUE_NAMES_OWNING_GOAL", "name the owning goal", e)
    for r in rec.get("restatements") or []:
        if not isinstance(r, Mapping) or any(not _str(r.get(f)) for f in SIX_FIELDS):
            raise _deny("SV_ISSUE_RESTATEMENT_INVALID", "ISSUE_BODY_IS_SIX_FIELD_NON_ALLOW", "each restatement is a six-field body", e)
    if rec.get("lifecycle_state") not in ISSUE_STATES:
        raise _deny("SV_ISSUE_STATE_INVALID", "LIFECYCLE_STATE_DECLARED", "one of " + ", ".join(ISSUE_STATES), e)
    if not _base_ok(rec.get("observed_base")):
        raise _deny("SV_ISSUE_BASE_UNBOUND", "BASE_BOUND_TO_REGISTRY_GENERATION_AND_LEDGER_HEAD",
                    "observed_base{registry_generation int, ledger_head 40-hex}", e)
    if not _str(rec.get("opened_by_session")):
        raise _deny("AUTHOR_SESSION_NOT_DECLARED", "PR_AUTHOR_SESSION_DECLARED", "name the opening session", e)
    if rec.get("issue_id") != issue_identity(rec):
        raise _deny("SV_ISSUE_IDENTITY_MISMATCH", "ISSUE_IDENTITY_IS_CONTENT_ADDRESSED", "issue_id = issue_identity(record)", e,
                    expected=issue_identity(rec))
    _epoch_or_unknown(rec, e)
    if rec.get("issue_sha256") != sha({k: v for k, v in rec.items() if k != "issue_sha256"}):
        raise _fail("SV_ISSUE_DIGEST_MISMATCH", "RECORD_DIGEST_VERIFIES", "reseal the record (issue_sha256)", e)
    return dict(rec)


# ------------------------------------------------------------------ SV_CHANGE
def change_digest(content: Iterable[Mapping[str, Any]]) -> str:
    return sha(sorted(({"path": c["path"], "blob_digest": c["blob_digest"]} for c in content), key=lambda c: c["path"]))


CANONICAL_SERIALIZATION = {"format": "JSON", "sort_keys": True, "separators": [",", ":"], "encoding": "UTF-8",
                           "ensure_ascii": False, "trailing_newline": False}  # == canon()


def change_identity_input(rec: Mapping[str, Any]) -> dict[str, Any]:
    """The hashed form: {target_repository, base_ref (registry_generation and ledger_head kept, as recorded),
    content: [{path, blob_digest (null when deleted), deleted}] sorted by path}."""
    base = rec.get("base_ref")
    if not _base_ok(base):
        raise _deny("SV_CHANGE_BASE_UNBOUND", "BASE_BOUND_TO_REGISTRY_GENERATION_AND_LEDGER_HEAD",
                    "base_ref keeps registry_generation (int) and ledger_head (40-hex); change_id hashes both", "change_identity")
    content = []
    for c in rec.get("content") or []:
        if isinstance(c, Mapping):
            deleted = c.get("deleted", False) is True
            content.append({"path": c.get("path"), "blob_digest": None if deleted else c.get("blob_digest"), "deleted": deleted})
    return {"target_repository": rec.get("target_repository"), "base_ref": dict(base),
            "content": sorted(content, key=lambda c: str(c["path"]))}


def change_identity(rec: Mapping[str, Any]) -> str:
    """change_id = "svc:" + hex sha256(canon(change_identity_input(rec))). canon() is the pinned serialization
    (CANONICAL_SERIALIZATION). Writer evidence is not identity: the same content on the same base is one change."""
    return "svc:" + hashlib.sha256(canon(change_identity_input(rec))).hexdigest()


def request_digest(rec: Mapping[str, Any]) -> str:
    return sha({k: v for k, v in rec.items() if k not in CHANGE_NON_REQUEST_FIELDS})


def validate_change(rec: Any) -> dict[str, Any]:
    e = "validate_change"
    if not isinstance(rec, Mapping) or rec.get("schema") != CHANGE_SCHEMA:
        raise _deny("SV_CHANGE_SCHEMA_MISMATCH", "RECORD_SCHEMA_IS_" + CHANGE_SCHEMA, "supply a stegverse.sv_change.v1 record", e)
    if not _str(rec.get("declared_session")):
        raise _fail("AUTHOR_SESSION_NOT_DECLARED", "PR_AUTHOR_SESSION_DECLARED", "declared_session names the authoring session", e)
    mode = mode_check(rec, "SV_CHANGE", "base_ref", e)
    if not _base_ok(rec.get("base_ref")):
        raise _deny("SV_CHANGE_BASE_UNBOUND", "BASE_BOUND_TO_REGISTRY_GENERATION_AND_LEDGER_HEAD",
                    "base_ref{registry_generation int, ledger_head 40-hex}", e)
    if not _str(rec.get("target_repository")) or rec.get("change_id") != change_identity(rec):
        raise _deny("SV_CHANGE_IDENTITY_INVALID", "CHANGE_IDENTITY_IS_CONTENT_ADDRESSED",
                    "change_id = change_identity(record) over {target_repository, base_ref, content}", e, expected=change_identity(rec))
    res = rec.get("resolves")
    if not isinstance(res, list) or any(not (isinstance(i, str) and re.match(r"^svi:[0-9a-f]{64}$", i)) for i in res):
        raise _deny("SV_CHANGE_RESOLVES_INVALID", "CHANGE_RESOLVES_CLAIMED_SV_ISSUES", "resolves lists svi: ids", e)
    if not res and mode == "NATIVE":
        raise _deny("SV_CHANGE_RESOLVES_NOTHING", "CHANGE_RESOLVES_CLAIMED_SV_ISSUES", "resolves lists at least one svi: id", e)
    flags = rec.get("migration_flags") or []
    if mode == "MIGRATED_HISTORICAL" and (MIGRATION_FLAG_RESOLVES in flags) != (not res):
        raise _deny("MIGRATION_FLAG_MISMATCH", "MIGRATED_GAPS_ARE_FLAGGED",
                    "migration_flags carries " + MIGRATION_FLAG_RESOLVES + " exactly when resolves is empty", e)
    if not _str(rec.get("owning_goal")):
        raise _deny("SV_CHANGE_GOAL_ABSENT", "CHANGE_NAMES_OWNING_GOAL", "name the owning goal", e)
    if not _base_ok(rec.get("base_ref")):
        raise _deny("SV_CHANGE_BASE_UNBOUND", "BASE_BOUND_TO_REGISTRY_GENERATION_AND_LEDGER_HEAD",
                    "base_ref{registry_generation int, ledger_head 40-hex}", e)
    content = rec.get("content")
    if not isinstance(content, list) or not content:
        raise _deny("SV_CHANGE_CONTENT_EMPTY", "CHANGE_DIGEST_COVERS_CONTENT", "content lists every changed path", e)
    for c in content:
        if not isinstance(c, Mapping) or not _str(c.get("path")) or not (isinstance(c.get("blob_digest"), str) and DIGEST.match(c["blob_digest"])) \
                or not _writer_ok(c.get("writer_session")):
            raise _deny("SV_CHANGE_CONTENT_ENTRY_INVALID", "CHANGE_DIGEST_COVERS_CONTENT",
                        "each entry has path, sha256 blob_digest, writer_session{session|null, evidence_class}", e)
    if len({c["path"] for c in content}) != len(content):
        raise _deny("SV_CHANGE_CONTENT_DUPLICATE_PATH", "CHANGE_DIGEST_COVERS_CONTENT", "one entry per path", e)
    if (rec.get("head") or {}).get("change_digest") != change_digest(content):
        raise _fail("SV_CHANGE_DIGEST_MISMATCH", "CHANGE_DIGEST_COVERS_CONTENT", "head.change_digest = change_digest(content)", e,
                    expected=change_digest(content))
    if sorted(rec.get("touched_paths") or []) != sorted(c["path"] for c in content):
        raise _deny("SV_CHANGE_TOUCHED_PATHS_MISMATCH", "TOUCHED_PATHS_EQUAL_CONTENT_PATHS", "touched_paths equals the content paths", e)
    if rec.get("lifecycle_state") not in CHANGE_STATES:
        raise _deny("SV_CHANGE_STATE_INVALID", "LIFECYCLE_STATE_DECLARED", "one of " + ", ".join(CHANGE_STATES), e)
    ref = rec.get("required_checks_ref")
    if not isinstance(ref, Mapping) or not all(_str(ref.get(k)) for k in ("file", "blob_sha", "row_id")):
        raise _fail("REQUIRED_CHECKS_ROW_ABSENT", "REQUIRED_CHECKS_ROW_RESOLVES", "required_checks_ref{file, blob_sha, row_id}", e)
    for v in rec.get("validation_receipts") or []:
        if not isinstance(v, Mapping) or v.get("disposition") not in DISPOSITIONS or not _str(v.get("check_id")) \
                or v.get("evidence_class") not in VALIDATION_EVIDENCE or not _str(v.get("ref")) \
                or not (isinstance(v.get("digest"), str) and DIGEST.match(v["digest"])) \
                or (v["evidence_class"] == "LEDGER_RECEIPT" and not v["ref"].startswith("refs/")):
            raise _deny("VALIDATION_RECEIPT_INVALID", "VALIDATION_RECEIPT_IS_DISPOSITION",
                        "{check_id, disposition, change_digest, evidence_class LEDGER_RECEIPT (ref refs/...) | OBSERVED_ARTIFACT, ref, digest sha256}", e)
    if rec.get("request_digest") != request_digest(rec):
        raise _fail("REQUEST_DIGEST_MISMATCH", "AUTHORIZATION_BINDS_FULL_REQUEST", "request_digest = request_digest(record)", e,
                    expected=request_digest(rec))
    _epoch_or_unknown(rec, e)
    return dict(rec)


def _writer_ok(w: Any) -> bool:
    if not isinstance(w, Mapping) or set(w) != {"session", "evidence_class"} or w.get("evidence_class") not in WRITER_EVIDENCE:
        return False
    return w["session"] is None if w["evidence_class"] == UNKNOWN else _str(w["session"])


# ------------------------------------------------------------------ surfaces and admission inputs
LEDGER_WRITER_PATHS = ("resident-runtime/aggregate_repo_transition.py", "resident-runtime/ledger_store.py",
                       ".stegverse/transition-ledger/emit.py", "org-kernel/kernel.py", "org-kernel/organization-ledger/",
                       "resident-runtime/propagate_repository_receipts.py", "resident-runtime/federation_cycle.py",
                       ".github/workflows/organization-ledger-transition.yml")


def surface_kind(path: str) -> str:
    """Typed surface for coverage (Q-SCENARIO-GENERALIZATION rule S1)."""
    if any(path == p or (p.endswith("/") and path.startswith(p)) for p in LEDGER_WRITER_PATHS):
        return "ledger_writer"
    if path.startswith(".github/workflows/"):
        return "workflow"
    if path.startswith("schemas/") or path.endswith(".schema.json"):
        return "schema"
    if path == "data/canonical-task-registry.json" or path.startswith("data/canonical-task-records/"):
        return "registry"
    if path.endswith(".py"):
        return "transition"
    return "doc"


def required_for(paths: Iterable[str], row: Mapping[str, Any] = REQUIRED_CHECKS) -> tuple[list[str], list[str]]:
    kinds = {surface_kind(p) for p in paths}
    checks, signoffs = set(row["surface_kinds"]["all"]["checks"]), set()
    for k in kinds:
        checks |= set(row["surface_kinds"][k]["checks"])
        signoffs |= set(row["surface_kinds"][k]["signoffs"])
    return sorted(checks), sorted(signoffs)


def admission_inputs(change: Mapping[str, Any], current_base: Mapping[str, Any]) -> dict[str, Any]:
    """The observed inputs the admission predicate and the scenario corpus bind to (registry/ledger, not GitHub)."""
    checks, signoffs = required_for(change["touched_paths"])
    ws = [c["writer_session"] for c in change["content"]]
    writers = sorted({w["session"] for w in ws if w["evidence_class"] != UNKNOWN})
    unobserved = sorted(c["path"] for c in change["content"] if c["writer_session"]["evidence_class"] == UNKNOWN)
    grants = sorted(g["session"] for g in change.get("co_author_grants") or [] if _str((g or {}).get("receipt_ref")))
    return {
        "record_mode": change.get("record_mode"),
        "writer_unobserved_paths": unobserved,
        "declared_session": change.get("declared_session"),
        "base_ref": dict(change["base_ref"]),
        "current_base": dict(current_base),
        "head_change_digest": change["head"]["change_digest"],
        "writer_sessions": writers,
        "co_author_grants": grants,
        "declared_session_matches_writers": not unobserved and all(w == change.get("declared_session") or w in grants for w in writers),
        "required_check_ids": checks,
        "validation_receipts": [dict(v) for v in change.get("validation_receipts") or []],
        "required_signoff_roles": signoffs,
        "signoffs": [dict(s) for s in change.get("signoffs") or []],
        "bound_request_digest": change.get("request_digest"),
        "recomputed_request_digest": request_digest(change),
        "touched_paths": sorted(change["touched_paths"]),
        "touched_surface_kinds": sorted({surface_kind(p) for p in change["touched_paths"]}),
        "admission_order_slot": change.get("admission_order_slot"),
    }


def evaluate_admission(obs: Mapping[str, Any], covered_kinds: Iterable[str] | None = None) -> dict[str, Any]:
    """Native admission predicate over admission_inputs(). Lane C's reference
    implementation (#164) replaces this by injection; the corpus tests run
    against whichever evaluator is supplied."""
    e = "evaluate_admission"
    if obs.get("record_mode") != "NATIVE":
        raise historical_refusal(e)
    if not _str(obs.get("declared_session")):
        raise _fail("AUTHOR_SESSION_NOT_DECLARED", "PR_AUTHOR_SESSION_DECLARED", "declare the authoring session", e)
    if obs.get("base_ref") != obs.get("current_base"):
        raise _deny("BASE_STALE", "BASE_IS_CURRENT", "re-propose on the current registry generation and ledger head", e,
                    base_ref=obs.get("base_ref"), current_base=obs.get("current_base"))
    if obs.get("bound_request_digest") != obs.get("recomputed_request_digest"):
        raise _fail("REQUEST_DIGEST_MISMATCH", "AUTHORIZATION_BINDS_FULL_REQUEST",
                    "a successor decision bound to the full request digest", e)
    if obs.get("writer_unobserved_paths"):
        raise _fail("BRANCH_WRITER_UNOBSERVED", "BRANCH_WRITER_IS_BRANCH_OWNER",
                    "an observed writer (DECLARED or OBSERVED_COMMIT_TRAILER) for every path; UNKNOWN never passes (JDQ Q-WRITER-IDENTITY)",
                    e, paths=obs["writer_unobserved_paths"])
    if not obs.get("declared_session_matches_writers") or any(
            w != obs.get("declared_session") and w not in (obs.get("co_author_grants") or []) for w in obs.get("writer_sessions") or []):
        raise _fail("BRANCH_HAS_FOREIGN_WRITER", "BRANCH_WRITER_IS_BRANCH_OWNER",
                    "a superseding SV_CHANGE by the owner that carries the foreign content openly, or a receipted co-author grant", e)
    required = list(obs.get("required_check_ids") or [])
    if not required:
        raise _fail("REQUIRED_CHECKS_ROW_ABSENT", "REQUIRED_CHECKS_ROW_RESOLVES", "resolve the required-checks row", e)
    by_id = {v.get("check_id"): v for v in obs.get("validation_receipts") or []
             if v.get("evidence_class") == "LEDGER_RECEIPT" and str(v.get("ref") or "").startswith("refs/")}
    unobserved = sorted(c for c in required if c not in by_id)
    if unobserved:
        artifact_only = sorted(c for c in unobserved if any(v.get("check_id") == c for v in obs.get("validation_receipts") or []))
        raise _fail("CHECK_SKIPPED_OR_UNOBSERVED", "MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED",
                    "a ledger-receipted ALLOW for every required check at the exact head (OBSERVED_ARTIFACT does not count)",
                    e, unobserved=unobserved, artifact_only=artifact_only)
    stale = sorted(c for c in required if by_id[c].get("change_digest") != obs.get("head_change_digest"))
    if stale:
        raise _fail("VALIDATION_NOT_AT_EXACT_HEAD", "VALIDATION_RECEIPT_BINDS_EXACT_HEAD", "re-run the checks at head.change_digest", e, stale=stale)
    failing = sorted(c for c in required if by_id[c].get("disposition") != "ALLOW")
    if failing:
        raise _deny("CHECK_NOT_PASSING", "MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED", "every required check ALLOW", e, failing=failing)
    have = {s.get("role") for s in obs.get("signoffs") or [] if _str((s or {}).get("receipt_ref")) and _str((s or {}).get("session"))}
    absent = sorted(set(obs.get("required_signoff_roles") or []) - have)
    if absent:
        raise _fail("SIGNOFF_ABSENT", "REQUIRED_SIGNOFF_RECORDED", "a receipted sign-off by each required role", e, absent=absent)
    if covered_kinds is not None:
        need = set(REQUIRED_CHECKS["coverage_required_kinds"])
        gap = sorted(k for k in obs.get("touched_surface_kinds") or [] if k in need and k not in set(covered_kinds))
        if gap:
            raise _fail("NO_SCENARIO_COVERAGE_FOR_SURFACE", "SCENARIO_COVERAGE_FOR_EVERY_TOUCHED_SURFACE",
                        "derive the scenario class for the surface first (SCENARIO_CORPUS_APPEND)", e, uncovered=gap)
    return {"disposition": "ALLOW", "failed_predicate": None}


def historical_refusal(entry: str) -> Refusal:
    return _fail("HISTORICAL_RECORD_NOT_ADMISSIBLE", "ADMITTED_RECORDS_ARE_NATIVE",
                 "a superseding NATIVE record (SV_CHANGE_SUPERSEDE) whose every unknown_fields pointer holds an observed value",
                 entry, "propose the NATIVE successor; this record stays history and is never admitted")


def admit(obs: Mapping[str, Any], evaluator: Callable[..., dict] = evaluate_admission, **kw: Any) -> dict[str, Any]:
    try:
        return evaluator(obs, **kw)
    except Refusal as r:
        return dict(r.record)


# ------------------------------------------------------------------ lifecycle
TRANSITIONS = {t["transition_class"]: t for t in LIFECYCLE["transitions"]}
_wc = importlib.util.spec_from_file_location("sv_work_items_worker_claim", ROOT / "scripts/project_worker_claim_into_canonical_task.py")
worker_claim = importlib.util.module_from_spec(_wc)
_wc.loader.exec_module(worker_claim)


def claim_projection(worker_registry: Mapping[str, Any], task_id: str) -> dict[str, Any]:
    """CLAIMED is a projection of a WorkerCoordinator claim/fence (C3); no second claim path."""
    try:
        proj = worker_claim.worker_projection(dict(worker_registry), task_id)
    except SystemExit as exc:
        raise _fail("WORKERCOORDINATOR_CLAIM_AMBIGUOUS", "WORKERCOORDINATOR_HOLDS_EXACTLY_ONE_CLAIM",
                    "one WorkerCoordinator row per work item", "claim_projection", detail=str(exc))
    if not proj.get("matched") or not _str(proj.get("claim_ref")) or proj.get("fence_ref") in (None, ""):
        raise _fail("WORKERCOORDINATOR_CLAIM_ABSENT", "CLAIM_IS_A_WORKERCOORDINATOR_CLAIM_AND_FENCE",
                    "WorkerCoordinator records the claim and fence first (control/worker-registry.json)", "claim_projection",
                    "re-project once WorkerCoordinator holds the claim; nothing waits")
    return {"session": proj.get("worker_id"), "claim_ref": proj["claim_ref"], "fence_ref": proj["fence_ref"],
            "worker_instance_id": proj.get("worker_instance_id"), "projection_only": True}


def work_items_projection(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """The canonical task's work_items[] (#160 6249905378 merged, C7): native id first, GitHub as a projection field, no approval flag."""
    out = []
    for r in records:
        kind = "SV_ISSUE" if r.get("schema") == ISSUE_SCHEMA else "SV_CHANGE"
        pj = r.get("projection") or {}
        out.append({"work_item_id": r.get("issue_id") or r.get("change_id"), "kind": kind,
                    "owning_goal": r.get("owning_goal"), "record_mode": r.get("record_mode"),
                    "record_sha256": r.get("issue_sha256") or r.get("request_digest"),
                    "lifecycle_state": r.get("lifecycle_state"),
                    "canonical_coordination_state": LIFECYCLE["canonical_coordination_state"][kind][r.get("lifecycle_state")],
                    "projection": {k: pj.get(k) for k in ("repo", "pr", "issue", "head_sha", "github_state")} if pj else None})
    return sorted(out, key=lambda w: w["work_item_id"])


COORDINATION_TASK_ID = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"


def work_items_record(records: Iterable[Mapping[str, Any]], coordination_task_id: str = COORDINATION_TASK_ID) -> dict[str, Any]:
    """SF-9: one work-items record per coordination task; goal_index is the multi-goal index (UNKNOWN goals included)."""
    items = work_items_projection(records)
    index: dict[str, list[str]] = {}
    for w in items:
        index.setdefault(w["owning_goal"], []).append(w["work_item_id"])
    return {"schema": "stegverse.canonical-task-work-items.v1", "coordination_task_id": coordination_task_id,
            "goal_index": {g: sorted(ids) for g, ids in sorted(index.items())}, "work_items": items}


def transition(transition_class: str, record: Mapping[str, Any] | None, *, hb_epoch: Any,
               context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate one lifecycle transition. Returns {disposition, ..., record}; never raises for a refusal."""
    ctx = dict(context or {})
    e = "transition"
    try:
        epoch_check(hb_epoch, e)
        t = TRANSITIONS.get(transition_class)
        if t is None:
            raise _fail("TRANSITION_UNDECLARED", "TRANSITION_IS_IN_LIFECYCLE_MANIFEST",
                        "declare the transition in data/sv-work-items/lifecycle-transitions.json", e)
        state = None if record is None or t["from_states"] == [None] else record.get("lifecycle_state")
        if state not in t["from_states"]:
            raise _deny("LIFECYCLE_STATE_NOT_ADMISSIBLE", "FROM_STATE_IS_DECLARED",
                        transition_class + " applies from " + repr(t["from_states"]), e, observed=state)
        new = dict(record or {})
        if transition_class == "SV_ISSUE_OPEN":
            validate_issue(record)
        if transition_class == "SV_ISSUE_CLAIM":
            if ctx.get("observed_generation") != (ctx.get("current_base") or {}).get("registry_generation"):
                raise _deny("STOP_STALE_COORDINATION", "SESSION_OBSERVED_REGISTRY_GENERATION_EQUALS_CURRENT",
                            "re-read the registry generation, then claim", e)
            new["claim"] = {**claim_projection(ctx.get("worker_registry") or {}, record["issue_id"]),
                            "observed_generation": ctx["observed_generation"]}
        if transition_class == "SV_ISSUE_RELEASE":
            try:
                claim_projection(ctx.get("worker_registry") or {}, record["issue_id"])
            except Refusal:
                new.pop("claim", None)
            else:
                raise _deny("WORKERCOORDINATOR_CLAIM_STILL_HELD", "RELEASE_FOLLOWS_WORKERCOORDINATOR_RELEASE",
                            "WorkerCoordinator releases the claim first", e)
        if transition_class == "SV_ISSUE_RESOLVE":
            ch = ctx.get("resolving_change") or {}
            if ch.get("lifecycle_state") != "APPLIED" or record.get("issue_id") not in (ch.get("resolves") or []):
                raise _fail("RESOLVING_CHANGE_NOT_APPLIED", "RESOLVING_SV_CHANGE_IS_APPLIED", "an APPLIED SV_CHANGE that lists this issue", e)
            new["resolved_by"] = ch.get("change_id")
        if transition_class == "SV_ISSUE_CLOSE_BY_INVARIANT":
            det = ctx.get("determination") or {}
            if det.get("disposition") != "ALLOW" or not _str(det.get("deciding_rule")) or not _str(det.get("receipt_ref")):
                raise _fail("INVARIANT_UNDECLARED", "INVARIANT_DETERMINATION_RECEIPT_NAMES_DECIDING_RULE",
                            "an INVARIANT_DETERMINATION ALLOW receipt naming the deciding rule", e)
            new["closed_by"] = {k: det[k] for k in ("deciding_rule", "receipt_ref")}
        if transition_class == "SV_CHANGE_PROPOSE":
            validate_change(record)
            claimed = {i.get("issue_id"): i for i in ctx.get("issues") or []}
            bad = [i for i in record["resolves"] if (claimed.get(i) or {}).get("lifecycle_state") != "CLAIMED"
                   or ((claimed.get(i) or {}).get("claim") or {}).get("session") != record["declared_session"]]
            if bad:
                raise _fail("RESOLVED_ISSUE_NOT_CLAIMED_BY_AUTHOR", "CHANGE_RESOLVES_CLAIMED_SV_ISSUES",
                            "claim each resolved SV_ISSUE with the declared session first (SV_ISSUE_CLAIM)", e, unclaimed=bad)
            obs = admission_inputs(record, record["base_ref"])
            if obs["writer_unobserved_paths"]:
                raise _fail("BRANCH_WRITER_UNOBSERVED", "BRANCH_WRITER_IS_BRANCH_OWNER",
                            "an observed writer for every path; UNKNOWN never passes (JDQ Q-WRITER-IDENTITY)", e,
                            paths=obs["writer_unobserved_paths"])
            if not obs["declared_session_matches_writers"]:
                raise _fail("BRANCH_HAS_FOREIGN_WRITER", "BRANCH_WRITER_IS_BRANCH_OWNER",
                            "a superseding SV_CHANGE by the owner that carries the foreign content openly", e)
        if transition_class == "SV_CHANGE_VERIFY":
            validate_change(record)
            obs = admission_inputs(record, record["base_ref"])
            out = admit({**obs, "required_signoff_roles": []})
            if out["disposition"] != "ALLOW":
                raise Refusal(out["disposition"], out["failure_code"], out["failed_predicate"], out["required_evidence_or_repair"],
                              "transition", "re-verify once every required check is receipted at the exact head")
        if transition_class == "SV_CHANGE_ADMIT":
            validate_change(record)
            if not (_str(ctx.get("predicate_digest")) and _str(ctx.get("corpus_head"))):
                raise _fail("ADMISSION_PROVENANCE_ABSENT", "MERGE_PROVENANCE_DECLARED",
                            "the admit receipt names the predicate digest and the corpus head", e)
            if record.get("record_mode") != "NATIVE":
                out = dict(historical_refusal(e).record)
                new["lifecycle_state"] = LIFECYCLE["admit_outcome_states"][out["disposition"]]
                return {**out, "predicate_digest": ctx["predicate_digest"], "corpus_head": ctx["corpus_head"],
                        "actor_session": ctx.get("actor_session"), "transition_class": transition_class, "record": new}
            obs = admission_inputs(record, ctx.get("current_base") or {})
            out = admit(obs, ctx.get("evaluator") or evaluate_admission, covered_kinds=ctx.get("covered_kinds"))
            new["lifecycle_state"] = LIFECYCLE["admit_outcome_states"][out["disposition"]]
            out = {**out, "predicate_digest": ctx["predicate_digest"], "corpus_head": ctx["corpus_head"],
                   "actor_session": ctx.get("actor_session")}
            return {**out, "transition_class": transition_class, "record": new}
        if transition_class == "SV_CHANGE_APPLY":
            if record.get("base_ref") != ctx.get("current_base"):
                raise _deny("BASE_STALE", "BASE_IS_CURRENT", "re-propose on the current base", e)
            new["applied"] = {"registry_generation": record["base_ref"]["registry_generation"] + 1}
        if transition_class in ("SV_ISSUE_SUPERSEDE", "SV_CHANGE_SUPERSEDE"):
            issue = transition_class == "SV_ISSUE_SUPERSEDE"
            succ, seal_field = ctx.get("successor"), ("issue_sha256" if issue else "request_digest")
            if not isinstance(succ, Mapping):
                raise _fail("SUCCESSOR_NOT_RECORDED", "SUCCESSOR_ISSUE_IS_RECORDED" if issue else "SUCCESSOR_CHANGE_IS_PROPOSED",
                            "supply the successor record", e)
            (validate_issue if issue else validate_change)(succ)
            if succ.get("supersedes") != record.get(seal_field):
                raise _fail("SUCCESSOR_DOES_NOT_NAME_PREDECESSOR", "SUCCESSOR_ISSUE_IS_RECORDED" if issue else "SUCCESSOR_CHANGE_IS_PROPOSED",
                            "successor.supersedes = predecessor " + seal_field, e)
            new["superseded_by"] = succ.get(seal_field)
        if transition_class == "SV_CHANGE_PROJECT_GITHUB":
            new["projection"] = {**(record.get("projection") or {}), **(ctx.get("projection") or {}), "authority_effect": "NONE"}
        new["lifecycle_state"] = t["to_state"]
        return {"disposition": "ALLOW", "transition_class": transition_class, "record": new}
    except Refusal as r:
        return {**r.record, "transition_class": transition_class, "record": dict(record or {})}


def record(result: Mapping[str, Any], predecessor: Mapping[str, Any] | None, *, hb_epoch: Any,
           append: Callable[..., dict]) -> dict[str, Any]:
    """Hand a transition outcome (ALLOW or refusal) to the existing repository emitter."""
    epoch_check(hb_epoch, "record")
    rec = result["record"]
    rid = rec.get("issue_id") or rec.get("change_id") or rec.get("class_id")
    six = {f: result.get(f) for f in SIX_FIELDS}
    return append(str(rid) + ":" + result["transition_class"], result["transition_class"],
                  sha(predecessor), sha(rec if result["disposition"] == "ALLOW" else predecessor),
                  evidence={"record": rec, "disposition": result["disposition"], **six,
                            "invariant": LIFECYCLE["invariant"]},
                  authority_effect="NONE_RECORD_ONLY", hb_epoch=int(epoch_check(hb_epoch, "record")))
