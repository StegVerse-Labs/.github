#!/usr/bin/env python3
"""Execute the existing MIR worker with live per-transition Master Records probes.

This is a diagnostic wrapper around the existing MIR round-trip worker. It does
not create a new runtime, scheduler, dispatcher, transport, credential path, or
transition authority. The existing WorkerCoordinator claim/fence and
Interlock/InTr lane remain authoritative. The wrapper observes transition
consequences already produced by the proven SV002-derived event path and sends a
confirmation packet to Master Records after each observed step.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

from workers import mir_roundtrip_egress_authenticity_worker as base

TASK_ID = base.TASK_ID
ROOT_GOAL = base.ROOT_GOAL
COSV = base.COSV
DIAGNOSTIC_REL = Path("receipts/mir-roundtrip-egress-authenticity/live-transition-diagnostic.latest.json")
PACKET_DIR_REL = Path("receipts/mir-roundtrip-egress-authenticity/live-transition-confirmations")
SCHEMA = "stegverse.mir-live-transition-confirmation/v1"


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _safe(value: Any, depth: int = 0) -> Any:
    if depth > 3:
        return type(value).__name__
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return {"bytes": len(value), "sha256": _sha256(value)}
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if len(out) >= 24:
                out["_truncated"] = True
                break
            out[str(key)] = _safe(item, depth + 1)
        return out
    if isinstance(value, (list, tuple)):
        return [_safe(item, depth + 1) for item in list(value)[:24]]
    for attr in ("lease_id", "runtime_id", "state", "queue_id", "receipt_hash", "packet_id"):
        if hasattr(value, attr):
            return {"type": type(value).__name__, attr: _safe(getattr(value, attr), depth + 1)}
    return {"type": type(value).__name__}


def _resolve_stegos_root(root: Path) -> Path:
    return base.resolve_repo(
        ("STEGVERSE_STEGOS_SOURCE_ROOT", "STEGVERSE_STEGOS_ROOT"),
        ("StegVerse-Labs/StegOS", "StegOS"),
        (root.parent / "StegOS",),
    )


class Probe:
    def __init__(self, root: Path, invocation: dict[str, Any]) -> None:
        self.root = root.resolve()
        self.claim_id, self.fence = base.validate_invocation(invocation)
        self.sequence = 0
        self.rows: list[dict[str, Any]] = []
        self.first_non_return: str | None = None
        self.mr = base.import_master_records_worker(self.root)
        self.packet_dir = self.root / PACKET_DIR_REL
        self.diagnostic_path = self.root / DIAGNOSTIC_REL

    def _persist(self) -> None:
        state = "ALL_OBSERVED_TRANSITIONS_RETURNED" if self.first_non_return is None else "FIRST_NON_RETURN_IDENTIFIED"
        base.atomic_json(self.diagnostic_path, {
            "schema": "stegverse.mir-live-transition-master-records-diagnostic/v1",
            "state": state,
            "goal_task_id": TASK_ID,
            "root_goal_task_id": ROOT_GOAL,
            "cosv_task_vector": COSV,
            "claim_id": self.claim_id,
            "fencing_token": self.fence,
            "first_non_return_transition_id": self.first_non_return,
            "transition_confirmations": self.rows,
            "master_records_grants_transition_authority": False,
            "authority_effect": "NONE_DIAGNOSTIC_ONLY",
        })

    def record(self, transition_id: str, evidence: Any = None) -> dict[str, Any]:
        self.sequence += 1
        packet = {
            "schema": SCHEMA,
            "state": "TRANSITION_OBSERVED",
            "transition_sequence": self.sequence,
            "transition_id": transition_id,
            "goal_task_id": TASK_ID,
            "root_goal_task_id": ROOT_GOAL,
            "cosv_task_vector": COSV,
            "claim_id": self.claim_id,
            "fencing_token": self.fence,
            "destination_profile": "MIR",
            "transition_evidence": _safe(evidence),
            "master_records_may_grant_transition_authority": False,
            "authority_effect": "NONE_CONFIRMATION_EVIDENCE_ONLY",
        }
        packet_path = self.packet_dir / f"{self.sequence:03d}-{transition_id}.json"
        base.atomic_json(packet_path, packet)
        try:
            result = self.mr.execute(packet_path)
        except Exception as exc:
            result = {"state": "BOUNDARY", "reason": f"MASTER_RECORDS_PROBE_EXCEPTION:{type(exc).__name__}:{exc}", "authority_effect": "NONE"}
        returned = isinstance(result, dict) and result.get("state") == "RETURNED"
        if not returned and self.first_non_return is None:
            self.first_non_return = transition_id
        row = {
            "transition_sequence": self.sequence,
            "transition_id": transition_id,
            "packet_ref": str(packet_path),
            "master_records_state": result.get("state") if isinstance(result, dict) else None,
            "master_records_reason": result.get("reason") if isinstance(result, dict) else "INVALID_MASTER_RECORDS_RESULT",
            "returned": returned,
            "custody_ref": result.get("custody_ref") if isinstance(result, dict) else None,
            "reconstructed_ref": result.get("reconstructed_ref") if isinstance(result, dict) else None,
        }
        self.rows.append(row)
        self._persist()
        return row


def _patch_method(cls: type, name: str, probe: Probe, transition: str, evidence_builder: Callable[..., Any] | None = None) -> None:
    original = getattr(cls, name)

    def wrapped(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        evidence = evidence_builder(self, result, args, kwargs) if evidence_builder else result
        probe.record(transition, evidence)
        return result

    setattr(cls, name, wrapped)


def _install_probes(probe: Probe, stegos_root: Path) -> None:
    if str(stegos_root) not in sys.path:
        sys.path.insert(0, str(stegos_root))

    from stegos import canonical_runtime_local_evidence as local_evidence
    from stegos import ephemeral_runtime_lease as lease
    from stegos import mir_profile_runtime as mir_runtime
    from stegos import sovereign_local_event_runtime as local_runtime

    original_transition = lease.LeaseMachine.transition
    def transition(self, next_state, *args, **kwargs):
        result = original_transition(self, next_state, *args, **kwargs)
        label = getattr(next_state, "value", str(next_state))
        probe.record(f"LEASE_STATE_{label}", {"lease_id": getattr(self.request, "lease_id", None), "state": label})
        return result
    lease.LeaseMachine.transition = transition

    for method, label in (
        ("open_after_local_verification", "LEASE_LOCAL_IDENTITY_ACCEPTED"),
        ("record_transition", "BOUNDED_EVENT_TRANSITION_RECORDED"),
        ("queue_return", "GOVERNED_RETURN_QUEUED"),
        ("export_evidence", "EVIDENCE_EXPORT_STATE_RECORDED"),
    ):
        if hasattr(lease.LeaseMachine, method):
            _patch_method(lease.LeaseMachine, method, probe, label, lambda self, result, args, kwargs: {"lease_id": getattr(self.request, "lease_id", None), "state": getattr(getattr(self, "state", None), "value", str(getattr(self, "state", "")))})

    _patch_method(local_evidence.RetainedNodeProofVerifier, "verify", probe, "CURRENT_NODE_PROOF_VERIFIED")
    _patch_method(local_runtime.SovereignLocalEventRuntimeAdapter, "provision", probe, "EVENT_COMPUTE_PROVISIONED")
    _patch_method(local_runtime.SovereignLocalEventRuntimeAdapter, "materialize", probe, "EVENT_EPHEMERAL_RUNTIME_MATERIALIZED")
    _patch_method(local_runtime.SovereignLocalEventRuntimeAdapter, "verify_local", probe, "EXECUTION_TIME_RUNTIME_IDENTITY_VERIFIED")

    original_execute = mir_runtime.MirProfileRuntimeExecutor.execute
    def execute(self, *args, **kwargs):
        response = original_execute(self, *args, **kwargs)
        parsed: Any = None
        try:
            parsed = json.loads(bytes(response).decode("utf-8"))
        except Exception:
            parsed = {"response_sha256": _sha256(bytes(response))}
        probe.record("RTC-FARSIDE-FINAL-009", parsed)
        return response
    mir_runtime.MirProfileRuntimeExecutor.execute = execute

    original_enqueue = local_evidence.LocalReturnPathCarrier.enqueue
    def enqueue(self, evidence, *args, **kwargs):
        if isinstance(evidence, Mapping):
            ingress = evidence.get("request_ingress_receipt")
            egress = evidence.get("response_egress_receipt")
            if ingress is not None:
                probe.record("CURRENT_INTERLOCK_INTR_INGRESS_RECEIVED", ingress)
            if egress is not None:
                probe.record("RTC-STEGVERSE-EGRESS-007", egress)
            if ingress is not None and egress is not None:
                probe.record("RTC-INTERLOCK-INTR-TRANSPORT-008", {
                    "request_ingress_receipt": ingress,
                    "response_egress_receipt": egress,
                    "receipt_chain_linked": evidence.get("receipt_chain_linked"),
                })
        result = original_enqueue(self, evidence, *args, **kwargs)
        probe.record("MIR_DESTINATION_EVIDENCE_RETAINED", result)
        return result
    local_evidence.LocalReturnPathCarrier.enqueue = enqueue

    _patch_method(local_evidence.LocalEvidenceExporter, "export", probe, "MIR_EVIDENCE_EXPORTED")
    _patch_method(local_evidence.LocalClosureRetainer, "retain", probe, "EVENT_EPHEMERAL_LEASE_CLOSURE_RETAINED")

    original_packet_retain = local_evidence.LocalExactReturnPacketRetainer.retain
    def packet_retain(self, *args, **kwargs):
        result = original_packet_retain(self, *args, **kwargs)
        probe.record("EXACT_GOVERNED_RETURN_PACKET_RETAINED", result)
        return result
    local_evidence.LocalExactReturnPacketRetainer.retain = packet_retain

    _patch_method(local_runtime.SovereignLocalEventRuntimeAdapter, "release", probe, "EVENT_COMPUTE_RELEASED")


def run(invocation: dict[str, Any], *, root: Path) -> dict[str, Any]:
    probe = Probe(root, invocation)
    probe.record("WORKERCOORDINATOR_CLAIM_FENCE_BOUND", {"claim_id": probe.claim_id, "fencing_token": probe.fence})
    stegos_root = _resolve_stegos_root(root.resolve())
    probe.record("MIR_EVENT_INGRESS_INTENT_BOUND", {"destination_profile": "MIR", "stegos_source_root": str(stegos_root)})
    _install_probes(probe, stegos_root)
    try:
        response = base.run(invocation, root=root)
    except Exception as exc:
        probe.record("MIR_EVENT_FAIL_CLOSED", {"error_type": type(exc).__name__, "error": str(exc)})
        return {
            "schema": "stegverse.worker-response/v0.1",
            "state": "HANDOFF_READY",
            "transition_id": "MIR_EVENT_TRANSITION_FAIL_CLOSED",
            "transition_sequence": probe.sequence,
            "expected_next_transition": "REPAIR_FIRST_EXACT_EVENT_OR_CONFIRMATION_BOUNDARY",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "first_non_return_transition_id": probe.first_non_return,
            "transition_diagnostic_ref": str(DIAGNOSTIC_REL),
            "authority_effect": "NONE_FAIL_CLOSED",
        }
    if probe.first_non_return is not None:
        return {
            "schema": "stegverse.worker-response/v0.1",
            "state": "HANDOFF_READY",
            "transition_id": "MIR_MASTER_RECORDS_CONFIRMATION_BOUNDARY_IDENTIFIED",
            "transition_sequence": probe.sequence,
            "expected_next_transition": "REPAIR_FIRST_MASTER_RECORDS_CONFIRMATION_RETURN_BOUNDARY",
            "first_non_return_transition_id": probe.first_non_return,
            "transition_diagnostic_ref": str(DIAGNOSTIC_REL),
            "underlying_transition_id": response.get("transition_id"),
            "authority_effect": "NONE_DIAGNOSTIC_ONLY",
        }
    return {
        **response,
        "transition_diagnostic_ref": str(DIAGNOSTIC_REL),
        "all_observed_transition_confirmations_returned": True,
    }


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
        if not isinstance(invocation, dict):
            raise RuntimeError("worker_invocation_object_required")
        response = run(invocation, root=Path.cwd())
    except Exception as exc:
        response = {
            "schema": "stegverse.worker-response/v0.1",
            "state": "HANDOFF_READY",
            "transition_id": "MIR_TRANSITION_PROBE_SETUP_FAIL_CLOSED",
            "transition_sequence": 0,
            "expected_next_transition": "REPAIR_TRANSITION_PROBE_SETUP_BOUNDARY",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "authority_effect": "NONE_FAIL_CLOSED",
        }
    print(json.dumps(response, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
