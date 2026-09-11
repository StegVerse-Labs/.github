#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from task_registry_checkin_event_history import DEFAULT_LEDGER, append_event  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--event-type", choices=["CHECK_OUT", "RETURNED", "STOPPED"], default="RETURNED")
    parser.add_argument("--repository")
    parser.add_argument("--branch")
    parser.add_argument("--pull-request", type=int)
    parser.add_argument("--source-head")
    parser.add_argument("--first-unresolved-predicate")
    parser.add_argument("--repositories", default="")
    parser.add_argument("--components", default="")
    parser.add_argument("--event-at")
    parser.add_argument("--ledger")
    args = parser.parse_args()

    disposition = json.load(sys.stdin)
    if disposition.get("schema") != "stegverse.task-registry-checkin-disposition/v1":
        raise SystemExit("registry disposition schema mismatch")
    if disposition.get("task_id") != args.task_id:
        raise SystemExit("registry disposition task mismatch")
    if disposition.get("authority_effect") != "NONE":
        raise SystemExit("registry disposition authority widening")

    configured = args.ledger or os.environ.get("STEGVERSE_TASK_REGISTRY_EVENT_LEDGER")
    ledger = Path(configured).expanduser().resolve() if configured else DEFAULT_LEDGER
    event = append_event(ledger, {
        "event_type": args.event_type,
        "task_id": args.task_id,
        "session_id": args.session_id,
        "event_at": args.event_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "context": {
            "repository": args.repository,
            "branch": args.branch,
            "pull_request": args.pull_request,
            "source_head": args.source_head,
            "first_unresolved_predicate": args.first_unresolved_predicate,
            "repositories": [x for x in args.repositories.split(",") if x],
            "components": [x for x in args.components.split(",") if x],
        },
        "registry_disposition": disposition,
    })
    print(json.dumps({
        "schema": "stegverse.task-registry-session-return-receipt/v1",
        "task_id": args.task_id,
        "session_id": args.session_id,
        "event_type": args.event_type,
        "event_sha256": event["event_sha256"],
        "predecessor_event_sha256": event["predecessor_event_sha256"],
        "authority_effect": "NONE",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
