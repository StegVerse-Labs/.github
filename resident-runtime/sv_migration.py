"""MIGRATED_HISTORICAL records: derivation rules for history that predates the native path.

Nothing here invents a value. A field the history does not carry is UNKNOWN_NOT_AUTHENTICALLY_OBSERVED,
listed in unknown_fields, and permitted only where the schema's x-migrated-unknown-allowed says so. Every
other field is copied or derived by a published rule:
  surface        <- the first repository path in retry_entrypoint, typed by sv_work_items.surface_kind
                    (UNKNOWN when the entrypoint names no path)
  issue_id       <- sv_work_items.issue_identity; reworded restatements merge into one record (restatements[])
  change_id      <- sv_work_items.change_identity over {target_repository, base_ref, content}
  writer_session <- {session, DECLARED} when the history names a session, else {null, UNKNOWN}
  migration_provenance <- original base not observed unless the history records it; migrated_at_base = the base field
`lift_v0_*` converts records written against the 1673cb5f draft schemas by these rules only. Stdlib, no clock.
"""
from __future__ import annotations

import copy
import re
import sys
from typing import Any, Iterable, Mapping

wi = sys.modules["sv_work_items"]
U = wi.UNKNOWN
PATH = re.compile(r"(?<![\w/.-])((?:\.?[\w-]+/)+[\w.-]+\.(?:py|json|jsonl|yml|yaml|md|sh))")


def derive_surface(retry_entrypoint: Any) -> Any:
    m = PATH.search(retry_entrypoint) if isinstance(retry_entrypoint, str) else None
    return {"kind": wi.surface_kind(m.group(1)), "path": m.group(1)} if m else U


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
    rec["head"] = {"change_digest": wi.change_digest(rec["content"])}
    rec["touched_paths"] = sorted(c["path"] for c in rec["content"])
    if not rec.get("resolves"):
        rec["migration_flags"] = [wi.MIGRATION_FLAG_RESOLVES]
    rec["unknown_fields"] = sorted(wi.sentinel_pointers(rec))
    rec["change_id"] = wi.change_identity(rec)
    rec["request_digest"] = wi.request_digest(rec)
    return rec


def _writer(w: Any) -> dict[str, Any]:
    if isinstance(w, Mapping):
        return dict(w)
    return {"session": None, "evidence_class": U} if (not isinstance(w, str) or U in w) else {"session": w, "evidence_class": "DECLARED"}


def lift_v0_issue(rec: Mapping[str, Any]) -> dict[str, Any]:
    r = copy.deepcopy(dict(rec))
    r["_old_id"] = r.get("issue_id")
    r.setdefault("surface", derive_surface((r.get("disposition") or {}).get("retry_entrypoint")))
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
