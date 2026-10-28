#!/usr/bin/env python3
"""Fail-closed preflight for an ALREADY REGISTERED Goal's PROPOSED -> INGRESS_ADMITTED edge.

The edge is the canonical-task-record schema's own: ``coordination_state`` moves
from PROPOSED to INGRESS_ADMITTED, and only when the shard's
``allowed_next_transitions`` names INGRESS_ADMITTED (the same predicate
run_canonical_work_event_bootstrap.py applies).

This is not new-task registration (#3232/#3233), a Registry mutator,
a WorkerCoordinator allocator, or an InTr/Organization Ledger writer.
The original Registry owner must issue an actual manifest-directed transition;
only its authenticated original receipt/readback may authorize a state change.
No device, clock, provider or external machine is consulted.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable

TASK_ID = "STEGAPP-EPHEMERAL-COMPOSITION-001"
# Exact value read back from the already-registered original task vector;
# this preflight is scoped to its PROPOSED/UNCLAIMED predecessor state.
REGISTERED_PROPOSED_COSV = "10300000011000"
SCHEMA = "stegverse.existing-task-admission-preflight/v1"
GOAL = "STEGAPP-EPHEMERAL-COMPOSITION-001"
RETRY = "StegVerse-Labs/.github#3291 / original Registry owner transition"
SHA_KEYS = ("task_id", "correlation_id", "root_correlation_id", "parent_task_id",
            "goal", "source_refs", "targets", "dependencies", "blockers",
            "expected_evidence_predicates", "worker_claim")
SHA = "sha256:"
FROM_STATE = "PROPOSED"
TO_STATE = "INGRESS_ADMITTED"
# Anchored, as elsewhere in the stack: a digest without the sha256: prefix is not one.
SHA256_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


def _hash(value: Any) -> str:
    return SHA + hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False).encode("utf-8")).hexdigest()


def _fail(code: str, predicate: str, repair: str) -> dict[str, Any]:
    return dict(disposition="FAIL_CLOSED", failure_code=code,
                failed_predicate=predicate,
                required_evidence_or_repair=repair,
                retry_entrypoint=RETRY, owning_existing_goal=GOAL,
                next_attempt="Re-evaluate original owner evidence on current Registry head",
                authority_effect="NONE_PREFLIGHT_ONLY",
                state_written=False, claim_or_fence_minted=False,
                ledger_appended=False)


def evaluate(registry: Any, shard: Any, vector: Any, owner_receipt: Any,
             native_receipt_verifier: Callable[[dict[str, Any]], Any] | None = None
             ) -> dict[str, Any]:
    """Return evidence-only decision, never mutate a source or grant authority.

    The verifier MUST be provided by the actual owner trust boundary, not the
    request payload. Its result must bind the same receipt and sovereign
    organization-ledger readback; a missing verifier always fails closed.
    """
    result = _fail("EXISTING_TASK_ADMISSION_NOT_VERIFIED",
                   "ORIGINAL_OWNER_REGISTRY_TRANSITION_EVIDENCED",
                   "original owner manifest, exact generation, authentic "
                   "organization-ledger receipt and native verifier")
    try:
        if not isinstance(registry, dict) or type(registry.get("generation")) is not int:
            return _fail("CANONICAL_REGISTRY_UNREADABLE", "REGISTRY_GENERATION_OBSERVED",
                         "re-read current canonical aggregate Registry")
        tasks = registry.get("tasks")
        if not isinstance(tasks, list):
            return _fail("CANONICAL_REGISTRY_UNREADABLE", "REGISTRY_TASK_ROWS_READABLE",
                         "complete canonical Registry task rows")
        rows = [r for r in tasks if isinstance(r, dict) and r.get("task_id") == TASK_ID]
        if len(rows) != 1 or not isinstance(shard, dict) or shard.get("task_id") != TASK_ID:
            return _fail("EXISTING_TASK_IDENTITY_NOT_UNIQUE",
                         "EXACTLY_ONE_CANONICAL_EXISTING_TASK",
                         "canonical aggregate row plus matching shard for existing task")
        row = rows[0]
        # Refuse a forged claim/fence as an explicit authority violation
        # before reporting general shard drift. No claim is ever minted here.
        claims = (row.get("worker_claim"), shard.get("worker_claim"))
        if any(not isinstance(c, dict) or c.get("claim_ref") is not None
               or c.get("fence_ref") is not None or c.get("projection_only") is not True
               or c.get("authority") not in (None, "WORKERCOORDINATOR")
               for c in claims):
            return _fail("UNAUTHENTICATED_WORKER_OWNERSHIP_CONFLICT",
                         "NO_SYNTHETIC_WORKER_CLAIM_OR_FENCE",
                         "reconcile original WorkerCoordinator evidence")
        if any(row.get(k) != shard.get(k) for k in SHA_KEYS):
            return _fail("AGGREGATE_SHARD_OWNER_DRIFT",
                         "EXISTING_TASK_IDENTITY_AND_SCOPE_AGREE",
                         "reconcile original Registry owner aggregate/shard without changing identity")
        if row.get("coordination_state") != FROM_STATE or shard.get("coordination_state") != FROM_STATE:
            return _fail("EXISTING_TASK_STATE_EDGE_CHANGED",
                         "ORIGINAL_STATE_PROPOSED",
                         "use owner transition matching actual source-state edge")
        allowed = shard.get("allowed_next_transitions")
        if not isinstance(allowed, list) or TO_STATE not in allowed:
            return _fail("EXISTING_TASK_EDGE_NOT_ALLOWED",
                         "INGRESS_ADMITTED_IN_ALLOWED_NEXT_TRANSITIONS",
                         "original Registry owner must list INGRESS_ADMITTED in the "
                         "shard's allowed_next_transitions")
        # Canonical task-record/v1 does NOT embed cosv_task_vector.
        # The source of truth is the separately registered COSV task vector,
        # bound by its full task identity and invariant schema. Do not infer
        # one from a row field that is not in this schema.
        expected_vector_identity = "StegVerse-Labs/.github:task:" + TASK_ID
        if (not isinstance(vector, dict)
                or vector.get("schema") != "stegverse.cosv-task-vector/v0.1"
                or vector.get("identity") != expected_vector_identity
                or vector.get("profile") != "task.v1"
                or vector.get("level") != "task"
                or not isinstance(vector.get("vector"), str)
                or len(vector["vector"]) != 14
                or not vector["vector"].isdigit()
                or vector["vector"] != REGISTERED_PROPOSED_COSV
                or not isinstance(vector.get("exact_metrics"), dict)
                or vector["exact_metrics"].get("lifecycle") != "UNCLAIMED"
                or vector.get("authority_effect") != "NONE"):
            return _fail("COSV_PROJECTION_MISMATCH", "CANONICAL_COSV_UNCHANGED",
                         "read the identity-bound original task COSV vector from current Registry")
        if not isinstance(owner_receipt, dict):
            return result
        expected = {
            "task_id": TASK_ID,
            "from_state": FROM_STATE,
            "to_state": TO_STATE,
            "observed_registry_generation": registry["generation"],
            "next_registry_generation": registry["generation"] + 1,
            "previous_task_sha256": _hash(row),
            "cosv": vector["vector"],
            "claim_or_fence_minted": False,
        }
        if any(owner_receipt.get(k) != v for k, v in expected.items()):
            return _fail("OWNER_DECISION_NOT_BOUND_TO_CURRENT_STATE",
                         "OWNER_DECISION_EXACT_PREDECESSOR_AND_COSV",
                         "original manifest decision bound to the current Registry row")
        if (owner_receipt.get("disposition") != "ALLOW"
                or not isinstance(owner_receipt.get("organization_receipt_sha256"), str)
                or not SHA256_DIGEST.match(owner_receipt["organization_receipt_sha256"])):
            return _fail("ORIGINAL_OWNER_ALLOW_OR_LEDGER_RECEIPT_MISSING",
                         "OWNER_ALLOW_AND_SOVEREIGN_RECORDING_PRESENT",
                         "native manifest ALLOW and its original organization receipt")
        if not callable(native_receipt_verifier):
            return result
        observed = native_receipt_verifier(owner_receipt)
        if (not isinstance(observed, dict)
                or observed.get("disposition") != "ALLOW"
                or observed.get("original_manifest_bound") is not True
                or observed.get("organization_receipt_sha256") !=
                    owner_receipt["organization_receipt_sha256"]
                or observed.get("task_id") != TASK_ID):
            return result
        return dict(schema=SCHEMA, disposition="ALLOW",
                    predicate="EXISTING_TASK_ORIGINAL_OWNER_EVIDENCE_VERIFIED",
                    task_id=TASK_ID, observed_registry_generation=registry["generation"],
                    next_state=TO_STATE, owner_receipt_sha256=_hash(owner_receipt),
                    organization_receipt_sha256=owner_receipt["organization_receipt_sha256"],
                    authority_effect="NONE_PREFLIGHT_ONLY",
                    state_written=False, claim_or_fence_minted=False,
                    ledger_appended=False,
                    native_workercoordinator_claim_required=True)
    except (TypeError, ValueError, OverflowError, RecursionError):
        return _fail("EXISTING_TASK_ADMISSION_INPUT_NOT_CANONICAL",
                     "INPUTS_CANONICAL_SERIALIZABLE",
                     "canonical Registry, shard, vector and native owner evidence")
