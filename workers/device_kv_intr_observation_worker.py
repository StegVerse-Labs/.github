#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import os
import socket
import socketserver
import struct
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path.cwd().resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from heartbeat_runtime.independent_oscillator import current_reference
from heartbeat_runtime.intr_derived_carrier import derive_intr_carrier_signal, recover_intr_packet_bytes
from heartbeat_runtime.intr_subsignal_runtime import (
    default_heartbeat_runtime_root,
    persist_local_intr_subsignal,
)
TASK_ID = "SHWP-DEVICE-KV-INTR-OBSERVATION-001"
PARENT_TASK_ID = "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001"
PARENT_RECEIPT = ROOT / "receipts" / "stegos-sovereign-relay" / f"{PARENT_TASK_ID}.json"
RECEIPT_ROOT = ROOT / "receipts" / "device-kv-intr"
RECEIPT = RECEIPT_ROOT / f"{TASK_ID}.json"
ENDPOINT_RECEIPTS = RECEIPT_ROOT / "endpoint-receipts"
TRANSPORT_RECEIPTS = RECEIPT_ROOT / "transport-receipts"
CARRIER_SIGNALS = RECEIPT_ROOT / "carrier-signals"
EVENT_REQUEST_DIR = ROOT / "intr-materialization"
EVENT_INGRESS_DIR = ROOT / "receipts" / "sovereign-network" / "device-kv-intr-ingress"
EVENT_MATERIALIZATION_ENV = "STEGVERSE_DEVICE_KV_INTR_MATERIALIZATION_ID"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_uri(value: Any) -> str:
    if isinstance(value, (bytes, bytearray)):
        data = bytes(value)
    elif isinstance(value, str):
        data = value.encode("utf-8")
    else:
        data = canonical_json(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(dict(value), handle, indent=2, sort_keys=True)
        handle.write("\n")
        tmp = handle.name
    os.replace(tmp, path)


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_canonical_device_kv_connector(stegos_root: Path):
    registry = stegos_root / "specs/universal-intr-connector-profiles.v1.json"
    backbone = stegos_root / "stegos/intr_backbone.py"
    if not registry.is_file() or not backbone.is_file():
        raise RuntimeError("canonical StegOS InTr connector source missing")
    root_text = str(stegos_root)
    inserted = False
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
        inserted = True
    try:
        module = importlib.import_module("stegos.intr_backbone")
        origin = Path(module.__file__).resolve()
        if stegos_root.resolve() not in origin.parents:
            raise RuntimeError("loaded stegos.intr_backbone does not originate from admitted local StegOS root")
        connector = module.connector_from_registry(registry, "device-kv")
        if connector.profile.profile_id != "device-kv":
            raise RuntimeError("canonical device-kv connector profile mismatch")
        if connector.profile.payload_schema != "kv.interlock.request.v1":
            raise RuntimeError("canonical device-kv payload schema mismatch")
        return connector
    finally:
        if inserted:
            try:
                sys.path.remove(root_text)
            except ValueError:
                pass


def find_source_root(env_name: str, repo_name: str, required: str) -> Path | None:
    candidates: list[Path] = []
    explicit = os.environ.get(env_name)
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend([
        ROOT.parent / repo_name,
        ROOT / repo_name,
        ROOT / "StegVerse-Labs" / repo_name,
        ROOT.parent.parent / repo_name,
    ])
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if (resolved / required).is_file():
            return resolved
    return None



def event_materialization_basis() -> dict[str, Any] | None:
    mid = os.environ.get(EVENT_MATERIALIZATION_ENV)
    if not mid:
        return None
    request = load_json(EVENT_REQUEST_DIR / f"{mid}.json")
    ingress = load_json(EVENT_INGRESS_DIR / f"{mid}.json")
    if not request or not ingress:
        return None
    expected = {
        "schema":"stegverse.universal-intr-materialization-request/v1",
        "state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
        "destination":{"boundary":"KV","subsystem":"KnowledgeVault:Interlock"},
        "downstream_owner_ref":"StegVerse-Labs/continuity-vault-kit#79",
        "event_triggered":True,"always_on_receiver_required":False,
        "second_user_device_required":False,
        "receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "request_grants_execution_authority":False,"claim_or_fence_minted":False,
        "transport_grants_execution_authority":False,"credential_authority":"TV/TVC",
        "github_token_runtime_authority":"NONE","authority_transfer":False,
    }
    if any(request.get(k) != v for k,v in expected.items()) or request.get("boundary_path") != ["DEVICE_SYSTEM","KV"]:
        return None
    if ingress.get("schema") != "stegverse.device-kv-intr-materialization-ingress/v1" or ingress.get("state") != "INGRESS_ADMITTED":
        return None
    for key in ("materialization_id","request_hash","transport_intent_hash","payload_hash","operation_id","packet_id"):
        if ingress.get(key) != request.get(key):
            return None
    if ingress.get("claim_or_fence_minted") is not False or ingress.get("credential_authority") != "TV/TVC":
        return None
    source_ref = ingress.get("node_id") or ingress.get("interlock_id") or request.get("transport_intent_hash")
    if not isinstance(source_ref,str) or not source_ref:
        return None
    return {
        "mode":"EVENT_MATERIALIZATION_INGRESS",
        "continuity_id":"event-"+mid,
        "state_root":"kv-event://"+mid,
        "source_identity_ref":"intr-event://"+source_ref,
        "next_boundary_identity_ref":"kv-event://"+mid,
        "prior_receipt_hash":sha256_uri(ingress),
        "materialization_id":mid,
        "transport_intent_hash":request.get("transport_intent_hash"),
        "queued_payload_hash":request.get("payload_hash"),
    }

def blocker(problem: str, action: str, release: str) -> dict[str, Any]:
    return {
        "dependency_class": "INTERNAL_CAPABILITY",
        "problem_statement": problem,
        "solution_required": True,
        "may_remain_blocked": False,
        "next_solution_action": action,
        "machine_observable_release_condition": release,
        "physical_additional_machine_required": False,
        "third_party_runtime_required": False,
        "github_token_required": False,
        "non_tv_tvc_secret_or_token_required": False,
        "human_action_required": False,
    }


def worker_response(state: str, transition: str, epoch: int, blocked: dict[str, Any] | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "DEVICE_KV_INTR_OBSERVED",
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 8,
        "checkpoint_ref": str(RECEIPT.relative_to(ROOT)),
        "evidence_refs": [
            str(RECEIPT.relative_to(ROOT)),
            str(PARENT_RECEIPT.relative_to(ROOT)),
            "workers/device_kv_intr_observation_worker.py",
            "docs/DEVICE_KV_INTR_SOVEREIGN_OBSERVATION_MIRROR_HANDOFF.md",
        ],
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 2,
            "external_cost_usd": 0,
            "task_class": "device_kv_intr_observation",
        },
    }
    if blocked is not None:
        value["blocker"] = blocked
    return value


