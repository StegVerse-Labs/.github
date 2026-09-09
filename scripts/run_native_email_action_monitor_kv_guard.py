#!/usr/bin/env python3
"""Run the native email monitor with fail-closed KV persistence before live archive.

The underlying monitor remains canonical. This guard wraps only its broker so that
normalized GitHub failure incidents from the currently inspected live INBOX batch are
persisted with exact-byte readback before any ARCHIVE_IDS operation is allowed.
Archived replay is also persisted before returning its incident proposals.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_native_email_action_monitor as monitor
from persist_native_email_incidents_to_kv import persist_incidents


class KVGuardedBroker:
    def __init__(self, inner: monitor.Broker, kv_root: Path):
        self.inner = inner
        self.kv_root = kv_root.expanduser().resolve()
        self.live_incidents: list[dict[str, Any]] = []
        self.kv_receipts: list[dict[str, Any]] = []

    def call(self, operation: str, **payload: Any) -> dict[str, Any]:
        response = self.inner.call(operation, **payload)
        if operation == "SEARCH_MESSAGES" and payload.get("query") == monitor.INBOX_QUERY and payload.get("label_ids") == ["INBOX"]:
            rows = monitor.stable_rows(response, "messages")
            self.live_incidents = monitor.cluster_incidents(rows)
        elif operation == "ARCHIVE_IDS":
            # This executes before the provider archive call would otherwise happen.
            # Persist exactly the normalized incident set derived from the inspected
            # live batch. No incidents means there is nothing failure-specific to persist.
            if self.live_incidents:
                self.kv_receipts = persist_incidents(self.live_incidents, kv_root=self.kv_root)
            response = self.inner.call(operation, **payload)
        return response


def persist_replay_incidents(receipt: dict[str, Any], kv_root: Path) -> list[dict[str, Any]]:
    incidents = receipt.get("incidents")
    if not isinstance(incidents, list) or not incidents:
        return []
    return persist_incidents([row for row in incidents if isinstance(row, dict)], kv_root=kv_root)


def run_guarded(broker_command: list[str], *, kv_root: Path, batch_limit: int, replay_checkpoint_path: Path | None) -> dict[str, Any]:
    guarded = KVGuardedBroker(monitor.Broker(broker_command), kv_root)
    receipt = monitor.run(guarded, batch_limit, replay_checkpoint_path)
    replay_receipts: list[dict[str, Any]] = []
    if receipt.get("state") == "ARCHIVED_REPLAY_PENDING":
        replay_receipts = persist_replay_incidents(receipt, kv_root)
    all_receipts = [*replay_receipts, *guarded.kv_receipts]
    receipt["kv_persistence"] = {
        "required_for_failure_incidents": True,
        "state": "KV_STORED_VERIFIED" if all_receipts or int(receipt.get("incident_count") or 0) == 0 else "KV_PERSISTENCE_NOT_OBSERVED",
        "record_count": len(all_receipts),
        "write_receipts": all_receipts,
        "archive_after_kv_persistence": True,
        "exact_byte_readback_required": True,
        "kv_root_materialized": True,
        "authority_effect": "NONE_STORAGE_EVIDENCE_ONLY",
    }
    if int(receipt.get("incident_count") or 0) > 0:
        if len(all_receipts) != int(receipt.get("incident_count") or 0):
            raise RuntimeError("kv_incident_persistence_count_mismatch")
        if not all(row.get("exact_byte_readback_verified") is True for row in all_receipts):
            raise RuntimeError("kv_exact_byte_readback_not_verified")
    return receipt


def parse_broker_command(args: argparse.Namespace) -> list[str]:
    if args.broker_json:
        value = json.loads(args.broker_json)
        if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
            raise RuntimeError("broker JSON command invalid")
        return value
    if not args.broker:
        raise RuntimeError("broker command required")
    return list(args.broker)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--broker", nargs="+")
    group.add_argument("--broker-json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--batch-limit", type=int, default=monitor.BATCH_LIMIT)
    parser.add_argument("--kv-root", type=Path, required=True)
    args = parser.parse_args()

    replay_checkpoint_path = None
    if args.output and args.output.name == "native-email-action-monitor.latest.json":
        replay_checkpoint_path = args.output.with_name("native-email-archived-failure-replay.checkpoint.json")
    receipt = run_guarded(
        parse_broker_command(args),
        kv_root=args.kv_root,
        batch_limit=args.batch_limit,
        replay_checkpoint_path=replay_checkpoint_path,
    )
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if receipt["state"] in {"PASS", "ARCHIVED_REPLAY_PENDING", "ARCHIVED_REPLAY_COMPLETE"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
