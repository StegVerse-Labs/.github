#!/usr/bin/env python3
"""Bounded replay and batch closure over the EXISTING organization receipt ledger.

This module grants no transition/custody authority. It never mutates individual
organization receipts or the organization ledger HEAD. Master Records acceptance
must be obtained separately through the existing authorized custody path.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import time
from pathlib import Path
import tempfile
from typing import Mapping

import aggregate_repo_transition as org

SCHEMA = "stegverse.organization-receipt-batch/v1"
ACK = "PENDING_MASTER_RECORDS"
CLOSURE_REASONS = {
    "ROUTINE_THRESHOLD", "TASK_CLOSURE", "WORKER_EXPIRY",
    "CONSEQUENTIAL_GOVERNANCE_BOUNDARY", "CUSTODY_RECOVERY",
    "INTER_ORGANIZATION_HANDOFF", "MANIFEST_RELEASE_CONDITION",
    "MANIFEST_RELEASE_DELTA_EXPIRY",
}
# A manifested receipt packet records its own establishment in its first
# receipt. That t(0) accounting is what distinguishes "establishment never
# occurred" from "a failure occurred after establishment"; without it an
# absent packet is ambiguous. Expiry is then computable from the packet's own
# member #1 with no external lookup.
ESTABLISHMENT_KEY = "receipt_packet_establishment"
ESTABLISHMENT_KINDS = {"MANIFEST_ASSIGNMENT_T0", "PRIOR_PACKET_RELEASE"}


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


RECEIPT_REFUSAL_RETRY_ENTRYPOINT = "resident-runtime/organization_batch_custody.py::verified_organization_receipt"
_DIGEST = re.compile(r"(?:sha256:)?([0-9a-f]{64})")


class OrganizationReceiptRefused(ValueError):
    """A successor gate refused because the Organization receipt did not verify.

    Same disposition rule as org-kernel/kernel.py refusal_disposition and
    record_refusal: a deterministic refusal is DENY and is not retried; anything
    else is FAIL_CLOSED and names its retry entrypoint. Nothing is committed.
    """

    def __init__(self, failed_predicate: str, *, deterministic: bool, detail: str = ""):
        super().__init__(failed_predicate + (": " + detail if detail else ""))
        self.failed_predicate = failed_predicate
        self.detail = detail
        self.disposition = "DENY" if deterministic else "FAIL_CLOSED"
        self.retry_entrypoint = None if deterministic else RECEIPT_REFUSAL_RETRY_ENTRYPOINT

    def refusal(self) -> dict:
        refusal = {
            "disposition": self.disposition,
            "failed_predicate": self.failed_predicate,
            "retry_entrypoint": self.retry_entrypoint,
            "consequence_committed": False,
            "authority_effect": "NONE_REFUSAL_ONLY",
        }
        if self.detail:
            refusal["detail"] = self.detail
        return refusal


def _state_digest(value, predicate: str) -> str:
    if value is None or value == "":
        raise OrganizationReceiptRefused(predicate + "_ABSENT", deterministic=False)
    match = _DIGEST.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise OrganizationReceiptRefused(predicate + "_INVALID", deterministic=True)
    return "sha256:" + match.group(1)


def verified_organization_receipt(root, digest, *, state_receipt_sha256,
                                  expected_transition_id=None, expected_predecessor=None) -> dict:
    """Read back one Organization receipt and bind it to the exact state receipt.

    `root` is the Organization ledger root the append used, supplied by the
    caller (aggregate_transition(..., ledger=root)); ledger_root() is only the
    existing fallback when the caller holds none. The receipt must verify under
    _verified_receipt and name `state_receipt_sha256` as its source transition.
    When supplied, the source transition id must equal `expected_transition_id`
    and the retained source receipt's prior_state_ref_or_hash must equal
    `expected_predecessor`. Master Records plays no part. Any failure raises
    OrganizationReceiptRefused; the verified receipt row is returned otherwise.
    """
    source = _state_digest(state_receipt_sha256, "STATE_RECEIPT_SHA256")
    if digest is None or digest == "":
        raise OrganizationReceiptRefused("ORGANIZATION_RECEIPT_SHA256_ABSENT", deterministic=False)
    if not isinstance(digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
        raise OrganizationReceiptRefused("ORGANIZATION_RECEIPT_SHA256_INVALID", deterministic=True)
    try:
        ledger = Path(root).expanduser().resolve() if root is not None else org.ledger_root()
    except org.LedgerLocationRequired as exc:
        raise OrganizationReceiptRefused(exc.failed_predicate, deterministic=False, detail=str(exc)) from exc
    if not (ledger / "receipts" / (digest[7:] + ".json")).is_file():
        raise OrganizationReceiptRefused("ORGANIZATION_RECEIPT_READBACK_MISSING", deterministic=False, detail=digest)
    try:
        row = _verified_receipt(ledger, digest)
    except ValueError as exc:
        raise OrganizationReceiptRefused("ORGANIZATION_RECEIPT_VERIFICATION_FAILED", deterministic=True, detail=str(exc)) from exc
    try:
        # A receipt is Organization reality only on a root that is one reality:
        # no superseded custody generation and no fork.
        org.verify_custody_lineage(ledger)
    except org.CustodyRefused as exc:
        raise OrganizationReceiptRefused(exc.failed_predicate, deterministic=False, detail=exc.detail) from exc
    if not row.get("source_transition_sha256"):
        raise OrganizationReceiptRefused("ORGANIZATION_RECEIPT_SOURCE_ABSENT", deterministic=True, detail=digest)
    if row["source_transition_sha256"] != source:
        raise OrganizationReceiptRefused("ORGANIZATION_RECEIPT_NOT_BOUND_TO_STATE_RECEIPT", deterministic=True, detail=digest)
    if expected_transition_id is not None and row.get("source_transition_id") != expected_transition_id:
        raise OrganizationReceiptRefused("ORGANIZATION_RECEIPT_TRANSITION_MISMATCH", deterministic=True,
                                         detail=str(expected_transition_id))
    if expected_predecessor is not None:
        expected = _state_digest(expected_predecessor, "EXPECTED_PREDECESSOR")
        path = ledger / "source-receipts" / (source[7:] + ".json")
        if not path.is_file():
            raise OrganizationReceiptRefused("ORGANIZATION_SOURCE_RECEIPT_READBACK_MISSING", deterministic=False, detail=source)
        retained = _read(path)
        try:
            retained_digest = org.verify_source(retained)["source_transition_sha256"]
        except (KeyError, ValueError) as exc:
            raise OrganizationReceiptRefused("ORGANIZATION_SOURCE_RECEIPT_INVALID", deterministic=True, detail=str(exc)) from exc
        if retained_digest != source:
            raise OrganizationReceiptRefused("ORGANIZATION_SOURCE_RECEIPT_INVALID", deterministic=True, detail=source)
        prior = retained.get("prior_state_ref_or_hash")
        match = _DIGEST.fullmatch(prior) if isinstance(prior, str) else None
        if match is None or "sha256:" + match.group(1) != expected:
            raise OrganizationReceiptRefused("ORGANIZATION_RECEIPT_PREDECESSOR_STALE", deterministic=True, detail=expected)
    return row


def verified_organization_source_receipt(root, digest, *, state_receipt_sha256,
                                         expected_transition_id=None) -> tuple[dict, dict]:
    """verified_organization_receipt() plus the exact source receipt retained under the same ledger root.

    The content of a transition is resolved from source-receipts/HEX.json, the
    bytes retain_source() kept when the Organization append verified them. The
    retained receipt must verify and hash to the Organization receipt's own
    source transition digest. Returns (organization receipt row, source receipt).
    """
    row = verified_organization_receipt(root, digest, state_receipt_sha256=state_receipt_sha256,
                                        expected_transition_id=expected_transition_id)
    try:
        ledger = Path(root).expanduser().resolve() if root is not None else org.ledger_root()
    except org.LedgerLocationRequired as exc:
        raise OrganizationReceiptRefused(exc.failed_predicate, deterministic=False, detail=str(exc)) from exc
    source = row["source_transition_sha256"]
    path = ledger / "source-receipts" / (source[7:] + ".json")
    if not path.is_file():
        raise OrganizationReceiptRefused("ORGANIZATION_SOURCE_RECEIPT_READBACK_MISSING", deterministic=False, detail=source)
    retained = _read(path)
    try:
        verified = org.verify_source(retained)
    except (KeyError, ValueError) as exc:
        raise OrganizationReceiptRefused("ORGANIZATION_SOURCE_RECEIPT_INVALID", deterministic=True, detail=str(exc)) from exc
    if verified["source_transition_sha256"] != source or verified["source_transition_id"] != row.get("source_transition_id"):
        raise OrganizationReceiptRefused("ORGANIZATION_SOURCE_RECEIPT_INVALID", deterministic=True, detail=source)
    return row, retained


def verified_organization_record(root, result, *, expected_transition_id=None, expected_predecessor=None) -> dict:
    """verified_organization_receipt() for a submit_state_receipt() result or a projection of one.

    The Organization receipt digest is read from the nested receipt and the
    top-level projection; when both are present they must agree.
    """
    if not isinstance(result, dict) or result.get("state") != "RECORDED":
        # The producer's own BOUNDARY reason is the evidence of why it did not record.
        reason = result.get("reason") if isinstance(result, dict) else None
        raise OrganizationReceiptRefused("ORGANIZATION_RECORD_NOT_RECORDED", deterministic=False,
                                         detail=str(reason) if reason else "")
    nested = result.get("organization_receipt")
    nested = nested if isinstance(nested, dict) else {}
    top, inner = result.get("organization_receipt_sha256"), nested.get("receipt_sha256")
    if top is not None and inner is not None and top != inner:
        raise OrganizationReceiptRefused("ORGANIZATION_RECEIPT_TOP_LEVEL_NESTED_CONFLICT", deterministic=True)
    for key in ("source_transition_sha256", "previous_receipt_sha256"):
        projected = result.get("organization_" + key)
        if projected is not None and key in nested and nested[key] != projected:
            raise OrganizationReceiptRefused("ORGANIZATION_RECEIPT_TOP_LEVEL_NESTED_CONFLICT", deterministic=True, detail=key)
    row = verified_organization_receipt(
        root, top if top is not None else inner,
        state_receipt_sha256=result.get("receipt_sha256"),
        expected_transition_id=expected_transition_id,
        expected_predecessor=expected_predecessor,
    )
    # What the caller carries must be what the ledger holds.
    if nested and nested != row:
        raise OrganizationReceiptRefused("ORGANIZATION_RECEIPT_READBACK_CONFLICT", deterministic=True)
    for key in ("source_transition_sha256", "previous_receipt_sha256"):
        projected = result.get("organization_" + key)
        if projected is not None and projected != row.get(key):
            raise OrganizationReceiptRefused("ORGANIZATION_RECEIPT_READBACK_CONFLICT", deterministic=True, detail=key)
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
    org.verify_custody_lineage(root)
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
    org.verify_custody_lineage(root)
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
        source_state = "SOURCE_DIGESTS_AND_REQUIRED_EVIDENCE_BYTES_PASS"
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


def export_batch(root: Path, batch_id: str) -> dict:
    """Prepare exact locally retained source bytes for the existing MR ingress.

    No network delivery or Master Records acknowledgement occurs here. This
    deterministic envelope can be carried by the already-authorized TV/TVC
    transport; only Master Records independently accepts it.
    """
    root=Path(root)
    batch=_verified_batch(root,batch_id)
    hashes=batch.get("ordered_receipt_hashes")
    if not isinstance(hashes,list) or not hashes:
        raise ValueError("organization batch receipt set invalid")
    receipts=[_verified_receipt(root,digest) for digest in hashes]
    sources=[]
    source_map={}
    for row in receipts:
        source_hash=row["source_transition_sha256"]
        source_path=root/"source-receipts"/(source_hash[7:]+".json")
        if not source_path.is_file():
            raise ValueError("exact organization source receipt unavailable: "+source_hash)
        source=_read(source_path)
        verified=org.verify_source(source)
        if verified["source_transition_sha256"]!=source_hash or verified["source_transition_id"]!=row["source_transition_id"]:
            raise ValueError("exact organization source receipt binding invalid")
        source_map[source_hash]=source
        sources.append(source)
    result=verify_batch(root,batch_id,source_receipts=source_map)
    if result.get("source_reconstruction")!="SOURCE_DIGESTS_AND_REQUIRED_EVIDENCE_BYTES_PASS":
        raise ValueError("organization-local required evidence reconstruction incomplete")
    return {
        "schema":"stegverse.master-records.organization-batch-submission/v1",
        "batch":batch,
        "organization_receipts":receipts,
        "source_receipts":sources,
        "authority_requested":False,
        "record_requested":True,
        "reconstruction_requested":True,
    }



def export_batch_record(root: Path, batch_id: str) -> dict:
    """Prepare the batch COMMITMENT for Master Records organization record. Contents stay local.

    The organization reports the batched record, not the individual receipts that
    compose it. It verifies the batch locally first - including exact source
    digests and required-evidence bytes - and then carries only the immutable
    batch commitment and the RESULT of that verification across the boundary.

    Two properties depend on this. Master Records holding a commitment it did not
    receive the contents of is what makes its reconstruction independent of the
    organization's, so the delta between the two is evidence of tampering rather
    than a comparison of one store with its own copy. And inline required-evidence
    bytes - which may carry health PII on the VACC path - never leave the
    organization's private ledger root by construction rather than by policy.
    """
    root = Path(root)
    batch = _verified_batch(root, batch_id)
    local = export_batch(root, batch_id)
    verification = verify_batch(root, batch_id, source_receipts={
        row["source_transition_sha256"]: source
        for row, source in zip(local["organization_receipts"], local["source_receipts"])
    })
    return {
        "schema": "stegverse.master-records.organization-batch-record-submission/v1",
        "batch": batch,
        "local_verification": {
            "organization_chain": verification["organization_chain"],
            "source_reconstruction": verification["source_reconstruction"],
            "receipt_count": verification["receipt_count"],
        },
        "receipt_contents_scope": "ORGANIZATION_LOCAL_ONLY_NOT_TRANSMITTED",
        "authority_requested": False,
        "record_requested": True,
        "reconstruction_requested": True,
    }


def submit_released_batch(root: Path, batch_id: str) -> dict:
    """Submit an immutable released batch through the existing canonical custody transport."""
    envelope = export_batch_record(root, batch_id)
    module_path = Path(__file__).resolve().parents[1] / "workers" / "canonical_state_transition_custody.py"
    spec = importlib.util.spec_from_file_location("canonical_state_transition_custody_for_org_batch", module_path)
    if spec is None or spec.loader is None:
        return {"state":"FAIL_CLOSED","reason":"CANONICAL_CUSTODY_CLIENT_UNAVAILABLE","batch_id":batch_id,"authority_effect":"NONE"}
    custody = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(custody)
    result = custody.submit_organization_batch(envelope)
    if result.get("state") not in {"COMPLETED","FAILED"}:
        return {
            "schema":"stegverse.organization-batch-custody-execution-result/v1",
            "state":"FAILED",
            "execution_result":"FAILED",
            "reason":"ORGANIZATION_BATCH_CUSTODY_EXECUTION_RESULT_INVALID",
            "batch_id":batch_id,
            "custody_result":result,
            "governance_disposition":None,
            "authority_effect":"NONE",
        }
    if result.get("governance_disposition") is not None:
        return {
            "schema":"stegverse.organization-batch-custody-execution-result/v1",
            "state":"FAILED",
            "execution_result":"FAILED",
            "reason":"ORGANIZATION_BATCH_CUSTODY_GOVERNANCE_ESCALATION_DETECTED",
            "batch_id":batch_id,
            "custody_result":result,
            "governance_disposition":None,
            "authority_effect":"NONE",
        }
    return result



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


ORGANIZATION_BATCH_TASK_ID = "ORGANIZATION-BATCH-CUSTODY-REPLAY-001"
ORGANIZATION_BATCH_COSV_TASK_VECTOR = "10000000100000"
ORGANIZATION_BATCH_POLICY_EXTENSION = "stegverse_organization_receipt_batch"
ORGANIZATION_BATCH_TASK_EXTENSION = "stegverse_canonical_task"
ORGANIZATION_BATCH_REQUEST_REF = (
    "control/resident-execution-request.d/"
    "canonical-work-organization-batch-custody-replay-001.json"
)


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def organization_batch_parent_manifest(validated) -> dict:
    """The governing parent manifest a batch-bound SDK request declares.

    Both receivers of the SDK `derive_execution_request` schema -- the worker
    InTr ingress and the organization manifest ingress -- read the same
    canonical task binding and COUNT release policy, so this is the one place
    that validates them. Every failure is a typed ValueError naming the part
    that is missing or does not match.
    """
    _require(validated.get("canonical_task_id") == ORGANIZATION_BATCH_TASK_ID,
             "ORGANIZATION_BATCH_CANONICAL_TASK_BINDING_REQUIRED")
    manifest = validated.get("canonical_manifest")
    _require(isinstance(manifest, Mapping), "ORGANIZATION_BATCH_CANONICAL_MANIFEST_REQUIRED")
    extensions = manifest.get("extensions")
    _require(isinstance(extensions, Mapping), "ORGANIZATION_BATCH_MANIFEST_EXTENSIONS_REQUIRED")
    task_binding = extensions.get(ORGANIZATION_BATCH_TASK_EXTENSION)
    _require(isinstance(task_binding, Mapping), "ORGANIZATION_BATCH_TASK_BINDING_REQUIRED")
    _require(task_binding.get("task_id") == ORGANIZATION_BATCH_TASK_ID,
             "ORGANIZATION_BATCH_TASK_ID_MISMATCH")
    _require(task_binding.get("cosv_task_vector") == ORGANIZATION_BATCH_COSV_TASK_VECTOR,
             "ORGANIZATION_BATCH_COSV_MISMATCH")
    _require(task_binding.get("canonical_request_ref") == ORGANIZATION_BATCH_REQUEST_REF,
             "ORGANIZATION_BATCH_REQUEST_REF_MISMATCH")
    _require(task_binding.get("authority_effect") == "NONE",
             "ORGANIZATION_BATCH_TASK_BINDING_AUTHORITY_ESCALATION")
    policy = extensions.get(ORGANIZATION_BATCH_POLICY_EXTENSION)
    _require(isinstance(policy, Mapping), "ORGANIZATION_BATCH_RECEIPT_BATCH_POLICY_REQUIRED")
    condition = policy.get("release_condition")
    _require(isinstance(condition, Mapping) and condition.get("type") == "COUNT",
             "ORGANIZATION_BATCH_COUNT_RELEASE_CONDITION_REQUIRED")
    count = condition.get("count")
    _require(type(count) is int and count >= 1, "ORGANIZATION_BATCH_RELEASE_COUNT_INVALID")
    graph = validated.get("state_graph")
    graph_request = graph.get("request") if isinstance(graph, Mapping) else None
    canonical_binding = graph_request.get("canonical_task_binding") if isinstance(graph_request, Mapping) else None
    _require(isinstance(canonical_binding, Mapping), "ORGANIZATION_BATCH_SDK_TASK_BINDING_REQUIRED")
    _require(canonical_binding.get("task_id") == ORGANIZATION_BATCH_TASK_ID,
             "ORGANIZATION_BATCH_SDK_TASK_ID_MISMATCH")
    _require(canonical_binding.get("receipt_batch") == dict(policy),
             "ORGANIZATION_BATCH_SDK_BATCH_POLICY_MISMATCH")
    return {"receipt_batch": dict(policy)}


def organization_batch_parent_manifest_absent_predicate(validated) -> str | None:
    """Name what is absent when a request declares no organization batch at all.

    `None` means the request declares some part of a batch -- the receipt-batch
    policy extension, or a canonical task binding to the batch task at the
    request, manifest-extension or SDK-graph level -- so the parent manifest is
    applicable and must validate in full. A request declaring none of it is one
    the parent manifest does not govern, and this names what was looked for.
    """
    manifest = validated.get("canonical_manifest")
    extensions = manifest.get("extensions") if isinstance(manifest, Mapping) else None
    extensions = extensions if isinstance(extensions, Mapping) else {}
    graph = validated.get("state_graph")
    graph_request = graph.get("request") if isinstance(graph, Mapping) else None
    graph_binding = graph_request.get("canonical_task_binding") if isinstance(graph_request, Mapping) else None
    task_binding = extensions.get(ORGANIZATION_BATCH_TASK_EXTENSION)
    declares_policy = ORGANIZATION_BATCH_POLICY_EXTENSION in extensions or (
        isinstance(graph_binding, Mapping) and "receipt_batch" in graph_binding)
    declares_task = (
        validated.get("canonical_task_id") == ORGANIZATION_BATCH_TASK_ID
        or (isinstance(task_binding, Mapping) and task_binding.get("task_id") == ORGANIZATION_BATCH_TASK_ID)
        or (isinstance(graph_binding, Mapping) and graph_binding.get("task_id") == ORGANIZATION_BATCH_TASK_ID)
    )
    if declares_policy or declares_task:
        return None
    return ("ORGANIZATION_BATCH_RECEIPT_BATCH_POLICY_EXTENSION_ABSENT"
            "+ORGANIZATION_BATCH_CANONICAL_TASK_BINDING_ABSENT")


def _manifest_release_count(parent_manifest: dict) -> int:
    """Read the receipt release count from the governing parent manifest."""
    if not isinstance(parent_manifest, dict):
        raise ValueError("governing parent manifest required")
    policy = parent_manifest.get("receipt_batch")
    if not isinstance(policy, dict):
        raise ValueError("parent manifest receipt_batch policy required")
    condition = policy.get("release_condition")
    if not isinstance(condition, dict) or condition.get("type") != "COUNT":
        raise ValueError("parent manifest COUNT receipt batch release condition required")
    count = condition.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise ValueError("parent manifest receipt batch release count invalid")
    return count


def _oscillator():
    """Canonical heartbeat derivation; HB is computed, never a running process."""
    import sys
    if str(org.ROOT) not in sys.path:
        sys.path.insert(0, str(org.ROOT))
    from heartbeat_runtime import independent_oscillator
    return independent_oscillator


def current_heartbeat_epoch(*, now_ns: int | None = None) -> int:
    """Present heartbeat epoch. Requires no scheduler, sampler or live process."""
    osc = _oscillator()
    if now_ns is None:
        now_ns = time.time_ns()
    return int(osc.current_reference(now_ns=now_ns)["epoch"])


def _manifest_establishment(parent_manifest: dict) -> dict | None:
    """Read the optional t(0) establishment declared by the governing manifest.

    Absent, the packet is count-governed only and cannot expire; this keeps
    manifests written before establishment existed valid and unchanged.
    """
    policy = parent_manifest.get("receipt_batch")
    if not isinstance(policy, dict):
        raise ValueError("parent manifest receipt_batch policy required")
    establishment = policy.get("establishment")
    if establishment is None:
        return None
    if not isinstance(establishment, dict):
        raise ValueError("parent manifest establishment invalid")
    identifier = establishment.get("heartbeat_id")
    delta = establishment.get("expiry_delta_heartbeats")
    osc = _oscillator()
    try:
        epoch = osc.decode_heartbeat_id(identifier)
    except (TypeError, ValueError) as exc:
        raise ValueError("parent manifest establishment heartbeat invalid") from exc
    if not isinstance(delta, int) or isinstance(delta, bool) or delta < 1:
        raise ValueError("parent manifest expiry delta invalid")
    return {
        "establishment_heartbeat_id": identifier,
        "establishment_heartbeat_epoch": epoch,
        "expiry_delta_heartbeats": delta,
        "expiry_heartbeat_epoch": epoch + delta,
        "expiry_heartbeat_id": osc.encode_heartbeat_id(epoch + delta),
    }


def manifest_declares_establishment(parent_manifest: dict) -> bool:
    """True when the governing manifest declares a t(0) establishment."""
    return _manifest_establishment(parent_manifest) is not None


def establishment_record(parent_manifest: dict, *, kind: str, released_batch: dict | None = None) -> dict:
    """Build the t(0) accounting carried by a packet's own first receipt."""
    if kind not in ESTABLISHMENT_KINDS:
        raise ValueError("unsupported receipt packet establishment kind")
    declared = _manifest_establishment(parent_manifest)
    if declared is None:
        raise ValueError("parent manifest establishment required to establish a receipt packet")
    return {
        "establishment_kind": kind,
        "establishment_heartbeat_id": declared["establishment_heartbeat_id"],
        "expiry_delta_heartbeats": declared["expiry_delta_heartbeats"],
        "expiry_heartbeat_id": declared["expiry_heartbeat_id"],
        "release_authorized_at_establishment": True,
        "released_batch": released_batch,
        "authority_effect": "NONE_PACKET_ACCOUNTING_ONLY",
    }


