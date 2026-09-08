#!/usr/bin/env python3
"""Move only fully reviewed GitHub failure/error notification IDs to Gmail Trash.

This is a cleanup gate, not a reviewer or remediation authority. It requires durable
review dispositions plus the existing StegHealth reconciliation result before calling
the bounded TV/TVC broker TRASH_IDS operation. Gmail Trash is not permanent deletion.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

REVIEW_SCHEMA = "stegverse.github-failure-error-review/v1"
RECONCILE_SCHEMA = "stegverse.email-failure-canonical-work-handoff/v1"
BROKER_REQUEST_SCHEMA = "stegverse.native-email-broker-request/v1"
BROKER_RESPONSE_SCHEMA = "stegverse.native-email-broker-response/v1"
RECEIPT_SCHEMA = "stegverse.github-failure-error-cleanup-receipt/v1"
CLEANUP_STATES = {"RESOLVED", "REMEDIATION_ACTION_APPLIED", "DUPLICATE_MAPPED_TO_RESOLVED_INCIDENT"}
BATCH_LIMIT = 100


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object:{path}")
    return value


def write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def cleanup_ids(review: Mapping[str, Any], reconciliation: Mapping[str, Any]) -> list[str]:
    require(review.get("schema") == REVIEW_SCHEMA, "review schema invalid")
    require(reconciliation.get("schema") == RECONCILE_SCHEMA, "reconciliation schema invalid")
    require(reconciliation.get("state") == "STEGHEALTH_TASK_CREATION_COMPLETE", "StegHealth reconciliation incomplete")
    require(reconciliation.get("retry_required") is False, "reconciliation retry pending")

    entries = review.get("incidents")
    require(isinstance(entries, list), "review incidents missing")
    ids: list[str] = []
    for row in entries:
        require(isinstance(row, dict), "review incident must be object")
        require(row.get("notification_class") in {"FAILURE", "ERROR"}, "notification class invalid")
        require(row.get("review_state") == "REVIEWED", "incident not reviewed")
        require(row.get("resolution_state") in CLEANUP_STATES, "incident remediation not cleanup eligible")
        require(isinstance(row.get("mapped_incident_id"), str) and row["mapped_incident_id"], "mapped incident missing")
        require(isinstance(row.get("remediation_evidence_refs"), list) and row["remediation_evidence_refs"], "remediation evidence missing")
        refs = row.get("gmail_message_ids")
        require(isinstance(refs, list) and refs and all(isinstance(v, str) and v for v in refs), "gmail message ids invalid")
        ids.extend(refs)
    require(len(ids) == len(set(ids)), "duplicate Gmail message ID across review incidents")
    return ids


def broker_call(command: Sequence[str], message_ids: list[str]) -> dict[str, Any]:
    request = {
        "schema": BROKER_REQUEST_SCHEMA,
        "operation": "TRASH_IDS",
        "credential_authority": "TV/TVC",
        "credential_material_requested": False,
        "message_ids": message_ids,
    }
    completed = subprocess.run(list(command), input=json.dumps(request), text=True, capture_output=True, check=False, timeout=120)
    require(completed.returncode == 0, "broker TRASH_IDS failed")
    result = json.loads(completed.stdout)
    require(isinstance(result, dict), "broker result invalid")
    require(result.get("schema") == BROKER_RESPONSE_SCHEMA, "broker response schema invalid")
    require(result.get("operation") == "TRASH_IDS", "broker operation mismatch")
    require(result.get("credential_authority") == "TV/TVC", "broker credential authority mismatch")
    require(result.get("credential_material_exported") is False, "broker exported credential material")
    require(result.get("provider_operation_authority_transferred") is False, "broker transferred provider authority")
    require(result.get("permanent_delete") is False, "cleanup may not claim permanent deletion")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--reconciliation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--broker-command", nargs="+", required=True)
    args = parser.parse_args()

    review = load(args.review)
    reconciliation = load(args.reconciliation)
    ids = cleanup_ids(review, reconciliation)
    trashed: list[str] = []
    failed: list[str] = []
    for start in range(0, len(ids), BATCH_LIMIT):
        batch = ids[start:start + BATCH_LIMIT]
        result = broker_call(args.broker_command, batch)
        batch_trashed = result.get("trashed_ids")
        batch_failed = result.get("failed_ids", [])
        require(isinstance(batch_trashed, list) and isinstance(batch_failed, list), "trash result invalid")
        require(set(batch_trashed).isdisjoint(batch_failed), "trash result overlap")
        require(set(batch_trashed) | set(batch_failed) == set(batch), "trash result does not cover exact batch")
        trashed.extend(batch_trashed)
        failed.extend(batch_failed)

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "state": "PASS" if not failed else "PARTIAL_TRASH_FAILURE",
        "review_ref": str(args.review),
        "reconciliation_ref": str(args.reconciliation),
        "reviewed_cleanup_candidate_count": len(ids),
        "trashed_count": len(trashed),
        "failed_count": len(failed),
        "trashed_ids": trashed,
        "failed_ids": failed,
        "permanent_delete": False,
        "credential_authority": "TV/TVC",
        "cleanup_mints_execution_authority": False,
        "durable_failure_error_lineage_retained": True,
        "authority_effect": "NONE_CLEANUP_RECEIPT_ONLY",
    }
    write(args.output, receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