def write_blocked(base: dict[str, Any], transition: str, problem: str, action: str, release: str, epoch: int) -> int:
    blocked = blocker(problem, action, release)
    atomic_write(RECEIPT, {**base, "state": "ACTIVE", "transition_id": transition, "blocker": blocked})
    json.dump(worker_response("ACTIVE", transition, epoch, blocked), sys.stdout)
    print()
    return 0


def send_frame(sock: socket.socket, payload: bytes) -> None:
    sock.sendall(struct.pack("!Q", len(payload)) + payload)


def recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("carrier closed before exact frame completed")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_frame(sock: socket.socket, max_bytes: int = 1024 * 1024) -> bytes:
    size = struct.unpack("!Q", recv_exact(sock, 8))[0]
    if size < 1 or size > max_bytes:
        raise ValueError("bounded carrier frame size invalid")
    return recv_exact(sock, size)


def build_transport_receipt(*, receipt_id: str, packet_id: str, direction: str, from_role: str, to_role: str,
                            operation_hash: str, payload_hash: str, prior_receipt_hash: str | None,
                            boundary_identity_ref: str, recorded_at: str | None = None) -> dict[str, Any]:
    body = {
        "schema": "stegverse.intr.hop_receipt/v1",
        "receipt_id": receipt_id,
        "packet_id": packet_id,
        "hop_index": 1,
        "direction": direction,
        "from_role": from_role,
        "to_role": to_role,
        "operation_hash": operation_hash,
        "payload_hash": payload_hash,
        "prior_receipt_hash": prior_receipt_hash,
        "boundary_identity_ref": boundary_identity_ref,
        "boundary_verification": "VERIFIED",
        "transition_state": "RECEIVED",
        "secret_plaintext_present": False,
        "authority_transfer": False,
        "recorded_at": recorded_at or now_iso(),
    }
    return {**body, "receipt_hash": sha256_uri(body)}