def _packet_establishment(rows: list[dict]) -> dict | None:
    """Read the establishment recorded by the open packet's own member #1."""
    if not rows:
        return None
    record = (rows[0].get("boundary_evidence") or {}).get(ESTABLISHMENT_KEY)
    if record is None:
        return None
    if not isinstance(record, dict) or record.get("establishment_kind") not in ESTABLISHMENT_KINDS:
        raise ValueError("receipt packet establishment record invalid")
    return record


def open_packet_state(parent_manifest: dict, *, root: Path | None = None, now_ns: int | None = None) -> dict:
    """Return open-packet accounting: count, declared establishment and expiry."""
    root = Path(root) if root else org.ledger_root()
    release_count = _manifest_release_count(parent_manifest)
    declared = _manifest_establishment(parent_manifest)
    head_path = root / "HEAD.json"
    if not head_path.exists():
        rows: list[dict] = []
    else:
        head = _read(head_path)
        tip = head.get("receipt_sha256")
        _verified_receipt(root, tip)
        _, prior = _batch_head(root)
        rows = _segment(root, tip, prior["last_org_receipt_sha256"] if prior else None)
    established = _packet_establishment(rows)
    if declared is not None and rows and established is None:
        raise ValueError("manifested receipt packet has no t(0) establishment record")
    count_satisfied = len(rows) >= release_count
    expired = False
    expiry_heartbeat_id = None
    if established is not None:
        osc = _oscillator()
        expiry_heartbeat_id = established["expiry_heartbeat_id"]
        expired = current_heartbeat_epoch(now_ns=now_ns) >= osc.decode_heartbeat_id(expiry_heartbeat_id)
    return {
        "receipt_count": len(rows),
        "release_count": release_count,
        "establishment_heartbeat_id": established["establishment_heartbeat_id"] if established else None,
        "expiry_heartbeat_id": expiry_heartbeat_id,
        "expired": expired,
        "release_condition_satisfied": bool(rows) and (count_satisfied or expired),
    }


