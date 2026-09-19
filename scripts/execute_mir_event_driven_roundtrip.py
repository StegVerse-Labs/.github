#!/usr/bin/env python3
"""Execute the current MIR event through the proven SV002 event-triggered order.

The standing MIR request is the event. It is converted to a non-authorizing
Universal InTr materialization request before any EVENT_EPHEMERAL runtime exists.
The request explicitly grants no execution authority and mints no claim/fence.
Interlock/InTr transition semantics remain authoritative; WorkerCoordinator may
coordinate task ownership elsewhere but is not a prerequisite for event creation.

Every observed transition is sent through the canonical Master Records
state-transition custody path. The temporary MIR probe is not used to create or
record canonical state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

TASK_ID = "MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001"
ROOT_GOAL = "MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001"
COSV = "50000000100000"
REQUEST_REL = Path("control/resident-execution-request.d/mir-roundtrip-egress-authenticity-001.json")
ROUTE_BINDING_REL = Path("data/mir-roundtrip-egress-sv002-route-binding.v1.json")
RECEIPT_REL = Path("receipts/mir-roundtrip-egress-authenticity/current.latest.json")
EVENT_REL = Path("receipts/mir-roundtrip-egress-authenticity/event-materialization.latest.json")
CANONICAL_CUSTODY_REL = Path("receipts/mir-roundtrip-egress-authenticity/canonical-custody.latest.json")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"json_object_required:{path}")
    return value


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def repo_roots() -> dict[str, str]:
    raw = (os.getenv("STEGVERSE_REPO_ROOTS_JSON") or "").strip()
    if not raw:
        return {}
    value = json.loads(raw)
    return value if isinstance(value, dict) else {}


def resolve_repo(env_names: tuple[str, ...], root_keys: tuple[str, ...], fallbacks: tuple[Path, ...]) -> Path:
    for name in env_names:
        raw = (os.getenv(name) or "").strip()
        if raw:
            path = Path(raw).expanduser().resolve()
            if path.is_dir():
                return path
    roots = repo_roots()
    for key in root_keys:
        raw = roots.get(key)
        if isinstance(raw, str) and raw:
            path = Path(raw).expanduser().resolve()
            if path.is_dir():
                return path
    for candidate in fallbacks:
        path = candidate.expanduser().resolve()
        if path.is_dir():
            return path
    raise RuntimeError("required_repository_root_not_materialized:" + ",".join(root_keys))


def validate_standing_event(request: dict[str, Any]) -> None:
    require(request.get("schema") == "stegverse.resident-execution-request/v1", "mir_event_request_schema_mismatch")
    require(request.get("state") == "REQUESTED", "mir_event_not_requested")
    require(request.get("task_id") == TASK_ID, "mir_event_task_mismatch")
    require(request.get("cosv_task_vector") == COSV, "mir_event_cosv_mismatch")
    require(request.get("generic_sv002_route_reproof_required") is False, "generic_sv002_reproof_forbidden")
    require(request.get("manual_device_prerequisite") is False, "manual_device_prerequisite_forbidden")
    require(request.get("second_machine_required") is False, "second_machine_forbidden")
    require(request.get("request_granted_authority") is False, "standing_event_authority_forbidden")


def external_ingress(mirror_return: dict[str, Any]) -> dict[str, Any]:
    continuation = mirror_return.get("manifest_continuation")
    require(isinstance(continuation, dict), "mir_manifest_continuation_missing")
    receipts = continuation.get("continuation_receipts")
    require(isinstance(receipts, list), "mir_continuation_receipts_missing")
    row = next((x for x in receipts if isinstance(x, dict) and x.get("transition_class") == "EXTERNAL_FRAMEWORK_INGRESS"), None)
    require(isinstance(row, dict), "mir_external_ingress_receipt_missing")
    require(continuation.get("required_next_receipt") == "STEGVERSE_RETURN_EXIT", "mir_return_exit_requirement_missing")
    return row


def execute(source_root: Path, runtime_root: Path) -> dict[str, Any]:
    source = source_root.resolve()
    runtime = runtime_root.resolve()
    request = load(source / REQUEST_REL)
    validate_standing_event(request)
    request_sha = stable_hash(request)
    event_id = "MIR-EVENT-" + request_sha.split(":", 1)[1][:24]
    correlation_id = f"{TASK_ID}:{event_id}"

    site_root = resolve_repo(("STEGVERSE_SITE_ROOT",), ("StegVerse-Labs/Site", "Site"), (source.parent / "Site",))
    stegos_root = resolve_repo(("STEGVERSE_STEGOS_SOURCE_ROOT", "STEGVERSE_STEGOS_ROOT"), ("StegVerse-Labs/StegOS", "StegOS"), (source.parent / "StegOS",))
    route_path = site_root / ROUTE_BINDING_REL
    route = load(route_path)
    require(route.get("schema") == "stegverse.mir-roundtrip.sv002-route-duplication/v1", "route_binding_schema_mismatch")
    require(route.get("goal_task_id") == TASK_ID and route.get("cosv_task_vector") == COSV, "route_binding_goal_cosv_mismatch")
    baseline = route.get("baseline") if isinstance(route.get("baseline"), dict) else {}
    require(baseline.get("historical_status") == "SUCCESSFUL_ENGINEERING_LANE", "sv002_proven_route_missing")
    require(baseline.get("generic_route_mechanics_must_not_be_reproved_before_current_mir_invocation") is True, "sv002_generic_reproof_gate_present")
    historical = baseline.get("historical_validation_identity") if isinstance(baseline.get("historical_validation_identity"), dict) else {}
    node_id = str(historical.get("node") or "")
    require(bool(node_id), "historical_route_node_identity_missing")
    route_sha = "sha256:" + hashlib.sha256(route_path.read_bytes()).hexdigest()

    sys.path.insert(0, str(stegos_root))
    sys.path.insert(0, str(source))
    from stegos.canonical_runtime_local_evidence import (
        LocalClosureRetainer, LocalEvidenceExporter, LocalExactReturnPacketRetainer,
        LocalReturnPathCarrier, RetainedNodeProofVerifier,
    )
    from stegos.mir_node_mirror import build_run2_request
    from stegos.mir_profile_runtime import build_mir_runtime_intent, run_mir_profile_transition
    from stegos.sovereign_local_event_runtime import SovereignLocalEventRuntimeAdapter
    from stegos.universal_intr_materialization import build_materialization_request, persist_materialization_request
    from workers.canonical_state_transition_custody import CanonicalTransitionCustody

    manifest = {
        "schema": "stegverse.mir-route-duplication-manifest/v1",
        "goal_task_id": TASK_ID,
        "root_goal_task_id": ROOT_GOAL,
        "cosv_task_vector": COSV,
        "event_id": event_id,
        "destination_profile": "MIR",
        "destination": "STEGVERSE_OWNED_MIR_MIRROR",
        "route_binding_ref": "StegVerse-Labs/Site/data/mir-roundtrip-egress-sv002-route-binding.v1.json",
        "route_binding_sha256": route_sha,
        "components": ["RTC-STEGVERSE-EGRESS-007", "RTC-INTERLOCK-INTR-TRANSPORT-008", "RTC-FARSIDE-FINAL-009"],
        "generic_sv002_route_reproof_performed": False,
        "historical_route_binding_grants_present_authority": False,
        "workercoordinator_claim_required_for_event_creation": False,
        "claim_or_fence_minted": False,
        "request_grants_execution_authority": False,
    }
    history = [{
        "schema": "stegverse.mir-route-duplication-event/v1",
        "event_type": "MIR_MIRROR_ROUTE_DUPLICATION",
        "event_id": event_id,
        "goal_task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "destination_profile": "MIR",
        "route_binding_sha256": route_sha,
        "workercoordinator_claim_required_for_event_creation": False,
    }]
    mirror_request = build_run2_request(manifest=manifest, history=history, response_to=correlation_id, revision=1)
    intent, _payload = build_mir_runtime_intent(mirror_request)
    materialization = build_materialization_request(
        intent,
        payload_ref=f"opaque://mir-roundtrip/{event_id}",
        downstream_owner_ref="StegVerse-Labs/StegOS:MIRProfileMirror",
    )
    require(materialization.get("request_grants_execution_authority") is False, "mir_materialization_authority_forbidden")
    require(materialization.get("claim_or_fence_minted") is False, "mir_materialization_claim_fence_forbidden")
    require(materialization.get("event_triggered") is True, "mir_materialization_must_be_event_triggered")
    require(materialization.get("always_on_receiver_required") is False, "mir_materialization_idle_receiver_forbidden")
    materialization_path = persist_materialization_request(runtime, materialization)

    custody = CanonicalTransitionCustody(correlation_id)
    materialization_evidence = {
        "evidence_id": "MIR_EVENT_MATERIALIZATION_REQUEST_QUEUED:materialization-request",
        "evidence_type": "MIR_MATERIALIZATION_REQUEST",
        "origin_transition_id": "MIR_EVENT_MATERIALIZATION_REQUEST_QUEUED",
        "encoding": "canonical-json",
        "sha256": stable_hash(materialization).split(":", 1)[1],
        "content": materialization,
    }
    custody.record(
        "MIR_EVENT_MATERIALIZATION_REQUEST_QUEUED",
        outcome="OBSERVED",
        evidence={
            "event_id": event_id,
            "request_sha256": request_sha,
            "materialization_id": materialization["materialization_id"],
            "request_hash": materialization["request_hash"],
            "materialization_ref": str(materialization_path),
            "event_triggered": True,
            "claim_or_fence_minted": False,
            "request_grants_execution_authority": False,
        },
        required_evidence_manifest=[materialization_evidence],
        resulting_state_ref_or_hash=str(materialization["request_hash"]),
    )

    evidence_root = runtime / "mir-roundtrip-egress-authenticity" / event_id
    runtime_adapter = SovereignLocalEventRuntimeAdapter(
        sovereign_source_root=source,
        runtime_base=runtime / "ephemeral-runtime",
    )
    result = run_mir_profile_transition(
        node_proof={
            "node_id": node_id,
            "receipt_sha256": route_sha,
            "user_verified_by_device": False,
            "proof_class": "FROZEN_PROVEN_ROUTE_BINDING_EVIDENCE_ONLY",
            "grants_present_authority": False,
        },
        mirror_request=mirror_request,
        implementation_ref=f"StegVerse-Labs/.github:{TASK_ID}:{COSV}:{event_id}",
        node_verifier=RetainedNodeProofVerifier(expected_node_id=node_id),
        compute=runtime_adapter,
        materializer=runtime_adapter,
        identity=runtime_adapter,
        rendezvous_adapter=runtime_adapter,
        return_carrier=LocalReturnPathCarrier(evidence_root),
        exporter=LocalEvidenceExporter(evidence_root),
        closure_retainer=LocalClosureRetainer(evidence_root),
        packet_retainer=LocalExactReturnPacketRetainer(evidence_root),
        state_custody=custody,
    )

    decoded = json.loads(result.response_payload.decode("utf-8"))
    require(decoded.get("state") == "MIR_PROFILE_MIRROR_EXECUTED", "mir_profile_transition_not_observed")
    mirror_return = decoded.get("mirror_return")
    require(isinstance(mirror_return, dict), "mir_mirror_return_missing")
    far_side = external_ingress(mirror_return)
    require(far_side.get("external_system_profile") == "MIR", "mir_far_side_profile_mismatch")
    require(far_side.get("correlation_id") == correlation_id, "mir_far_side_correlation_mismatch")
    require(result.evidence.get("receipt_chain_linked") is True, "mir_intr_receipt_chain_not_linked")
    exact_packet_sha = "sha256:" + hashlib.sha256(result.response_payload).hexdigest()

    canonical_summary = {
        "schema": "stegverse.mir-canonical-state-transition-custody-summary/v1",
        "state": "ONE_WAY_CANONICAL_CUSTODY_COMPLETE",
        "event_id": event_id,
        "correlation_id": correlation_id,
        "goal_task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "transition_count": len(custody.records),
        "transition_records": custody.records,
        "temporary_probe_used_as_primary_custody": False,
        "master_records_grants_transition_authority": False,
        "authority_effect": "NONE_CUSTODY_SUMMARY_ONLY",
    }
    atomic_json(runtime / CANONICAL_CUSTODY_REL, canonical_summary)
    atomic_json(runtime / EVENT_REL, {
        "schema":"stegverse.mir-event-materialization-receipt/v1",
        "state":"EVENT_MATERIALIZED_AND_EXECUTED",
        "event_id":event_id,
        "correlation_id":correlation_id,
        "materialization":materialization,
        "materialization_ref":str(materialization_path),
        "workercoordinator_claim_required_for_event_creation":False,
        "claim_or_fence_minted":False,
        "request_grants_execution_authority":False,
        "authority_effect":"NONE_EVENT_EVIDENCE_ONLY",
    })
    receipt = {
        "schema":"stegverse.mir-roundtrip-egress-authenticity-receipt/v1",
        "state":"ONE_WAY_MIR_MIRROR_TRANSPORT_CONFIRMED",
        "goal_task_id":TASK_ID,
        "root_goal_task_id":ROOT_GOAL,
        "cosv_task_vector":COSV,
        "event_id":event_id,
        "correlation_id":correlation_id,
        "destination_profile":"MIR",
        "current_goal_cosv_binding_observed":True,
        "mir_destination_profile_binding_observed":True,
        "final_stegverse_side_egress_transition_observed":True,
        "authentic_interlock_intr_transport_observed":True,
        "mir_mirror_far_side_transition_observed":True,
        "mir_destination_evidence_retained":True,
        "master_records_reconstructs_each_observed_transition":True,
        "successful_one_way_mir_transport_identified":True,
        "canonical_transition_custody_ref":str(runtime / CANONICAL_CUSTODY_REL),
        "canonical_transition_count":len(custody.records),
        "response_packet_sha256":exact_packet_sha,
        "governed_return_packet_retained":True,
        "full_round_trip_requires_return_admission":True,
        "successful_data_transport_round_trip_identified":False,
        "communication_complete":False,
        "workercoordinator_claim_required_for_event_creation":False,
        "claim_or_fence_minted":False,
        "credential_authority":"TV/TVC",
        "transition_authority":"Interlock/InTr",
        "master_records_authority":"Master Records",
        "authority_effect":"NONE_EXECUTION_EVIDENCE_ONLY",
    }
    atomic_json(runtime / RECEIPT_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        value = execute(args.source_root, args.runtime_root)
    except Exception as exc:
        value = {
            "schema":"stegverse.mir-event-driven-execution-failure/v1",
            "state":"FAIL_CLOSED",
            "goal_task_id":TASK_ID,
            "cosv_task_vector":COSV,
            "error_type":type(exc).__name__,
            "error":str(exc),
            "workercoordinator_claim_required_for_event_creation":False,
            "authority_effect":"NONE_FAIL_CLOSED",
        }
    print(json.dumps(value, sort_keys=True))
    return 0 if value.get("state") == "ONE_WAY_MIR_MIRROR_TRANSPORT_CONFIRMED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
