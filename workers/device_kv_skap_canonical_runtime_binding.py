"""Canonical Runtime Lane domain binding for Device->KV->SKAP->KV->Device.

This module materializes one local-only StegOS EVENT_EPHEMERAL lease from the
actual retained StegBrowser Node plus the authentic Gateway DEVICE->KV sidecar.
It does not run the domain consequence itself and does not mint a
WorkerCoordinator claim/fence. The fenced worker later consumes the exact
LEASE_OPEN snapshot through StegOS' WorkerCoordinator->Canonical Runtime Lane
bridge.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

TASK_ID = "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001"
COSV = "50000000102000"
RETAINED_NODE_SCHEMA = "stegbrowser.resident-node-state/v2"
GATEWAY_SIDECAR_SCHEMA = "stegverse.service-gateway.device-kv-canonical-stage/v1"
BINDING_SCHEMA = "stegverse.device-kv-skap.canonical-runtime-domain-binding/v1"
EVIDENCE_SCHEMA = "stegverse.device-kv-skap.canonical-runtime-evidence/v1"
CLOSURE_SCHEMA = "stegverse.device-kv-skap.canonical-runtime-closure/v1"


class DeviceKVSKAPCanonicalRuntimeBindingError(ValueError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise DeviceKVSKAPCanonicalRuntimeBindingError(reason)


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DeviceKVSKAPCanonicalRuntimeBindingError(f"{label}_invalid_json:{path}") from exc
    _require(isinstance(value, dict), f"{label}_object_required")
    return value


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256_uri(value: Any) -> str:
    raw = value if isinstance(value, (bytes, bytearray)) else _canonical(value)
    return "sha256:" + hashlib.sha256(bytes(raw)).hexdigest()


def _write_once(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(dict(value), sort_keys=True, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != raw:
        raise DeviceKVSKAPCanonicalRuntimeBindingError(f"write_once_collision:{path}")
    path.write_text(raw, encoding="utf-8")
    _require(path.read_text(encoding="utf-8") == raw, f"write_readback_mismatch:{path}")


def normalize_retained_node(record: Mapping[str, Any]) -> dict[str, Any]:
    _require(record.get("schema") == RETAINED_NODE_SCHEMA, "retained_node_schema_invalid")
    _require(record.get("origin") == "STEGBROWSER_RESIDENT", "retained_node_origin_invalid")
    node_ref = record.get("nodeRef")
    genesis = record.get("genesisHash")
    profile = record.get("profileRef")
    source_hb = record.get("sourceDeviceHBReference")
    generation = record.get("stateGeneration")
    commitment = record.get("stateCommitment")
    history = record.get("transitionHistory")
    _require(isinstance(node_ref, str) and re.fullmatch(r"SV-NODE-[0-9a-f]{24}", node_ref) is not None, "retained_node_ref_invalid")
    _require(isinstance(genesis, str) and re.fullmatch(r"[0-9a-f]{64}", genesis) is not None, "retained_node_genesis_invalid")
    _require(isinstance(profile, str) and bool(profile), "retained_node_profile_required")
    _require(isinstance(source_hb, str) and bool(source_hb), "retained_node_source_hb_required")
    _require(isinstance(generation, int) and not isinstance(generation, bool) and generation >= 1, "retained_node_generation_invalid")
    _require(isinstance(commitment, str) and re.fullmatch(r"[0-9a-f]{64}", commitment) is not None, "retained_node_state_commitment_invalid")
    _require(isinstance(history, list), "retained_node_transition_history_required")
    return {
        "schema": RETAINED_NODE_SCHEMA,
        "node_ref": node_ref,
        "genesis_hash": genesis,
        "origin": "STEGBROWSER_RESIDENT",
        "profile_ref": profile,
        "source_device_hb_reference": source_hb,
        "state_generation": generation,
        "state_commitment": commitment,
        "transition_count": len(history),
        "source_record_hash": _sha256_uri(record),
        "credential_material_present": False,
        "authority_effect": "NONE_CONTINUITY_ONLY",
    }


def _install_stegos(stegos_root: Path) -> None:
    root = stegos_root.resolve()
    _require((root / "stegos" / "ephemeral_runtime_lease.py").is_file(), "stegos_lease_source_missing")
    _require((root / "stegos" / "sovereign_local_event_runtime.py").is_file(), "stegos_local_event_runtime_source_missing")
    _require((root / "stegos" / "universal_intr_materialization.py").is_file(), "stegos_intr_materialization_source_missing")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _validate_gateway_sidecar(sidecar: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    from stegos.universal_intr_transport import canonical_json, sha256_uri, validate_transport_intent

    _require(sidecar.get("schema") == GATEWAY_SIDECAR_SCHEMA, "gateway_sidecar_schema_invalid")
    _require(sidecar.get("credential_material_present") is False, "gateway_sidecar_credential_material_forbidden")
    _require(sidecar.get("authority_effect") == "NONE_EVIDENCE_ONLY", "gateway_sidecar_authority_invalid")
    payload = sidecar.get("payload")
    intent = sidecar.get("intent")
    receipt = sidecar.get("receipt")
    _require(isinstance(payload, Mapping), "gateway_sidecar_payload_required")
    _require(isinstance(intent, Mapping), "gateway_sidecar_intent_required")
    _require(isinstance(receipt, Mapping), "gateway_sidecar_receipt_required")
    validate_transport_intent(intent)
    _require(intent.get("source", {}).get("boundary") == "DEVICE_SYSTEM", "gateway_sidecar_source_invalid")
    _require(intent.get("destination", {}).get("boundary") == "KV", "gateway_sidecar_destination_invalid")
    payload_bytes = canonical_json(dict(payload)).encode("utf-8")
    _require(intent.get("payload_hash") == sha256_uri(payload_bytes), "gateway_sidecar_payload_hash_mismatch")
    _require(receipt.get("schema") == "stegverse.intr.hop_receipt/v1", "gateway_sidecar_receipt_schema_invalid")
    _require(receipt.get("packet_id") == intent.get("packet_id"), "gateway_sidecar_receipt_packet_mismatch")
    _require(receipt.get("payload_hash") == intent.get("payload_hash"), "gateway_sidecar_receipt_payload_mismatch")
    _require(receipt.get("transition_state") == "RECEIVED", "gateway_sidecar_receipt_not_received")
    _require(receipt.get("secret_plaintext_present") is False, "gateway_sidecar_receipt_plaintext_forbidden")
    _require(receipt.get("authority_transfer") is False, "gateway_sidecar_receipt_authority_transfer_forbidden")
    receipt_body = dict(receipt)
    claimed = receipt_body.pop("receipt_hash", None)
    _require(claimed == sha256_uri(receipt_body), "gateway_sidecar_receipt_hash_invalid")
    return payload, intent, receipt


@dataclass
class CanonicalRoundtripRuntime:
    runtime_root: Path
    machine: Any
    adapter: Any
    compute_lease: Mapping[str, Any]
    runtime: Mapping[str, Any]
    normalized_node: Mapping[str, Any]
    materialization_request: Mapping[str, Any]
    artifact_paths: Mapping[str, Path]


def materialize_roundtrip_runtime(
    *,
    control_root: Path,
    runtime_base: Path,
    stegos_root: Path,
    retained_node_path: Path,
    gateway_sidecar_path: Path,
) -> CanonicalRoundtripRuntime:
    _install_stegos(stegos_root)
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
    from stegos.sovereign_local_event_runtime import SovereignLocalEventRuntimeAdapter
    from stegos.universal_intr_materialization import build_materialization_request
    from stegos.universal_intr_transport import sha256_uri

    retained_raw = _load_json(retained_node_path, "retained_node")
    node = normalize_retained_node(retained_raw)
    sidecar = _load_json(gateway_sidecar_path, "gateway_sidecar")
    payload, intent, receipt = _validate_gateway_sidecar(sidecar)

    materialization = build_materialization_request(
        intent,
        payload_ref=f"{gateway_sidecar_path.resolve()}#payload",
        downstream_owner_ref=TASK_ID,
    )
    consequence_registry = {
        "schema": "stegverse.device-kv-skap.runtime-consequence/v1",
        "task_id": TASK_ID,
        "cosv": COSV,
        "operation": "device-kv-skap-roundtrip",
        "implementation_ref": "StegVerse-Labs/.github/workers/run_device_kv_skap_roundtrip_worker.py",
        "transition_authority": "Interlock/InTr",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    lease_basis = f"{node['node_ref']}|{node['state_commitment']}|{receipt['receipt_hash']}|{materialization['materialization_id']}"
    lease_id = "DKS-CRL-" + hashlib.sha256(lease_basis.encode("utf-8")).hexdigest()[:24]
    state_root_binding = sha256_uri({
        "node_ref": node["node_ref"],
        "node_state_commitment": node["state_commitment"],
        "device_kv_receipt_hash": receipt["receipt_hash"],
        "materialization_request_hash": materialization["request_hash"],
    })
    request = LeaseRequest(
        lease_id=lease_id,
        trigger_id=str(materialization["materialization_id"]),
        operation="device-kv-skap-roundtrip",
        implementation_ref="StegVerse-Labs/.github/workers/run_device_kv_skap_roundtrip_worker.py",
        source_receipt_id=str(receipt["receipt_hash"]),
        consequence_id="device-kv-skap-roundtrip",
        consequence_registry_hash=sha256_uri(consequence_registry),
        generation=int(node["state_generation"]),
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
        authority=AuthorityBoundary(credential_authority="TV/TVC"),
    )
    request.validate()

    adapter = SovereignLocalEventRuntimeAdapter(
        sovereign_source_root=control_root.resolve(),
        runtime_base=runtime_base.resolve(),
    )
    machine = LeaseMachine(request)
    machine.transition(LeaseState.REQUESTED)
    machine.transition(LeaseState.ADMITTED)
    machine.transition(LeaseState.PROVISIONING)
    compute_lease = adapter.provision(request)
    runtime = adapter.materialize(compute_lease, request.implementation_ref)
    local = adapter.verify_local(runtime, request.implementation_ref)
    _require(local.get("verified") is True, "canonical_local_runtime_identity_not_verified")
    machine.transition(LeaseState.LOCAL_READY)
    machine.open_after_local_verification()
    _require(machine.state == LeaseState.LEASE_OPEN, "canonical_local_runtime_lease_not_open")

    runtime_root = Path(str(runtime.get("runtime_root", ""))).resolve()
    _require(runtime_root.is_dir(), "canonical_runtime_root_missing")
    control_dir = runtime_root / "control" / "device-kv-skap-domain"
    paths = {
        "retained_node": control_dir / "retained-node.normalized.json",
        "materialization": control_dir / "materialization-request.json",
        "lease_snapshot": control_dir / "lease-open.snapshot.json",
        "binding": control_dir / "binding.json",
        "bridge_receipt": runtime_root / "receipts" / "sovereign-host" / "device-kv-skap-roundtrip" / "canonical-runtime-bridge.json",
        "domain_evidence": runtime_root / "receipts" / "sovereign-host" / "device-kv-skap-roundtrip" / "canonical-runtime-evidence.json",
        "closure": runtime_root / "receipts" / "sovereign-host" / "device-kv-skap-roundtrip" / "canonical-runtime-closure.json",
    }
    _write_once(paths["retained_node"], node)
    _write_once(paths["materialization"], materialization)
    snapshot = machine.snapshot()
    _write_once(paths["lease_snapshot"], snapshot)
    binding = {
        "schema": BINDING_SCHEMA,
        "state": "CANONICAL_RUNTIME_LEASE_OPEN",
        "task_id": TASK_ID,
        "cosv": COSV,
        "runtime_root": str(runtime_root),
        "runtime_id": runtime.get("runtime_id"),
        "lease_id": request.lease_id,
        "lease_state": machine.state.value,
        "runtime_class": request.runtime_class.value,
        "rendezvous_requirement": request.rendezvous.value,
        "node_ref": node["node_ref"],
        "node_state_generation": node["state_generation"],
        "node_state_commitment": node["state_commitment"],
        "device_kv_receipt_hash": receipt["receipt_hash"],
        "materialization_request_hash": materialization["request_hash"],
        "local_identity_verification": dict(local),
        "requires_other_machine": False,
        "persistent_host_required": False,
        "worker_claim_observed": False,
        "transition_authority": "Interlock/InTr",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_RUNTIME_BINDING_ONLY",
    }
    _write_once(paths["binding"], binding)
    return CanonicalRoundtripRuntime(
        runtime_root=runtime_root,
        machine=machine,
        adapter=adapter,
        compute_lease=compute_lease,
        runtime=runtime,
        normalized_node=node,
        materialization_request=materialization,
        artifact_paths=paths,
    )


def close_roundtrip_runtime(
    context: CanonicalRoundtripRuntime,
    *,
    terminal_evidence: Mapping[str, Any],
    bridge_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    from stegos.ephemeral_runtime_lease import LeaseState

    _require(terminal_evidence.get("state") == "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED", "terminal_roundtrip_evidence_required")
    _require(bridge_receipt.get("state") == "CANONICAL_RUNTIME_CAPABILITY_EXECUTION_OBSERVED", "canonical_runtime_bridge_execution_required")
    _require(bridge_receipt.get("runtime_lease_id") == context.machine.request.lease_id, "bridge_runtime_lease_binding_mismatch")
    _require(bridge_receipt.get("node_ref") == context.normalized_node["node_ref"], "bridge_node_binding_mismatch")
    _require(bridge_receipt.get("result", {}).get("status") == "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED", "bridge_terminal_status_invalid")

    context.machine.record_transition()
    context.machine.queue_return()
    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "state": "EVIDENCE_RETAINED_PRE_RELEASE",
        "task_id": TASK_ID,
        "cosv": COSV,
        "lease_id": context.machine.request.lease_id,
        "runtime_id": context.runtime.get("runtime_id"),
        "runtime_class": context.machine.request.runtime_class.value,
        "node_ref": context.normalized_node["node_ref"],
        "node_state_generation": context.normalized_node["state_generation"],
        "node_state_commitment": context.normalized_node["state_commitment"],
        "worker_claim_id": bridge_receipt.get("worker_claim_id"),
        "worker_fence": bridge_receipt.get("worker_fence"),
        "materialization_request_hash": context.materialization_request["request_hash"],
        "bridge_receipt_hash": bridge_receipt.get("receipt_hash"),
        "terminal_worker_checkpoint_sha256": terminal_evidence.get("canonical_checkpoint_sha256"),
        "terminal_worker_result_state": terminal_evidence.get("state"),
        "lease_history": [state.value for state in context.machine.history],
        "evidence_retained_before_release": True,
        "requires_other_machine": False,
        "persistent_host_required": False,
        "transition_authority": "Interlock/InTr",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_RUNTIME_EVIDENCE_ONLY",
    }
    evidence = {**evidence, "evidence_hash": _sha256_uri(evidence)}
    _write_once(context.artifact_paths["domain_evidence"], evidence)
    context.machine.export_evidence()
    context.machine.transition(LeaseState.RELEASING)
    release = context.adapter.release(context.compute_lease)
    context.machine.transition(LeaseState.LEASE_CLOSED)
    closure = {
        "schema": CLOSURE_SCHEMA,
        "state": "LEASE_CLOSED",
        "task_id": TASK_ID,
        "cosv": COSV,
        "lease_id": context.machine.request.lease_id,
        "runtime_id": context.runtime.get("runtime_id"),
        "evidence_hash": evidence["evidence_hash"],
        "bridge_receipt_hash": bridge_receipt.get("receipt_hash"),
        "release": dict(release),
        "lease_history": [state.value for state in context.machine.history],
        "evidence_retained_before_release": True,
        "requires_other_machine": False,
        "persistent_host_required": False,
        "credential_authority": "TV/TVC",
        "transition_authority": "Interlock/InTr",
        "authority_effect": "NONE_CLOSURE_ONLY",
    }
    closure = {**closure, "closure_hash": _sha256_uri(closure)}
    _write_once(context.artifact_paths["closure"], closure)
    return {"evidence": evidence, "closure": closure}
