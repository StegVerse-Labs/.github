from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from workers.stegos_sovereign_relay_bridge import find_stegos_root

CREDENTIAL_AUTHORITY = "TV/TVC"
IMPLEMENTATION_REF = "StegVerse-Labs/.github#493:SV002_PUBLIC_OBSERVATION_RUNTIME"
CONSEQUENCE_ID = "materialize_sv002_public_observation_receiver"
EVIDENCE_SCHEMA = "stegverse.sv002-observation-esrl-runtime-materialization/v1"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "SV002:PublicObservation"}
TASK_ID = "SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _digest_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else _canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def _persist_lease_snapshot(path: Path, machine: Any, lease_machine_type: Any) -> dict[str, Any]:
    snapshot = machine.snapshot()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            restored = lease_machine_type.from_snapshot(existing)
        except Exception as exc:
            raise RuntimeError("sv002_canonical_lease_existing_snapshot_invalid") from exc
        _require(
            restored.request.as_dict() == machine.request.as_dict(),
            "sv002_canonical_lease_snapshot_request_drift",
        )
        old_history = list(existing.get("history") or [])
        new_history = list(snapshot.get("history") or [])
        _require(
            len(new_history) >= len(old_history)
            and new_history[: len(old_history)] == old_history,
            "sv002_canonical_lease_snapshot_non_monotonic",
        )
    raw = json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(raw, encoding="utf-8")
    temporary.replace(path)
    _require(
        path.read_text(encoding="utf-8") == raw,
        "sv002_canonical_lease_snapshot_persistence_failed",
    )
    return snapshot


