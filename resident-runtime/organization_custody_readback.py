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


def _source_for(store, row: dict[str, Any]) -> dict[str, Any]:
    digest = row["source_transition_sha256"]
    if not isinstance(digest, str) or not SHA.fullmatch(digest):
        raise ValueError("SOURCE_DIGEST_INVALID")
    source = batch._get(store, org.ledger_store.source_key(digest))
    if source is None:
        raise ValueError("SOURCE_RECEIPT_MISSING:" + digest)
    checked = org.verify_source(source)  # also verifies inline required evidence
    if (
        checked["source_transition_sha256"] != digest
        or checked["source_transition_id"] != row["source_transition_id"]
        or checked["source_receipt_schema"] != row["source_receipt_schema"]
    ):
        raise ValueError("SOURCE_RECEIPT_BINDING_MISMATCH:" + digest)
    return source


def _verified_batches(root, receipt_hashes: list[str]) -> list[dict[str, Any]]:
    root = batch._ledger(root)
    if not root.exists(batch.BATCH_HEAD_KEY):
        if root.list_prefix(batch.BATCH_PREFIX):
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
        verified = batch._verify_batch(root, cursor)
        if verified["organization_chain"] != "PASS":
            raise ValueError("ORGANIZATION_BATCH_VERIFICATION_FAILED")
        rows.append(item)
        cursor = item.get("previous_batch_commitment")
    rows.reverse()
    # A batch closure is a contiguous prefix of the current full HEAD graph.
    flat = [digest for item in rows for digest in item["ordered_receipt_hashes"]]
    if flat != receipt_hashes[:len(flat)]:
        raise ValueError("ORGANIZATION_BATCH_PREFIX_MISMATCH")
    inventory = {key[len(batch.BATCH_PREFIX):-len(".json")] for key in root.list_prefix(batch.BATCH_PREFIX)}
    if inventory != {digest[7:] for digest in seen}:
        raise ValueError("ORGANIZATION_BATCH_ORPHAN_DETECTED")
    return rows


# A released batch's post-commit Master Records carriage (#3012) is recorded
# beside the receipts under batch-submissions/, named by key from the sovereign
# receipt that released the batch. Readback surfaces that record as it stands
# on the same declared store: COMPLETED, FAILED or NOT_ATTEMPTED as the
# immutable receipt says; PENDING while the outbox (the ledger itself) still
# holds the release without its receipt; FAIL_CLOSED when the record named is
# not the record found. None of these is a predicate of anything: the batch is
# on the verified chain either way, and no state here is or mints an ALLOW.
SUBMISSION_PENDING = "PENDING"
SUBMISSION_FAIL_CLOSED = "FAIL_CLOSED"
SUBMISSION_RECEIPT_ABSENT = "SUBMISSION_RECEIPT_ABSENT"
SUBMISSION_RECEIPT_HASH_MISMATCH = "SUBMISSION_RECEIPT_HASH_MISMATCH"
SUBMISSION_RECEIPT_INVALID = "SUBMISSION_RECEIPT_INVALID"
SUBMISSION_RECEIPT_KEY_MISMATCH = "SUBMISSION_RECEIPT_KEY_MISMATCH"


def _release_carrier(ordered: list[dict[str, Any]], index: dict[str, int], item: dict[str, Any]) -> dict[str, Any] | None:
    """The receipt that released `item`: the first one appended after the batch's last member."""
    position = index.get(item["last_org_receipt_sha256"])
    if position is None or position + 1 >= len(ordered):
        return None
    return ordered[position + 1]


