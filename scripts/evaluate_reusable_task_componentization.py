#!/usr/bin/env python3
"""Deterministically evaluate whether a process should be decomposed into reusable task components.

This evaluator is coordination-only. It grants no execution, transition, credential,
custody, publication, or user-verification authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

WEIGHTS = {
    "repeated_subflow": 4,
    "multiple_authority_crossings": 3,
    "multiple_round_trips": 2,
    "cross_repository_or_org_spread": 2,
    "task_specific_adapter_duplicates_generic_work": 5,
    "handoff_sequence_growth": 2,
    "failure_path_branching": 2,
    "independent_reusability": 4,
    "optional_subflow_present": 3,
    "independent_evidence_predicate": 3,
}


def classify(score: int) -> str:
    if score >= 13:
        return "STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION"
    if score >= 9:
        return "COMPONENTIZATION_REQUIRED_UNLESS_EXPLICIT_NON_REUSE_JUSTIFICATION_EXISTS"
    if score >= 5:
        return "SEARCH_EXISTING_REUSABLE_COMPONENTS_AND_RECORD_REUSE_ANALYSIS"
    return "KEEP_COMPOSED_AND_REEVALUATE_AT_NEXT_EVALUATION_POINT"


def evaluate(payload: dict) -> dict:
    signals = payload.get("signals", {})
    unknown = sorted(set(signals) - set(WEIGHTS))
    if unknown:
        raise ValueError(f"unknown signals: {', '.join(unknown)}")

    active = []
    score = 0
    for name, weight in WEIGHTS.items():
        value = signals.get(name, False)
        if not isinstance(value, bool):
            raise ValueError(f"signal {name} must be boolean")
        if value:
            active.append(name)
            score += weight

    return {
        "schema": "stegverse.reusable-task-componentization-evaluation/v1",
        "task_id": payload.get("task_id"),
        "cosv_task_vector": payload.get("cosv_task_vector"),
        "score": score,
        "active_signals": active,
        "decision": classify(score),
        "must_search_existing_components": score >= 5,
        "componentization_required": score >= 9,
        "must_stop_scope_growth": score >= 13,
        "authority_effect": "NONE_COORDINATION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text())
    result = evaluate(payload)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