def release_satisfied_packet_before_next_transition(parent_manifest: dict, *, root: Path | None = None, now_ns: int | None = None,
                                                   custody_exclusivity_verifier=None) -> dict | None:
    """Release the satisfied packet immediately before the next receipt append.

    Release is authorized once, at establishment, by the governing manifest.
    Nothing decides anything here: the condition fires, it is not adjudicated.
    """
    root = Path(root) if root else org.ledger_root()
    state = open_packet_state(parent_manifest, root=root, now_ns=now_ns)
    if not state["release_condition_satisfied"]:
        return None
    reason = "MANIFEST_RELEASE_DELTA_EXPIRY" if (
        state["expired"] and state["receipt_count"] < state["release_count"]
    ) else "MANIFEST_RELEASE_CONDITION"
    return close_batch(reason, root=root, custody_exclusivity_verifier=custody_exclusivity_verifier)


def _verified_head(root: Path) -> tuple[dict, str]:
    """HEAD.json of this root, naming a verified receipt under this root's receipts/."""
    head = _read(root / "HEAD.json")
    if head.get("organization") != org.C["organization"]:
        raise ValueError("organization ledger HEAD identity mismatch")
    tip = head.get("receipt_sha256")
    _verified_receipt(root, tip)
    # HEAD must name its own tip under this root's receipts/. The absolute prefix
    # is wherever a materializer last supplied the root, so it is not compared:
    # the same root supplied at another node's path is the same ledger.
    if Path(str(head.get("receipt_path") or "")).parts[-2:] != ("receipts", tip[7:] + ".json"):
        raise ValueError("organization ledger HEAD receipt path mismatch")
    return head, tip


