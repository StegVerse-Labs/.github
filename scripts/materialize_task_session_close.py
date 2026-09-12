#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RETURN_RECORDER = ROOT / "scripts" / "record_task_registry_session_return.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--actor-kind", required=True)
    parser.add_argument("--repository")
    parser.add_argument("--branch")
    parser.add_argument("--pull-request", type=int)
    parser.add_argument("--source-head")
    parser.add_argument("--first-unresolved-predicate")
    parser.add_argument("--repositories", default="")
    parser.add_argument("--components", default="")
    parser.add_argument("--event-type", choices=["RETURNED", "CHECK_OUT"], default="RETURNED")
    parser.add_argument("--ledger")
    args = parser.parse_args()

    disposition = json.load(sys.stdin)
    if disposition.get("schema") != "stegverse.task-registry-checkin-disposition/v1":
        raise SystemExit("registry disposition schema mismatch")
    if disposition.get("task_id") != args.task_id:
        raise SystemExit("registry disposition task mismatch")
    if disposition.get("authority_effect") != "NONE":
        raise SystemExit("registry disposition authority widening")

    cmd = [
        sys.executable,
        str(RETURN_RECORDER),
        "--task-id", args.task_id,
        "--session-id", args.session_id,
        "--actor-kind", args.actor_kind,
        "--event-type", args.event_type,
    ]
    optional = {
        "--repository": args.repository,
        "--branch": args.branch,
        "--pull-request": str(args.pull_request) if args.pull_request is not None else None,
        "--source-head": args.source_head,
        "--first-unresolved-predicate": args.first_unresolved_predicate,
        "--repositories": args.repositories,
        "--components": args.components,
        "--ledger": args.ledger,
    }
    for flag, value in optional.items():
        if value not in (None, ""):
            cmd.extend([flag, value])

    proc = subprocess.run(
        cmd,
        input=json.dumps(disposition),
        text=True,
        capture_output=True,
        check=True,
    )
    return_receipt = json.loads(proc.stdout)
    return_event_sha256 = return_receipt.get("event_sha256")
    if not isinstance(return_event_sha256, str) or not return_event_sha256.startswith("sha256:"):
        raise SystemExit("session return receipt missing canonical event hash")
    if return_receipt.get("actor_kind") != str(args.actor_kind).strip().upper():
        raise SystemExit("session return receipt actor mismatch")

    print(json.dumps({
        "schema": "stegverse.task-session-close/v1",
        "task_id": args.task_id,
        "session_id": args.session_id,
        "actor_kind": return_receipt["actor_kind"],
        "return_receipt": return_receipt,
        "continuity_materialized": True,
        "footer_handoff_emission_admissible": True,
        "required_pre_footer_return_event_sha256": return_event_sha256,
        "runtime_identity_attestation_proven": False,
        "authority_effect": "NONE",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
