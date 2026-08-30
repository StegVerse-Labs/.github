#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import socket
import socketserver
import struct
import sys
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path.cwd().resolve()
TASK_ID = "SHWP-DEVICE-KV-INTR-OBSERVATION-001"
PARENT_TASK_ID = "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001"
PARENT_RECEIPT = ROOT / "receipts" / "stegos-sovereign-relay" / f"{PARENT_TASK_ID}.json"
RECEIPT_ROOT = ROOT / "receipts" / "device-kv-intr"
RECEIPT = RECEIPT_ROOT / f"{TASK_ID}.json"
ENDPOINT_RECEIPTS = RECEIPT_ROOT / "endpoint-receipts"
TRANSPORT_RECEIPTS = RECEIPT_ROOT / "transport-receipts"


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
        name = handle.name
    os.replace(name, path)


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


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


def worker_response(*, state: str, transition: str, epoch: int, blocker_value: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
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
    if blocker_value is not None:
        result["blocker"] = blocker_value
    return result


def write_blocked(base: dict[str, Any], transition: str, problem: str, action: str, release: str, epoch: int) -> int:
    blocked = blocker(problem, action, release)
    receipt = {**base, "state": "ACTIVE", "transition_id": transition, "blocker": blocked}
    atomic_write(RECEIPT, receipt)
    json.dump(worker_response(state="ACTIVE", transition=transition, epoch=epoch, blocker_value=blocked), sys.stdout)
    print()
    return 0


def _transport_receipt(
    *,
    receipt_id: str,
    packet_id: str,
    from_role: str,
    to_role: str,
    operation_hash: str,
    payload_hash: str,
    prior_receipt_hash: str | None,
    boundary_identity_ref: str,
) -> dict[str, Any]:
    body = {
        "schema": "stegverse.intr.hop_receipt/v1",
        "receipt_id": receipt_id,
        "packet_id": packet_id,
        "hop_index": 1,
        "direction": "FORWARD",
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
        "recorded_at": now_iso(),
    }
    return {**body, "receipt_hash": sha256_uri(body)}


def _validate_transport_receipt(receipt: Mapping[str, Any], *, from_role: str, to_role: str, payload_hash: str, prior: str | None) -> None:
    expected_fields = {
        "schema", "receipt_id", "packet_id", "hop_index", "direction", "from_role", "to_role",
        "operation_hash", "payload_hash", "prior_receipt_hash", "boundary_identity_ref",
        "boundary_verification", "transition_state", "secret_plaintext_present", "authority_transfer",
        "recorded_at", "receipt_hash",
    }
    if set(receipt) != expected_fields:
        raise ValueError("noncanonical transport receipt field set")
    if receipt.get("schema") != "stegverse.intr.hop_receipt/v1":
        raise ValueError("transport receipt schema mismatch")
    if receipt.get("hop_index") != 1 or receipt.get("direction") != "FORWARD":
        raise ValueError("transport receipt hop/direction mismatch")
    if receipt.get("from_role") != from_role or receipt.get("to_role") != to_role:
        raise ValueError("transport receipt boundary mismatch")
    if receipt.get("payload_hash") != payload_hash or receipt.get("prior_receipt_hash") != prior:
        raise ValueError("transport receipt payload/lineage mismatch")
    if receipt.get("boundary_verification") != "VERIFIED" or receipt.get("transition_state") != "RECEIVED":
        raise ValueError("transport receipt was not received at verified boundary")
    if receipt.get("secret_plaintext_present") is not False or receipt.get("authority_transfer") is not False:
        raise ValueError("transport receipt authority/plaintext violation")
    body = dict(receipt)
    claimed = body.pop("receipt_hash", None)
    if claimed != sha256_uri(body):
        raise ValueError("transport receipt hash mismatch")


def _send_frame(sock: socket.socket, payload: bytes) -> None:
    sock.sendall(struct.pack("!Q", len(payload)) + payload)


def _recv_exact(sock: socket.socket, count: int) -> bytes:
    chunks: list[bytes] = []
    remaining = count
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("transport closed before exact frame completed")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _recv_frame(sock: socket.socket, *, max_bytes: int = 1024 * 1024) -> bytes:
    length = struct.unpack("!Q", _recv_exact(sock, 8))[0]
    if length <= 0 or length > max_bytes:
        raise ValueError("invalid bounded transport frame length")
    return _recv_exact(sock, length)


def _controlled_request(controlled: Mapping[str, Any], *, continuity_id: str, fencing_token: int) -> dict[str, Any]:
    request = dict(controlled)
    request["request_id"] = "DEVICE-KV-INTR-" + hashlib.sha256(
        f"{continuity_id}:{fencing_token}".encode("utf-8")
    ).hexdigest()[:24]
    request["requester"] = {"module": "StegOS", "component": "DEVICE_KV_INTR_OBSERVER"}
    return request


def _request_envelope(request: Mapping[str, Any], *, continuity_id: str, state_root: str) -> dict[str, Any]:
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
        "prior_receipt_hash": None,
        "authority": {
            "authority_transfer": False,
            "transport_grants_execution_authority": False,
            "model_output_grants_execution_authority": False,
            "credential_authority_effect": "NONE",
        },
        "boundary_proof": {
            "required": True,
            "source_identity_ref": f"stegos-node://{continuity_id}",
            "next_boundary_identity_ref": state_root,
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
    timing = task.get("heartbeat_timing") or {}
    fence = timing.get("fencing_token")
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
    if not parent or parent.get("state") != "COMPLETED" or parent.get("transition_id") != "RELAY_NODE_KV_CONTINUITY_VERIFIED":
        return write_blocked(
            base,
            "PARENT_NODE_KV_CONTINUITY_REQUIRED",
            "Authentic relay Node-KV teardown/recreation continuity has not yet been observed.",
            "Allow the already-admitted parent continuity task to complete on the deployment-local sovereign WorkerCoordinator.",
            "parent receipt is COMPLETED with transition_id RELAY_NODE_KV_CONTINUITY_VERIFIED",
            epoch,
        )

    continuity = parent.get("continuity_evidence")
    if not isinstance(continuity, dict):
        return write_blocked(
            base,
            "PARENT_NODE_KV_EVIDENCE_REPAIR_REQUIRED",
            "Parent receipt lacks canonical continuity_evidence.",
            "Repair the parent evidence projection without manufacturing a new runtime observation.",
            "parent continuity_evidence is present and validates against merged StegOS source",
            epoch,
        )

    stegos_root = find_source_root("STEGVERSE_STEGOS_ROOT", "StegOS", "stegos/relay_node_kv_continuity.py")
    kv_root = find_source_root("STEGVERSE_KV_SOURCE_ROOT", "continuity-vault-kit", "runtime/kv_interlock_endpoint.py")
    if stegos_root is None or kv_root is None:
        missing = "StegOS" if stegos_root is None else "continuity-vault-kit"
        return write_blocked(
            base,
            "LOCAL_SOURCE_MATERIALIZATION_REQUIRED",
            f"Already-local {missing} source is not materialized on the sovereign carrier.",
            "Materialize current source through the existing credential-free sovereign source path; do not introduce a network credential checkout.",
            "both StegOS and continuity-vault-kit runtime source roots resolve locally",
            epoch,
        )

    for source_root in (stegos_root, kv_root):
        if str(source_root) not in sys.path:
            sys.path.insert(0, str(source_root))

    try:
        from stegos.relay_node_kv_continuity import validate_node_kv_continuity_evidence
        from runtime.kv_interlock_endpoint import KVInterlockRuntime
        validate_node_kv_continuity_evidence(continuity)
    except Exception as exc:
        return write_blocked(
            base,
            "NODE_KV_CONTINUITY_VALIDATION_REQUIRED",
            f"Parent Node-KV continuity failed current-source validation: {type(exc).__name__}: {exc}",
            "Repair or rematerialize the exact parent continuity evidence and retry under a fresh fence.",
            "current merged StegOS validator accepts the authentic parent continuity evidence",
            epoch,
        )

    continuity_id = str(continuity["continuity_id"])
    state_root = str(continuity["node_kv_state_root"])
    execution = handoff.get("execution") or {}
    controlled = execution.get("controlled_operation")
    if not isinstance(controlled, dict):
        return 4
    request = _controlled_request(controlled, continuity_id=continuity_id, fencing_token=fence)
    envelope = _request_envelope(request, continuity_id=continuity_id, state_root=state_root)
    request_wire = canonical_json({"request": request, "envelope": envelope}).encode("utf-8")
    request_wire_hash = sha256_uri(request_wire)

    endpoint_refs: list[str] = []

    def receipt_store(value: dict[str, Any]) -> str:
        digest = sha256_uri(value)
        path = ENDPOINT_RECEIPTS / f"{digest[7:]}.json"
        atomic_write(path, value)
        endpoint_refs.append(digest)
        return digest

    def authority_validator(authority_ref: str, received_request: dict[str, Any], received_envelope: dict[str, Any]) -> bool:
        proof = received_envelope.get("boundary_proof") or {}
        return (
            authority_ref == "CONTROLLED_NON_SENSITIVE_OBSERVATION_ONLY"
            and received_request.get("record_class") == "transport-capability-observation"
            and received_request.get("requested_scope") == ["capability_status"]
            and proof.get("source_identity_ref") == f"stegos-node://{continuity_id}"
            and proof.get("next_boundary_identity_ref") == state_root
            and proof.get("verification_state") == "VERIFIED"
        )

    def policy_evaluator(received_request: dict[str, Any]) -> dict[str, Any]:
        if received_request.get("requested_scope") != ["capability_status"]:
            return {"decision": "DENY", "granted_scope": [], "context": {}, "source_refs": [], "policy_profile": "DEVICE_KV_INTR_OBSERVATION_DENY"}
        return {
            "decision": "ALLOW_BOUNDED_CONTEXT",
            "granted_scope": ["capability_status"],
            "context": {"capability_status": "OBSERVATION_ONLY"},
            "source_refs": [f"node-kv-continuity:{continuity_id}"],
            "policy_profile": "DEVICE_KV_INTR_OBSERVATION_ONLY",
            "redaction_profile": "NO_PERSONAL_DATA",
        }

    runtime = KVInterlockRuntime(
        authority_validator=authority_validator,
        policy_evaluator=policy_evaluator,
        receipt_store=receipt_store,
    )

    server_state: dict[str, Any] = {}
    operation_hash = sha256_uri({"request_id": request["request_id"], "operation": request["operation"], "packet_id": envelope["packet_id"]})

    class Handler(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            raw = _recv_frame(self.request)
            server_state["request_wire_hash"] = sha256_uri(raw)
            packet = json.loads(raw.decode("utf-8"))
            received_request = packet.get("request")
            received_envelope = packet.get("envelope")
            if received_request != request or received_envelope != envelope:
                raise ValueError("receiver exact request/envelope identity mismatch")

            request_receipt = _transport_receipt(
                receipt_id="DEVICE-KV-" + envelope["packet_id"],
                packet_id=envelope["packet_id"],
                from_role="DEVICE",
                to_role="KV",
                operation_hash=operation_hash,
                payload_hash=envelope["payload_hash"],
                prior_receipt_hash=None,
                boundary_identity_ref=state_root,
            )
            _validate_transport_receipt(request_receipt, from_role="DEVICE", to_role="KV", payload_hash=envelope["payload_hash"], prior=None)
            atomic_write(TRANSPORT_RECEIPTS / "device-to-kv.json", request_receipt)

            response = runtime.handle(
                received_request,
                intr_envelope=received_envelope,
                intr_receipt_ref=request_receipt["receipt_hash"],
            )
            response_hash = sha256_uri(response)
            response_receipt = _transport_receipt(
                receipt_id="KV-DEVICE-" + envelope["packet_id"],
                packet_id=envelope["packet_id"] + "-RETURN",
                from_role="KV",
                to_role="DEVICE",
                operation_hash=operation_hash,
                payload_hash=response_hash,
                prior_receipt_hash=request_receipt["receipt_hash"],
                boundary_identity_ref=f"stegos-node://{continuity_id}",
            )
            _validate_transport_receipt(response_receipt, from_role="KV", to_role="DEVICE", payload_hash=response_hash, prior=request_receipt["receipt_hash"])
            atomic_write(TRANSPORT_RECEIPTS / "kv-to-device.json", response_receipt)

            response_wire = canonical_json({
                "response": response,
                "request_receipt": request_receipt,
                "response_receipt": response_receipt,
            }).encode("utf-8")
            server_state.update({
                "response": response,
                "response_hash": response_hash,
                "request_receipt": request_receipt,
                "response_receipt": response_receipt,
                "response_wire_hash": sha256_uri(response_wire),
            })
            _send_frame(self.request, response_wire)

    try:
        with socketserver.TCPServer(("127.0.0.1", 0), Handler, bind_and_activate=True) as server:
            server.allow_reuse_address = False
            host, port = server.server_address
            thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
            thread.start()
            try:
                with socket.create_connection((host, port), timeout=5.0) as client:
                    client.settimeout(5.0)
                    _send_frame(client, request_wire)
                    response_wire = _recv_frame(client)
            finally:
                server.shutdown()
                thread.join(timeout=5.0)
    except Exception as exc:
        return write_blocked(
            base,
            "DEVICE_KV_INTR_RUNTIME_REPAIR_REQUIRED",
            f"Authentic deployment-local DEVICE<->KV transport failed closed: {type(exc).__name__}: {exc}",
            "Repair the exact local boundary/runtime predicate and retry under a fresh WorkerCoordinator fence; do not substitute hosted evidence.",
            "exact request and response bytes traverse the bounded sovereign runtime and validate",
            epoch,
        )

    try:
        response_packet = json.loads(response_wire.decode("utf-8"))
        if server_state.get("request_wire_hash") != request_wire_hash:
            raise ValueError("receiver request wire digest mismatch")
        if sha256_uri(response_wire) != server_state.get("response_wire_hash"):
            raise ValueError("client response wire digest mismatch")
        if response_packet.get("response") != server_state.get("response"):
            raise ValueError("response body identity mismatch")
        request_receipt = response_packet["request_receipt"]
        response_receipt = response_packet["response_receipt"]
        _validate_transport_receipt(request_receipt, from_role="DEVICE", to_role="KV", payload_hash=envelope["payload_hash"], prior=None)
        _validate_transport_receipt(response_receipt, from_role="KV", to_role="DEVICE", payload_hash=sha256_uri(response_packet["response"]), prior=request_receipt["receipt_hash"])
        persisted_request = load_json(TRANSPORT_RECEIPTS / "device-to-kv.json")
        persisted_response = load_json(TRANSPORT_RECEIPTS / "kv-to-device.json")
        if persisted_request != request_receipt or persisted_response != response_receipt:
            raise ValueError("durable transport receipt readback mismatch")
        if not endpoint_refs or not all((ENDPOINT_RECEIPTS / f"{ref[7:]}.json").is_file() for ref in endpoint_refs):
            raise ValueError("durable KV endpoint receipt readback missing")
        endpoint_receipt_ref = response_packet["response"].get("receipt", {}).get("receipt_ref")
        if endpoint_receipt_ref not in endpoint_refs:
            raise ValueError("KV endpoint response is not bound to durable endpoint receipt")
    except Exception as exc:
        return write_blocked(
            base,
            "DEVICE_KV_INTR_RECONSTRUCTION_REPAIR_REQUIRED",
            f"DEVICE_KV_INTR durable reconstruction failed closed: {type(exc).__name__}: {exc}",
            "Repair exact durable receipt/response identity and rerun the authentic transport under a fresh fence.",
            "durable transport and endpoint receipts reconstruct the same request/response execution",
            epoch,
        )

    observation = {
        **base,
        "state": "OBSERVED",
        "transition_id": "DEVICE_KV_INTR_OBSERVED",
        "observed_at": now_iso(),
        "parent_continuity_id": continuity_id,
        "node_kv_state_root": state_root,
        "parent_state_root_continuity_verified": True,
        "request_id": request["request_id"],
        "request_payload_hash": envelope["payload_hash"],
        "request_wire_sha256": request_wire_hash,
        "request_receiver_wire_sha256": server_state["request_wire_hash"],
        "request_receipt_hash": request_receipt["receipt_hash"],
        "kv_interlock_decision": response_packet["response"].get("decision"),
        "kv_endpoint_receipt_ref": endpoint_receipt_ref,
        "response_payload_hash": sha256_uri(response_packet["response"]),
        "response_wire_sha256": sha256_uri(response_wire),
        "response_receiver_wire_sha256": server_state["response_wire_hash"],
        "response_receipt_hash": response_receipt["receipt_hash"],
        "request_exact_bytes_transported": True,
        "response_exact_bytes_transported": True,
        "device_to_kv_receipt_verified": True,
        "kv_to_device_receipt_verified": True,
        "receipt_lineage_verified": response_receipt["prior_receipt_hash"] == request_receipt["receipt_hash"],
        "durable_receipt_readback_verified": True,
        "same_execution_reconstructed": True,
        "boundary_identity_source": "AUTHENTIC_PARENT_NODE_KV_CONTINUITY",
        "transport_grants_execution_authority": False,
        "secret_plaintext_present": False,
    }
    atomic_write(RECEIPT, observation)
    reread = load_json(RECEIPT)
    if reread != observation:
        return 5

    json.dump(worker_response(state="COMPLETED", transition="DEVICE_KV_INTR_OBSERVED", epoch=epoch), sys.stdout)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