def validate_transport_receipt(receipt: Mapping[str, Any], *, direction: str, from_role: str, to_role: str,
                               payload_hash: str, prior: str | None) -> None:
    fields = {
        "schema", "receipt_id", "packet_id", "hop_index", "direction", "from_role", "to_role",
        "operation_hash", "payload_hash", "prior_receipt_hash", "boundary_identity_ref",
        "boundary_verification", "transition_state", "secret_plaintext_present", "authority_transfer",
        "recorded_at", "receipt_hash",
    }
    if set(receipt) != fields:
        raise ValueError("noncanonical transport receipt fields")
    if receipt.get("schema") != "stegverse.intr.hop_receipt/v1":
        raise ValueError("transport receipt schema mismatch")
    if receipt.get("hop_index") != 1 or receipt.get("direction") != direction:
        raise ValueError("transport receipt direction mismatch")
    if receipt.get("from_role") != from_role or receipt.get("to_role") != to_role:
        raise ValueError("transport receipt boundary mismatch")
    if receipt.get("payload_hash") != payload_hash or receipt.get("prior_receipt_hash") != prior:
        raise ValueError("transport receipt identity mismatch")
    if receipt.get("boundary_verification") != "VERIFIED" or receipt.get("transition_state") != "RECEIVED":
        raise ValueError("transport boundary was not verified/received")
    if receipt.get("secret_plaintext_present") is not False or receipt.get("authority_transfer") is not False:
        raise ValueError("transport receipt authority/plaintext violation")
    body = dict(receipt)
    claimed = body.pop("receipt_hash")
    if claimed != sha256_uri(body):
        raise ValueError("transport receipt hash mismatch")


