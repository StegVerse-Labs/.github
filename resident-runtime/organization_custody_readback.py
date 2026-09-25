#!/usr/bin/env python3
"""Read-only, complete organization HEAD/source replay on the existing resident.

No external transport, session authentication, Master Records acknowledgement,
InTr decision, new ledger or task-state transition is performed here. The
existing authorized resident caller owns session origin and return transport.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import aggregate_repo_transition as org
import organization_batch_custody as batch

SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")


def _source_for(root: Path, row: dict[str, Any]) -> dict[str, Any]:
    digest = row["source_transition_sha256"]
    if not isinstance(digest, str) or not SHA.fullmatch(digest):
        raise ValueError("SOURCE_DIGEST_INVALID")
    path = root / "source-receipts" / (digest[7:] + ".json")
    if not path.is_file():
        raise ValueError("SOURCE_RECEIPT_MISSING:" + digest)
    source = batch._read(path)
    checked = org.verify_source(source)  # also verifies inline required evidence
    if (
        checked["source_transition_sha256"] != digest
        or checked["source_transition_id"] != row["source_transition_id"]
        or checked["source_receipt_schema"] != row["source_receipt_schema"]
    ):
        raise ValueError("SOURCE_RECEIPT_BINDING_MISMATCH:" + digest)
    return source


def _verified_batches(root: Path, receipt_hashes: list[str]) -> list[dict[str, Any]]:
    if not (root / "BATCH_HEAD.json").is_file():
        if (root / "batches").is_dir() and any((root / "batches").glob("*.json")):
            raise ValueError("BATCH_HEAD_MISSING_WITH_BATCHES")
        return []
    head_digest, _ = batch._batch_head(root)
    cursor = head_digest
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    while cursor is not None:
        if cursor in seen:
            raise ValueError("ORGANIZATION_BATCH_CYCLE")
        seen.add(cursor)
        item = batch._verified_batch(root, cursor)
        verified = batch.verify_batch(root, cursor)
        if verified["organization_chain"] != "PASS":
            raise ValueError("ORGANIZATION_BATCH_VERIFICATION_FAILED")
        rows.append(item)
        cursor = item.get("previous_batch_commitment")
    rows.reverse()
    # A batch closure is a contiguous prefix of the current full HEAD graph.
    flat = [digest for item in rows for digest in item["ordered_receipt_hashes"]]
    if flat != receipt_hashes[:len(flat)]:
        raise ValueError("ORGANIZATION_BATCH_PREFIX_MISMATCH")
    inventory = {p.stem for p in (root / "batches").glob("*.json")}
    if inventory != {digest[7:] for digest in seen}:
        raise ValueError("ORGANIZATION_BATCH_ORPHAN_DETECTED")
    return rows


def readback(
    root: Path,
    *,
    correlation_ids: tuple[str, ...],
    include_exact: bool = True,
) -> dict[str, Any]:
    """Verify the entire resident HEAD chain, even when matches are historical.

    Exact bytes are returned only to the resident-local caller. That caller must
    keep them inside the existing private runtime and authorized return path.
    """
    root = Path(root).expanduser().resolve()
    head_path = root / "HEAD.json"
    if not head_path.is_file():
        if (root / "receipts").is_dir() and any((root / "receipts").glob("*.json")):
            raise ValueError("ORGANIZATION_HEAD_MISSING_WITH_RECEIPTS")
        raise ValueError("ORGANIZATION_HEAD_NOT_MATERIALIZED")
    head = batch._read(head_path)
    tip = head.get("receipt_sha256")
    if head.get("organization") != org.C["organization"] or not isinstance(tip, str) or not SHA.fullmatch(tip):
        raise ValueError("ORGANIZATION_HEAD_IDENTITY_INVALID")
    ordered = batch._segment(root, tip, None)
    if not ordered or ordered[-1]["receipt_sha256"] != tip:
        raise ValueError("ORGANIZATION_HEAD_PREDECESSOR_INVALID")
    all_hashes = [row["receipt_sha256"] for row in ordered]
    sources = [_source_for(root, row) for row in ordered]
    batches = _verified_batches(root, all_hashes)
    # Do not call the candidate stable if another resident append raced readback.
    if batch._read(head_path) != head:
        raise ValueError("ORGANIZATION_HEAD_CHANGED_DURING_READBACK")
    ids = set(correlation_ids)
    matches = []
    for row, source in zip(ordered, sources):
        bound = {
            row.get("subject_or_correlation_id"),
            row.get("source_transition_id"),
            source.get("subject_or_correlation_id"),
            source.get("transition_id"),
        }
        evidence = row.get("boundary_evidence")
        if isinstance(evidence, dict):
            bound.update((evidence.get("task_id"), evidence.get("correlation_id")))
        if bound.isdisjoint(ids):
            continue
        matches.append({
            "organization_receipt_sha256": row["receipt_sha256"],
            "immediate_predecessor_sha256": row.get("previous_receipt_sha256"),
            "source_transition_sha256": row["source_transition_sha256"],
            "source_transition_id": row["source_transition_id"],
            "source_transition_outcome": source.get("transition_outcome"),
            "organization_transition_class": row.get("org_transition_class"),
            "subject_or_correlation_id": source.get("subject_or_correlation_id"),
            "boundary_evidence": row.get("boundary_evidence"),
        })
    result: dict[str, Any] = {
        "schema": "stegverse.organization-custody-readback/v1",
        "state": "VERIFIED_LOCAL_READBACK",
        "organization": head["organization"],
        "head_receipt_sha256": tip,
        "head_snapshot": head,
        "complete_organization_chain": "PASS",
        "all_source_digests_and_required_evidence": "PASS",
        "receipt_count": len(ordered),
        "batch_count": len(batches),
        "batch_chain": "PASS" if batches else "NO_CLOSED_BATCH",
        "last_batch_id": batches[-1]["batch_id"] if batches else None,
        "match_count": len(matches),
        "matching_transitions": matches,
        "requested_correlation_ids": sorted(ids),
        "master_records_acknowledgement": "NOT_QUERIED",
        "master_records_reconstruction": "NOT_QUERIED",
        "runtime_admission_inferred": False,
        "authority_effect": "NONE_READBACK_ONLY",
    }
    if include_exact:
        result["exact_organization_receipts"] = ordered
        result["exact_source_receipts"] = sources
        result["exact_batches"] = batches
    return result
