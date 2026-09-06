"""Deterministic composition for the canonical cross-task coordination ledger.

The base ledger remains `control/cross-task-coordination.json`. Canonical extension
fragments live in `control/cross-task-coordination.d/*.json` and are composed in
lexicographic filename order. Composition is non-authorizing and fails closed on
schema drift or duplicate stable identifiers.

When a sibling `control/worker-registry.json` exists, the composed ledger also
validates coverage parity for unreleased BOUND WorkerCoordinator claims. The
worker registry remains authoritative for claim/fence ownership; coordination
claims are projections used only for collision/adjacency resolution.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

LEDGER_SCHEMA = "stegverse.cross-task-coordination-ledger/v1"
FRAGMENT_SCHEMA = "stegverse.cross-task-coordination-fragment/v1"
WORKER_REGISTRY_SCHEMA = "stegverse.heartbeat-worker-registry/v0.1"
COLLECTIONS = ("goals", "tasks", "predicates", "evidence", "claims", "gaps")
ID_FIELDS = {
    "goals": "goal_id",
    "tasks": "task_id",
    "predicates": "predicate_id",
    "evidence": "evidence_id",
    "claims": "claim_id",
}
TERMINAL_WORKER_STATES = {"COMPLETED", "FAILED_TERMINAL"}


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


def _worker_claim_fence(task: dict[str, Any]) -> int | None:
    timing = task.get("heartbeat_timing")
    if isinstance(timing, dict) and isinstance(timing.get("fencing_token"), int):
        return int(timing["fencing_token"])
    lease = task.get("lease")
    if isinstance(lease, dict) and isinstance(lease.get("fencing_token"), int):
        return int(lease["fencing_token"])
    return None


def _unreleased_bound_worker_claims(worker_registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if worker_registry.get("schema") != WORKER_REGISTRY_SCHEMA:
        raise CoordinationLedgerError("unsupported worker registry schema for coordination claim coverage")
    tasks = worker_registry.get("tasks")
    if not isinstance(tasks, list):
        raise CoordinationLedgerError("worker registry tasks must be list")

    claims: dict[str, dict[str, Any]] = {}
    for task in tasks:
        if not isinstance(task, dict):
            raise CoordinationLedgerError("worker registry task must be object")
        claim_id = str(task.get("claim_id") or "")
        if not claim_id or task.get("executor_binding") != "BOUND":
            continue
        if task.get("archive_eligible") is True or task.get("state") in TERMINAL_WORKER_STATES:
            continue
        if claim_id in claims:
            raise CoordinationLedgerError(f"duplicate unreleased WorkerCoordinator claim: {claim_id}")
        claims[claim_id] = task
    return claims


def validate_worker_claim_coverage(ledger: dict[str, Any], worker_registry: dict[str, Any]) -> dict[str, Any]:
    """Fail closed when coordination claim mirrors drift from WorkerCoordinator truth.

    Coverage validation grants no authority and does not infer runtime execution.
    It only requires every unreleased BOUND WorkerCoordinator claim to be visible
    in the composed coordination ledger with matching identity, and rejects stale
    ACTIVE worker-bound coordination mirrors whose canonical claim is no longer
    unreleased in the worker registry.
    """
    registry_claims = _unreleased_bound_worker_claims(worker_registry)
    ledger_rows = ledger.get("claims", [])
    if not isinstance(ledger_rows, list):
        raise CoordinationLedgerError("ledger claims must be list")
    ledger_claims = {
        str(row.get("claim_id")): row
        for row in ledger_rows
        if isinstance(row, dict) and row.get("claim_id")
    }

    for claim_id, task in registry_claims.items():
        row = ledger_claims.get(claim_id)
        if row is None:
            raise CoordinationLedgerError(f"unmirrored active WorkerCoordinator claim: {claim_id}")
        expected = {
            "task_id": str(task.get("task_id") or ""),
            "worker_id": str(task.get("worker_id") or ""),
            "worker_instance_id": str(task.get("worker_instance_id") or ""),
            "fencing_token": _worker_claim_fence(task),
        }
        for field, value in expected.items():
            if value in (None, ""):
                continue
            if row.get(field) != value:
                raise CoordinationLedgerError(
                    f"WorkerCoordinator coordination claim identity mismatch: {claim_id}:{field}"
                )
        if row.get("state") != "ACTIVE":
            raise CoordinationLedgerError(f"unreleased WorkerCoordinator claim not ACTIVE in coordination: {claim_id}")

    for claim_id, row in ledger_claims.items():
        if row.get("state") != "ACTIVE":
            continue
        worker_bound = any(row.get(field) not in (None, "") for field in ("worker_id", "worker_instance_id", "fencing_token"))
        if worker_bound and claim_id not in registry_claims:
            raise CoordinationLedgerError(f"stale active WorkerCoordinator coordination claim: {claim_id}")

    return {
        "mode": "WORKER_REGISTRY_UNRELEASED_BOUND_CLAIM_PARITY",
        "worker_registry_schema": WORKER_REGISTRY_SCHEMA,
        "validated_claim_ids": sorted(registry_claims),
        "authority_effect": "NONE",
        "runtime_execution_inferred": False,
    }


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
    worker_registry_path: Path | None = None,
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
    result = compose_coordination_ledger(base, fragments)

    registry_path = Path(worker_registry_path) if worker_registry_path is not None else base_path.parent / "worker-registry.json"
    if registry_path.exists():
        claim_coverage = validate_worker_claim_coverage(result, _read_object(registry_path))
        result["composition"]["worker_claim_coverage"] = claim_coverage
    return result


__all__ = [
    "COLLECTIONS",
    "CoordinationLedgerError",
    "FRAGMENT_SCHEMA",
    "LEDGER_SCHEMA",
    "WORKER_REGISTRY_SCHEMA",
    "compose_coordination_ledger",
    "load_composed_coordination_ledger",
    "validate_worker_claim_coverage",
]