def close_batch(reason: str, *, root: Path | None = None, custody_exclusivity_verifier=None) -> dict:
    if reason not in CLOSURE_REASONS:
        raise ValueError("unsupported organization batch closure reason")
    root = Path(root) if root else org.ledger_root()
    head, tip = _verified_head(root)
    rows = org.verify_custody_lineage(root)
    if _verified_receipt(root, tip).get("org_transition_class") == org.CUSTODY_RELEASED_CLASS:
        # Batch closure writes the root; a released root takes no writer.
        raise org.CustodyRefused("CUSTODY_RELEASED_ROOT_IS_READ_ONLY", retry_entrypoint=org.CUSTODY_ASSUME_RETRY,
                                 detail=tip, repair="close the packet at the successor after it assumes custody")
    # Batch closure is a consequential write; a successor needs an attestation.
    org.require_consequential_custody(root, rows, tip, "ORGANIZATION_BATCH_CLOSURE", custody_exclusivity_verifier)
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
    parser.add_argument("--export-batch")
    parser.add_argument("--export-batch-record")
    parser.add_argument("--submit-released-batch")
    parser.add_argument("--root")
    args = parser.parse_args()
    root = Path(args.root) if args.root else org.ledger_root()
    if sum(bool(value) for value in (args.closure_reason,args.verify_batch,args.export_batch,args.export_batch_record,args.submit_released_batch)) != 1:
        parser.error("provide exactly one batch operation")
    if args.closure_reason:
        result=close_batch(args.closure_reason,root=root)
    elif args.verify_batch:
        result=verify_batch(root,args.verify_batch)
    elif args.export_batch:
        result=export_batch(root,args.export_batch)
    elif args.export_batch_record:
        result=export_batch_record(root,args.export_batch_record)
    else:
        result=submit_released_batch(root,args.submit_released_batch)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
