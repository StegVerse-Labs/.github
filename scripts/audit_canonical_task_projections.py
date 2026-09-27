#!/usr/bin/env python3
"""Read-only full-shard / aggregate / COSV coverage audit.

Do not promote shard state into the aggregate: admission, ownership and receipt
authority remain with their existing producers. Exit 1 only for structural
corruption; projection gaps and competing claims are actionable findings.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def vector(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("vector")
    return None


def evaluate(registry: dict, shards: dict[str, dict], index: dict) -> dict:
    rows = registry.get("tasks") or []
    entries = index.get("tasks") or []
    reg_ids = [r.get("task_id") for r in rows]
    idx_ids = [r.get("task_id") for r in entries]
    aggregate = {r["task_id"]: r for r in rows if r.get("task_id")}
    indexed = {r["task_id"]: r for r in entries if r.get("task_id")}
    malformed = []
    for task_id, shard in shards.items():
        if shard.get("task_id") != task_id:
            malformed.append({"shard": task_id, "actual_task_id": shard.get("task_id")})
    for population, names in (("aggregate", reg_ids), ("index", idx_ids)):
        for task_id, n in sorted(Counter(names).items()):
            if n > 1:
                malformed.append({"population": population, "duplicate_task_id": task_id, "count": n})
    shard_not_aggregate = sorted(set(shards) - set(aggregate))
    omitted_checked_out = sorted(
        task_id for task_id in shard_not_aggregate
        if shards[task_id].get("checkout_state") == "CHECKED_OUT"
        and shards[task_id].get("coordination_state") in {"ACTIVE", "CHECKED_OUT"}
    )
    aggregate_not_shard = sorted(set(aggregate) - set(shards))
    shard_drift = []
    for task_id in sorted(set(aggregate) & set(shards)):
        row, shard = aggregate[task_id], shards[task_id]
        differences = {}
        for key in ("coordination_state", "checkout_state", "root_correlation_id", "parent_task_id"):
            if key in row and key in shard and row[key] != shard[key]:
                differences[key] = {"aggregate": row[key], "shard": shard[key]}
        av = vector(row.get("cosv_task_vector") or row.get("cosv"))
        sv = vector(shard.get("cosv_task_vector") or shard.get("cosv"))
        if av and sv and av != sv:
            differences["cosv"] = {"aggregate": av, "shard": sv}
        if differences:
            shard_drift.append({"task_id": task_id, "differences": differences})
    vector_conflicts = []
    for task_id in sorted(set(indexed) & (set(shards) | set(aggregate))):
        source = shards.get(task_id) or aggregate[task_id]
        actual = vector(source.get("cosv_task_vector") or source.get("cosv"))
        indexed_value = vector(indexed[task_id].get("vector"))
        if actual and indexed_value and actual != indexed_value:
            vector_conflicts.append({"task_id": task_id, "source": actual, "index": indexed_value})
    return {
        "schema": "stegverse.canonical-task-projection-audit/v1",
        "registry_generation": registry.get("generation"),
        "authority_effect": "NONE_READ_ONLY",
        "counts": {
            "aggregate": len(rows),
            "exact_shards": len(shards),
            "cosv_index": len(entries),
            "shards_absent_from_aggregate": len(shard_not_aggregate),
            "omitted_checked_out_owner_shards": len(omitted_checked_out),
            "aggregate_without_exact_shard": len(aggregate_not_shard),
            "indexed_not_in_aggregate": len(set(indexed) - set(aggregate)),
            "aggregate_not_indexed": len(set(aggregate) - set(indexed)),
        },
        "structural_errors": malformed,
        "shards_absent_from_aggregate": shard_not_aggregate,
        "omitted_checked_out_owner_shards": omitted_checked_out,
        "aggregate_without_exact_shard": aggregate_not_shard,
        "shard_aggregate_drift": shard_drift,
        "cosv_conflicts_where_both_emitted": vector_conflicts,
        "indexed_not_in_aggregate": sorted(set(indexed) - set(aggregate)),
        "aggregate_not_indexed": sorted(set(aggregate) - set(indexed)),
        "interpretation": {
            "missing_aggregate_row": "RECONCILE_EXISTING_OWNER_NOT_NEW_REGISTRATION",
            "missing_shard": "INVESTIGATE_PROJECTION_OR_LEGACY_AGGREGATE_RECORD",
            "missing_index": "REPORT_COVERAGE_DIFFERENCE_NOT_IMPLICIT_FAILURE",
            "runtime_proof": "NOT_EVALUATED_NO_RESIDENT_ACCESS",
        },
    }


def load_shards(directory: Path) -> tuple[dict[str, dict], list[str]]:
    """Exclude verified session-note sidecars, never hide malformed task shards."""
    shards: dict[str, dict] = {}
    notes: list[str] = []
    for path in sorted(directory.glob("*.json")):
        record = json.loads(path.read_text())
        suffix = ".current-session-note.json"
        if path.name.endswith(suffix):
            expected = path.name[:-len(suffix)]
            if (isinstance(record, dict) and record.get("goal_task_id") == expected
                    and "task_id" not in record):
                notes.append(path.name)
                continue
        shards[path.stem] = record
    return shards, notes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--strict-drift", action="store_true",
                        help="Fail when overlapping shard / aggregate or emitted COSV contradict.")
    args = parser.parse_args()
    root = args.root
    registry = json.loads((root / "data/canonical-task-registry.json").read_text())
    index = json.loads((root / "control/task-vector-index.json").read_text())
    directory = root / "data/canonical-task-records"
    shards, notes = load_shards(directory)
    report = evaluate(registry, shards, index)
    report["verified_non_task_session_notes"] = notes
    print(json.dumps(report, sort_keys=True, indent=2))
    if report["structural_errors"]:
        return 1
    if args.strict_drift and (report["shard_aggregate_drift"] or report["cosv_conflicts_where_both_emitted"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
