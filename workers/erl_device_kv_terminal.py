#!/usr/bin/env python3
"""Execute the ERL terminal DEVICE_SYSTEM -> KV hop inside the existing DEVICE_KV owner.

This module is a bounded helper, not a worker/listener/scheduler/authority source. It
accepts only an already-admitted ERL terminal materialization, reuses the original
full-path Universal InTr intent, transports the exact canonical acquisition-envelope
bytes over a deployment-local ephemeral loopback carrier, emits hop 3, verifies the
complete three-hop chain, and durably reads back the exact bytes at the KV side.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import socket
import socketserver
import struct
import tempfile
import threading
from pathlib import Path
from typing import Any, Mapping

FULL_PATH = ["EXTERNAL_SYSTEM", "STEGOS_ECOSYSTEM", "DEVICE_SYSTEM", "KV"]
TERMINAL_PATH = ["DEVICE_SYSTEM", "KV"]
PROFILE_DIR = Path("receipts/sovereign-network/erl-active-research-intr")
TERMINAL_RECEIPT_DIR = Path("receipts/device-kv-intr/erl-terminal-receipts")
TERMINAL_PAYLOAD_DIR = Path("receipts/device-kv-intr/erl-terminal-payload-readback")
RESULT_DIR = Path("receipts/device-kv-intr/erl-terminal-results")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, (bytes, bytearray)) else canonical(value)
    return "sha256:" + hashlib.sha256(bytes(raw)).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "json_object_required:" + str(path))
    return value


def atomic_write_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == raw, "write_once_collision:" + str(path))
        return
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(raw)
        temp = Path(handle.name)
    os.replace(temp, path)
    require(path.read_bytes() == raw, "write_readback_mismatch:" + str(path))


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    raw = json.dumps(dict(value), indent=2, sort_keys=True).encode("utf-8") + b"\n"
    atomic_write_bytes(path, raw)


def _load_transport(stegos_root: Path):
    path = stegos_root / "stegos/universal_intr_transport.py"
    require(path.is_file(), "universal_intr_transport_source_missing")
    spec = importlib.util.spec_from_file_location("erl_terminal_universal_intr_transport", path)
    require(spec is not None and spec.loader is not None, "universal_intr_transport_loader_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_erl_terminal_request(request: Any) -> bool:
    return (
        isinstance(request, dict)
        and request.get("erl_full_path") == FULL_PATH
        and isinstance(request.get("erl_transport_intent"), dict)
        and isinstance(request.get("erl_upstream_receipt_hashes"), list)
    )


def _send_frame(sock: socket.socket, payload: bytes) -> None:
    sock.sendall(struct.pack("!Q", len(payload)) + payload)


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    left = size
    while left:
        chunk = sock.recv(left)
        if not chunk:
            raise RuntimeError("carrier_closed_before_exact_frame")
        chunks.append(chunk)
        left -= len(chunk)
    return b"".join(chunks)


def _recv_frame(sock: socket.socket, max_bytes: int = 1024 * 1024) -> bytes:
    size = struct.unpack("!Q", _recv_exact(sock, 8))[0]
    require(0 < size <= max_bytes, "bounded_carrier_frame_size_invalid")
    return _recv_exact(sock, size)


def _resolve_payload(runtime_root: Path, payload_ref: Any) -> tuple[Path, dict[str, Any], bytes]:
    require(isinstance(payload_ref, str) and payload_ref.startswith("runtime-local:"), "erl_payload_ref_must_be_runtime_local")
    rel = payload_ref[len("runtime-local:"):]
    require(bool(rel), "erl_payload_ref_empty")
    runtime = runtime_root.resolve()
    path = (runtime / rel).resolve()
    require(path != runtime and runtime in path.parents, "erl_payload_ref_outside_runtime")
    require(path.is_file(), "erl_payload_not_materialized")
    envelope = load_json(path)
    raw = canonical(envelope)
    return path, envelope, raw


def execute(*, runtime_root: Path, stegos_root: Path, request: Mapping[str, Any], ingress: Mapping[str, Any], boundary_identity_ref: str) -> dict[str, Any]:
    require(is_erl_terminal_request(request), "erl_terminal_request_required")
    transport = _load_transport(stegos_root.resolve())
    intent = dict(request["erl_transport_intent"])
    transport.validate_transport_intent(intent)
    require(intent.get("boundary_path") == FULL_PATH, "erl_terminal_full_intent_path_invalid")
    require(request.get("boundary_path") == TERMINAL_PATH, "erl_terminal_projection_path_invalid")
    require(request.get("transport_intent_hash") == transport.sha256_uri(intent), "erl_terminal_intent_hash_mismatch")
    for key in ("operation_id", "packet_id", "payload_hash"):
        require(request.get(key) == intent.get(key), "erl_terminal_identity_mismatch:" + key)
        require(ingress.get(key) == intent.get(key), "erl_terminal_ingress_identity_mismatch:" + key)
    upstream_hashes = request.get("erl_upstream_receipt_hashes")
    require(isinstance(upstream_hashes, list) and len(upstream_hashes) == 2, "erl_terminal_upstream_hash_count_invalid")
    require(request.get("prior_transport_receipt_hash") == upstream_hashes[-1], "erl_terminal_prior_hash_mismatch")

    profile_path = runtime_root / PROFILE_DIR / f"{request['materialization_id']}.json"
    require(profile_path.is_file(), "erl_profile_admission_evidence_missing")
    profile = load_json(profile_path)
    hops = profile.get("hop_receipts")
    require(isinstance(hops, list) and len(hops) == 2, "erl_profile_upstream_receipts_invalid")
    require([item.get("receipt_hash") for item in hops] == upstream_hashes, "erl_profile_upstream_hash_binding_mismatch")
    transport.validate_receipt_chain(intent, hops)

    payload_path, envelope, payload_bytes = _resolve_payload(runtime_root, request.get("payload_ref"))
    require(transport.sha256_uri(envelope) == intent.get("payload_hash"), "erl_terminal_payload_hash_mismatch")
    require(hashlib.sha256(payload_bytes).hexdigest() == intent["payload_hash"][7:], "erl_terminal_exact_canonical_bytes_hash_mismatch")

    hop3 = transport.build_hop_receipt(
        intent,
        hop_index=3,
        receipt_id="ERL-ACTIVE-" + intent["packet_id"] + "-3",
        boundary_identity_ref=boundary_identity_ref,
        recorded_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        prior_receipt_hash=upstream_hashes[-1],
        transition_state="RECEIVED",
    )
    transport.validate_receipt_chain(intent, [*hops, hop3])

    receiver: dict[str, bytes] = {}
    class Handler(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            raw = _recv_frame(self.request)
            require(raw == payload_bytes, "erl_terminal_receiver_exact_bytes_mismatch")
            receiver["raw"] = raw
            _send_frame(self.request, hashlib.sha256(raw).digest())

    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as server:
        host, port = server.server_address
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        thread.start()
        try:
            with socket.create_connection((host, port), timeout=5.0) as client:
                client.settimeout(5.0)
                _send_frame(client, payload_bytes)
                ack = _recv_frame(client, max_bytes=64)
        finally:
            server.shutdown()
            thread.join(timeout=5.0)
    require(receiver.get("raw") == payload_bytes, "erl_terminal_receiver_missing_exact_bytes")
    require(ack == hashlib.sha256(payload_bytes).digest(), "erl_terminal_receiver_ack_mismatch")

    payload_readback = runtime_root / TERMINAL_PAYLOAD_DIR / f"{request['materialization_id']}.json"
    atomic_write_bytes(payload_readback, payload_bytes)
    require(payload_readback.read_bytes() == payload_bytes, "erl_terminal_kv_readback_mismatch")
    receipt_path = runtime_root / TERMINAL_RECEIPT_DIR / f"{request['materialization_id']}.json"
    atomic_write_json(receipt_path, hop3)
    require(load_json(receipt_path) == hop3, "erl_terminal_receipt_readback_mismatch")

    result = {
        "schema": "stegverse.erl.device-kv-terminal-observation/v1",
        "state": "ERL_TERMINAL_DEVICE_KV_OBSERVED",
        "materialization_id": request["materialization_id"],
        "operation_id": intent["operation_id"],
        "packet_id": intent["packet_id"],
        "payload_hash": intent["payload_hash"],
        "transport_intent_hash": transport.sha256_uri(intent),
        "upstream_receipt_hashes": upstream_hashes,
        "terminal_receipt": hop3,
        "terminal_receipt_hash": hop3["receipt_hash"],
        "complete_three_hop_chain_verified": True,
        "payload_ref": request["payload_ref"],
        "payload_source_path": str(payload_path),
        "kv_payload_readback_ref": str(payload_readback.relative_to(runtime_root)),
        "kv_payload_readback_sha256": transport.sha256_uri(payload_readback.read_bytes()),
        "exact_payload_bytes_transported": True,
        "durable_payload_readback_verified": True,
        "durable_terminal_receipt_readback_verified": True,
        "provider_operation_attempted": False,
        "transport_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_TRANSPORT_OBSERVATION_ONLY",
    }
    result_path = runtime_root / RESULT_DIR / f"{request['materialization_id']}.json"
    atomic_write_json(result_path, result)
    require(load_json(result_path) == result, "erl_terminal_result_readback_mismatch")
    return result
