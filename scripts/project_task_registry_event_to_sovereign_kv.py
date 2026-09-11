#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

EVENT_SCHEMA = "stegverse.task-registry-checkin-event/v1"
REQUEST_SCHEMA = "stegverse.task-registry-sovereign-kv-projection-request/v1"
RECEIPT_SCHEMA = "stegverse.task-registry-sovereign-kv-projection-receipt/v1"
CUSTODY_CLASS = "STEGVERSE_SOVEREIGN_KV"


def load_event(path: Path) -> dict:
    event = json.loads(path.read_text(encoding="utf-8"))
    if event.get("schema") != EVENT_SCHEMA:
        raise SystemExit("task registry event schema mismatch")
    if event.get("authority_effect") != "NONE":
        raise SystemExit("task registry event authority widening")
    event_hash = event.get("event_sha256")
    if not isinstance(event_hash, str) or not event_hash.startswith("sha256:"):
        raise SystemExit("task registry event hash missing")
    return event


def build_request(event: dict) -> dict:
    return {
        "schema": REQUEST_SCHEMA,
        "task_id": event.get("task_id"),
        "session_id": event.get("session_id"),
        "event_sha256": event["event_sha256"],
        "predecessor_event_sha256": event.get("predecessor_event_sha256"),
        "custody_class": CUSTODY_CLASS,
        "exact_event": event,
        "authority_effect": "NONE",
    }


def validate_receipt(receipt: dict, request: dict) -> dict:
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise SystemExit("sovereign KV projection receipt schema mismatch")
    if receipt.get("authority_effect") != "NONE":
        raise SystemExit("sovereign KV projection receipt authority widening")
    if receipt.get("custody_class") != CUSTODY_CLASS:
        raise SystemExit("sovereign KV custody class mismatch")
    if receipt.get("event_sha256") != request["event_sha256"]:
        raise SystemExit("sovereign KV receipt event hash mismatch")
    if receipt.get("stored_event_sha256") != request["event_sha256"]:
        raise SystemExit("sovereign KV stored event hash mismatch")
    for field in ("provider_adapter_ref", "interlock_intr_receipt_ref", "kv_instance_ref"):
        if not isinstance(receipt.get(field), str) or not receipt[field].strip():
            raise SystemExit(f"sovereign KV receipt missing {field}")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-file", required=True)
    parser.add_argument("--request-only", action="store_true")
    parser.add_argument("--adapter-command")
    args = parser.parse_args()

    event = load_event(Path(args.event_file).expanduser().resolve())
    request = build_request(event)
    if args.request_only:
        print(json.dumps(request, sort_keys=True))
        return 0

    command = args.adapter_command or os.environ.get("STEGVERSE_TASK_REGISTRY_KV_ADAPTER_COMMAND")
    if not command:
        raise SystemExit("sovereign KV adapter command not configured")
    proc = subprocess.run(
        shlex.split(command),
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=True,
    )
    receipt = validate_receipt(json.loads(proc.stdout), request)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
