"""Functional Memory bridge for WorkerCoordinator assignment transitions.

This module adds no scheduler, runtime, authority plane, or custody store. It binds
WorkerCoordinator assignment review to the existing canonical Master Records
state-transition custody path. Every non-ALLOW assignment becomes reconstructable
functional memory, and any retained prior assignment memory must reconstruct
before a later assignment review may consume it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

from workers.canonical_state_transition_custody import (
    build_state_receipt,
    query_state_receipts,
    reconstruct_state_receipt,
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


def _memory_from_reconstruction(
    task_id: str,
    result: dict[str, Any],
    *,
    expected_receipt_sha256: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    receipt_sha256 = result.get("receipt_sha256")
    if (
        result.get("state") != "PASS"
        or not isinstance(receipt_sha256, str)
        or (expected_receipt_sha256 is not None and receipt_sha256 != expected_receipt_sha256)
        or result.get("reconstructed_receipt_sha256") != receipt_sha256
        or result.get("required_evidence_validation_status") != "PASS"
    ):
        return None, str(result.get("reason") or "FUNCTIONAL_MEMORY_RECONSTRUCTION_FAILED")
    receipt = result.get("receipt")
    if not isinstance(receipt, dict):
        return None, "FUNCTIONAL_MEMORY_RECONSTRUCTED_RECEIPT_INVALID"
    if receipt.get("transition_id") != TRANSITION_ID or receipt.get("subject_or_correlation_id") != task_id:
        return None, "FUNCTIONAL_MEMORY_RECONSTRUCTED_IDENTITY_INVALID"
    evidence = receipt.get("transition_evidence")
    memory = evidence.get("functional_memory") if isinstance(evidence, dict) else None
    if not isinstance(memory, dict) or memory.get("schema") != SCHEMA or memory.get("task_id") != task_id:
        return None, "FUNCTIONAL_MEMORY_RECONSTRUCTED_CONTENT_INVALID"
    sequence = receipt.get("transition_sequence")
    if not isinstance(sequence, int) or sequence < 1 or memory.get("sequence") != sequence:
        return None, "FUNCTIONAL_MEMORY_RECONSTRUCTED_SEQUENCE_INVALID"
    return dict(memory), None


def _recover_pointer_from_master_records(task: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool, str | None]:
    task_id = str(task.get("task_id") or "")
    if not task_id:
        return None, None, False, "FUNCTIONAL_MEMORY_TASK_ID_INVALID"
    query = query_state_receipts(task_id, TRANSITION_ID)
    if query.get("state") != "PASS":
        return None, None, False, str(query.get("reason") or "FUNCTIONAL_MEMORY_DISCOVERY_FAILED")
    records = query.get("records")
    if not isinstance(records, list):
        return None, None, False, "FUNCTIONAL_MEMORY_DISCOVERY_RESULT_INVALID"
    if not records:
        return None, None, True, None

    previous_receipt_sha256 = None
    expected_sequence = 1
    latest_memory = None
    latest_pointer = None
    for result in records:
        if not isinstance(result, dict):
            return None, None, False, "FUNCTIONAL_MEMORY_DISCOVERY_RECORD_INVALID"
        memory, reason = _memory_from_reconstruction(task_id, result)
        if memory is None:
            return None, None, False, reason
        receipt = result.get("receipt")
        sequence = receipt.get("transition_sequence") if isinstance(receipt, dict) else None
        if sequence != expected_sequence:
            return None, None, False, "FUNCTIONAL_MEMORY_SEQUENCE_GAP_OR_REORDER"
        expected_prior = None if previous_receipt_sha256 is None else f"sha256:{previous_receipt_sha256}"
        if receipt.get("prior_state_ref_or_hash") != expected_prior:
            return None, None, False, "FUNCTIONAL_MEMORY_PREDECESSOR_CHAIN_INVALID"
        receipt_sha256 = result.get("receipt_sha256")
        latest_memory = memory
        latest_pointer = {
            "schema": SCHEMA,
            "state": "RECORDED",
            "sequence": sequence,
            "admissibility_resolution": memory.get("admissibility_resolution"),
            "task_registry_generation": memory.get("task_registry_generation"),
            "generation_bound_cosv_id": memory.get("generation_bound_cosv_id"),
            "receipt_sha256": receipt_sha256,
            "master_record_ref": result.get("master_record_ref"),
            "reconstruction_status": "PASS",
            "required_evidence_validation_status": "PASS",
            "pointer_recovered_from_master_records": True,
            "authority_effect": "NONE_CUSTODY_RECONSTRUCTION_ONLY",
        }
        previous_receipt_sha256 = receipt_sha256
        expected_sequence += 1
    return latest_memory, latest_pointer, True, None


def reconstruct_prior_functional_memory(task: dict[str, Any]) -> tuple[dict[str, Any] | None, bool, str | None]:
    pointer = task.get("functional_memory")
    if not isinstance(pointer, dict):
        memory, recovered_pointer, valid, reason = _recover_pointer_from_master_records(task)
        if not valid:
            return None, False, reason
        if recovered_pointer is not None:
            task["functional_memory"] = recovered_pointer
        return memory, True, None

    receipt_sha256 = pointer.get("receipt_sha256")
    if not isinstance(receipt_sha256, str) or not receipt_sha256:
        return None, False, "FUNCTIONAL_MEMORY_RECEIPT_POINTER_INVALID"
    result = reconstruct_state_receipt(receipt_sha256)
    memory, reason = _memory_from_reconstruction(str(task.get("task_id") or ""), result, expected_receipt_sha256=receipt_sha256)
    if memory is None:
        return None, False, reason
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
    prior_ref = None
    if isinstance(previous, dict) and isinstance(previous.get("receipt_sha256"), str):
        prior_ref = f"sha256:{previous['receipt_sha256']}"
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
        required_evidence_manifest=[evidence],
        proof_scope="WORKERCOORDINATOR_ASSIGNMENT_DISPOSITION_ONLY",
        proof_ceiling="NON_ALLOW_ASSIGNMENT_AND_FUNCTIONAL_MEMORY_CUSTODY_ONLY",
    )
    result = submit_state_receipt(receipt)
    complete = (
        result.get("state") == "RECORDED"
        and result.get("reconstruction_status") == "PASS"
        and result.get("required_evidence_validation_status") == "PASS"
        and isinstance(result.get("receipt_sha256"), str)
        and result.get("receipt_sha256") == result.get("reconstructed_receipt_sha256")
    )
    if not complete:
        return {
            "state": "BOUNDARY",
            "reason": str(result.get("reason") or "FUNCTIONAL_MEMORY_MASTER_RECORDS_CUSTODY_INCOMPLETE"),
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
