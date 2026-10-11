#!/usr/bin/env python3
"""Materialize COSV task-vector index shards for vectorized registry tasks.

Projection only. The effective COSV index is the aggregate
``control/task-vector-index.json`` plus ``control/task-vector-index.d/*.json``
shards, merged the way ``scripts/materialize_reusable_task_construct.py``
resolves it. A scheduled task whose ``task_id`` has no effective row dies at
``verify_task_pointer`` ("canonical COSV task pointer must resolve exactly
once"). This script closes that gap deterministically and fails closed where
the registry does not provide a machine source to bind.

For every task declared on a registry surface with a COSV binding
(``cosv_task_vector``, ``source_state_vector_ref`` or an embedded
``machine_readable_state.cosv.vector``) that has no effective index row, a
shard is derived ONLY when:

* some registry surface names a ``source_state_vector_ref`` for the task,
* the registry declares exactly one COSV vector for the task,
* the referenced file exists inside the repository root,
* it is a ``task.v1`` / ``level: task`` record whose identity ends
  ``:task:<task_id>``,
* its vector equals the registry's declared vector.

Otherwise the task is reported as FAIL_CLOSED with one predicate:

* ``SOURCE_REF_ABSENT``: no registry surface names a source state-vector.
* ``SOURCE_REF_CONFLICT``: registry surfaces name different sources.
* ``REGISTRY_VECTOR_ABSENT``: a source is named but no vector is declared.
* ``VECTOR_SOURCE_NOT_MATERIALIZED``: the referenced file does not exist
  (or escapes the repository root).
* ``VECTOR_IDENTITY_MISMATCH``: the file is not a ``task.v1`` task-level
  record identified as ``:task:<task_id>``.
* ``VECTOR_VALUE_MISMATCH``: the file vector and the registry vector differ,
  the registry declares conflicting vectors, or the vector is malformed.
* ``VECTOR_SOURCE_INCOMPLETE``: the file binds the vector but is not a
  complete COSV record (``scripts/cosv.py`` ``validate_record`` plus
  ``exact_metrics.symbol_order``), which the index completeness test
  requires of every registry-bound source. Only new derivations are gated
  on this; the runtime pointer gate does not require it.

Nothing is written for a fail-closed task and no vector is ever fabricated.
Existing effective rows are inspected with the ``verify_task_pointer``
predicate; defects are reported, and ``--normalize-shards`` rewrites a shard
that carries only ``cosv_task_vector`` into the full shape when its source
passes.

Default mode writes derivable shards and prints a JSON receipt. ``--check``
writes nothing and exits 1 when any shard would be added or normalized, any
task fails closed, or any existing row is defective, unless the item is listed
in an ``--owner-items`` file (a ratchet of acknowledged owner items that may
only shrink). The aggregate index is never modified. ``authority_effect`` is
``NONE`` throughout: this emits non-authorizing projections and claims no
runtime transition.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


def _load_cosv() -> Any:
    spec = importlib.util.spec_from_file_location("cosv", Path(__file__).resolve().with_name("cosv.py"))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cosv = _load_cosv()

SHARD_SCHEMA = "stegverse.cosv-task-vector-index-entry/v1"
SYMBOL_ORDER = "LRUIVGOCMTBEAP"
RECEIPT_SCHEMA = "stegverse.cosv-task-vector-index-shard-materialization-receipt/v1"
OWNER_ITEMS_SCHEMA = "stegverse.cosv-task-vector-index-owner-items/v1"
VECTOR_RE = re.compile(r"^[0-9]{14}$")

AGGREGATE_INDEX = "control/task-vector-index.json"
INDEX_SHARDS = "control/task-vector-index.d"
REGISTRY_SURFACES = (
    "control/worker-registry.json",
    "control/organization-task-registry.json",
    "control/worker-registry.d",
    "data/canonical-task-registry.json",
    "data/canonical-task-records",
)

PREDICATES = (
    "SOURCE_REF_ABSENT",
    "SOURCE_REF_CONFLICT",
    "REGISTRY_VECTOR_ABSENT",
    "VECTOR_SOURCE_NOT_MATERIALIZED",
    "VECTOR_IDENTITY_MISMATCH",
    "VECTOR_VALUE_MISMATCH",
    "VECTOR_SOURCE_INCOMPLETE",
    "INDEX_ROW_VECTOR_ABSENT",
    "INDEX_ROW_NOT_NON_AUTHORIZING",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


# --------------------------------------------------------------------------- registry


def iter_registry_rows(root: Path) -> list[tuple[str, dict[str, Any]]]:
    """Yield (surface_ref, row) in resolution order.

    Order mirrors the effective-index completeness test and
    ``build_canonical_work_intr_request.resolve_task``: operational worker and
    organization registries first, then the monolithic canonical registry,
    then canonical task-record shards.
    """
    rows: list[tuple[str, dict[str, Any]]] = []
    for surface in REGISTRY_SURFACES:
        path = root / surface
        if path.is_dir():
            paths = sorted(path.glob("*.json"))
        elif path.is_file():
            paths = [path]
        else:
            continue
        for item in paths:
            payload = load_json(item)
            if not isinstance(payload, dict):
                continue
            ref = rel(root, item)
            if isinstance(payload.get("task_id"), str) and payload["task_id"]:
                rows.append((ref, payload))
            for task in payload.get("tasks", []) or []:
                if isinstance(task, dict) and isinstance(task.get("task_id"), str) and task["task_id"]:
                    rows.append((ref, task))
    return rows


def embedded_vector(row: dict[str, Any]) -> str | None:
    state = row.get("machine_readable_state")
    if not isinstance(state, dict):
        return None
    cosv = state.get("cosv")
    if not isinstance(cosv, dict):
        return None
    vector = cosv.get("vector")
    return vector if isinstance(vector, str) and vector else None


def is_vectorized(row: dict[str, Any]) -> bool:
    return bool(row.get("cosv_task_vector") or row.get("source_state_vector_ref") or embedded_vector(row))


def collect_declarations(root: Path) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    declarations: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for ref, row in iter_registry_rows(root):
        declarations.setdefault(row["task_id"], []).append((ref, row))
    return {task_id: rows for task_id, rows in declarations.items() if any(is_vectorized(r) for _, r in rows)}


# --------------------------------------------------------------------------- index


def load_effective_index(root: Path) -> dict[str, tuple[str, dict[str, Any]]]:
    """Return task_id -> (origin, row); origin is 'aggregate' or the shard path."""
    aggregate_path = root / AGGREGATE_INDEX
    if not aggregate_path.is_file():
        raise SystemExit(f"FAIL_CLOSED: aggregate COSV index missing: {aggregate_path}")
    aggregate = load_json(aggregate_path)
    if not isinstance(aggregate, dict) or not isinstance(aggregate.get("tasks"), list):
        raise SystemExit("FAIL_CLOSED: canonical COSV task-vector index shape is invalid")
    rows: dict[str, tuple[str, dict[str, Any]]] = {}
    for raw in aggregate["tasks"]:
        if not isinstance(raw, dict) or not isinstance(raw.get("task_id"), str) or not raw["task_id"]:
            raise SystemExit("FAIL_CLOSED: canonical COSV task-vector index row is invalid")
        if raw["task_id"] in rows:
            raise SystemExit(f"FAIL_CLOSED: duplicate canonical COSV task-vector index row: {raw['task_id']}")
        rows[raw["task_id"]] = ("aggregate", dict(raw))
    shard_root = root / INDEX_SHARDS
    if shard_root.is_dir():
        for path in sorted(shard_root.glob("*.json")):
            shard = load_json(path)
            if not isinstance(shard, dict) or shard.get("schema") != SHARD_SCHEMA:
                continue
            task_id = shard.get("task_id")
            if not isinstance(task_id, str) or not task_id:
                raise SystemExit(f"FAIL_CLOSED: canonical COSV task-vector index shard missing task_id: {path}")
            existing = rows.get(task_id)
            if existing is None:
                rows[task_id] = (rel(root, path), dict(shard))
                continue
            for key in ("source_state_vector_ref", "vector", "vector_state", "authority_effect"):
                if shard.get(key) != existing[1].get(key):
                    raise SystemExit(f"FAIL_CLOSED: canonical COSV task-vector index shard disagrees for {task_id}:{key}")
    return rows


# --------------------------------------------------------------------------- source predicate


def inspect_source(root: Path, task_id: str, source_ref: str, vector: str | None) -> tuple[str | None, str | None]:
    """Return (predicate, detail); predicate None means the source binds ``vector``."""
    source_path = (root / source_ref.split("#", 1)[0]).resolve()
    try:
        source_path.relative_to(root.resolve())
    except ValueError:
        return "VECTOR_SOURCE_NOT_MATERIALIZED", "source state-vector escapes repository root"
    if not source_path.is_file():
        return "VECTOR_SOURCE_NOT_MATERIALIZED", f"missing {source_ref}"
    try:
        record = load_json(source_path)
    except (OSError, json.JSONDecodeError) as exc:
        return "VECTOR_SOURCE_NOT_MATERIALIZED", f"unreadable {source_ref}: {exc}"
    if not isinstance(record, dict):
        return "VECTOR_IDENTITY_MISMATCH", "source state-vector is not an object"
    identity = str(record.get("identity") or "")
    if record.get("profile") != "task.v1":
        return "VECTOR_IDENTITY_MISMATCH", f"profile={record.get('profile')!r}"
    if record.get("level") != "task":
        return "VECTOR_IDENTITY_MISMATCH", f"level={record.get('level')!r}"
    if not identity.endswith(f":task:{task_id}"):
        return "VECTOR_IDENTITY_MISMATCH", f"identity={identity!r}"
    file_vector = record.get("vector")
    if not isinstance(file_vector, str) or not VECTOR_RE.match(file_vector):
        return "VECTOR_VALUE_MISMATCH", f"source vector malformed: {file_vector!r}"
    if vector is not None and file_vector != vector:
        return "VECTOR_VALUE_MISMATCH", f"source vector {file_vector} != registry vector {vector}"
    return None, None


def inspect_record_completeness(root: Path, source_ref: str) -> tuple[str | None, str | None]:
    """The index completeness test's record predicate for registry-bound sources."""
    record = load_json(root / source_ref.split("#", 1)[0])
    if not cosv.validate_record(record):
        return "VECTOR_SOURCE_INCOMPLETE", "source record fails cosv.validate_record (identity/profile/level/vector/evidence_refs/observed_at/exact_metrics)"
    metrics = record.get("exact_metrics")
    if not isinstance(metrics, dict) or metrics.get("symbol_order") != SYMBOL_ORDER:
        return "VECTOR_SOURCE_INCOMPLETE", f"exact_metrics.symbol_order != {SYMBOL_ORDER}"
    return None, None


