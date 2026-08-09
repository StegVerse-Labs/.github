#!/usr/bin/env python3
"""Manage heartbeat subsignal leases without making heartbeat cadence lease authority."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "control" / "heartbeat-subsignals.json"
TERMINAL_ACTIONS = {"NONE", "OPEN", "EXTEND", "CLOSE"}
STATES = {"IDLE", "OPEN_REQUESTED", "OPEN", "EXTENDING", "HANDOFF_READY", "CLOSE_REQUESTED", "CLOSED"}


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "stegverse.heartbeat-subsignals/v1":
        raise SystemExit("unsupported heartbeat subsignal schema")
    if "steggate_transport_lease" not in data.get("subsignals", {}):
        raise SystemExit("steggate_transport_lease subsignal missing")
    return data


def validate(lease: dict) -> None:
    if lease.get("lease_action") not in TERMINAL_ACTIONS:
        raise SystemExit("invalid lease_action")
    if lease.get("state") not in STATES:
        raise SystemExit("invalid lease state")
    deps = lease.get("dependent_tasks", [])
    if len(deps) != len(set(deps)):
        raise SystemExit("duplicate dependent task")
    if lease.get("release_policy", {}).get("wall_clock_expiry_authority") is not False:
        raise SystemExit("wall clock cannot be lease expiry authority")
    if lease.get("authority_effect") is not False:
        raise SystemExit("heartbeat subsignal cannot grant authority")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["register", "unregister", "open", "extend", "close", "handoff"])
    parser.add_argument("--task-id")
    parser.add_argument("--lease-id")
    parser.add_argument("--successor-lease-id")
    parser.add_argument("--epoch", type=int)
    parser.add_argument("--path", default=str(DEFAULT_PATH))
    args = parser.parse_args()

    path = Path(args.path)
    data = load(path)
    lease = data["subsignals"]["steggate_transport_lease"]

    if args.action in {"register", "unregister"} and not args.task_id:
        raise SystemExit("--task-id is required")
    if args.action == "open" and (not args.lease_id or args.epoch is None):
        raise SystemExit("open requires --lease-id and --epoch")
    if args.action == "handoff" and not args.successor_lease_id:
        raise SystemExit("handoff requires --successor-lease-id")

    if args.action == "register":
        deps = set(lease.get("dependent_tasks", []))
        deps.add(args.task_id)
        lease["dependent_tasks"] = sorted(deps)
    elif args.action == "unregister":
        lease["dependent_tasks"] = [x for x in lease.get("dependent_tasks", []) if x != args.task_id]
    elif args.action == "open":
        if lease.get("state") not in {"IDLE", "CLOSED", "OPEN_REQUESTED"}:
            raise SystemExit(f"cannot open lease from {lease.get('state')}")
        lease["lease_id"] = args.lease_id
        lease["state"] = "OPEN_REQUESTED"
        lease["lease_action"] = "OPEN"
        lease["opened_epoch"] = args.epoch
        lease["successor_lease_id"] = None
    elif args.action == "extend":
        if lease.get("state") not in {"OPEN", "EXTENDING", "OPEN_REQUESTED"}:
            raise SystemExit(f"cannot extend lease from {lease.get('state')}")
        lease["state"] = "OPEN" if lease.get("state") == "OPEN" else "EXTENDING"
        lease["lease_action"] = "EXTEND"
    elif args.action == "close":
        if lease.get("state") in {"IDLE", "CLOSED"}:
            raise SystemExit("lease is not open")
        lease["state"] = "CLOSE_REQUESTED"
        lease["lease_action"] = "CLOSE"
    elif args.action == "handoff":
        if lease.get("state") not in {"OPEN", "EXTENDING"}:
            raise SystemExit(f"cannot hand off lease from {lease.get('state')}")
        if args.successor_lease_id == lease.get("lease_id"):
            raise SystemExit("successor lease id must differ from current lease id")
        lease["successor_lease_id"] = args.successor_lease_id
        lease["state"] = "HANDOFF_READY"
        lease["lease_action"] = "EXTEND"

    validate(lease)
    data["generation"] = int(data.get("generation", 0)) + 1
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "generation": data["generation"],
        "lease_id": lease["lease_id"],
        "state": lease["state"],
        "lease_action": lease["lease_action"],
        "dependent_tasks": lease.get("dependent_tasks", []),
        "successor_lease_id": lease.get("successor_lease_id")
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
