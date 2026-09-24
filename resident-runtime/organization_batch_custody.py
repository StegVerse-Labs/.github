#!/usr/bin/env python3
"""Bounded replay and batch closure over the EXISTING organization receipt ledger.

This module grants no transition/custody authority. It never mutates individual
organization receipts or the organization ledger HEAD. Master Records acceptance
must be obtained separately through the existing authorized custody path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import tempfile

import aggregate_repo_transition as org

SCHEMA = "stegverse.organization-receipt-batch/v1"
ACK = "PENDING_MASTER_RECORDS"
CLOSURE_REASONS = {
    "ROUTINE_THRESHOLD", "TASK_CLOSURE", "WORKER_EXPIRY",
    "CONSEQUENTIAL_GOVERNANCE_BOUNDARY", "CUSTODY_RECOVERY",
    "INTER_ORGANIZATION_HANDOFF",
}


def _read(path: Path) -> dict:
    row = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(row, dict):
        raise ValueError("organization batch JSON object required")
    return row


def _verified_receipt(root: Path, digest: str) -> dict:
    if not isinstance(digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
        raise ValueError("organization receipt digest invalid")
    path = root / "receipts" / (digest[7:] + ".json")
    if not path.is_file():
        raise ValueError("organization receipt missing: " + digest)
    row = _read(path)
    body = dict(row)
    claimed = body.pop("receipt_sha256", None)
    if claimed != digest or org.sha(body) != digest:
        raise ValueError("organization receipt hash mismatch: " + digest)
    if row.get("schema") != "stegverse.organization-transition-receipt/v1":
        raise ValueError("organization receipt schema mismatch")
    if row.get("organization") != org.C["organization"]:
        raise ValueError("organization receipt owner mismatch")
    if row.get("source_receipt_schema") not in org.C["consumes"]:
        raise ValueError("organization source schema mismatch")
    if row.get("source_receipt_schema") == "stegverse.canonical-state-transition-receipt/v1":
        if row.get("canonical_state_transition_receipt_sha256") != row.get("source_transition_sha256"):
            raise ValueError("canonical source digest binding mismatch")
    else:
        if row.get("repo_receipt_sha256") != row.get("source_transition_sha256"):
            raise ValueError("repository source digest binding mismatch")
    return row


def _ordered_commitment(hashes: list[str]) -> str:
    return "sha256:" + hashlib.sha256(
        b"STEGVERSE_ORGANIZATION_BATCH_ORDERED_V1\n" + org.canon(hashes)
    ).hexdigest()


def _boundary_commitment(rows: list[dict]) -> str:
    """Bind organization-level evidence pointers, NOT unseen source evidence bytes."""
    return org.sha([
        {
            "organization_receipt_sha256": row["receipt_sha256"],
            "source_transition_sha256": row["source_transition_sha256"],
            "boundary_evidence": row["boundary_evidence"],
        }
        for row in rows
    ])


def _verified_batch(root: Path, digest: str) -> dict:
    if not isinstance(digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
        raise ValueError("organization batch digest invalid")
    path = root / "batches" / (digest[7:] + ".json")
    if not path.is_file():
        raise ValueError("organization batch missing: " + digest)
    batch = _read(path)
    body = dict(batch)
    if body.pop("batch_id", None) != digest or org.sha(body) != digest:
        raise ValueError("organization batch hash mismatch")
    if batch.get("schema") != SCHEMA or batch.get("organization_id") != org.C["organization"]:
        raise ValueError("organization batch identity mismatch")
    return batch


def _batch_head(root: Path) -> tuple[str | None, dict | None]:
    path = root / "BATCH_HEAD.json"
    if not path.exists():
        if (root / "batches").is_dir() and any((root / "batches").glob("*.json")):
            raise ValueError("unindexed organization batch exists; recover custody before appending")
        return None, None
    head = _read(path)
    digest = head.get("batch_id")
    batch = _verified_batch(root, digest)
    if head.get("organization") != org.C["organization"] or head.get("last_org_receipt_sha256") != batch["last_org_receipt_sha256"]:
        raise ValueError("organization batch HEAD mismatch")
    return digest, batch


def _segment(root: Path, tip: str, predecessor: str | None) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    cursor: str | None = tip
    while cursor != predecessor:
        if cursor is None:
            raise ValueError("organization predecessor batch does not connect to current HEAD")
        if cursor in seen:
            raise ValueError("organization ledger cycle")
        seen.add(cursor)
        row = _verified_receipt(root, cursor)
        rows.append(row)
        cursor = row.get("previous_receipt_sha256")
    if not rows:
        raise ValueError("no new organization receipts to batch")
    rows.reverse()
    # A path that walks from HEAD but silently excludes an immutable receipt
    # is not a complete organization ledger replay. Include already-batched
    # ancestors in the inventory, then reject orphaned or omitted files.
    reachable = {row["receipt_sha256"][7:] for row in rows}
    ancestor = predecessor
    while ancestor is not None:
        if ancestor[7:] in reachable:
            raise ValueError("organization ledger ancestor cycle")
        reachable.add(ancestor[7:])
        ancestor = _verified_receipt(root, ancestor).get("previous_receipt_sha256")
    inventory = {path.stem for path in (root / "receipts").glob("*.json")}
    if inventory != reachable:
        raise ValueError("organization ledger orphaned or omitted receipt detected")
    for i, row in enumerate(rows):
        expected = predecessor if i == 0 else rows[i - 1]["receipt_sha256"]
        if row.get("previous_receipt_sha256") != expected:
            raise ValueError("organization receipt predecessor mismatch")
    return rows


def verify_batch(root: Path, batch_id: str, *, source_receipts: dict[str, dict] | None = None) -> dict:
    """Verify immutable batch and local org chain; source proof is separate."""
    batch = _verified_batch(root, batch_id)
    predecessor_id = batch.get("previous_batch_commitment")
    prior = _verified_batch(root, predecessor_id) if predecessor_id else None
    previous_org = prior["last_org_receipt_sha256"] if prior else None
    hashes = batch.get("ordered_receipt_hashes")
    if not isinstance(hashes, list) or not hashes or len(set(hashes)) != len(hashes):
        raise ValueError("organization batch receipt set invalid")
    floor = prior["contiguous_receipt_range"][1] + 1 if prior else 1
    if batch.get("contiguous_receipt_range") != [floor, floor + len(hashes) - 1]:
        raise ValueError("organization batch sequence range invalid")
    rows = [_verified_receipt(root, digest) for digest in hashes]
    for i, row in enumerate(rows):
        expected = previous_org if i == 0 else hashes[i - 1]
        if row.get("previous_receipt_sha256") != expected:
            raise ValueError("organization batch receipt predecessor invalid")
    if batch.get("first_org_receipt_sha256") != hashes[0] or batch.get("last_org_receipt_sha256") != hashes[-1]:
        raise ValueError("organization batch boundary mismatch")
    if batch.get("ordered_receipt_commitment") != _ordered_commitment(hashes):
        raise ValueError("organization batch ordered commitment mismatch")
    if batch.get("required_evidence_commitment") != _boundary_commitment(rows):
        raise ValueError("organization batch evidence reference commitment mismatch")
    if batch.get("acknowledgement_state") != ACK:
        raise ValueError("batch declaration cannot self-assert Master Records acceptance")
    actual_cross = sorted(set(
        str(row["source_transition_sha256"]) for row in rows
        if row.get("source_transition_sha256")
    ))
    if batch.get("cross_boundary_predecessor_refs") != [
        row.get("previous_receipt_sha256") for row in rows[:1] if row.get("previous_receipt_sha256")
    ]:
        raise ValueError("organization batch external predecessor invalid")
    if batch.get("source_transition_commitments") != actual_cross:
        raise ValueError("organization batch source commitments invalid")
    source_state = "NOT_SUPPLIED"
    if source_receipts is not None:
        for row in rows:
            source = source_receipts.get(row["source_transition_sha256"])
            if not isinstance(source, dict) or org.verify_source(source)["source_transition_sha256"] != row["source_transition_sha256"]:
                raise ValueError("source transition receipt missing or invalid")
            if source.get("transition_id") != row.get("source_transition_id"):
                raise ValueError("source transition identity mismatch")
        source_state = "SOURCE_DIGESTS_PASS_REQUIRED_EVIDENCE_BYTES_NOT_EVALUATED"
    return {
        "state": "PASS", "schema": "stegverse.organization-batch-local-verification/v1",
        "batch_id": batch_id, "receipt_count": len(rows),
        "first_org_receipt_sha256": hashes[0],
        "last_org_receipt_sha256": hashes[-1],
        "organization_chain": "PASS",
        "source_reconstruction": source_state,
        "master_records_acknowledgement": "NOT_ESTABLISHED",
        "authority_effect": "NONE_VERIFICATION_ONLY",
    }


def _atomic_json(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".org-batch-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(row, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def close_batch(reason: str, *, root: Path | None = None) -> dict:
    if reason not in CLOSURE_REASONS:
        raise ValueError("unsupported organization batch closure reason")
    root = Path(root) if root else org.ledger_root()
    head = _read(root / "HEAD.json")
    if head.get("organization") != org.C["organization"]:
        raise ValueError("organization ledger HEAD identity mismatch")
    tip = head.get("receipt_sha256")
    _verified_receipt(root, tip)
    if Path(str(head.get("receipt_path") or "")).resolve() != (root / "receipts" / (tip[7:] + ".json")).resolve():
        raise ValueError("organization ledger HEAD receipt path mismatch")
    prior_id, prior = _batch_head(root)
    if prior is not None and prior.get("last_org_receipt_sha256") == tip:
        if prior["closure_reason"] != reason:
            raise ValueError("no new organization receipts; conflicting batch closure")
        return prior  # Idempotent retry, not a second batch.
    rows = _segment(root, tip, prior["last_org_receipt_sha256"] if prior else None)
    hashes = [row["receipt_sha256"] for row in rows]
    body = {
        "schema": SCHEMA,
        "organization_id": org.C["organization"],
        "contiguous_receipt_range": [prior["contiguous_receipt_range"][1] + 1 if prior else 1,
                                      (prior["contiguous_receipt_range"][1] if prior else 0) + len(hashes)],
        "previous_batch_commitment": prior_id,
        "first_org_receipt_sha256": hashes[0],
        "last_org_receipt_sha256": hashes[-1],
        "ordered_receipt_hashes": hashes,
        "ordered_receipt_commitment": _ordered_commitment(hashes),
        "source_transition_commitments": sorted(set(row["source_transition_sha256"] for row in rows)),
        "cross_boundary_predecessor_refs": [
            row["previous_receipt_sha256"] for row in rows[:1] if row.get("previous_receipt_sha256")
        ],
        "required_evidence_commitment": _boundary_commitment(rows),
        "required_evidence_scope": "ORGANIZATION_BOUNDARY_REFERENCES_ONLY",
        "closure_reason": reason,
        "acknowledgement_state": ACK,
        "authority_effect": "NONE_BATCH_CUSTODY_PROPOSAL_ONLY",
    }
    digest = org.sha(body)
    batch = dict(body, batch_id=digest)
    destination = root / "batches" / (digest[7:] + ".json")
    if destination.exists() and _read(destination) != batch:
        raise ValueError("organization batch identity collision")
    if not destination.exists():
        _atomic_json(destination, batch)
    verify_batch(root, digest)
    if _read(root / "HEAD.json") != head:
        raise ValueError("organization ledger advanced during batch closure; retry under existing ledger lock")
    _atomic_json(root / "BATCH_HEAD.json", {
        "organization": org.C["organization"],
        "batch_id": digest,
        "last_org_receipt_sha256": tip,
    })
    return batch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--closure-reason", choices=sorted(CLOSURE_REASONS))
    parser.add_argument("--verify-batch")
    parser.add_argument("--root")
    args = parser.parse_args()
    root = Path(args.root) if args.root else org.ledger_root()
    if bool(args.closure_reason) == bool(args.verify_batch):
        parser.error("provide exactly one of --closure-reason or --verify-batch")
    result = close_batch(args.closure_reason, root=root) if args.closure_reason else verify_batch(root, args.verify_batch)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
