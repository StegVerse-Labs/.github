#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

POLICY_REL = Path("control/stegindex-preflight-policy.json")
INDEX_HANDOFF = Path("STEGINDEX_MIRROR_HANDOFF.md")
CAP_REGISTRY = Path("registry/capabilities.json")
PRED_REGISTRY = Path("registry/predicates.json")


class PreflightError(RuntimeError):
    pass


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _index_root(explicit: Path | None = None) -> Path:
    raw = explicit or Path(str(os.environ.get("STEGVERSE_STEGINDEX_SOURCE_ROOT") or "").strip())
    if not str(raw):
        raise PreflightError("STEGVERSE_STEGINDEX_SOURCE_ROOT is not configured")
    root = Path(raw).expanduser().resolve()
    required = (root / INDEX_HANDOFF, root / CAP_REGISTRY, root / PRED_REGISTRY)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise PreflightError("StegIndex source incomplete: " + ",".join(missing))
    return root


def _score(entry: dict[str, Any], query: str) -> int:
    q = query.lower().strip()
    fields = [
        str(entry.get("capability_id") or ""),
        str(entry.get("purpose") or ""),
        str(entry.get("owner_repo") or ""),
        " ".join(str(x) for x in entry.get("aliases", [])),
        " ".join(str(x) for x in entry.get("interfaces", [])),
    ]
    text = " ".join(fields).lower()
    if q == str(entry.get("capability_id") or "").lower():
        return 100
    if q and q in text:
        return 50
    terms = [t for t in q.replace(":", " ").replace("-", " ").split() if t]
    return sum(1 for term in terms if term in text)


def resolve(
    *,
    index_root: Path,
    query: str,
    requested_predicate: str | None = None,
    capability_id: str | None = None,
) -> dict[str, Any]:
    caps_doc = _load(index_root / CAP_REGISTRY)
    preds_doc = _load(index_root / PRED_REGISTRY)
    entries = list(caps_doc.get("entries") or [])
    pred_defs = {p["predicate_id"]: p for p in preds_doc.get("predicates") or [] if isinstance(p, dict) and p.get("predicate_id")}

    if capability_id:
        capabilities = [entry for entry in entries if entry.get("capability_id") == capability_id]
    else:
        ranked = sorted(((_score(entry, query), entry) for entry in entries), key=lambda item: item[0], reverse=True)
        capabilities = [entry for score, entry in ranked if score > 0]

    predicates: list[dict[str, Any]] = []
    for cap in capabilities:
        missing = list(cap.get("missing_predicates") or [])
        names = [requested_predicate] if requested_predicate else missing
        for name in names:
            if not name:
                continue
            known = name in pred_defs
            is_missing = name in missing
            predicates.append({
                "predicate_id": name,
                "current_truth_state": "FALSE" if is_missing else ("UNKNOWN" if known else "UNKNOWN"),
                "satisfier_capability_id": cap.get("capability_id"),
                "satisfier_owner": cap.get("blocking_owner") or cap.get("owner_repo"),
                "satisfier_interface": cap.get("invocation_surface"),
                "machine_executable_now": False,
                "user_action_required": bool(cap.get("user_action_required")),
                "external_authority_required": False,
                "evidence_current": cap.get("current_evidence_state"),
                "provenance": list(cap.get("provenance") or []),
            })

    first = next((p for p in predicates if p["current_truth_state"] in {"FALSE","UNKNOWN","STALE","CONTRADICTORY"}), None)
    machine_continuation = bool(first and first.get("machine_executable_now"))
    generic_blocker_permitted = bool(first and not machine_continuation)

    return {
        "schema": "stegverse.stegindex-preflight-result/v1",
        "query": query,
        "capabilities": capabilities,
        "predicates": predicates,
        "first_actionable_predicate": first,
        "machine_continuation_required": machine_continuation,
        "generic_blocker_permitted": generic_blocker_permitted,
        "index_root": str(index_root),
        "network_fetch_performed": False,
        "credential_read_or_acquired": False,
        "github_token_required": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_READ_RESOLVE_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve mandatory StegIndex preflight from an already-local canonical StegIndex source.")
    parser.add_argument("--index-root", type=Path)
    parser.add_argument("--query", required=True)
    parser.add_argument("--predicate")
    parser.add_argument("--capability-id")
    args = parser.parse_args()

    try:
        root = _index_root(args.index_root)
        result = resolve(index_root=root, query=args.query, requested_predicate=args.predicate, capability_id=args.capability_id)
    except PreflightError as exc:
        result = {
            "schema": "stegverse.stegindex-preflight-result/v1",
            "query": args.query,
            "capabilities": [],
            "predicates": [],
            "first_actionable_predicate": None,
            "machine_continuation_required": False,
            "generic_blocker_permitted": False,
            "state": "PREFLIGHT_UNAVAILABLE",
            "problem_statement": str(exc),
            "source_unavailable_is_implementation_missing": False,
            "network_fetch_performed": False,
            "credential_read_or_acquired": False,
            "github_token_required": False,
            "credential_authority": "TV/TVC",
            "authority_effect": "NONE_READ_RESOLVE_ONLY",
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("state") != "PREFLIGHT_UNAVAILABLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
