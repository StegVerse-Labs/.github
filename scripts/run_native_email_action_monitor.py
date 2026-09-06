#!/usr/bin/env python3
"""Run the bounded StegVerse email-action monitor through a local TV/TVC-governed broker.

The handler mirrors the established monitor semantics:
1. inspect the newest bounded INBOX batch;
2. resolve exact message IDs before mutation;
3. cluster GitHub/task-update failure signals as non-authorizing incident proposals;
4. archive the exact reviewed batch;
5. measure actionable backlog depth and inbox totals;
6. emit one durable monitor receipt.

The handler never receives provider credentials and never treats email, GitHub, CI,
archive success, or incident clustering as runtime/execution evidence.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from normalize_github_failure_email_events import incident_id, signature  # noqa: E402

INBOX_QUERY = "-in:spam -in:trash"
ACTIONABLE_QUERY = (
    '-in:spam -in:trash (subject:"[Task Update]" OR from:notifications@github.com) '
    '(failed OR failure OR "requires handoff" OR "requires reconciliation" OR '
    '"not evidence promotable" OR "needs attention" OR blocker OR blocked)'
)
BATCH_LIMIT = 100


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def stable_rows(value: Any, key: str) -> list[dict[str, Any]]:
    rows = value.get(key) if isinstance(value, dict) else None
    require(isinstance(rows, list), f"broker response missing {key}")
    require(all(isinstance(row, dict) for row in rows), f"broker {key} rows must be objects")
    return rows


class Broker:
    def __init__(self, command: Sequence[str]):
        require(bool(command), "broker command required")
        self.command = list(command)

    def call(self, operation: str, **payload: Any) -> dict[str, Any]:
        request = {
            "schema": "stegverse.native-email-broker-request/v1",
            "operation": operation,
            "credential_authority": "TV/TVC",
            "credential_material_requested": False,
            **payload,
        }
        completed = subprocess.run(
            self.command,
            input=json.dumps(request),
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        require(completed.returncode == 0, f"broker operation failed:{operation}")
        try:
            response = json.loads(completed.stdout)
        except Exception as exc:
            raise RuntimeError(f"broker returned invalid JSON:{operation}") from exc
        require(isinstance(response, dict), "broker response must be object")
        require(response.get("schema") == "stegverse.native-email-broker-response/v1", "broker response schema invalid")
        require(response.get("operation") == operation, "broker operation mismatch")
        require(response.get("credential_authority") == "TV/TVC", "broker credential authority mismatch")
        require(response.get("credential_material_exported") is False, "broker exported credential material")
        require(response.get("provider_operation_authority_transferred") is False, "broker transferred provider authority")
        return response


def message_id(row: Mapping[str, Any]) -> str:
    value = row.get("message_id") or row.get("id")
    require(isinstance(value, str) and value, "message id required")
    return value


def cluster_incidents(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in messages:
        subject = str(row.get("subject") or "")
        sender = str(row.get("from") or row.get("sender") or "")
        if "[Task Update]" not in subject and "github" not in sender.lower():
            continue
        sig = signature(row)
        groups.setdefault(sig, []).append(row)
    incidents: list[dict[str, Any]] = []
    for sig, rows in sorted(groups.items()):
        incidents.append({
            "incident_id": incident_id(sig),
            "kind": "GITHUB_FAILURE_EMAIL_CLUSTER",
            "normalized_repository": sig[0],
            "normalized_workflow": sig[1],
            "normalized_error_signature": sig[2],
            "observation_count": len(rows),
            "observation_refs": sorted({message_id(row) for row in rows}),
            "state": "INCIDENT_PROPOSED_NOT_ADMITTED",
            "task_ingress_required": True,
            "email_observation_is_execution_evidence": False,
            "incident_proposal_mints_execution_authority": False,
        })
    return incidents


def run(broker: Broker, batch_limit: int = BATCH_LIMIT) -> dict[str, Any]:
    require(1 <= batch_limit <= 100, "batch limit must be 1..100")

    inspected = broker.call(
        "SEARCH_MESSAGES",
        query=INBOX_QUERY,
        label_ids=["INBOX"],
        max_results=batch_limit,
    )
    messages = stable_rows(inspected, "messages")

    exact = broker.call(
        "SEARCH_IDS",
        query=INBOX_QUERY,
        label_ids=["INBOX"],
        max_results=batch_limit,
    )
    ids = exact.get("message_ids")
    require(isinstance(ids, list) and all(isinstance(v, str) and v for v in ids), "broker message_ids invalid")
    require(len(ids) <= batch_limit, "broker exceeded bounded batch")

    incidents = cluster_incidents(messages)

    archive = broker.call("ARCHIVE_IDS", message_ids=ids)
    archived = archive.get("archived_ids")
    failed = archive.get("failed_ids", [])
    require(isinstance(archived, list), "broker archived_ids invalid")
    require(isinstance(failed, list), "broker failed_ids invalid")
    require(set(archived).isdisjoint(set(failed)), "archive result overlap")
    require(set(archived) | set(failed) == set(ids), "archive result does not cover exact bounded batch")

    actionable = broker.call(
        "SEARCH_IDS",
        query=ACTIONABLE_QUERY,
        label_ids=["INBOX"],
        max_results=BATCH_LIMIT,
    )
    actionable_ids = actionable.get("message_ids")
    require(isinstance(actionable_ids, list), "actionable message_ids invalid")
    actionable_more = bool(actionable.get("next_page_token"))

    counts = broker.call("GET_LABEL_COUNTS", label_names=["INBOX"])
    labels = counts.get("labels")
    require(isinstance(labels, dict) and isinstance(labels.get("INBOX"), dict), "INBOX counts missing")
    inbox = labels["INBOX"]

    return {
        "schema": "stegverse.native-email-action-monitor-receipt/v1",
        "state": "PASS" if not failed else "PARTIAL_ARCHIVE_FAILURE",
        "provider": inspected.get("provider"),
        "bounded_batch_limit": batch_limit,
        "inspected_visible_count": len(messages),
        "processed_exact_count": len(ids),
        "archived_count": len(archived),
        "archive_failed_count": len(failed),
        "archive_failed_ids": failed,
        "incident_count": len(incidents),
        "incidents": incidents,
        "actionable_returned_count": len(actionable_ids),
        "actionable_more_than_returned": actionable_more,
        "actionable_minimum": len(actionable_ids) + (1 if actionable_more else 0),
        "inbox": inbox,
        "credential_authority": "TV/TVC",
        "credential_material_exported": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "email_observation_is_runtime_evidence": False,
        "archive_success_is_runtime_evidence": False,
        "incident_proposals_require_canonical_task_ingress": True,
        "authority_effect": "NONE_MAILBOX_MAINTENANCE_AND_INCIDENT_PROPOSAL_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", nargs="+", required=True, help="Already-local TV/TVC-governed broker command")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--batch-limit", type=int, default=BATCH_LIMIT)
    args = parser.parse_args()
    receipt = run(Broker(args.broker), args.batch_limit)
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if receipt["state"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
