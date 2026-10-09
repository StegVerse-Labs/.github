"""Functional Memory bridge for WorkerCoordinator assignment transitions.

This module adds no scheduler, runtime, authority plane, or custody store. It binds
WorkerCoordinator assignment review to the existing canonical state-transition
custody path. Every non-ALLOW assignment becomes functional memory recorded in
the Organization ledger, and any retained prior assignment memory must resolve
from its verified Organization receipt and retained source receipt before a
later assignment review may consume it. Master Records is evidence only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

from workers.canonical_state_transition_custody import (
    build_state_receipt,
    require_predecessor_master_records_organization_record,
    organization_receipt_custody,
    organization_receipt_gate,
    sha256_uri,
    submit_state_receipt,
)

SCHEMA = "stegverse.worker-assignment-functional-memory/v1"
TRANSITION_ID = "WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW"
VERDICT_TO_ADMISSIBILITY = {
    "ADMIT": "ALLOW",
    "UPDATE": "DEFER",
    "RETIRE": "DENY",
    "BLOCK": "DENY",
}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def canonical_task_context(root: Path, task: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    registry_path = Path(root) / "data" / "canonical-task-registry.json"
    generation = None
    task_registered = False
    if registry_path.is_file():
        value = json.loads(registry_path.read_text(encoding="utf-8"))
        raw_generation = value.get("generation")
        if isinstance(raw_generation, int):
            generation = raw_generation
        task_id = str(task.get("task_id") or "")
        task_registered = any(
            isinstance(row, dict) and row.get("task_id") == task_id
            for row in value.get("tasks", [])
        )

    operational = packet.get("operational_state_vector")
    vector = operational.get("vector") if isinstance(operational, dict) else None
    generation_bound_cosv_id = None
    if isinstance(generation, int):
        generation_bound_cosv_id = f"RG{generation}:{vector if isinstance(vector, str) and vector else 'UNDECLARED'}"

    return {
        "task_id": str(task.get("task_id") or ""),
        "task_registry_generation": generation,
        "task_registered_in_canonical_registry": task_registered,
        "cosv_task_vector": vector,
        "generation_bound_cosv_id": generation_bound_cosv_id,
        "authority_effect": "NONE",
    }


def _memory_from_source_receipt(
    task_id: str,
    receipt: Any,
) -> tuple[dict[str, Any] | None, str | None]:
    """Functional memory content of one verified Organization ledger source receipt."""
    if not isinstance(receipt, dict):
        return None, "FUNCTIONAL_MEMORY_SOURCE_RECEIPT_INVALID"
    if receipt.get("transition_id") != TRANSITION_ID or receipt.get("subject_or_correlation_id") != task_id:
        return None, "FUNCTIONAL_MEMORY_SOURCE_IDENTITY_INVALID"
    evidence = receipt.get("transition_evidence")
    memory = evidence.get("functional_memory") if isinstance(evidence, dict) else None
    if not isinstance(memory, dict) or memory.get("schema") != SCHEMA or memory.get("task_id") != task_id:
        return None, "FUNCTIONAL_MEMORY_SOURCE_CONTENT_INVALID"
    sequence = receipt.get("transition_sequence")
    if not isinstance(sequence, int) or sequence < 1 or memory.get("sequence") != sequence:
        return None, "FUNCTIONAL_MEMORY_SOURCE_SEQUENCE_INVALID"
    return dict(memory), None


def _refusal_reason(refusal: dict[str, Any]) -> str:
    return f"ORGANIZATION_RECEIPT_REFUSED:{refusal['disposition']}:{refusal['failed_predicate']}"


def _ledger(custody: Any, root: Path | None) -> Path:
    """The Organization ledger root: caller-supplied, else STEGVERSE_ORG_LEDGER_ROOT; never a host path."""
    try:
        return Path(root).expanduser().resolve() if root is not None else custody.org.ledger_root()
    except custody.org.LedgerLocationRequired as exc:
        raise custody.OrganizationReceiptRefused(exc.failed_predicate, deterministic=False, detail=str(exc)) from exc


def _recover_pointer_from_organization_ledger(
    task: dict[str, Any], root: Path | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool, str | None]:
    """Discover the task's functional memory chain by replaying the Organization ledger.

    The ledger is replayed with the existing verifier from HEAD; every receipt
    of this transition for this task is read back with its retained source
    receipt. Master Records plays no part.
    """
    task_id = str(task.get("task_id") or "")
    if not task_id:
        return None, None, False, "FUNCTIONAL_MEMORY_TASK_ID_INVALID"
    custody = organization_receipt_custody()
    try:
        ledger = _ledger(custody, root)
        head_path = ledger / "HEAD.json"
        if not head_path.is_file():
            return None, None, True, None
        try:
            chain = custody._segment(ledger, custody.org.load(head_path).get("receipt_sha256"), None)
        except (KeyError, ValueError) as exc:
            raise custody.OrganizationReceiptRefused("ORGANIZATION_LEDGER_REPLAY_FAILED", deterministic=True,
                                                     detail=str(exc)) from exc
        records = []
        for row in chain:
            if row.get("source_transition_id") != TRANSITION_ID or row.get("subject_or_correlation_id") != task_id:
                continue
            records.append(custody.verified_organization_source_receipt(
                ledger, row["receipt_sha256"], state_receipt_sha256=row["source_transition_sha256"],
                expected_transition_id=TRANSITION_ID))
    except custody.OrganizationReceiptRefused as exc:
        return None, None, False, _refusal_reason(exc.refusal())
    if not records:
        return None, None, True, None

    previous_receipt_sha256 = None
    expected_sequence = 1
    latest_memory = None
    latest_pointer = None
    for organization, receipt in records:
        memory, reason = _memory_from_source_receipt(task_id, receipt)
        if memory is None:
            return None, None, False, reason
        sequence = receipt.get("transition_sequence")
        if sequence != expected_sequence:
            return None, None, False, "FUNCTIONAL_MEMORY_SEQUENCE_GAP_OR_REORDER"
        expected_prior = None if previous_receipt_sha256 is None else f"sha256:{previous_receipt_sha256}"
        if receipt.get("prior_state_ref_or_hash") != expected_prior:
            return None, None, False, "FUNCTIONAL_MEMORY_PREDECESSOR_CHAIN_INVALID"
        receipt_sha256 = organization["source_transition_sha256"].split(":", 1)[1]
        latest_memory = memory
        latest_pointer = {
            "schema": SCHEMA,
            "state": "RECORDED",
            "sequence": sequence,
            "admissibility_resolution": memory.get("admissibility_resolution"),
            "task_registry_generation": memory.get("task_registry_generation"),
            "generation_bound_cosv_id": memory.get("generation_bound_cosv_id"),
            "receipt_sha256": receipt_sha256,
            "organization_receipt_sha256": organization["receipt_sha256"],
            "pointer_recovered_from_organization_ledger": True,
            "authority_effect": "NONE_CUSTODY_RECONSTRUCTION_ONLY",
        }
        previous_receipt_sha256 = receipt_sha256
        expected_sequence += 1
    return latest_memory, latest_pointer, True, None


def reconstruct_prior_functional_memory(
    task: dict[str, Any], *, root: Path | None = None,
) -> tuple[dict[str, Any] | None, bool, str | None]:
    """Resolve retained prior functional memory from the verified Organization receipt.

    Content is read from the Organization ledger's retained source receipt
    under the same ledger root (`root`, else STEGVERSE_ORG_LEDGER_ROOT). Master
    Records reconstruction is not consulted. A refusal is typed DENY or
    FAIL_CLOSED in the returned reason and nothing is consumed.
    """
    pointer = task.get("functional_memory")
    if not isinstance(pointer, dict):
        memory, recovered_pointer, valid, reason = _recover_pointer_from_organization_ledger(task, root)
        if not valid:
            return None, False, reason
        if recovered_pointer is not None:
            task["functional_memory"] = recovered_pointer
        return memory, True, None

    receipt_sha256 = pointer.get("receipt_sha256")
    if not isinstance(receipt_sha256, str) or not receipt_sha256:
        return None, False, "FUNCTIONAL_MEMORY_RECEIPT_POINTER_INVALID"
    custody = organization_receipt_custody()
    try:
        _, receipt = custody.verified_organization_source_receipt(
            _ledger(custody, root), pointer.get("organization_receipt_sha256"),
            state_receipt_sha256=receipt_sha256, expected_transition_id=TRANSITION_ID)
    except custody.OrganizationReceiptRefused as exc:
        return None, False, _refusal_reason(exc.refusal())
    memory, reason = _memory_from_source_receipt(str(task.get("task_id") or ""), receipt)
    if memory is None:
        return None, False, reason
    if pointer.get("sequence") is not None and pointer.get("sequence") != memory.get("sequence"):
        return None, False, "FUNCTIONAL_MEMORY_SOURCE_SEQUENCE_INVALID"
    return memory, True, None


def bind_assignment_review(
    *,
    root: Path,
    task: dict[str, Any],
    packet: dict[str, Any],
    prior_memory: dict[str, Any] | None,
    prior_memory_valid: bool,
    prior_memory_reason: str | None,
) -> dict[str, Any]:
    bound = dict(packet)
    review = dict(bound.get("review") or {})
    predicates = dict(review.get("predicates") or {})
    predicates["functional_memory_reconstruction_valid"] = bool(prior_memory_valid)
    review["predicates"] = predicates
    reasons = list(review.get("reasons") or [])
    if not prior_memory_valid:
        review["verdict"] = "BLOCK"
        if "FUNCTIONAL_MEMORY_RECONSTRUCTION_FAILED" not in reasons:
            reasons.append("FUNCTIONAL_MEMORY_RECONSTRUCTION_FAILED")
    review["reasons"] = sorted(set(reasons))
    bound["review"] = review

    context = canonical_task_context(root, task, bound)
    disposition = VERDICT_TO_ADMISSIBILITY.get(str(review.get("verdict")), "DENY")
    bound["assignment_transition"] = {
        **context,
        "admissibility_resolution": disposition,
        "worker_materialization_permitted": disposition == "ALLOW",
        "non_allow_requires_master_records": disposition != "ALLOW",
        "prior_functional_memory_consumed": prior_memory is not None,
        "prior_functional_memory_valid": bool(prior_memory_valid),
        "prior_functional_memory_reason": prior_memory_reason,
        "prior_functional_memory": prior_memory,
    }
    bound.pop("packet_sha256", None)
    bound["packet_sha256"] = _sha(bound)
    return bound


def record_non_allow_functional_memory(
    *,
    task: dict[str, Any],
    trigger: dict[str, Any],
    packet: dict[str, Any],
) -> dict[str, Any]:
    transition = packet.get("assignment_transition") or {}
    resolution = str(transition.get("admissibility_resolution") or "")
    if resolution == "ALLOW":
        raise ValueError("ALLOW assignment must not emit a non-ALLOW functional-memory pack")

    previous = task.get("functional_memory")
    if isinstance(previous, dict):
        if transition.get("prior_functional_memory_valid") is not True or transition.get("prior_functional_memory_consumed") is not True:
            return {
                "state": "BOUNDARY",
                "reason": "FUNCTIONAL_MEMORY_PREDECESSOR_NOT_RECONSTRUCTED",
                "authority_effect": "NONE",
            }
    previous_sequence = previous.get("sequence") if isinstance(previous, dict) else 0
    sequence = int(previous_sequence) + 1 if isinstance(previous_sequence, int) else 1
    pack = {
        "schema": SCHEMA,
        "sequence": sequence,
        "task_id": packet.get("task_id"),
        "goal_id": packet.get("goal_id"),
        "task_registry_generation": transition.get("task_registry_generation"),
        "generation_bound_cosv_id": transition.get("generation_bound_cosv_id"),
        "cosv_task_vector": transition.get("cosv_task_vector"),
        "assignment_packet_sha256": packet.get("packet_sha256"),
        "assignment_request_id": trigger.get("packet_id"),
        "trigger_source": trigger.get("source"),
        "worker_assignment_verdict": packet.get("review", {}).get("verdict"),
        "admissibility_resolution": resolution,
        "admissibility_reasons": list(packet.get("review", {}).get("reasons") or []),
        "admissibility_matrix": dict(packet.get("review", {}).get("predicates") or {}),
        "admissibility_matrix_sha256": _sha(packet.get("review", {}).get("predicates") or {}),
        "worker_materialized": False,
        "claim_minted": False,
        "fence_minted": False,
        "prior_functional_memory_receipt_sha256": previous.get("receipt_sha256") if isinstance(previous, dict) else None,
        "authority_effect": "NONE_STATE_MEMORY_ONLY",
    }
    pack_sha = _sha(pack)
    evidence = {
        "evidence_id": f"worker-assignment-functional-memory:{packet.get('task_id')}:{sequence}",
        "evidence_type": "WORKERCOORDINATOR_NON_ALLOW_ASSIGNMENT_FUNCTIONAL_MEMORY",
        "origin_transition_id": TRANSITION_ID,
        "encoding": "canonical-json",
        "sha256": pack_sha,
        "content": pack,
    }
    predecessor_sha256 = previous.get("receipt_sha256") if isinstance(previous, dict) else None
    try:
        prior_ref, predecessor_evidence = require_predecessor_master_records_organization_record(
            predecessor_sha256,
            successor_transition_id=TRANSITION_ID,
        )
    except RuntimeError as exc:
        return {
            "state": "BOUNDARY",
            "reason": str(exc),
            "authority_effect": "NONE",
        }
    outcome = "PARTIAL" if resolution == "DEFER" else "DENY"
    receipt = build_state_receipt(
        transition_id=TRANSITION_ID,
        transition_sequence=sequence,
        subject_or_correlation_id=str(packet.get("task_id") or ""),
        transition_outcome=outcome,
        prior_state_ref_or_hash=prior_ref,
        resulting_state_ref_or_hash=f"sha256:{pack_sha}",
        governance_decision_ref_where_applicable=f"sha256:{packet.get('packet_sha256')}",
        transition_evidence={
            "functional_memory": pack,
            "admissibility_resolution": resolution,
            "worker_materialized": False,
            "master_records_grants_assignment_authority": False,
        },
        required_evidence_manifest=[*predecessor_evidence, evidence],
        proof_scope="WORKERCOORDINATOR_ASSIGNMENT_DISPOSITION_ONLY",
        proof_ceiling="NON_ALLOW_ASSIGNMENT_AND_FUNCTIONAL_MEMORY_CUSTODY_ONLY",
    )
    result = submit_state_receipt(receipt)
    # Organization ledger record closes the transition; Master Records
    # reconstruction fields are evidence only and never gate it.
    gate = organization_receipt_gate(result, expected_transition_id=TRANSITION_ID, record_refusal=True)
    if not gate["verified"]:
        return {
            "state": "BOUNDARY",
            "reason": str(result.get("reason") or "FUNCTIONAL_MEMORY_MASTER_RECORDS_ORGANIZATION_RECORD_INCOMPLETE"),
            "refusal": gate["refusal"],
            "sequence": sequence,
            "authority_effect": "NONE",
        }
    return {
        "schema": SCHEMA,
        "state": "RECORDED",
        "sequence": sequence,
        "admissibility_resolution": resolution,
        "task_registry_generation": transition.get("task_registry_generation"),
        "generation_bound_cosv_id": transition.get("generation_bound_cosv_id"),
        "receipt_sha256": result.get("receipt_sha256"),
        "organization_receipt_sha256": gate["organization_receipt_sha256"],
        "organization_readback_custody_basis": gate["organization_readback_custody_basis"],
        "master_record_ref": result.get("master_record_ref"),
        "reconstruction_status": result.get("reconstruction_status"),
        "required_evidence_validation_status": result.get("required_evidence_validation_status"),
        "authority_effect": "NONE_CUSTODY_RECONSTRUCTION_ONLY",
    }


def allow_manifest_context(packet: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    transition = dict(packet.get("assignment_transition") or {})
    previous = task.get("functional_memory")
    return {
        "task_registry_generation": transition.get("task_registry_generation"),
        "generation_bound_cosv_id": transition.get("generation_bound_cosv_id"),
        "cosv_task_vector": transition.get("cosv_task_vector"),
        "admissibility_resolution": "ALLOW",
        "admission_packet_sha256": packet.get("packet_sha256"),
        "prior_functional_memory_receipt_sha256": previous.get("receipt_sha256") if isinstance(previous, dict) else None,
        "authority_effect": "NONE_CONTEXT_ONLY",
    }


__all__ = [
    "SCHEMA",
    "TRANSITION_ID",
    "VERDICT_TO_ADMISSIBILITY",
    "allow_manifest_context",
    "bind_assignment_review",
    "canonical_task_context",
    "record_non_allow_functional_memory",
    "reconstruct_prior_functional_memory",
]
