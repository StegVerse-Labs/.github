#!/usr/bin/env python3
"""Deterministic source-side reconciliation for canonical task records.

Inputs are local JSON documents. This utility does not fetch Master Records or
claim runtime authority. It compares a task's declared evidence predicates with
an explicit Master Records/evidence projection supplied to it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

RECON_SCHEMA = "stegverse.task-master-records-reconciliation/v1"


def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def find_task(registry: dict[str, Any], task_id: str) -> dict[str, Any]:
    matches = [t for t in registry.get("tasks", []) if t.get("task_id") == task_id]
    if len(matches) != 1:
        raise SystemExit(f"FAIL_CLOSED: expected exactly one task {task_id}, found {len(matches)}")
    return matches[0]


def normalize_projection(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        rows = raw
    elif isinstance(raw, dict) and isinstance(raw.get("events"), list):
        rows = raw["events"]
    else:
        raise SystemExit("FAIL_CLOSED: Master Records projection must be a list or an object with events[]")
    for row in rows:
        if not isinstance(row, dict):
            raise SystemExit("FAIL_CLOSED: every projection event must be an object")
    return rows


def reconcile(task: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    task_id = task["task_id"]
    correlation_id = task["correlation_id"]
    correlated = [
        e for e in events
        if e.get("task_id") == task_id or e.get("correlation_id") == correlation_id
    ]

    expected = list(task.get("expected_evidence_predicates", []))
    predicate_results: list[dict[str, Any]] = []
    any_fail = False
    any_unknown = False

    for predicate in expected:
        refs: list[str] = []
        observed: list[str] = []
        for event in correlated:
            predicates = event.get("predicates", {})
            if isinstance(predicates, dict) and predicate in predicates:
                value = predicates[predicate]
                if isinstance(value, bool):
                    observed.append("PASS" if value else "FAIL")
                elif isinstance(value, str) and value in {"PASS", "FAIL", "UNKNOWN", "NOT_APPLICABLE"}:
                    observed.append(value)
                else:
                    observed.append("UNKNOWN")
                ref = event.get("ref") or event.get("record_ref") or event.get("receipt_hash")
                if isinstance(ref, str) and ref:
                    refs.append(ref)

        if "FAIL" in observed:
            result = "FAIL"
            any_fail = True
        elif "PASS" in observed:
            result = "PASS"
        elif observed and all(value == "NOT_APPLICABLE" for value in observed):
            result = "NOT_APPLICABLE"
        else:
            result = "UNKNOWN"
            any_unknown = True

        predicate_results.append({
            "predicate": predicate,
            "result": result,
            "evidence_refs": sorted(set(refs)),
        })

    completion_claimed = bool(task.get("completion", {}).get("claimed")) or task.get("coordination_state") in {"COMPLETION_CLAIMED", "CLOSED"}
    all_required_pass = bool(expected) and all(item["result"] in {"PASS", "NOT_APPLICABLE"} for item in predicate_results)

    if any_fail:
        state = "CONFLICT"
        closure = False
        followup = "REVOKE_COMPLETION" if completion_claimed else "REQUEST_RECONCILIATION"
    elif completion_claimed and all_required_pass:
        state = "CONSISTENT"
        closure = True
        followup = "REEVALUATE_DEPENDENTS"
    elif completion_claimed and (any_unknown or not expected):
        state = "TASK_AHEAD_OF_EVIDENCE"
        closure = False
        followup = "WAIT_FOR_EVIDENCE"
    elif correlated and task.get("coordination_state") in {"PROPOSED", "INGRESS_ADMITTED", "CLAIMABLE"}:
        state = "REALITY_AHEAD_OF_TASK"
        closure = False
        followup = "REQUEST_RECONCILIATION"
    elif not correlated:
        state = "UNKNOWN"
        closure = False
        followup = "WAIT_FOR_EVIDENCE"
    else:
        state = "CONSISTENT"
        closure = False
        followup = "NONE"

    body = {
        "schema": RECON_SCHEMA,
        "task_id": task_id,
        "correlation_id": correlation_id,
        "state": state,
        "task_claims": [task.get("coordination_state", "UNKNOWN")],
        "master_records_refs": sorted({
            ref for event in correlated
            for ref in [event.get("ref") or event.get("record_ref") or event.get("receipt_hash")]
            if isinstance(ref, str) and ref
        }),
        "predicate_results": predicate_results,
        "closure_admissible": closure,
        "proposed_followup": followup,
        "notes": [
            "Absence of projection evidence is not proof of non-occurrence.",
            "This reconciliation does not mint execution authority or runtime state."
        ],
        "authority_model": {
            "reconciliation_mints_execution_authority": False,
            "historical_event_mints_task_authority": False,
            "master_records_is_reality_authority": True
        }
    }
    body["reconciliation_id"] = canonical_hash(body)
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="data/canonical-task-registry.json")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--master-records-projection", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    registry = load(Path(args.registry))
    task = find_task(registry, args.task_id)
    events = normalize_projection(load(Path(args.master_records_projection)))
    result = reconcile(task, events)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
