#!/usr/bin/env python3
"""Derive conservative worker task-class cost basis from observed HB history.

Only completed task samples contribute to an expiry estimate. Sparse history
remains confidence NONE/LOW rather than inventing a precise timeout. This file
is accounting/estimation evidence; it grants no worker or execution authority.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / "control" / "worker-cost-observations.json"
DEFAULT_OUT = ROOT / "cost-basis" / "worker-runtime"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def quantile_nearest_rank(values: list[int], q: float) -> int:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("quantile requires values")
    rank = max(1, math.ceil(q * len(ordered)))
    return ordered[min(rank - 1, len(ordered) - 1)]


def confidence(samples: int) -> str:
    if samples == 0:
        return "NONE"
    if samples < 5:
        return "LOW"
    if samples < 20:
        return "MEDIUM"
    return "HIGH"


def task_class(record: dict[str, Any]) -> str | None:
    cost = record.get("cost") or {}
    value = cost.get("task_class")
    return str(value) if value else None


def is_complete(record: dict[str, Any]) -> bool:
    cost = record.get("cost") or {}
    transition = str(record.get("transition_id") or "").upper()
    return bool(cost.get("completed")) or transition in {"COMPLETE", "COMPLETED", "TASK_COMPLETED"}


def build(log: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_task: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in log.get("records", []):
        cls = task_class(record)
        task_id = record.get("task_id")
        if not cls or not task_id:
            continue
        by_task[(cls, str(task_id))].append(record)

    durations: dict[str, list[int]] = defaultdict(list)
    cost_values: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    evidence: dict[str, set[str]] = defaultdict(set)
    external_entity_classes: dict[str, set[str]] = defaultdict(set)

    for (cls, task_id), records in by_task.items():
        records.sort(key=lambda item: int(item.get("heartbeat_epoch", 0)))
        completed = [item for item in records if is_complete(item)]
        if not completed:
            continue
        start_epoch = int(records[0]["heartbeat_epoch"])
        completion_epoch = int(completed[-1]["heartbeat_epoch"])
        durations[cls].append(max(1, completion_epoch - start_epoch + 1))
        for item in records:
            cost = item.get("cost") or {}
            for field in (
                "compute_units", "token_units", "storage_bytes", "network_bytes",
                "operator_seconds", "external_cost_usd", "latency_ms", "recovery_actions"
            ):
                value = cost.get(field)
                if isinstance(value, (int, float)) and value >= 0:
                    cost_values[cls][field].append(float(value))
            for ref in cost.get("evidence_refs", []):
                evidence[cls].add(str(ref))
            entity_class = cost.get("external_entity_class")
            if entity_class:
                external_entity_classes[cls].add(str(entity_class))
        evidence[cls].add(f"worker-cost-log-task:{task_id}")

    result: dict[str, dict[str, Any]] = {}
    classes = sorted(set(durations) | {task_class(x) for x in log.get("records", []) if task_class(x)})
    for cls in classes:
        samples = durations.get(cls, [])
        conf = confidence(len(samples))
        if samples:
            median = statistics.median(samples)
            p90 = quantile_nearest_rank(samples, 0.90)
            # Conservative evidence-derived initial expiry: p90 + max(1, 25% p90).
            expiry = p90 + max(1, math.ceil(p90 * 0.25))
        else:
            median = p90 = expiry = None
        means: dict[str, float | None] = {}
        for field in (
            "compute_units", "token_units", "storage_bytes", "network_bytes",
            "operator_seconds", "external_cost_usd", "latency_ms", "recovery_actions"
        ):
            values = cost_values[cls].get(field, [])
            means[field] = statistics.fmean(values) if values else None
        result[cls] = {
            "schema": "stegverse.worker-runtime-cost-basis/v0.1",
            "task_class": cls,
            "external_entity_class": next(iter(external_entity_classes[cls])) if len(external_entity_classes[cls]) == 1 else None,
            "sample_count": len(samples),
            "hb_estimate": {
                "expected_completion_beats": float(median) if median is not None else None,
                "expected_idle_beats": None,
                "expiry_candidate_beats": float(expiry) if expiry is not None else None,
                "confidence": conf
            },
            "cost_estimate": {
                **means,
                "failure_probability": None,
                "expected_recovery_cost_usd": None
            },
            "selection_guidance": {
                "preferred_worker_classes": [],
                "observed_efficiency_notes": [
                    "Expiry is derived only from completed HB-relative task samples.",
                    "Estimator uses completed-sample median and p90; expiry candidate is p90 plus a 25%/one-beat floor reserve.",
                    "No worker selection claim is made until comparative worker-class evidence exists."
                ],
                "cost_never_overrides_admissibility": True
            },
            "evidence_refs": sorted(evidence[cls])
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default=str(DEFAULT_LOG))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    values = build(load(Path(args.log)))
    out = Path(args.out_dir)
    if not args.check:
        out.mkdir(parents=True, exist_ok=True)
        for cls, record in values.items():
            safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in cls).strip("-") or "unknown"
            (out / f"{safe}.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"task_classes": sorted(values), "records": values}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
