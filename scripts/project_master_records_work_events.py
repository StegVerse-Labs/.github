#!/usr/bin/env python3
"""Normalize explicit Master Records records into canonical work-event projection rows.

This adapter is deliberately source-side and non-authorizing. It never infers
execution from GitHub/source state and it does not fetch Master Records. Callers
supply one or more JSON records exported/materialized from the Master Records
authority surface.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "stegverse.master-records-work-event-projection/v1"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise SystemExit("FAIL_CLOSED: " + reason)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        rows = value
    elif isinstance(value, dict) and isinstance(value.get("events"), list):
        rows = value["events"]
    elif isinstance(value, dict) and isinstance(value.get("records"), list):
        rows = value["records"]
    elif isinstance(value, dict):
        rows = [value]
    else:
        raise SystemExit("FAIL_CLOSED: Master Records input must be object/list")
    require(all(isinstance(row, dict) for row in rows), "every Master Records row must be an object")
    return rows


def normalize(row: dict[str, Any], source_ref: str) -> dict[str, Any] | None:
    task_id = row.get("task_id") or row.get("goal_id") or row.get("machine_task")
    correlation_id = row.get("correlation_id") or row.get("root_correlation_id") or task_id
    if not isinstance(task_id, str) and not isinstance(correlation_id, str):
        return None

    predicates = row.get("predicates") if isinstance(row.get("predicates"), dict) else {}
    explicit_refs = [row.get("ref"), row.get("record_ref"), row.get("receipt_hash"), row.get("record_hash")]
    refs = sorted({value for value in explicit_refs if isinstance(value, str) and value})
    if not refs:
        refs = [source_ref]

    event = {
        "task_id": task_id if isinstance(task_id, str) else None,
        "correlation_id": correlation_id if isinstance(correlation_id, str) else None,
        "ref": refs[0],
        "source_refs": refs,
        "predicates": predicates,
        "observed_state": row.get("state") or row.get("transition") or row.get("transition_id"),
        "event_type": row.get("event_type") or row.get("schema") or "MASTER_RECORDS_EVENT",
        "master_records_source_only": True,
        "historical_event_mints_task_authority": False,
        "historical_event_mints_execution_authority": False,
    }
    event["projection_row_hash"] = sha_uri(event)
    return event


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--output")
    args = parser.parse_args()

    events: list[dict[str, Any]] = []
    skipped = 0
    for raw_path in args.inputs:
        path = Path(raw_path)
        for row in candidate_rows(load(path)):
            normalized = normalize(row, str(path))
            if normalized is None:
                skipped += 1
            else:
                events.append(normalized)

    events.sort(key=lambda e: (str(e.get("correlation_id") or ""), str(e.get("task_id") or ""), str(e.get("ref") or "")))
    body = {
        "schema": SCHEMA,
        "events": events,
        "counts": {"projected": len(events), "skipped_unbound": skipped},
        "authority_model": {
            "master_records_is_observed_reality_authority": True,
            "projection_mints_execution_authority": False,
            "projection_mints_task_admission": False,
        },
        "nonclaim": "PROJECTION_DOES_NOT_PROVE_ANY_EVENT_NOT_PRESENT_IN_SUPPLIED_MASTER_RECORDS_INPUTS",
    }
    body["projection_hash"] = sha_uri(body)
    text = json.dumps(body, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
