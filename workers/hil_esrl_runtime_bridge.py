from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from workers.stegos_sovereign_relay_bridge import find_stegos_root

CREDENTIAL_AUTHORITY = "TV/TVC"
HIL_IMPLEMENTATION_REF = "StegVerse-org/LLM-adapter@ad1a7c3f8bb727d1007f254930d9a77df0bfa94f"
HIL_CONSEQUENCE_ID = "materialize_hil_sovereign_receiver"
EVIDENCE_SCHEMA = "stegverse.hil-esrl-runtime-materialization/v1"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _digest_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else _canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def _receipt_identity(receipt: Mapping[str, Any]) -> str:
    return _digest_uri(dict(receipt))


def materialize_hil_runtime(
    *,
    control_root: Path,
    intake_runtime_root: Path,
    request: Mapping[str, Any],
    ingress_receipt: Mapping[str, Any],
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Materialize the sovereign runtime substrate required by one admitted HIL event.

    This bridge deliberately stops at ESRL LOCAL_READY. It does not claim the HIL
    public HTTPS rendezvous, receiver READY, custody, or TVC lifecycle. Those are
    downstream observations produced by the HIL receiver path itself.
    """

    _require(ingress_receipt.get("schema") == "stegverse.hil-intr-materialization-ingress/v1", "hil_ingress_receipt_schema_invalid")
    _require(ingress_receipt.get("state") == "INGRESS_ADMITTED", "hil_ingress_not_admitted")
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "operation_id", "packet_id"):
        _require(ingress_receipt.get(key) == request.get(key), f"hil_ingress_request_binding_mismatch:{key}")
    _require(ingress_receipt.get("credential_authority") == CREDENTIAL_AUTHORITY, "hil_ingress_credential_authority_invalid")
    _require(ingress_receipt.get("claim_or_fence_minted") is False, "hil_ingress_claim_or_fence_forbidden")
    _require(ingress_receipt.get("runtime_execution_attempted") is False, "hil_ingress_runtime_already_claimed")

    stegos_root = find_stegos_root(control_root, env)
    _require(stegos_root is not None, "stegos_esrl_source_surface_missing")
    assert stegos_root is not None
    if str(stegos_root) not in sys.path:
        sys.path.insert(0, str(stegos_root))

    from stegos.ephemeral_runtime_lease import (
        AuthorityBoundary,
        BatchingMode,
        LeaseMachine,
        LeaseProfile,
        LeaseRequest,
        LeaseState,
        RendezvousRequirement,
        RuntimeClass,
    )
    from stegos.sovereign_ephemeral_node_adapter import SovereignEphemeralNodeAdapter

    source_receipt_id = _receipt_identity(ingress_receipt)
    consequence_registry = {
        "schema": "stegverse.hil-esrl-consequence/v1",
        "destination": {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "HIL:Ingress"},
        "task_id": "SHWP-HIL-SOVEREIGN-RECEIVER-001",
        "operation": HIL_CONSEQUENCE_ID,
        "implementation_ref": HIL_IMPLEMENTATION_REF,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    consequence_registry_hash = _digest_uri(consequence_registry)
    lease_id = "HIL-ESRL-" + hashlib.sha256(
        f"{request['materialization_id']}|{source_receipt_id}|{HIL_CONSEQUENCE_ID}".encode("utf-8")
    ).hexdigest()[:24]
    state_root_binding = f"HIL-CUSTODY:{request['operation_id']}:{request['payload_hash']}"

    lease_request = LeaseRequest(
        lease_id=lease_id,
        trigger_id=str(request["materialization_id"]),
        operation=HIL_CONSEQUENCE_ID,
        implementation_ref=HIL_IMPLEMENTATION_REF,
        source_receipt_id=source_receipt_id,
        consequence_id=HIL_CONSEQUENCE_ID,
        consequence_registry_hash=consequence_registry_hash,
        generation=1,
        state_root_binding=state_root_binding,
        profile=LeaseProfile.INTAKE,
        runtime_class=RuntimeClass.EVENT_EPHEMERAL,
        rendezvous=RendezvousRequirement.REQUIRED,
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
        runtime_base=intake_runtime_root / "esrl-hil-runtime",
        stegos_source_root=stegos_root,
    )
    machine = LeaseMachine(lease_request)
    machine.transition(LeaseState.REQUESTED)
    machine.transition(LeaseState.ADMITTED)
    machine.transition(LeaseState.PROVISIONING)
    compute_lease = adapter.provision(lease_request)
    runtime = adapter.materialize(compute_lease, HIL_IMPLEMENTATION_REF)
    local = adapter.verify_local(runtime, HIL_IMPLEMENTATION_REF)
    _require(local.get("verified") is True, "hil_esrl_local_runtime_identity_failed")
    machine.transition(LeaseState.LOCAL_READY)

    runtime_root = Path(str(runtime.get("runtime_root", ""))).resolve()
    _require(runtime_root.is_dir(), "hil_esrl_runtime_root_missing")
    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "state": "LOCAL_READY",
        "lease_id": lease_id,
        "lease_state": machine.state.value,
        "source_receipt_id": source_receipt_id,
        "source_ingress_schema": ingress_receipt["schema"],
        "source_ingress_state": ingress_receipt["state"],
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "transport_intent_hash": request["transport_intent_hash"],
        "payload_hash": request["payload_hash"],
        "operation_id": request["operation_id"],
        "packet_id": request["packet_id"],
        "implementation_ref": HIL_IMPLEMENTATION_REF,
        "consequence_id": HIL_CONSEQUENCE_ID,
        "consequence_registry_hash": consequence_registry_hash,
        "state_root_binding": state_root_binding,
        "runtime_class": RuntimeClass.EVENT_EPHEMERAL.value,
        "lease_profile": LeaseProfile.INTAKE.value,
        "runtime_root": str(runtime_root),
        "runtime_id": runtime.get("runtime_id"),
        "runtime_instantiated": True,
        "local_identity_verified": True,
        "hil_public_https_rendezvous_observed": False,
        "receiver_ready_observed": False,
        "hil_custody_observed": False,
        "tvc_lifecycle_observed": False,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted_by_bridge": False,
        "heartbeat_grants_execution_authority": False,
        "credential_authority": CREDENTIAL_AUTHORITY,
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_RUNTIME_MATERIALIZATION_ONLY",
    }
    return {"runtime_root": runtime_root, "evidence": evidence}