def build_hb_carrier_signal(*, packet_id: str, payload_hash: str, packet_bytes: bytes, receipt_hash: str,
                            boundary_from: str, boundary_to: str, now_ns: int | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    sample_ns = time.time_ns() if now_ns is None else int(now_ns)
    reference = current_reference(now_ns=sample_ns)
    normalized_receipt = str(receipt_hash or "")
    if normalized_receipt.startswith("sha256:"):
        normalized_receipt = normalized_receipt[7:]
    signal = derive_intr_carrier_signal(
        packet_id=packet_id,
        payload_hash=payload_hash,
        sampled_unix_ms=sample_ns // 1_000_000,
        packet_bytes=packet_bytes,
        intr_transport_profile="stegverse.universal-intr.adjacent-hop/v1",
        boundary_from=boundary_from,
        boundary_to=boundary_to,
        packet_receipt_hash=normalized_receipt,
    )
    if signal["carrier"]["heartbeat_epoch"] != reference["epoch"] or signal["carrier"]["heartbeat_reference"] != reference["heartbeat_id"]:
        raise ValueError("HB-derived carrier/reference sampling mismatch")
    if recover_intr_packet_bytes(signal) != packet_bytes:
        raise ValueError("HB-derived carrier exact packet recovery failed")
    return signal, reference


def controlled_request(template: Mapping[str, Any], continuity_id: str, fence: int) -> dict[str, Any]:
    request = dict(template)
    request["request_id"] = "DEVICE-KV-INTR-" + hashlib.sha256(f"{continuity_id}:{fence}".encode()).hexdigest()[:24]
    request["requester"] = {"module": "StegOS", "component": "DEVICE_KV_INTR_OBSERVER"}
    return request


def request_envelope(request: Mapping[str, Any], continuity_id: str, state_root: str, *, source_identity_ref: str | None = None, next_boundary_identity_ref: str | None = None, prior_receipt_hash: str | None = None) -> dict[str, Any]:
    payload_hash = sha256_uri(request)
    packet_seed = sha256_uri({"request_id": request["request_id"], "payload_hash": payload_hash})
    return {
        "schema": "stegverse.kv-interlock.intr-envelope/v1",
        "protocol": "InTr",
        "packet_id": "KV-INTR-" + packet_seed[7:31],
        "direction": "REQUEST",
        "source_role": "DEVICE",
        "next_role": "KV",
        "request_id": request["request_id"],
        "operation": request["operation"],
        "payload_schema_version": "kv.interlock.request.v1",
        "payload_hash": payload_hash,
        "sealed_material_ref": "sealed://device-kv-intr/" + packet_seed[7:39],
        "prior_receipt_hash": prior_receipt_hash,
        "authority": {
            "authority_transfer": False,
            "transport_grants_execution_authority": False,
            "model_output_grants_execution_authority": False,
            "credential_authority_effect": "NONE",
        },
        "boundary_proof": {
            "required": True,
            "source_identity_ref": source_identity_ref or f"stegos-node://{continuity_id}",
            "next_boundary_identity_ref": next_boundary_identity_ref or state_root,
            "verification_state": "VERIFIED",
        },
        "receipt_policy": {
            "receipt_required": True,
            "receipt_contains_payload_plaintext": False,
            "receipt_chain_required": True,
            "ambiguous_disposition": "FAIL_CLOSED",
        },
    }


def main() -> int:
    invocation = json.load(sys.stdin)
    task = invocation.get("task") or {}
    handoff = invocation.get("handoff") or {}
    epoch = invocation.get("heartbeat_epoch")
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1" or task.get("task_id") != TASK_ID or not isinstance(epoch, int):
        return 2
    claim_id = task.get("claim_id")
    fence = (task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int):
        return 3

    base = {
        "schema": "stegverse.device-kv-intr.canonical-observation-evidence/v1",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "heartbeat_epoch": epoch,
        "claim_id": claim_id,
        "fencing_token": fence,
        "capability_type": "DEVICE_KV_INTR",
        "carrier": "LOOPBACK_TCP",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "github_token_used": False,
        "non_tv_tvc_secret_or_token_used": False,
        "heartbeat_grants_execution_authority": False,
        "physical_additional_machine_required": False,
        "third_party_runtime_required": False,
        "participant_or_personal_data_used": False,
        "provider_operation_authorized": False,
        "canonical_kv_mutation": False,
        "route_admitted": False,
        "public_ingress_claimed": False,
        "runtime_activation_claimed": False,
        "authority_effect": "NONE",
    }

    parent = load_json(PARENT_RECEIPT)
    event_basis = event_materialization_basis()
    parent_valid = bool(parent and parent.get("state") == "COMPLETED" and parent.get("transition_id") == "RELAY_NODE_KV_CONTINUITY_VERIFIED")
    if not parent_valid and event_basis is None:
        return write_blocked(base, "DEVICE_KV_ADMITTED_PREDECESSOR_REQUIRED",
            "Neither authentic relay Node-KV continuity nor an admitted canonical device-kv event-materialization ingress is currently available.",
            "Consume the next admitted DEVICE_KV Universal InTr event or allow the stronger relay continuity proof lane to complete.",
            "event materialization ingress validates or parent receipt is COMPLETED RELAY_NODE_KV_CONTINUITY_VERIFIED", epoch)

    continuity = parent.get("continuity_evidence") if parent_valid else None
    if parent_valid and not isinstance(continuity, dict):
        return write_blocked(base, "PARENT_NODE_KV_EVIDENCE_REPAIR_REQUIRED",
            "Parent receipt lacks canonical continuity_evidence.",
            "Repair the parent evidence projection without manufacturing runtime evidence.",
            "parent continuity_evidence exists and validates against current StegOS source", epoch)

    stegos_root = find_source_root("STEGVERSE_STEGOS_ROOT", "StegOS", "stegos/relay_node_kv_continuity.py")
    kv_root = find_source_root("STEGVERSE_KV_SOURCE_ROOT", "continuity-vault-kit", "runtime/kv_interlock_endpoint.py")
    if stegos_root is None or kv_root is None:
        return write_blocked(base, "LOCAL_SOURCE_MATERIALIZATION_REQUIRED",
            "Current StegOS and continuity-vault-kit source must already be materialized on the sovereign carrier.",
            "Materialize current source through the existing credential-free sovereign source path.",
            "both source roots resolve locally without credential checkout", epoch)

    try:
        continuity_mod = load_module(stegos_root / "stegos/relay_node_kv_continuity.py", "device_kv_continuity")
        kv_mod = load_module(kv_root / "runtime/kv_interlock_endpoint.py", "device_kv_endpoint")
        connector = load_canonical_device_kv_connector(stegos_root)
        if parent_valid:
            continuity_mod.validate_node_kv_continuity_evidence(continuity)
    except Exception as exc:
        return write_blocked(base, "NODE_KV_CONTINUITY_VALIDATION_REQUIRED",
            f"Parent Node-KV continuity failed current-source validation: {type(exc).__name__}: {exc}",
            "Repair the exact parent evidence or source materialization and retry under a fresh fence.",
            "current StegOS validator accepts the authentic parent continuity evidence", epoch)

    if parent_valid:
        continuity_id = str(continuity["continuity_id"]); state_root = str(continuity["node_kv_state_root"])
        source_identity_ref = f"stegos-node://{continuity_id}"; next_boundary_identity_ref = state_root; prior_event_receipt = None
        predecessor_mode = "AUTHENTIC_PARENT_NODE_KV_CONTINUITY"
    else:
        assert event_basis is not None
        continuity_id = str(event_basis["continuity_id"]); state_root = str(event_basis["state_root"])
        source_identity_ref = str(event_basis["source_identity_ref"]); next_boundary_identity_ref = str(event_basis["next_boundary_identity_ref"])
        prior_event_receipt = str(event_basis["prior_receipt_hash"]); predecessor_mode = "EVENT_MATERIALIZATION_INGRESS"
    controlled = (handoff.get("execution") or {}).get("controlled_operation")
    if not isinstance(controlled, dict):
        return 4
    request = controlled_request(controlled, continuity_id, fence)
    request_packet = connector.prepare(
        request,
        payload_schema="kv.interlock.request.v1",
        operation=request["operation"],
        operation_id=request["request_id"],
        prior_receipt_hash=prior_event_receipt,
    )
    request_intent = dict(request_packet.intent)
    envelope = request_envelope(
        request, continuity_id, state_root,
        source_identity_ref=source_identity_ref,
        next_boundary_identity_ref=next_boundary_identity_ref,
        prior_receipt_hash=request_intent.get("prior_transport_receipt_hash"),
    )
    envelope["packet_id"] = request_intent["packet_id"]
    envelope["payload_hash"] = request_intent["payload_hash"]
    envelope["sealed_material_ref"] = "sealed://device-kv-intr/" + request_intent["packet_id"]
    request_wire = canonical_json({"request": request, "envelope": envelope}).encode()
    request_wire_hash = sha256_uri(request_wire)
    request_receipt_recorded_at = now_iso()
    request_receipt = connector.accept_hop(
        request_packet,
        hop_index=1,
        receipt_id="DEVICE-KV-" + request_intent["packet_id"],
        boundary_identity_ref=state_root,
        recorded_at=request_receipt_recorded_at,
        prior_receipt_hash=request_intent.get("prior_transport_receipt_hash"),
        transition_state="RECEIVED",
    )
    request_transport_result = connector.validate_complete(request_packet, [request_receipt])
    request_carrier_signal, request_carrier_reference = build_hb_carrier_signal(
        packet_id=envelope["packet_id"],
        payload_hash=envelope["payload_hash"],
        packet_bytes=request_wire,
        receipt_hash=request_receipt["receipt_hash"],
        boundary_from="DEVICE_SYSTEM",
        boundary_to="KV",
    )
    request_carrier_wire = canonical_json(request_carrier_signal).encode()
    request_carrier_wire_hash = sha256_uri(request_carrier_wire)
    heartbeat_runtime_root = default_heartbeat_runtime_root()

    endpoint_ref_box: dict[str, str] = {}

    def receipt_store(value: dict[str, Any]) -> str:
        ref = sha256_uri(value)
        atomic_write(ENDPOINT_RECEIPTS / f"{ref[7:]}.json", value)
        endpoint_ref_box["ref"] = ref
        return ref

    def authority_validator(authority_ref: str, received_request: dict[str, Any], received_envelope: dict[str, Any]) -> bool:
        proof = received_envelope.get("boundary_proof") or {}
        return (
            authority_ref == "CONTROLLED_NON_SENSITIVE_OBSERVATION_ONLY"
            and received_request.get("record_class") == "transport-capability-observation"
            and received_request.get("requested_scope") == ["capability_status"]
            and proof.get("source_identity_ref") == source_identity_ref
            and proof.get("next_boundary_identity_ref") == next_boundary_identity_ref
            and proof.get("verification_state") == "VERIFIED"
        )

    def policy_evaluator(received_request: dict[str, Any]) -> dict[str, Any]:
        return {
            "decision": "ALLOW_BOUNDED_CONTEXT",
            "granted_scope": ["capability_status"],
            "context": {"capability_status": "OBSERVATION_ONLY"},
            "source_refs": [f"node-kv-continuity:{continuity_id}"],
            "policy_profile": "DEVICE_KV_INTR_OBSERVATION_ONLY",
            "redaction_profile": "NO_PERSONAL_DATA",
        }

    runtime = kv_mod.KVInterlockRuntime(
        authority_validator=authority_validator,
        policy_evaluator=policy_evaluator,
        receipt_store=receipt_store,
    )
    server_state: dict[str, Any] = {}

    class Handler(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            raw_carrier = recv_frame(self.request)
            server_state["request_carrier_wire_hash"] = sha256_uri(raw_carrier)
            received_signal = json.loads(raw_carrier.decode())
            recovered = recover_intr_packet_bytes(received_signal)
            server_state["request_wire_hash"] = sha256_uri(recovered)
            if recovered != request_wire:
                raise ValueError("receiver HB carrier exact request wire mismatch")
            if received_signal.get("intr", {}).get("packet_receipt_hash") != request_receipt["receipt_hash"][7:]:
                raise ValueError("receiver HB carrier request receipt binding mismatch")
            if received_signal.get("authority", {}).get("authority_effect") != "NONE_CARRIER_ONLY":
                raise ValueError("receiver HB carrier authority drift")
            packet = json.loads(recovered.decode())
            received_request = packet.get("request")
            received_envelope = packet.get("envelope")
            if received_request != request or received_envelope != envelope:
                raise ValueError("receiver exact request/envelope identity mismatch")

            if connector.validate_complete(request_packet, [request_receipt]) != request_transport_result:
                raise ValueError("canonical DEVICE->KV transport reconstruction mismatch")
            atomic_write(TRANSPORT_RECEIPTS / "device-to-kv.json", request_receipt)
            atomic_write(CARRIER_SIGNALS / "device-to-kv.json", received_signal)
            server_state["request_shared_carrier"] = persist_local_intr_subsignal(
                root=heartbeat_runtime_root,
                signal=received_signal,
            )

            response = runtime.handle(received_request, intr_envelope=received_envelope,
                                      intr_receipt_ref=request_receipt["receipt_hash"])
            endpoint_ref = endpoint_ref_box.get("ref")
            if not endpoint_ref:
                raise ValueError("KV endpoint receipt store returned no durable reference")
            response_hash = sha256_uri(response)
            response_packet = connector.prepare_response(
                request_packet,
                [request_receipt],
                response,
                payload_schema="kv.interlock.response.v1",
                operation_id=request["request_id"] + ":response",
            )
            if response_packet.payload_hash != response_hash:
                raise ValueError("canonical KV->DEVICE response payload hash mismatch")
            response_receipt = connector.accept_hop(
                response_packet,
                hop_index=1,
                receipt_id="KV-DEVICE-" + response_packet.intent["packet_id"],
                boundary_identity_ref=f"stegos-node://{continuity_id}",
                recorded_at=now_iso(),
                prior_receipt_hash=request_receipt["receipt_hash"],
                transition_state="RECEIVED",
            )
            response_transport_result = connector.validate_complete(response_packet, [response_receipt])
            atomic_write(TRANSPORT_RECEIPTS / "kv-to-device.json", response_receipt)
            response_wire = canonical_json({
                "response": response,
                "endpoint_receipt_ref": endpoint_ref,
                "request_receipt": request_receipt,
                "response_receipt": response_receipt,
            }).encode()
            response_carrier_signal, response_carrier_reference = build_hb_carrier_signal(
                packet_id=response_receipt["packet_id"],
                payload_hash=response_hash,
                packet_bytes=response_wire,
                receipt_hash=response_receipt["receipt_hash"],
                boundary_from="KV",
                boundary_to="DEVICE_SYSTEM",
            )
            atomic_write(CARRIER_SIGNALS / "kv-to-device.json", response_carrier_signal)
            response_carrier_wire = canonical_json(response_carrier_signal).encode()
            server_state.update({
                "response": response,
                "response_wire_hash": sha256_uri(response_wire),
                "response_carrier_wire_hash": sha256_uri(response_carrier_wire),
                "response_carrier_reference": response_carrier_reference,
                "response_packet": response_packet,
                "response_transport_result": response_transport_result,
            })
            send_frame(self.request, response_carrier_wire)

    try:
        with socketserver.TCPServer(("127.0.0.1", 0), Handler) as server:
            host, port = server.server_address
            thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
            thread.start()
            try:
                with socket.create_connection((host, port), timeout=5.0) as client:
                    client.settimeout(5.0)
                    send_frame(client, request_carrier_wire)
                    response_carrier_wire = recv_frame(client)
                    response_carrier_signal = json.loads(response_carrier_wire.decode())
                    response_wire = recover_intr_packet_bytes(response_carrier_signal)
            finally:
                server.shutdown()
                thread.join(timeout=5.0)
    except Exception as exc:
        return write_blocked(base, "DEVICE_KV_INTR_RUNTIME_REPAIR_REQUIRED",
            f"Authentic deployment-local DEVICE<->KV transport failed closed: {type(exc).__name__}: {exc}",
            "Repair the exact boundary/runtime predicate and retry under a fresh WorkerCoordinator fence.",
            "exact request and response bytes traverse the bounded sovereign runtime and validate", epoch)

    try:
        response_packet = json.loads(response_wire.decode())
        if server_state.get("request_carrier_wire_hash") != request_carrier_wire_hash:
            raise ValueError("receiver request carrier wire digest mismatch")
        if server_state.get("request_wire_hash") != request_wire_hash:
            raise ValueError("receiver request wire digest mismatch")
        if sha256_uri(response_carrier_wire) != server_state.get("response_carrier_wire_hash"):
            raise ValueError("client response carrier wire digest mismatch")
        if sha256_uri(response_wire) != server_state.get("response_wire_hash"):
            raise ValueError("client response wire digest mismatch")
        if response_carrier_signal.get("intr", {}).get("packet_receipt_hash") != response_packet["response_receipt"]["receipt_hash"][7:]:
            raise ValueError("client HB carrier response receipt binding mismatch")
        if response_carrier_signal.get("authority", {}).get("authority_effect") != "NONE_CARRIER_ONLY":
            raise ValueError("client HB carrier response authority drift")
        response_shared_carrier = persist_local_intr_subsignal(
            root=heartbeat_runtime_root,
            signal=response_carrier_signal,
        )
        response = response_packet.get("response")
        if response != server_state.get("response"):
            raise ValueError("response body identity mismatch")
        request_receipt = response_packet["request_receipt"]
        response_receipt = response_packet["response_receipt"]
        endpoint_ref = response_packet.get("endpoint_receipt_ref")
        if connector.validate_complete(request_packet, [request_receipt]) != request_transport_result:
            raise ValueError("canonical DEVICE->KV transport result drift")
        response_packet_obj = server_state.get("response_packet")
        if response_packet_obj is None:
            raise ValueError("canonical KV->DEVICE response packet missing")
        response_transport_result = connector.validate_complete(response_packet_obj, [response_receipt])
        if response_transport_result != server_state.get("response_transport_result"):
            raise ValueError("canonical KV->DEVICE transport result drift")
        if load_json(TRANSPORT_RECEIPTS / "device-to-kv.json") != request_receipt:
            raise ValueError("DEVICE->KV durable receipt readback mismatch")
        if load_json(TRANSPORT_RECEIPTS / "kv-to-device.json") != response_receipt:
            raise ValueError("KV->DEVICE durable receipt readback mismatch")
        if not isinstance(endpoint_ref, str) or endpoint_ref != endpoint_ref_box.get("ref"):
            raise ValueError("KV endpoint receipt reference binding mismatch")
        endpoint_receipt = load_json(ENDPOINT_RECEIPTS / f"{endpoint_ref[7:]}.json")
        if not endpoint_receipt or sha256_uri(endpoint_receipt) != endpoint_ref:
            raise ValueError("KV endpoint durable receipt readback mismatch")
        if response.get("decision") != "ALLOW_BOUNDED_CONTEXT":
            raise ValueError("controlled non-sensitive KV observation was not admitted")
        if response.get("context") != {"capability_status": "OBSERVATION_ONLY"}:
            raise ValueError("unexpected KV observation context")
    except Exception as exc:
        return write_blocked(base, "DEVICE_KV_INTR_RECONSTRUCTION_REPAIR_REQUIRED",
            f"DEVICE_KV_INTR durable reconstruction failed closed: {type(exc).__name__}: {exc}",
            "Repair exact durable receipt/response identity and rerun under a fresh fence.",
            "durable transport and endpoint receipts reconstruct the same request/response execution", epoch)

    observation = {
        **base,
        "state": "OBSERVED",
        "transition_id": "DEVICE_KV_INTR_OBSERVED",
        "observed_at": now_iso(),
        "parent_continuity_id": continuity_id,
        "node_kv_state_root": state_root,
        "parent_state_root_continuity_verified": parent_valid,
        "event_materialization_ingress_verified": event_basis is not None,
        "event_materialization_id": event_basis.get("materialization_id") if event_basis else None,
        "event_transport_intent_hash": event_basis.get("transport_intent_hash") if event_basis else None,
        "event_queued_payload_hash": event_basis.get("queued_payload_hash") if event_basis else None,
        "request_id": request["request_id"],
        "request_payload_hash": envelope["payload_hash"],
        "request_wire_sha256": request_wire_hash,
        "request_receiver_wire_sha256": server_state["request_wire_hash"],
        "request_carrier_wire_sha256": request_carrier_wire_hash,
        "request_receiver_carrier_wire_sha256": server_state["request_carrier_wire_hash"],
        "request_carrier_signal_id": request_carrier_signal["signal_id"],
        "request_carrier_heartbeat_epoch": request_carrier_reference["epoch"],
        "request_carrier_heartbeat_reference": request_carrier_reference["heartbeat_id"],
        "request_carrier_channel_slot": request_carrier_signal["carrier"]["channel_slot"],
        "request_carrier_phase_offset_deg": request_carrier_signal["carrier"]["phase_offset_deg"],
        "request_carrier_packet_recovery_verified": True,
        "request_shared_hb_signal_ref": server_state["request_shared_carrier"]["signal_ref"],
        "request_shared_hb_signal_sha256": server_state["request_shared_carrier"]["signal_sha256"],
        "request_receipt_hash": request_receipt["receipt_hash"],
        "kv_interlock_decision": response["decision"],
        "kv_endpoint_receipt_ref": endpoint_ref,
        "response_payload_hash": sha256_uri(response),
        "response_wire_sha256": sha256_uri(response_wire),
        "response_receiver_wire_sha256": server_state["response_wire_hash"],
        "response_carrier_wire_sha256": sha256_uri(response_carrier_wire),
        "response_receiver_carrier_wire_sha256": server_state["response_carrier_wire_hash"],
        "response_carrier_signal_id": response_carrier_signal["signal_id"],
        "response_carrier_heartbeat_epoch": server_state["response_carrier_reference"]["epoch"],
        "response_carrier_heartbeat_reference": server_state["response_carrier_reference"]["heartbeat_id"],
        "response_carrier_channel_slot": response_carrier_signal["carrier"]["channel_slot"],
        "response_carrier_phase_offset_deg": response_carrier_signal["carrier"]["phase_offset_deg"],
        "response_carrier_packet_recovery_verified": True,
        "response_shared_hb_signal_ref": response_shared_carrier["signal_ref"],
        "response_shared_hb_signal_sha256": response_shared_carrier["signal_sha256"],
        "response_receipt_hash": response_receipt["receipt_hash"],
        "request_exact_bytes_transported": True,
        "response_exact_bytes_transported": True,
        "request_transported_on_hb_derived_carrier": True,
        "response_transported_on_hb_derived_carrier": True,
        "hb_derived_carrier_transport_observed": True,
        "device_to_kv_receipt_verified": True,
        "kv_to_device_receipt_verified": True,
        "receipt_lineage_verified": response_receipt["prior_receipt_hash"] == request_receipt["receipt_hash"],
        "durable_receipt_readback_verified": True,
        "same_execution_reconstructed": True,
        "boundary_identity_source": predecessor_mode,
        "transport_grants_execution_authority": False,
        "secret_plaintext_present": False,
    }
    atomic_write(RECEIPT, observation)
    if load_json(RECEIPT) != observation:
        return 5
    json.dump(worker_response("COMPLETED", "DEVICE_KV_INTR_OBSERVED", epoch), sys.stdout)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())