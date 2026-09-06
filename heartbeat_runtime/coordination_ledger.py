"""Deterministic composition for the canonical cross-task coordination ledger.

The base ledger remains `control/cross-task-coordination.json`. Canonical extension
fragments live in `control/cross-task-coordination.d/*.json` and are composed in
lexicographic filename order. Composition is non-authorizing and fails closed on
schema drift or duplicate stable identifiers.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

LEDGER_SCHEMA = "stegverse.cross-task-coordination-ledger/v1"
FRAGMENT_SCHEMA = "stegverse.cross-task-coordination-fragment/v1"
COLLECTIONS = ("goals", "tasks", "predicates", "evidence", "claims", "gaps")
ID_FIELDS = {
    "goals": "goal_id",
    "tasks": "task_id",
    "predicates": "predicate_id",
    "evidence": "evidence_id",
    "claims": "claim_id",
}


class CoordinationLedgerError(RuntimeError):
    pass


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CoordinationLedgerError(f"unreadable coordination JSON: {path}") from exc
    if not isinstance(value, dict):
        raise CoordinationLedgerError(f"coordination JSON must be object: {path}")
    return value


def _gap_key(row: dict[str, Any]) -> tuple[str, str]:
    predicate_id = str(row.get("predicate_id") or "")
    subject = row.get("subject_binding")
    subject_key = json.dumps(subject, sort_keys=True, separators=(",", ":")) if isinstance(subject, dict) else ""
    return predicate_id, subject_key


def _existing_keys(ledger: dict[str, Any], collection: str) -> set[Any]:
    rows = ledger.get(collection, [])
    if not isinstance(rows, list):
        raise CoordinationLedgerError(f"ledger collection must be list: {collection}")
    if collection == "gaps":
        return {_gap_key(row) for row in rows if isinstance(row, dict)}
    field = ID_FIELDS[collection]
    return {str(row.get(field)) for row in rows if isinstance(row, dict) and row.get(field)}


def compose_coordination_ledger(base: dict[str, Any], fragments: list[dict[str, Any]]) -> dict[str, Any]:
    if base.get("schema") != LEDGER_SCHEMA:
        raise CoordinationLedgerError("unsupported base coordination ledger schema")
    result = deepcopy(base)
    for collection in COLLECTIONS:
        result.setdefault(collection, [])
        if not isinstance(result[collection], list):
            raise CoordinationLedgerError(f"ledger collection must be list: {collection}")

    fragment_ids: set[str] = set()
    for fragment in fragments:
        if fragment.get("schema") != FRAGMENT_SCHEMA:
            raise CoordinationLedgerError("unsupported coordination fragment schema")
        fragment_id = str(fragment.get("fragment_id") or "")
        if not fragment_id:
            raise CoordinationLedgerError("coordination fragment_id missing")
        if fragment_id in fragment_ids:
            raise CoordinationLedgerError(f"duplicate coordination fragment_id: {fragment_id}")
        fragment_ids.add(fragment_id)
        if fragment.get("authority_effect") not in {"NONE", "NONE_COORDINATION_ONLY"}:
            raise CoordinationLedgerError(f"coordination fragment authority effect invalid: {fragment_id}")

        for collection in COLLECTIONS:
            rows = fragment.get(collection, [])
            if rows is None:
                rows = []
            if not isinstance(rows, list):
                raise CoordinationLedgerError(f"fragment collection must be list: {fragment_id}:{collection}")
            seen = _existing_keys(result, collection)
            for row in rows:
                if not isinstance(row, dict):
                    raise CoordinationLedgerError(f"fragment row must be object: {fragment_id}:{collection}")
                if collection == "gaps":
                    key: Any = _gap_key(row)
                    if not key[0]:
                        raise CoordinationLedgerError(f"gap predicate_id missing: {fragment_id}")
                else:
                    field = ID_FIELDS[collection]
                    key = str(row.get(field) or "")
                    if not key:
                        raise CoordinationLedgerError(f"stable id missing: {fragment_id}:{collection}:{field}")
                if key in seen:
                    raise CoordinationLedgerError(f"duplicate canonical coordination record: {collection}:{key}")
                result[collection].append(deepcopy(row))
                seen.add(key)

    result["composition"] = {
        "mode": "BASE_PLUS_SORTED_APPEND_ONLY_FRAGMENTS",
        "fragment_schema": FRAGMENT_SCHEMA,
        "fragment_ids": sorted(fragment_ids),
        "authority_effect": "NONE",
    }
    return result


def load_composed_coordination_ledger(
    base_path: Path,
    fragments_dir: Path | None = None,
) -> dict[str, Any]:
    base_path = Path(base_path)
    base = _read_object(base_path)
    directory = Path(fragments_dir) if fragments_dir is not None else base_path.parent / "cross-task-coordination.d"
    fragments: list[dict[str, Any]] = []
    if directory.exists():
        if not directory.is_dir():
            raise CoordinationLedgerError(f"coordination fragment path is not directory: {directory}")
        for path in sorted(directory.glob("*.json"), key=lambda item: item.name):
            fragments.append(_read_object(path))
    return compose_coordination_ledger(base, fragments)


__all__ = [
    "COLLECTIONS",
    "CoordinationLedgerError",
    "FRAGMENT_SCHEMA",
    "LEDGER_SCHEMA",
    "compose_coordination_ledger",
    "load_composed_coordination_ledger",
]