# --------------------------------------------------------------------------- derivation


def fail(task_id: str, predicate: str, detail: str, **extra: Any) -> dict[str, Any]:
    assert predicate in PREDICATES
    return {"task_id": task_id, "predicate": predicate, "detail": detail, **extra}


def derive_shard(root: Path, task_id: str, rows: list[tuple[str, dict[str, Any]]]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Return (shard, None) or (None, fail_closed_row)."""
    declared = sorted({r["cosv_task_vector"] for _, r in rows if isinstance(r.get("cosv_task_vector"), str) and r["cosv_task_vector"]})
    embedded = sorted({v for _, r in rows if (v := embedded_vector(r))})
    vectors = sorted(set(declared) | set(embedded))
    refs = sorted({r["source_state_vector_ref"] for _, r in rows if isinstance(r.get("source_state_vector_ref"), str) and r["source_state_vector_ref"]})
    surfaces = [ref for ref, _ in rows]

    if not refs:
        conventional = f"control/task-vectors/{task_id}.json"
        return None, fail(
            task_id,
            "SOURCE_REF_ABSENT",
            "no registry surface names source_state_vector_ref",
            registry_surfaces=surfaces,
            declared_vectors=vectors,
            conventional_source_present=(root / conventional).is_file(),
        )
    if len(refs) > 1:
        return None, fail(task_id, "SOURCE_REF_CONFLICT", "registry surfaces disagree on source_state_vector_ref", registry_surfaces=surfaces, source_state_vector_refs=refs)
    source_ref = refs[0]
    if not vectors:
        return None, fail(task_id, "REGISTRY_VECTOR_ABSENT", "registry names a source but declares no COSV vector", registry_surfaces=surfaces, source_state_vector_ref=source_ref)
    if len(vectors) > 1:
        return None, fail(task_id, "VECTOR_VALUE_MISMATCH", "registry surfaces declare different COSV vectors", registry_surfaces=surfaces, declared_vectors=vectors, source_state_vector_ref=source_ref)
    vector = vectors[0]
    if not VECTOR_RE.match(vector):
        return None, fail(task_id, "VECTOR_VALUE_MISMATCH", f"registry vector malformed: {vector!r}", registry_surfaces=surfaces, source_state_vector_ref=source_ref)
    predicate, detail = inspect_source(root, task_id, source_ref, vector)
    if predicate is None:
        predicate, detail = inspect_record_completeness(root, source_ref)
    if predicate:
        return None, fail(task_id, predicate, detail or predicate, registry_surfaces=surfaces, source_state_vector_ref=source_ref, declared_vectors=vectors)

    # The binding surface is the first surface (in resolution order) that names the source.
    binding_ref, binding_row = next((ref, r) for ref, r in rows if r.get("source_state_vector_ref") == source_ref)

    def first(key: str) -> str | None:
        value = binding_row.get(key)
        if isinstance(value, str) and value:
            return value
        for _, r in rows:
            value = r.get(key)
            if isinstance(value, str) and value:
                return value
        return None

    shard: dict[str, Any] = {"schema": SHARD_SCHEMA, "task_id": task_id}
    repository = first("repository")
    if repository:
        shard["repository"] = repository
    shard["registry_ref"] = binding_ref
    shard["source_state_vector_ref"] = source_ref
    shard["cosv_task_vector"] = vector
    shard["vector"] = vector
    shard["vector_state"] = "EMITTED"
    shard["profile"] = "task.v1"
    shard["authority_effect"] = "NONE"
    handoff = first("handoff_ref")
    if handoff:
        shard["handoff_ref"] = handoff
    return shard, None


def inspect_existing_row(root: Path, origin: str, row: dict[str, Any]) -> dict[str, Any] | None:
    """Apply the verify_task_pointer predicate to an existing effective row."""
    task_id = row["task_id"]
    expected = row.get("vector") if isinstance(row.get("vector"), str) else row.get("cosv_task_vector")
    if not isinstance(expected, str) or not VECTOR_RE.match(expected):
        return fail(task_id, "INDEX_ROW_VECTOR_ABSENT", "row carries no well-formed vector", origin=origin)
    if row.get("vector_state") not in (None, "EMITTED") or row.get("authority_effect") not in (None, "NONE"):
        return fail(task_id, "INDEX_ROW_NOT_NON_AUTHORIZING", "row is not EMITTED / authority_effect NONE", origin=origin)
    source_ref = row.get("source_state_vector_ref")
    if not isinstance(source_ref, str) or not source_ref:
        return fail(task_id, "SOURCE_REF_ABSENT", "row lacks source_state_vector_ref", origin=origin)
    predicate, detail = inspect_source(root, task_id, source_ref, expected)
    if predicate:
        return fail(task_id, predicate, detail or predicate, origin=origin, source_state_vector_ref=source_ref)
    if row.get("vector") is None:
        return fail(task_id, "INDEX_ROW_VECTOR_ABSENT", "shard carries cosv_task_vector only; normalizable", origin=origin, normalizable=True)
    return None


def normalized_shard(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in row.items():
        out[key] = value
        if key == "cosv_task_vector":
            out["vector"] = value
            out["vector_state"] = "EMITTED"
            out["authority_effect"] = "NONE"
    return out


# --------------------------------------------------------------------------- main


def load_owner_items(path: Path | None) -> set[tuple[str, str]]:
    if path is None:
        return set()
    payload = load_json(path)
    if not isinstance(payload, dict) or payload.get("schema") != OWNER_ITEMS_SCHEMA:
        raise SystemExit(f"FAIL_CLOSED: owner items schema invalid: {path}")
    items: set[tuple[str, str]] = set()
    for item in payload.get("items", []):
        if not isinstance(item, dict) or item.get("predicate") not in PREDICATES or not isinstance(item.get("task_id"), str):
            raise SystemExit(f"FAIL_CLOSED: owner item invalid: {item!r}")
        items.add((item["task_id"], item["predicate"]))
    return items


def materialize(root: Path, *, check: bool, normalize: bool, owner_items: set[tuple[str, str]]) -> dict[str, Any]:
    effective = load_effective_index(root)
    declarations = collect_declarations(root)
    excluded_ids = {task_id for task_id in declarations if task_id in effective}

    added: list[dict[str, Any]] = []
    fail_closed: list[dict[str, Any]] = []
    for task_id in sorted(declarations):
        if task_id in effective:
            continue
        shard, failure = derive_shard(root, task_id, declarations[task_id])
        if failure:
            fail_closed.append(failure)
            continue
        assert shard is not None
        added.append(shard)

    defects: list[dict[str, Any]] = []
    normalized: list[dict[str, Any]] = []
    for task_id in sorted(effective):
        origin, row = effective[task_id]
        defect = inspect_existing_row(root, origin, row)
        if defect is None:
            continue
        if defect.get("normalizable") and origin != "aggregate" and normalize:
            normalized.append({"task_id": task_id, "origin": origin, "row": normalized_shard(row)})
        else:
            defects.append(defect)

    live = {(x["task_id"], x["predicate"]) for x in fail_closed + defects}
    deferred = [x for x in fail_closed + defects if (x["task_id"], x["predicate"]) in owner_items]
    fail_closed = [x for x in fail_closed if (x["task_id"], x["predicate"]) not in owner_items]
    defects = [x for x in defects if (x["task_id"], x["predicate"]) not in owner_items]
    stale = sorted(f"{t}:{p}" for t, p in owner_items - live)

    if not check:
        shard_root = root / INDEX_SHARDS
        shard_root.mkdir(parents=True, exist_ok=True)
        for shard in added:
            (shard_root / f"{shard['task_id']}.json").write_text(dump_json(shard), encoding="utf-8")
        for item in normalized:
            (root / item["origin"]).write_text(dump_json(item["row"]), encoding="utf-8")

    drift = bool(added or normalized)
    blocked = bool(fail_closed or defects or stale)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "mode": "check" if check else "write",
        "authority_effect": "NONE",
        "claims_runtime_transition": False,
        "effective_index_rows_before": len(effective),
        "effective_index_rows_after": len(effective) + len(added),
        "vectorized_registry_tasks": len(declarations),
        "vectorized_registry_tasks_indexed_before": len(excluded_ids),
        "vectorized_registry_tasks_indexed_after": len(excluded_ids) + len(added),
        "added": [x["task_id"] for x in added],
        "normalized": [x["task_id"] for x in normalized],
        "unchanged": len(effective) - len(normalized),
        "skipped_fail_closed": fail_closed,
        "existing_row_defects": defects,
        "deferred_owner_items": [{"task_id": x["task_id"], "predicate": x["predicate"]} for x in deferred],
        "stale_owner_items": stale,
        "status": "FAIL_CLOSED" if blocked else ("DRIFT" if (check and drift) else "OK"),
    }
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 on drift or fail-closed items")
    parser.add_argument("--normalize-shards", action="store_true", help="rewrite cosv_task_vector-only shards whose source passes into the full shape")
    parser.add_argument("--owner-items", help="acknowledged owner-items ratchet file (task_id + predicate)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    owner_items = load_owner_items(Path(args.owner_items).resolve() if args.owner_items else None)
    receipt = materialize(root, check=args.check, normalize=args.normalize_shards, owner_items=owner_items)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    # Write mode always exits 0: the receipt carries fail-closed owner items.
    # Check mode is a gate: anything but a clean OK is a failure.
    return 1 if args.check and receipt["status"] != "OK" else 0


if __name__ == "__main__":
    sys.exit(main())
