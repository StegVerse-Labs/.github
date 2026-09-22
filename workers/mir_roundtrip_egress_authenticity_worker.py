#!/usr/bin/env python3
"""Execute the current MIR MIRROR invocation through the proven SV002 substrate.

The historical SV002 lane is reusable engineering evidence, not present authority.
This worker duplicates that frozen route without inserting a new generic Node/A1-A4
re-proof gate. Present authority comes from the fresh WorkerCoordinator claim/fence
and current Interlock/InTr transitions. The worker binds the current Goal/COSV and
MIR destination, uses the existing StegOS EVENT_EPHEMERAL MIR-profile runtime,
retains exact destination evidence, and delegates current-event reconstruction to
Master Records. It creates no scheduler, transport plane, credential authority, or
device prerequisite.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

TASK_ID = "MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001"
ROOT_GOAL = "MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001"
COSV = "50000000100000"
ROUTE_BINDING_REL = Path("data/mir-roundtrip-egress-sv002-route-binding.v1.json")
RECEIPT_REL = Path("receipts/mir-roundtrip-egress-authenticity/current.latest.json")
ONE_WAY_REL = Path("receipts/mir-roundtrip-egress-authenticity/one-way-transition.latest.json")


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


def sha256_uri(raw: bytes) -> str:
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


def validate_invocation(invocation: dict[str, Any]) -> tuple[str, int]:
    require(invocation.get("schema") == "stegverse.worker-invocation/v0.1", "worker_invocation_schema_mismatch")
    task = invocation.get("task")
    scope = invocation.get("scope")
    require(isinstance(task, dict) and isinstance(scope, dict), "worker_invocation_task_scope_missing")
    require(task.get("task_id") == TASK_ID and task.get("state") == "ACTIVE", "current_mir_task_not_active")
    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), dict) else {}
    fence = timing.get("fencing_token")
    require(isinstance(claim_id, str) and bool(claim_id), "workercoordinator_claim_missing")
    require(isinstance(fence, int) and fence >= 1, "workercoordinator_fence_missing")
    require(scope.get("claim_id") == claim_id and scope.get("fencing_token") == fence, "claim_fence_scope_mismatch")
    require(claim_id.endswith(f"-G{fence}"), "claim_generation_mismatch")
    return claim_id, fence


def import_master_records_worker(root: Path):
    path = root / "workers/reusable_task_master_records_roundtrip.py"
    spec = importlib.util.spec_from_file_location("mir_mr_roundtrip", path)
    require(spec is not None and spec.loader is not None, "master_records_worker_import_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def first_external_ingress(mirror_return: dict[str, Any]) -> dict[str, Any]:
    continuation = mirror_return.get("manifest_continuation")
    require(isinstance(continuation, dict), "mir_manifest_continuation_missing")
    receipts = continuation.get("continuation_receipts")
    require(isinstance(receipts, list), "mir_continuation_receipts_missing")
    ingress = next(
        (item for item in receipts if isinstance(item, dict) and item.get("transition_class") == "EXTERNAL_FRAMEWORK_INGRESS"),
        None,
    )
    require(isinstance(ingress, dict), "mir_external_ingress_receipt_missing")
    require(continuation.get("required_next_receipt") == "STEGVERSE_RETURN_EXIT", "mir_return_exit_requirement_missing")
    return ingress


def run(invocation: dict[str, Any], *, root: Path) -> dict[str, Any]:
    claim_id, fence = validate_invocation(invocation)
    source_root = root.resolve()
    site_root = resolve_repo(("STEGVERSE_SITE_ROOT",), ("StegVerse-Labs/Site", "Site"), (source_root.parent / "Site",))
    stegos_root = resolve_repo(
        ("STEGVERSE_STEGOS_SOURCE_ROOT", "STEGVERSE_STEGOS_ROOT"),
        ("StegVerse-Labs/StegOS", "StegOS"),
        (source_root.parent / "StegOS",),
    )

    route_path = site_root / ROUTE_BINDING_REL
    route_bytes = route_path.read_bytes()
    route = json.loads(route_bytes)
    require(isinstance(route, dict), "route_binding_object_required")
    require(route.get("schema") == "stegverse.mir-roundtrip.sv002-route-duplication/v1", "route_binding_schema_mismatch")
    require(route.get("goal_task_id") == TASK_ID and route.get("cosv_task_vector") == COSV, "route_goal_cosv_mismatch")
    require(route.get("instruction") == "DUPLICATE_PROVEN_SV002_ROUTE_FIRST_THEN_APPLY_MIR_SPECIFIC_REQUIREMENTS", "duplicate_first_instruction_missing")
    baseline = route.get("baseline") or {}
    require(baseline.get("historical_status") == "SUCCESSFUL_ENGINEERING_LANE", "proven_sv002_route_status_missing")
    require(baseline.get("generic_route_mechanics_must_not_be_reproved_before_current_mir_invocation") is True, "generic_reproof_gate_not_removed")
    historical = baseline.get("historical_validation_identity") or {}
    node_id = str(historical.get("node") or "")
    interlock_id = str(historical.get("interlock") or "")
    require(bool(node_id) and bool(interlock_id), "frozen_proven_route_identity_incomplete")
    route_binding_sha256 = sha256_uri(route_bytes)

    mir_binding = route.get("mir_specific_bindings_added_after_duplication") or {}
    require(mir_binding.get("destination_profile") == "MIR", "mir_destination_profile_missing")
    require(mir_binding.get("destination") == "STEGVERSE_OWNED_MIR_MIRROR", "mir_mirror_destination_mismatch")

    sys.path.insert(0, str(stegos_root))
    from stegos.mir_node_mirror import build_run2_request
    from stegos.mir_profile_runtime import run_mir_profile_transition
    from stegos.sovereign_local_event_runtime import SovereignLocalEventRuntimeAdapter
    from stegos.canonical_runtime_local_evidence import (
        LocalClosureRetainer,
        LocalEvidenceExporter,
        LocalExactReturnPacketRetainer,
        LocalReturnPathCarrier,
        RetainedNodeProofVerifier,
    )

    manifest = {
        "schema": "stegverse.mir-route-duplication-manifest/v1",
        "goal_task_id": TASK_ID,
        "root_goal_task_id": ROOT_GOAL,
        "cosv_task_vector": COSV,
        "destination_profile": "MIR",
        "destination": "STEGVERSE_OWNED_MIR_MIRROR",
        "route_binding_ref": "StegVerse-Labs/Site/data/mir-roundtrip-egress-sv002-route-binding.v1.json",
        "route_binding_sha256": route_binding_sha256,
        "components": ["RTC-STEGVERSE-EGRESS-007", "RTC-INTERLOCK-INTR-TRANSPORT-008", "RTC-FARSIDE-FINAL-009"],
        "retained_route_node_id": node_id,
        "retained_route_interlock_id": interlock_id,
        "claim_id": claim_id,
        "fencing_token": fence,
        "generic_sv002_route_reproof_performed": False,
        "historical_route_binding_grants_present_authority": False,
    }
    history = [{
        "schema": "stegverse.mir-route-duplication-event/v1",
        "event_type": "MIR_MIRROR_ROUTE_DUPLICATION",
        "goal_task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "destination_profile": "MIR",
        "claim_id": claim_id,
        "fencing_token": fence,
        "route_binding_sha256": route_binding_sha256,
    }]
    correlation_id = f"{TASK_ID}:{claim_id}:G{fence}"
    mirror_request = build_run2_request(manifest=manifest, history=history, response_to=correlation_id, revision=1)

    state_base_raw = (os.getenv("STEGVERSE_HEARTBEAT_ROOT") or "").strip()
    state_base = (
        Path(state_base_raw).expanduser().resolve()
        if state_base_raw
        else Path(os.getenv("XDG_STATE_HOME", "/tmp")).expanduser().resolve() / "stegverse"
    )
    evidence_root = state_base / "mir-roundtrip-egress-authenticity" / claim_id
    runtime_adapter = SovereignLocalEventRuntimeAdapter(
        sovereign_source_root=source_root,
        runtime_base=state_base / "ephemeral-runtime",
    )

    result = run_mir_profile_transition(
        node_proof={
            "node_id": node_id,
            "receipt_sha256": route_binding_sha256,
            "user_verified_by_device": False,
            "proof_class": "FROZEN_PROVEN_ROUTE_BINDING_EVIDENCE_ONLY",
            "grants_present_authority": False,
        },
        mirror_request=mirror_request,
        implementation_ref=f"StegVerse-Labs/.github:{TASK_ID}:{COSV}",
        node_verifier=RetainedNodeProofVerifier(expected_node_id=node_id),
        compute=runtime_adapter,
        materializer=runtime_adapter,
        identity=runtime_adapter,
        rendezvous_adapter=runtime_adapter,
        return_carrier=LocalReturnPathCarrier(evidence_root),
        exporter=LocalEvidenceExporter(evidence_root),
        closure_retainer=LocalClosureRetainer(evidence_root),
        packet_retainer=LocalExactReturnPacketRetainer(evidence_root),
    )

    decoded = json.loads(result.response_payload.decode("utf-8"))
    require(decoded.get("state") == "MIR_PROFILE_MIRROR_EXECUTED", "mir_profile_runtime_transition_not_observed")
    mirror_return = decoded.get("mirror_return")
    require(isinstance(mirror_return, dict), "mir_mirror_return_missing")
    ingress = first_external_ingress(mirror_return)
    require(ingress.get("external_system_profile") == "MIR", "mir_far_side_profile_mismatch")
    require(ingress.get("correlation_id") == correlation_id, "mir_far_side_correlation_mismatch")
    require(result.evidence.get("bounded_execution_observed") is True, "bounded_mir_execution_not_observed")
    require(result.evidence.get("receipt_chain_linked") is True, "mir_intr_receipt_chain_not_linked")
    require(result.closure.get("state") == "LEASE_CLOSED", "mir_runtime_lease_not_closed")
    require(result.closure.get("evidence_retained_before_release") is True, "mir_evidence_not_retained_before_release")

    exact_packet_sha = sha256_uri(result.response_payload)
    one_way = {
        "schema": "stegverse.mir-mirror-one-way-transition-evidence/v1",
        "state": "MIR_MIRROR_ONE_WAY_TRANSITION_OBSERVED",
        "goal_task_id": TASK_ID,
        "root_goal_task_id": ROOT_GOAL,
        "cosv_task_vector": COSV,
        "destination_profile": "MIR",
        "destination": "STEGVERSE_OWNED_MIR_MIRROR",
        "claim_id": claim_id,
        "fencing_token": fence,
        "retained_route_node_id": node_id,
        "retained_route_interlock_id": interlock_id,
        "route_binding_sha256": route_binding_sha256,
        "runtime_id": result.evidence.get("runtime_id"),
        "lease_id": result.evidence.get("lease_id"),
        "request_ingress_receipt": result.evidence.get("request_ingress_receipt"),
        "mir_external_ingress_receipt": ingress,
        "response_egress_receipt": result.evidence.get("response_egress_receipt"),
        "return_queue_receipt": result.evidence.get("return_queue_receipt"),
        "response_packet_sha256": exact_packet_sha,
        "receipt_chain_linked": True,
        "generic_sv002_route_reproof_performed": False,
        "historical_route_binding_grants_present_authority": False,
        "provenance": "MIR_MIRROR_BUILD_TEST_COUNTERPART_RUNTIME",
        "authentic_external_mir_endpoint_claimed": False,
        "authority_effect": "NONE_RUNTIME_EVIDENCE_ONLY",
    }
    one_way_path = root / ONE_WAY_REL
    atomic_json(one_way_path, one_way)

    master_records = import_master_records_worker(root).execute(one_way_path)
    require(isinstance(master_records, dict) and master_records.get("state") == "RETURNED", "master_records_current_transition_reconstruction_not_returned")

    receipt = {
        "schema": "stegverse.mir-roundtrip-egress-authenticity-receipt/v1",
        "state": "ONE_WAY_MIR_MIRROR_TRANSPORT_CONFIRMED",
        "goal_task_id": TASK_ID,
        "root_goal_task_id": ROOT_GOAL,
        "cosv_task_vector": COSV,
        "claim_id": claim_id,
        "fencing_token": fence,
        "destination_profile": "MIR",
        "provenance": "MIR_MIRROR_BUILD_TEST_COUNTERPART_RUNTIME",
        "current_goal_cosv_binding_observed": True,
        "mir_destination_profile_binding_observed": True,
        "final_stegverse_side_egress_transition_observed": True,
        "authentic_interlock_intr_transport_observed": True,
        "mir_mirror_far_side_transition_observed": True,
        "mir_destination_evidence_retained": True,
        "master_records_reconstructs_current_final_exit_transition": True,
        "successful_one_way_mir_transport_identified": True,
        "master_records": master_records,
        "one_way_evidence_ref": str(one_way_path),
        "response_packet_sha256": exact_packet_sha,
        "governed_return_packet_retained": True,
        "full_round_trip_requires_return_admission": True,
        "successful_data_transport_round_trip_identified": False,
        "communication_complete": False,
        "authentic_external_mir_endpoint_claimed": False,
        "credential_authority": "TV/TVC",
        "transition_authority": "Interlock/InTr",
        "master_records_authority": "Master Records",
        "authority_effect": "NONE_EXECUTION_EVIDENCE_ONLY",
    }
    atomic_json(root / RECEIPT_REL, receipt)
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "HANDOFF_READY",
        "transition_id": "MIR_MIRROR_ONE_WAY_TRANSPORT_CONFIRMED",
        "transition_sequence": 1,
        "expected_next_transition": "GOVERNED_RETURN_ADMISSION_FROM_RETAINED_EXACT_PACKET",
        "checkpoint_ref": str(RECEIPT_REL),
        "evidence_refs": [str(RECEIPT_REL), str(ONE_WAY_REL)],
        "authority_effect": "NONE_EXISTING_AUTHORITY_COMPOSITION_ONLY",
    }


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
        require(isinstance(invocation, dict), "worker_invocation_object_required")
        response = run(invocation, root=Path.cwd())
    except Exception as exc:
        response = {
            "schema": "stegverse.worker-response/v0.1",
            "state": "HANDOFF_READY",
            "transition_id": "MIR_MIRROR_ROUTE_DUPLICATION_FAIL_CLOSED",
            "transition_sequence": 1,
            "expected_next_transition": "RETRY_CURRENT_MIR_BOUND_INVOCATION_AFTER_MACHINE_REMEDIATION",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "authority_effect": "NONE_FAIL_CLOSED",
        }
    print(json.dumps(response, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
