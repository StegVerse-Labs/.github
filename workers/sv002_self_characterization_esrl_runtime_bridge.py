from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from workers.stegos_sovereign_relay_bridge import find_stegos_root

CREDENTIAL_AUTHORITY = "TV/TVC"
IMPLEMENTATION_REF = "STEGVERSE-002-EXPERIMENT-RERUN-001:SV002_SELF_CHARACTERIZATION"
CONSEQUENCE_ID = "execute_sv002_self_characterization_rerun"
EVIDENCE_SCHEMA = "stegverse.sv002-self-characterization-esrl-runtime-materialization/v1"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "SV002:SelfCharacterization"}
TASK_ID = "STEGVERSE-002-EXPERIMENT-RERUN-001"
COSV = "50000000107000"
INGRESS_SCHEMA = "stegverse.sv002-self-characterization-intr-materialization-ingress/v1"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def materialize_sv002_self_characterization_runtime(
    *,
    control_root: Path,
    intake_runtime_root: Path,
    request: Mapping[str, Any],
    ingress_receipt: Mapping[str, Any],
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Materialize one admitted self-characterization event on the existing ESRL substrate."""
    require(ingress_receipt.get("schema") == INGRESS_SCHEMA, "sv002_rerun_ingress_receipt_schema_invalid")
    require(ingress_receipt.get("state") == "INGRESS_ADMITTED", "sv002_rerun_ingress_not_admitted")
    require(request.get("destination") == DESTINATION, "sv002_rerun_destination_invalid")
    require(request.get("goal_task_id") == TASK_ID, "sv002_rerun_goal_binding_invalid")
    require(request.get("cosv_task_vector") == COSV, "sv002_rerun_cosv_binding_invalid")
    require(request.get("invocation_count") == 1, "sv002_rerun_invocation_count_invalid")
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "operation_id", "packet_id"):
        require(ingress_receipt.get(key) == request.get(key), f"sv002_rerun_ingress_binding_mismatch:{key}")
    require(ingress_receipt.get("goal_task_id") == TASK_ID, "sv002_rerun_ingress_goal_invalid")
    require(ingress_receipt.get("cosv_task_vector") == COSV, "sv002_rerun_ingress_cosv_invalid")
    require(ingress_receipt.get("invocation_count") == 1, "sv002_rerun_ingress_invocation_count_invalid")
    require(ingress_receipt.get("claim_or_fence_minted") is False, "sv002_rerun_ingress_claim_forbidden")
    require(ingress_receipt.get("runtime_execution_attempted") is False, "sv002_rerun_ingress_runtime_already_claimed")
    require(ingress_receipt.get("credential_authority") == CREDENTIAL_AUTHORITY, "sv002_rerun_ingress_credential_authority_invalid")

    stegos_root = find_stegos_root(control_root, env)
    require(stegos_root is not None, "stegos_esrl_source_surface_missing")
    assert stegos_root is not None
    if str(stegos_root) not in sys.path:
        sys.path.insert(0, str(stegos_root))

    from stegos.ephemeral_runtime_lease import (
        AuthorityBoundary, BatchingMode, LeaseMachine, LeaseProfile, LeaseRequest,
        LeaseState, RendezvousRequirement, RuntimeClass,
    )
    from stegos.sovereign_ephemeral_node_adapter import SovereignEphemeralNodeAdapter

    source_receipt_id = digest_uri(dict(ingress_receipt))
    registry = {
        "schema": "stegverse.sv002-self-characterization-esrl-consequence/v1",
        "destination": DESTINATION,
        "task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "operation": CONSEQUENCE_ID,
        "implementation_ref": IMPLEMENTATION_REF,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    registry_hash = digest_uri(registry)
    lease_id = "SV002-RERUN-ESRL-" + hashlib.sha256(
        f"{request['materialization_id']}|{source_receipt_id}|{CONSEQUENCE_ID}".encode("utf-8")
    ).hexdigest()[:24]
    state_root_binding = f"SV002-RERUN:{request['operation_id']}:{request['payload_hash']}"

    lease_request = LeaseRequest(
        lease_id=lease_id,
        trigger_id=str(request["materialization_id"]),
        operation=CONSEQUENCE_ID,
        implementation_ref=IMPLEMENTATION_REF,
        source_receipt_id=source_receipt_id,
        consequence_id=CONSEQUENCE_ID,
        consequence_registry_hash=registry_hash,
        generation=1,
        state_root_binding=state_root_binding,
        profile=LeaseProfile.INTAKE,
        runtime_class=RuntimeClass.EVENT_EPHEMERAL,
        rendezvous=RendezvousRequirement.NOT_REQUIRED,
        batching_mode=BatchingMode.SINGLE,
        persistent_host_required=False,
        participant_machine_required=False,
        developer_machine_required=False,
        stateful=True,
        max_operations=1,
        credential_mandate_required=False,
        authority=AuthorityBoundary(credential_authority=CREDENTIAL_AUTHORITY),
    )
    lease_request.validate()

    adapter = SovereignEphemeralNodeAdapter(
        sovereign_source_root=control_root,
        runtime_base=intake_runtime_root / "esrl-sv002-self-characterization-runtime",
        stegos_source_root=stegos_root,
    )
    machine = LeaseMachine(lease_request)
    machine.transition(LeaseState.REQUESTED)
    machine.transition(LeaseState.ADMITTED)
    machine.transition(LeaseState.PROVISIONING)
    compute_lease = adapter.provision(lease_request)
    runtime = adapter.materialize(compute_lease, IMPLEMENTATION_REF)
    local = adapter.verify_local(runtime, IMPLEMENTATION_REF)
    require(local.get("verified") is True, "sv002_rerun_esrl_local_runtime_identity_failed")
    machine.transition(LeaseState.LOCAL_READY)
    machine.open_after_local_verification()
    require(machine.state == LeaseState.LEASE_OPEN, "sv002_rerun_esrl_lease_open_required")

    runtime_root = Path(str(runtime.get("runtime_root", ""))).resolve()
    require(runtime_root.is_dir(), "sv002_rerun_esrl_runtime_root_missing")
    snapshot = machine.snapshot()
    snapshot_path = runtime_root / "receipts/sovereign-network/sv002-experiment-rerun/canonical-runtime-lease.snapshot.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
    if snapshot_path.exists():
        require(snapshot_path.read_text(encoding="utf-8") == rendered, "sv002_rerun_lease_snapshot_collision")
    else:
        snapshot_path.write_text(rendered, encoding="utf-8")

    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "state": "LEASE_OPEN",
        "lease_id": lease_id,
        "lease_state": machine.state.value,
        "source_receipt_id": source_receipt_id,
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "goal_task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "invocation_count": 1,
        "implementation_ref": IMPLEMENTATION_REF,
        "consequence_id": CONSEQUENCE_ID,
        "consequence_registry_hash": registry_hash,
        "state_root_binding": state_root_binding,
        "runtime_class": RuntimeClass.EVENT_EPHEMERAL.value,
        "lease_profile": LeaseProfile.INTAKE.value,
        "runtime_root": str(runtime_root),
        "runtime_id": runtime.get("runtime_id"),
        "runtime_instantiated": True,
        "local_identity_verified": True,
        "canonical_runtime_lease_snapshot_ref": str(snapshot_path),
        "canonical_runtime_lease_snapshot_sha256": digest_uri(snapshot),
        "same_device_execution_required": True,
        "requires_other_machine": False,
        "persistent_host_required": False,
        "public_rendezvous_required": False,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted_by_bridge": False,
        "heartbeat_grants_execution_authority": False,
        "credential_authority": CREDENTIAL_AUTHORITY,
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_RUNTIME_MATERIALIZATION_ONLY",
    }
    return {"runtime_root": runtime_root, "evidence": evidence}
