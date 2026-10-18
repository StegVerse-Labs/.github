"""MIGRATED_HISTORICAL records: derivation rules for history that predates the native path.

Nothing here invents a value. A field the history does not carry is UNKNOWN_NOT_AUTHENTICALLY_OBSERVED,
listed in unknown_fields, and permitted only where the schema's x-migrated-unknown-allowed says so. Every
other field is copied or derived by a published rule:
  surface        <- resolve_surface(retry_entrypoint) through the pinned data/sv-work-items/surface-aliases.json:
                    patch entrypoints, repository paths, lane aliases, bare names (RF-2); box-local paths and paths
                    outside every supplied repository tree are NON_REPOSITORY_EVIDENCE (RF-3); an alias declared in
                    unresolved_declarations (target exists only at another PR head) stays UNKNOWN and its
                    alias_disposition is FAIL_CLOSED, never ALLOW (FB-1); otherwise UNKNOWN
  surface (class column) <- derive_surface_with_class_column: only when the entrypoint resolves to UNKNOWN, the same
                    resolver runs on the lane table's Class column; the result carries migration_flags
                    SURFACE_DERIVED_FROM_CLASS_COLUMN (derived, not observed). Builders supply the cells only (FB-2)
  required_checks_ref.blob_sha <- the recorded 40-hex blob; any placeholder (WORKTREE) becomes UNKNOWN
  content.deleted <- recorded value; when the history records none, deleted = (blob_digest is null), the schema's
                    "null exactly when deleted" rule read backwards (TVC#519 makes deleted required)
  issue_id       <- sv_work_items.issue_identity; reworded restatements merge into one record (restatements[])
  change_id      <- sv_work_items.change_identity over {target_repository, base_ref, content}
  writer_session <- {session, DECLARED} when the history names a session, else {null, UNKNOWN}
  migration_provenance <- original base not observed unless the history records it; migrated_at_base = the base field
`lift_v0_*` converts records written against the 1673cb5f draft schemas by these rules only. Stdlib, no clock.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Collection, Iterable, Mapping

wi = sys.modules["sv_work_items"]
U = wi.UNKNOWN
NRE = wi.NON_REPOSITORY_EVIDENCE
EXT = r"(?:py|json|jsonl|yml|yaml|md|sh|diff|patch|js|cjs|mjs|ts|toml|txt)"
PATH = re.compile(r"(?<![\w.-])((?:[/~]|\.{1,2}/)?(?:[\w.*-]+/)+[\w.*-]+\." + EXT + r")")
BARE = re.compile(r"(?<![\w/.-])([\w-][\w.-]*\." + EXT + r")(?![\w/])")
SURFACE_ALIASES_PATH = wi.ROOT / "data/sv-work-items/surface-aliases.json"
SURFACE_ALIASES_BLOB = "debd7d7b0544b11bc1ac87d0b82bb21c22247c55"  # git blob sha of surface-aliases.json; the lifter refuses any other table


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def load_aliases(path: Path = SURFACE_ALIASES_PATH, pin: str | None = None) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    if git_blob(raw) != (pin or SURFACE_ALIASES_BLOB):
        raise wi._fail("SURFACE_ALIAS_TABLE_UNPINNED", "SURFACE_ALIASES_ARE_DECLARED_AND_PINNED",
                       "use data/sv-work-items/surface-aliases.json at blob " + (pin or SURFACE_ALIASES_BLOB), "load_aliases",
                       observed_blob=git_blob(raw))
    table = json.loads(raw)
    if tuple(table["box_local_prefixes"]) != wi.BOX_LOCAL_PREFIXES:
        raise wi._fail("SURFACE_ALIAS_TABLE_INCONSISTENT", "SURFACE_ALIASES_ARE_DECLARED_AND_PINNED",
                       "box_local_prefixes equals sv_work_items.BOX_LOCAL_PREFIXES", "load_aliases")
    return table


def _surface(path: str, repo_paths: Collection[str] | None) -> dict[str, str]:
    if path == NRE or wi.is_box_local(path) or (repo_paths is not None and path not in repo_paths):
        return {"kind": NRE, "path": path}
    return {"kind": wi.surface_kind(path), "path": path}


def _resolved(entry: Mapping[str, Any], token: str, repo_paths) -> Any:
    if entry["path"] == U:
        return U
    if entry["path"] == NRE:
        return {"kind": NRE, "path": token}
    return {"kind": wi.surface_kind(entry["path"]), "path": entry["path"]}  # verified against a declared tree


def resolve_surface(text: Any, repo_paths: Collection[str] | None = None, table: Mapping[str, Any] | None = None) -> Any:
    """RF-2/RF-3 resolution, in the table's declared order: patch entrypoints, repository paths (box-local or outside every
    supplied tree -> NON_REPOSITORY_EVIDENCE), lane aliases, bare names; otherwise UNKNOWN. Never guesses."""
    if not isinstance(text, str) or not text.strip():
        return U
    table = table if table is not None else load_aliases()
    for e in table["patch_entrypoints"]:
        if e["entrypoint"] in text:
            return _resolved(e, e["entrypoint"], repo_paths)
    m = PATH.search(text)
    if m:
        return _surface(m.group(1), repo_paths)
    e = _alias_match(text, table)
    if e is not None:
        return U if e.get("disposition") == "FAIL_CLOSED" else _resolved(e, e["alias"], repo_paths)
    for m in BARE.finditer(text):
        for e in table["bare_names"]:
            if e["name"] == m.group(1):
                return _resolved(e, e["name"], repo_paths)
    return U


def _alias_match(text: str, table: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Longest whole-token alias among lane_aliases and unresolved_declarations."""
    entries = list(table["lane_aliases"]) + list(table.get("unresolved_declarations") or [])
    for e in sorted(entries, key=lambda e: (-len(e["alias"]), e["alias"])):
        if re.search(r"(?<![\w/.-])" + re.escape(e["alias"]) + r"(?![\w/-])", text):
            return e
    return None