def _master_records_submission(store, carried: dict[str, Any] | None, batch_id: str) -> dict[str, Any] | None:
    """What the same store records of the batch's post-commit carriage, verified, or None.

    None is a batch whose release named no submission receipt key: one closed
    by the operator, or released before the post-commit step existed (its
    result, if any, is inline on the carrier). Otherwise the receipt at the
    named key is read through `store` -- the store the readback is already
    reading, never another root -- and its self-hash checked by
    organization_batch_custody.released_batch_submission.
    """
    if not isinstance(carried, dict):
        return None
    key = carried.get("submission_receipt_key")
    if not isinstance(key, str) or not key:
        return None
    report: dict[str, Any] = {
        "receipt_key": key,
        "self_hash_verified": False,
        "authority_effect": "NONE",
    }
    if key != batch.submission_key(batch_id):
        # The sovereign receipt named a key that is not this batch's own.
        return {**report, "state": SUBMISSION_FAIL_CLOSED, "failed_predicate": SUBMISSION_RECEIPT_KEY_MISMATCH}
    try:
        receipt = batch.released_batch_submission(store, batch_id)
    except ValueError as exc:
        predicate = SUBMISSION_RECEIPT_HASH_MISMATCH if "hash mismatch" in str(exc) else SUBMISSION_RECEIPT_INVALID
        return {**report, "state": SUBMISSION_FAIL_CLOSED, "failed_predicate": predicate}
    if receipt is None:
        return {**report, "state": SUBMISSION_PENDING, "pending_reason": SUBMISSION_RECEIPT_ABSENT}
    return {
        **report,
        "state": receipt["execution_result"],
        "self_hash_verified": True,
        "submission_receipt_sha256": receipt["receipt_sha256"],
        "reason": receipt.get("reason"),
        "released_by_receipt_sha256": receipt.get("released_by_receipt_sha256"),
        "recorded_at": receipt.get("observed_at"),
    }