def materialize_sv002_observation_runtime(*, control_root: Path, intake_runtime_root: Path, request: Mapping[str, Any], ingress_receipt: Mapping[str, Any], env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Materialize one event-ephemeral runtime for a node-triggered SV002 read."""
    _require(ingress_receipt.get("schema") == "stegverse.sv002-intr-materialization-ingress/v1", "sv002_ingress_receipt_schema_invalid")
    _require(ingress_receipt.get("state") == "INGRESS_ADMITTED", "sv002_ingress_not_admitted")
    _require(request.get("destination") == DESTINATION, "sv002_materialization_destination_invalid")
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "operation_id", "packet_id"):
        _require(ingress_receipt.get(key) == request.get(key), f"sv002_ingress_request_binding_mismatch:{key}")
    _require(ingress_receipt.get("credential_authority") == CREDENTIAL_AUTHORITY, "sv002_ingress_credential_authority_invalid")
    _require(ingress_receipt.get("claim_or_fence_minted") is False, "sv002_ingress_claim_or_fence_forbidden")
    _require(ingress_receipt.get("runtime_execution_attempted") is False, "sv002_ingress_runtime_already_claimed")

    stegos_root = find_stegos_root(control_root, env)
    _require(stegos_root is not None, "stegos_esrl_source_surface_missing")
    assert stegos_root is not None
    if str(stegos_root) not in sys.path:
        sys.path.insert(0, str(stegos_root))

    from stegos.ephemeral_runtime_lease import AuthorityBoundary, BatchingMode, LeaseMachine, LeaseProfile, LeaseRequest, LeaseState, RendezvousRequirement, RuntimeClass
    from stegos.sovereign_ephemeral_node_adapter import SovereignEphemeralNodeAdapter
    from stegos.universal_intr_public_profile import verify_public_intr_profile

    source_receipt_id = _digest_uri(dict(ingress_receipt))
    registry = {"schema": "stegverse.sv002-observation-esrl-consequence/v1", "destination": DESTINATION, "task_id": TASK_ID, "operation": CONSEQUENCE_ID, "implementation_ref": IMPLEMENTATION_REF, "observer_direct_relation_to_stegverse_002": False, "authority_effect": "NONE_REQUEST_ONLY"}
    registry_hash = _digest_uri(registry)
    lease_id = "SV002-OBS-ESRL-" + hashlib.sha256(f"{request['materialization_id']}|{source_receipt_id}|{CONSEQUENCE_ID}".encode("utf-8")).hexdigest()[:24]
    state_root_binding = f"SV002-OBSERVATION:{request['operation_id']}:{request['payload_hash']}"
    lease_request = LeaseRequest(lease_id=lease_id, trigger_id=str(request["materialization_id"]), operation=CONSEQUENCE_ID, implementation_ref=IMPLEMENTATION_REF, source_receipt_id=source_receipt_id, consequence_id=CONSEQUENCE_ID, consequence_registry_hash=registry_hash, generation=1, state_root_binding=state_root_binding, profile=LeaseProfile.INTAKE, runtime_class=RuntimeClass.EVENT_EPHEMERAL, rendezvous=RendezvousRequirement.REQUIRED, batching_mode=BatchingMode.SINGLE, persistent_host_required=False, participant_machine_required=False, developer_machine_required=False, stateful=True, max_operations=1, credential_mandate_required=False, authority=AuthorityBoundary(credential_authority=CREDENTIAL_AUTHORITY))
    lease_request.validate()
    adapter = SovereignEphemeralNodeAdapter(sovereign_source_root=control_root, runtime_base=intake_runtime_root / "esrl-sv002-observation-runtime", stegos_source_root=stegos_root)
    machine = LeaseMachine(lease_request)
    machine.transition(LeaseState.REQUESTED); machine.transition(LeaseState.ADMITTED); machine.transition(LeaseState.PROVISIONING)
    compute_lease = adapter.provision(lease_request)
    runtime = adapter.materialize(compute_lease, IMPLEMENTATION_REF)
    local = adapter.verify_local(runtime, IMPLEMENTATION_REF)
    _require(local.get("verified") is True, "sv002_esrl_local_runtime_identity_failed")
    machine.transition(LeaseState.LOCAL_READY)
    _require(hasattr(machine, "snapshot"), "canonical_runtime_lease_continuation_not_materialized")
    machine.open_after_local_verification()
    _require(machine.state == LeaseState.PUBLIC_VERIFYING, "sv002_canonical_lease_public_verification_state_required")
    runtime_root = Path(str(runtime.get("runtime_root", ""))).resolve()
    _require(runtime_root.is_dir(), "sv002_esrl_runtime_root_missing")
    snapshot_path = runtime_root / "receipts/sovereign-network/sv002-public-observation/canonical-runtime-lease.snapshot.json"
    _persist_lease_snapshot(snapshot_path, machine, LeaseMachine)

    public_profile = verify_public_intr_profile(
        "https://stegverse.org/intr/profile",
        required_profile="SV002:PublicObservation",
    )
    _require(public_profile.get("verified") is True, "sv002_public_intr_profile_not_verified")
    _require(
        public_profile.get("observation_origin") == "INDEPENDENT_PUBLIC_HTTPS",
        "sv002_public_intr_profile_observation_origin_invalid",
    )
    machine.transition(LeaseState.LEASE_OPEN)
    snapshot = _persist_lease_snapshot(snapshot_path, machine, LeaseMachine)
    snapshot_hash = _digest_uri(snapshot)
    evidence = {"schema": EVIDENCE_SCHEMA, "state": "LEASE_OPEN", "lease_id": lease_id, "lease_state": machine.state.value, "source_receipt_id": source_receipt_id, "materialization_id": request["materialization_id"], "request_hash": request["request_hash"], "transport_intent_hash": request["transport_intent_hash"], "payload_hash": request["payload_hash"], "operation_id": request["operation_id"], "packet_id": request["packet_id"], "implementation_ref": IMPLEMENTATION_REF, "consequence_id": CONSEQUENCE_ID, "consequence_registry_hash": registry_hash, "state_root_binding": state_root_binding, "runtime_class": RuntimeClass.EVENT_EPHEMERAL.value, "lease_profile": LeaseProfile.INTAKE.value, "runtime_root": str(runtime_root), "runtime_id": runtime.get("runtime_id"), "runtime_instantiated": True, "local_identity_verified": True, "canonical_runtime_lease_snapshot_ref": str(snapshot_path), "canonical_runtime_lease_snapshot_sha256": snapshot_hash, "canonical_runtime_lease_resume_required": True, "public_intr_profile_url": public_profile.get("observed_profile_url"), "public_intr_profile_schema": public_profile.get("profile_schema"), "public_intr_profile_sha256": public_profile.get("profile_sha256"), "public_intr_required_profile": public_profile.get("required_profile"), "public_intr_observation_origin": public_profile.get("observation_origin"), "receiver_ready_observed": False, "public_route_observed": True, "observation_round_trip_observed": False, "observer_direct_relation_to_stegverse_002": False, "g18_completion_required": False, "request_grants_execution_authority": False, "claim_or_fence_minted_by_bridge": False, "heartbeat_grants_execution_authority": False, "credential_authority": CREDENTIAL_AUTHORITY, "github_token_runtime_authority": "NONE", "authority_effect": "NONE_RUNTIME_AND_PUBLIC_PROFILE_OBSERVATION_ONLY"}
    return {"runtime_root": runtime_root, "evidence": evidence}
