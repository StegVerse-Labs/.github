#!/usr/bin/env python3
"""Read-only deterministic query surface for canonical worker status."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "control" / "worker-status.json"


def query(status: dict, *, task_id: str | None = None, goal_id: str | None = None, states: set[str] | None = None) -> dict:
    rows = []
    for task in status.get("tasks", []):
        if task_id and task.get("task_id") != task_id:
            continue
        if goal_id and task.get("goal_id") != goal_id:
            continue
        if states and task.get("state") not in states:
            continue
        rows.append({
            "task_id": task.get("task_id"),
            "goal_id": task.get("goal_id"),
            "state": task.get("state"),
            "archive_eligible": bool(task.get("archive_eligible")),
            "archive_reason_codes": task.get("archive_reason_codes", []),
            "worker_id": task.get("worker_id"),
            "claim_id": task.get("claim_id"),
            "fencing_token": task.get("fencing_token"),
            "last_checkpoint_ref": task.get("last_checkpoint_ref"),
            "next_authorized_action": task.get("next_authorized_action"),
            "evidence_refs": task.get("evidence_refs", []),
        })
    return {
        "schema": "stegverse.worker-status-query/v0.1",
        "source_schema": status.get("schema"),
        "source_registry_generation": status.get("source_registry_generation"),
        "heartbeat_epoch": status.get("heartbeat_epoch"),
        "observational_only": True,
        "execution_authority": False,
        "count": len(rows),
        "tasks": sorted(rows, key=lambda item: (str(item.get("goal_id")), str(item.get("task_id")))),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id")
    parser.add_argument("--goal-id")
    parser.add_argument("--state", action="append", dest="states")
    args = parser.parse_args()
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    print(json.dumps(query(status, task_id=args.task_id, goal_id=args.goal_id, states=set(args.states or [])), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