def _batch_submissions(store, ordered: list[dict[str, Any]], batches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per verified batch, in chain order, with its carriage as recorded."""
    index = {row["receipt_sha256"]: position for position, row in enumerate(ordered)}
    rows: list[dict[str, Any]] = []
    for item in batches:
        batch_id = item["batch_id"]
        carrier = _release_carrier(ordered, index, item)
        carried = batch._carriage_of(carrier, batch_id)
        rows.append({
            "batch_id": batch_id,
            "closure_reason": item.get("closure_reason"),
            "released_by_receipt_sha256": carrier["receipt_sha256"] if carried is not None else None,
            "master_records_submission": _master_records_submission(store, carried, batch_id),
        })
    return rows


def readback(
    root,
    *,
    correlation_ids: tuple[str, ...],
    include_exact: bool = True,
) -> dict[str, Any]:
    """Verify the entire resident HEAD chain, even when matches are historical.

    `root` is the POSIX ledger root or the ledger store the append used; a
    Git ledger store is read from one committed tip of its durable ref.
    Exact bytes are returned only to the resident-local caller. That caller must
    keep them inside the existing private runtime and authorized return path.
    """
    if not org._is_store(root):
        root = Path(root).expanduser().resolve()
    with batch._pinned(root) as store:
        return _readback(store, correlation_ids=correlation_ids, include_exact=include_exact)


def _readback(root, *, correlation_ids: tuple[str, ...], include_exact: bool) -> dict[str, Any]:
    head = batch._get(root, org.ledger_store.HEAD_KEY)
    if head is None:
        if root.list_prefix(org.ledger_store.RECEIPT_PREFIX):
            raise ValueError("ORGANIZATION_HEAD_MISSING_WITH_RECEIPTS")
        raise ValueError("ORGANIZATION_HEAD_NOT_MATERIALIZED")
    tip = head.get("receipt_sha256")
    if head.get("organization") != org.C["organization"] or not isinstance(tip, str) or not SHA.fullmatch(tip):
        raise ValueError("ORGANIZATION_HEAD_IDENTITY_INVALID")
    ordered = batch._segment(root, tip, None)
    if not ordered or ordered[-1]["receipt_sha256"] != tip:
        raise ValueError("ORGANIZATION_HEAD_PREDECESSOR_INVALID")
    all_hashes = [row["receipt_sha256"] for row in ordered]
    sources = [_source_for(root, row) for row in ordered]
    batches = _verified_batches(root, all_hashes)
    submissions = _batch_submissions(root, ordered, batches)
    # Do not call the candidate stable if another resident append raced readback.
    if batch._get(root, org.ledger_store.HEAD_KEY) != head:
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
        # #3012: the post-commit Master Records carriage of each released batch,
        # as recorded on this store. Reported, never adjudicated: no state here
        # gates the readback or is an acknowledgement.
        "batch_submissions": submissions,
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


def reconcile_master_records(
    snapshot: dict[str, Any],
    *,
    get_json,
) -> dict[str, Any]:
    """Read-only comparison against EXISTING authenticated Master Records APIs.

    get_json(path, parameters) must be supplied by the resident's existing
    credential/transport owner. A local source record alone never satisfies
    Master Records organization record. Missing matches remain explicit.
    """
    if snapshot.get("state") != "VERIFIED_LOCAL_READBACK" or snapshot.get("complete_organization_chain") != "PASS":
        raise ValueError("ORGANIZATION_SNAPSHOT_NOT_VERIFIED")
    from urllib.parse import quote
    sources = {}
    for source in snapshot.get("exact_source_receipts", []):
        verified = org.verify_source(source)
        sources[verified["source_transition_sha256"]] = source
    canonical = []
    for item in snapshot.get("matching_transitions", []):
        source = sources.get(item["source_transition_sha256"])
        if not isinstance(source, dict):
            raise ValueError("MATCHED_EXACT_SOURCE_NOT_AVAILABLE")
        if source.get("schema") != "stegverse.canonical-state-transition-receipt/v1":
            canonical.append({"organization_receipt_sha256": item["organization_receipt_sha256"],
                              "state": "REPOSITORY_SOURCE_NOT_DIRECT_CANONICAL_CUSTODY"})
            continue
        query = get_json("/api/master-records/state-transitions/query", {
            "subject_or_correlation_id": source["subject_or_correlation_id"],
            "transition_id": source["transition_id"],
        })
        if (not isinstance(query, dict)
                or query.get("schema") != "stegverse.master-records.state-transition-query/v1"
                or query.get("subject_or_correlation_id") != source["subject_or_correlation_id"]
                or query.get("transition_id") != source["transition_id"]
                or not isinstance(query.get("records"), list)
                or query.get("count") != len(query["records"])):
            raise ValueError("MASTER_RECORDS_QUERY_RESPONSE_INVALID")
        digest = item["source_transition_sha256"][7:]
        same = [record for record in query["records"]
                if isinstance(record, dict) and record.get("receipt_sha256") == digest]
        if len(same) > 1:
            raise ValueError("MASTER_RECORDS_DUPLICATE_EXACT_TRANSITION")
        if same:
            record = same[0]
            if (record.get("state") != "PASS"
                    or record.get("reconstructed_receipt_sha256") != digest
                    or record.get("required_evidence_validation_status") != "PASS"
                    or record.get("receipt") != source):
                raise ValueError("MASTER_RECORDS_EXACT_TRANSITION_RECONSTRUCTION_MISMATCH")
            state = "MATCHING_INDEPENDENT_RECONSTRUCTION_PASS"
        else:
            state = "MATCH_NOT_FOUND_IN_AUTHENTIC_QUERY"
        canonical.append({
            "organization_receipt_sha256": item["organization_receipt_sha256"],
            "source_transition_sha256": item["source_transition_sha256"],
            "source_transition_id": source["transition_id"],
            "state": state,
        })
    batch_results = []
    for local in snapshot.get("exact_batches", []):
        batch_id = local["batch_id"]
        remote = get_json(
            "/api/master-records/organization-batches/" + quote(batch_id, safe=":") + "/reconstruction", {},
        )
        if (not isinstance(remote, dict)
                or remote.get("schema") != "stegverse.master-records.organization-batch-ack/v1"
                or remote.get("batch_id") != batch_id
                or remote.get("organization_id") != snapshot["organization"]
                or remote.get("organization_receipt_count") != len(local["ordered_receipt_hashes"])):
            raise ValueError("MASTER_RECORDS_BATCH_RECONSTRUCTION_IDENTITY_MISMATCH")
        if (remote.get("state") != "RECORDED"
                or remote.get("reconstruction_status") != "PASS"
                or remote.get("required_evidence_validation_status") != "PASS"
                or remote.get("receipt_sha256") != remote.get("reconstructed_receipt_sha256")):
            raise ValueError("MASTER_RECORDS_BATCH_RECONSTRUCTION_FAILED")
        batch_results.append({"batch_id": batch_id,
                              "master_records_receipt_sha256": remote["receipt_sha256"],
                              "state": "MATCHING_INDEPENDENT_BATCH_RECONSTRUCTION_PASS"})
    eligible = [x for x in canonical if x["state"] != "REPOSITORY_SOURCE_NOT_DIRECT_CANONICAL_CUSTODY"]
    return {
        "schema": "stegverse.organization-master-records-reconciliation/v1",
        "state": ("PASS" if (eligible or batch_results) and all(
            x["state"] == "MATCHING_INDEPENDENT_RECONSTRUCTION_PASS" for x in eligible
        ) else "INCOMPLETE" if eligible else "NO_APPLICABLE_MATCHING_CUSTODY"),
        "organization_head_receipt_sha256": snapshot["head_receipt_sha256"],
        "canonical_transition_results": canonical,
        "batch_results": batch_results,
        "master_records_grants_transition_authority": False,
        "authority_effect": "NONE_READ_ONLY_RECONSTRUCTION_COMPARISON",
    }