def alias_disposition(token: str, table: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """ALLOW with the surface only for an alias whose target was verified in a declared repository tree. An unresolved
    declaration returns its recorded six-field FAIL_CLOSED (its evidence is a PR head, not the base); an UNKNOWN or
    undeclared alias fails closed too. Nothing here can turn an unresolved declaration into ALLOW."""
    table = table if table is not None else load_aliases()
    e = _alias_match(token, table) if isinstance(token, str) else None
    if e is not None and e.get("disposition") == "FAIL_CLOSED":
        return {k: e[k] for k in ("disposition",) + tuple(wi.SIX_FIELDS)} | {"alias": e["alias"], "evidence": dict(e["evidence"])}
    if e is not None and e["path"] not in (U, NRE) and "verified" in e:
        return {"disposition": "ALLOW", "alias": e["alias"], "surface": _resolved(e, e["alias"], None)}
    return {"disposition": "FAIL_CLOSED", "failure_code": "SURFACE_ALIAS_UNRESOLVED", "failed_predicate": "SURFACE_ALIASES_ARE_DECLARED_AND_PINNED",
            "required_evidence_or_repair": "declare the alias in data/sv-work-items/surface-aliases.json with a target verified in a declared tree",
            "retry_entrypoint": "resident-runtime/sv_migration.py::alias_disposition", "owning_existing_goal": "StegVerse-org/.github#163",
            "next_attempt": "after the alias table is re-pinned (SURFACE_ALIASES_BLOB)", "alias": token}


def derive_surface_with_class_column(retry_entrypoint: Any, class_cell: Any,
                                     repo_paths: Collection[str] | None = None) -> tuple[Any, list[str]]:
    """FB-2 (from Lane D's builder): resolve the entrypoint; only if that is UNKNOWN, resolve the row's Class column by
    the same rules. Returns (surface, migration_flags); a class-column surface is flagged as derived, never observed."""
    s = resolve_surface(retry_entrypoint, repo_paths)
    if s == U and isinstance(class_cell, str) and class_cell.strip():
        c = resolve_surface(class_cell, repo_paths)
        if c != U:
            return c, [wi.MIGRATION_FLAG_SURFACE_FROM_CLASS]
    return s, []


def derive_surface(retry_entrypoint: Any, repo_paths: Collection[str] | None = None) -> Any:
    return resolve_surface(retry_entrypoint, repo_paths)


def recheck_surface(surface: Any, repo_paths: Collection[str] | None = None) -> Any:
    """A surface a source record already carries is re-resolved by the same rules (RF-3: patches/... is not a surface)."""
    if not isinstance(surface, Mapping) or not isinstance(surface.get("path"), str):
        return surface
    if surface.get("kind") == NRE:
        return dict(surface)
    return resolve_surface(surface["path"], repo_paths)


def provenance(base: Mapping[str, Any], original: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {"original_base_observed": original is not None, "original_base_ref": dict(original) if original else None,
            "migrated_at_base": dict(base)}


def finish_issue(body: Mapping[str, Any]) -> dict[str, Any]:
    rec = {k: v for k, v in body.items() if k not in ("issue_id", "issue_sha256", "unknown_fields")}
    rec["record_mode"] = "MIGRATED_HISTORICAL"
    if "migration_flags" in rec:
        rec["migration_flags"] = sorted(set(rec["migration_flags"]))
        if not rec["migration_flags"]:
            del rec["migration_flags"]
    rec["unknown_fields"] = sorted(wi.sentinel_pointers(rec))
    rec["issue_id"] = wi.issue_identity(rec)
    return wi.seal(rec, "issue_sha256")


def merge_issues(records: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Merge records with one identity: the first is kept, later ones become restatements. Returns (records, old->new id)."""
    out: dict[str, dict[str, Any]] = {}
    remap: dict[str, str] = {}
    for r in records:
        r = dict(r)
        old = r.pop("_old_id", None)
        if r["issue_id"] in out:
            keep = {k: v for k, v in out[r["issue_id"]].items() if k != "issue_sha256"}
            six = {f: r["disposition"][f] for f in wi.SIX_FIELDS}
            first = {f: keep["disposition"][f] for f in wi.SIX_FIELDS}
            if str(r.get("owning_goal")).strip() == U and six != first:
                # FB-3: without an observed goal two bodies under one id are not provably one issue; never merge them
                raise wi._fail("SV_ISSUE_ID_COLLISION", "ISSUE_ID_IS_UNIQUE_IN_RECORD_SET",
                               "name source_receipt.evidence_locator for each UNKNOWN-goal entry so each keeps its own identity",
                               "merge_issues", issue_id=r["issue_id"])
            if six != first and six not in keep.get("restatements", []):
                keep["restatements"] = keep.get("restatements", []) + [six]
                keep["unknown_fields"] = sorted(wi.sentinel_pointers(keep))
            out[r["issue_id"]] = wi.seal(keep, "issue_sha256")
        else:
            out[r["issue_id"]] = r
        if old:
            remap[old] = r["issue_id"]
    return sorted(out.values(), key=lambda x: x["issue_id"]), remap


def content_entry(c: Mapping[str, Any]) -> dict[str, Any]:
    """{path, blob_digest, deleted, writer_session}; deleted keeps its recorded value, else (blob_digest is null)."""
    return {"path": c.get("path"), "blob_digest": c.get("blob_digest"),
            "deleted": c["deleted"] if "deleted" in c else c.get("blob_digest") is None, "writer_session": c.get("writer_session")}


def finish_change(body: Mapping[str, Any]) -> dict[str, Any]:
    rec = {k: v for k, v in body.items() if k not in ("change_id", "request_digest", "unknown_fields", "migration_flags")}
    rec["record_mode"] = "MIGRATED_HISTORICAL"
    rec["content"] = [content_entry(c) for c in rec.get("content") or []]
    rcr = rec.get("required_checks_ref")
    if isinstance(rcr, Mapping) and not (isinstance(rcr.get("blob_sha"), str) and wi.GIT_SHA.match(rcr["blob_sha"])):
        rec["required_checks_ref"] = {**rcr, "blob_sha": U}  # a placeholder (e.g. WORKTREE) is not an observed blob
    old_head = (rec.get("head") or {}).get("change_digest")
    rec["head"] = {"change_digest": wi.change_digest(rec)}
    legacy = legacy_change_digest(rec["content"])
    # a receipt that bound this exact content in the pre-fa4dc6d2 digest form is re-expressed in the current form
    rec["validation_receipts"] = [{**v, "change_digest": rec["head"]["change_digest"]}
                                  if v.get("change_digest") in (legacy, old_head) and old_head == legacy else v
                                  for v in rec.get("validation_receipts") or []]
    rec["touched_paths"] = sorted(c["path"] for c in rec["content"])
    if not rec.get("resolves"):
        rec["migration_flags"] = [wi.MIGRATION_FLAG_RESOLVES]
    rec["unknown_fields"] = sorted(wi.sentinel_pointers(rec))
    rec["change_id"] = wi.change_identity(rec)
    rec["request_digest"] = wi.request_digest(rec)
    return rec


def legacy_change_digest(content: Iterable[Mapping[str, Any]]) -> str:
    """The 1673cb5f..fa4dc6d2 head digest (sha over sorted {path, blob_digest}); read only to re-express old receipts."""
    return wi.sha(sorted(({"path": c["path"], "blob_digest": c["blob_digest"]} for c in content), key=lambda c: c["path"]))


def _writer(w: Any) -> dict[str, Any]:
    if isinstance(w, Mapping):
        return dict(w)
    return {"session": None, "evidence_class": U} if (not isinstance(w, str) or U in w) else {"session": w, "evidence_class": "DECLARED"}


def lift_v0_issue(rec: Mapping[str, Any], repo_paths: Collection[str] | None = None) -> dict[str, Any]:
    r = copy.deepcopy(dict(rec))
    r["_old_id"] = r.get("issue_id")
    given = r.get("surface")
    derived = derive_surface((r.get("disposition") or {}).get("retry_entrypoint"), repo_paths)
    r["surface"] = recheck_surface(given, repo_paths) if isinstance(given, Mapping) else derived
    r.setdefault("migration_provenance", provenance(r.get("observed_base") or {}))
    old = r.pop("_old_id")
    out = finish_issue(r)
    return {**out, "_old_id": old}


def lift_v0_change(rec: Mapping[str, Any], issue_remap: Mapping[str, str]) -> dict[str, Any]:
    r = copy.deepcopy(dict(rec))
    r["content"] = [{**c, "writer_session": _writer(c.get("writer_session"))} for c in r.get("content") or []]
    vr = []
    for v in r.get("validation_receipts") or []:
        ref = v.get("ref", v.get("receipt_ref"))
        vr.append({"check_id": v.get("check_id"), "disposition": v.get("disposition"), "change_digest": v.get("change_digest"),
                   "evidence_class": v.get("evidence_class") or ("LEDGER_RECEIPT" if str(ref).startswith("refs/") else "OBSERVED_ARTIFACT"),
                   "ref": ref, "digest": v.get("digest", U)})  # v0 carried no digest: UNKNOWN, never synthesized
    r["validation_receipts"] = vr
    r["resolves"] = sorted(issue_remap.get(i, i) for i in r.get("resolves") or [])
    r.setdefault("migration_provenance", provenance(r.get("base_ref") or {}))
    return finish_change(r)
