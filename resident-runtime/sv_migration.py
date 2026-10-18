"""MIGRATED_HISTORICAL records: derivation rules for history that predates the native path.

Nothing here invents a value. A field the history does not carry is UNKNOWN_NOT_AUTHENTICALLY_OBSERVED,
listed in unknown_fields, and permitted only where the schema's x-migrated-unknown-allowed says so. Every
other field is copied or derived by a published rule:
  surface        <- resolve_surface(retry_entrypoint) through the pinned data/sv-work-items/surface-aliases.json:
                    patch entrypoints, repository paths, lane aliases, bare names (RF-2); box-local paths and paths
                    outside every supplied repository tree are NON_REPOSITORY_EVIDENCE (RF-3); otherwise UNKNOWN
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
SURFACE_ALIASES_BLOB = "125083bc84edb97f6132c37e467055410cd7c005"  # git blob sha of surface-aliases.json; the lifter refuses any other table


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
    for e in sorted(table["lane_aliases"], key=lambda e: -len(e["alias"])):
        if re.search(r"(?<![\w/.-])" + re.escape(e["alias"]) + r"(?![\w/-])", text):
            return _resolved(e, e["alias"], repo_paths)
    for m in BARE.finditer(text):
        for e in table["bare_names"]:
            if e["name"] == m.group(1):
                return _resolved(e, e["name"], repo_paths)
    return U


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
            if six != first and six not in keep.get("restatements", []):
                keep["restatements"] = keep.get("restatements", []) + [six]
                keep["unknown_fields"] = sorted(wi.sentinel_pointers(keep))
            out[r["issue_id"]] = wi.seal(keep, "issue_sha256")
        else:
            out[r["issue_id"]] = r
        if old:
            remap[old] = r["issue_id"]
    return sorted(out.values(), key=lambda x: x["issue_id"]), remap


def finish_change(body: Mapping[str, Any]) -> dict[str, Any]:
    rec = {k: v for k, v in body.items() if k not in ("change_id", "request_digest", "unknown_fields", "migration_flags")}
    rec["record_mode"] = "MIGRATED_HISTORICAL"
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
