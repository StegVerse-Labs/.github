import copy
import hashlib
import json
from pathlib import Path

import pytest

from workers.device_kv_skap_roundtrip_verifier import (
    INPUT_SCHEMA,
    TASK_ID,
    RoundTripEvidenceError,
    canonical,
    sha_uri,
    verify_manifest,
)


def _intent(*, operation_id, payload_hash, source, destination, prior):
    basis = {
        "operation_id": operation_id,
        "payload_hash": payload_hash,
        "source_boundary": source,
        "source_subsystem": source + ":test",
        "destination_boundary": destination,
        "destination_subsystem": destination + ":test",
        "boundary_path": [source, destination],
    }
    packet_id = "INTR-" + hashlib.sha256(canonical(basis)).hexdigest()[:24]
    return {
        "schema": "stegverse.universal-intr-transport/v1",
        "protocol": "InTr",
        "operation_id": operation_id,
        "packet_id": packet_id,
        "payload_hash": payload_hash,
        "prior_transport_receipt_hash": prior,
        "source": {"boundary": source, "subsystem": source + ":test"},
        "destination": {"boundary": destination, "subsystem": destination + ":test"},
        "boundary_path": [source, destination],
        "interlock_required": True,
        "transport_semantics": {
            "event_triggered": True,
            "always_on_receiver_required": False,
            "second_user_device_required": False,
            "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
            "exact_packet_transport_retry_allowed": True,
            "blind_consequence_retry_allowed": False,
        },
        "authority": {
            "authority_transfer": False,
            "transport_grants_execution_authority": False,
            "credential_authority": "TV/TVC",
        },
        "receipt_chain": {
            "required": True,
            "receipt_schema": "stegverse.intr.hop_receipt/v1",
            "payload_plaintext_in_receipts": False,
            "prior_hash_required_after_first_hop": True,
        },
    }


def _receipt(intent, *, prior, source, destination, receipt_id):
    operation_hash = sha_uri({
        "operation_id": intent["operation_id"],
        "packet_id": intent["packet_id"],
        "payload_hash": intent["payload_hash"],
    })
    body = {
        "schema": "stegverse.intr.hop_receipt/v1",
        "receipt_id": receipt_id,
        "packet_id": intent["packet_id"],
        "hop_index": 1,
        "direction": "FORWARD",
        "from_role": source,
        "to_role": destination,
        "operation_hash": operation_hash,
        "payload_hash": intent["payload_hash"],
        "prior_receipt_hash": prior,
        "boundary_identity_ref": "tvc://boundary/runtime-test",
        "boundary_verification": "VERIFIED",
        "transition_state": "RECEIVED",
        "secret_plaintext_present": False,
        "authority_transfer": False,
        "recorded_at": "2026-09-10T19:05:00Z",
    }
    return {**body, "receipt_hash": sha_uri(body)}


def _write(root: Path, name: str, value, *, binary=False):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        path.write_bytes(value)
    else:
        path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return str(path.relative_to(root))


def build_manifest(root: Path):
    spec = [
        ("device_kv", "DEVICE_SYSTEM", "KV", b"device-request"),
        ("kv_skap", "KV", "SKAP_VAULT", b"sealed-skap-ciphertext"),
        ("skap_kv", "SKAP_VAULT", "KV", b"skap-result-reference"),
        ("kv_device", "KV", "DEVICE_SYSTEM", b"device-result-reference"),
    ]
    previous = None
    manifest = {
        "schema": INPUT_SCHEMA,
        "task_id": TASK_ID,
        "current_device": True,
        "hosted_runtime_used": False,
        "second_user_operated_device_used": False,
    }
    receipts = {}
    for index, (name, source, destination, payload) in enumerate(spec, start=1):
        intent = _intent(operation_id=f"ROUNDTRIP-{index}", payload_hash=sha_uri(payload), source=source, destination=destination, prior=previous)
        receipt = _receipt(intent, prior=previous, source=source, destination=destination, receipt_id=f"R-{index}")
        manifest[name] = {
            "intent_path": _write(root, f"{name}/intent.json", intent),
            "payload_path": _write(root, f"{name}/payload.bin", payload, binary=True),
            "receipt_path": _write(root, f"{name}/receipt.json", receipt),
        }
        receipts[name] = receipt
        previous = receipt["receipt_hash"]
    manifest["readback"] = {
        "skap": {
            "observed": True,
            "exact_readback": True,
            "source_receipt_hash": receipts["kv_skap"]["receipt_hash"],
            "object_sha256": "sha256:" + "a" * 64,
            "credential_material_present": False,
        },
        "kv": {
            "observed": True,
            "exact_readback": True,
            "source_receipt_hash": receipts["skap_kv"]["receipt_hash"],
            "object_sha256": "sha256:" + "b" * 64,
            "credential_material_present": False,
        },
    }
    return manifest


def test_four_leg_manifest_verifies_as_one_roundtrip(tmp_path):
    proof = verify_manifest(build_manifest(tmp_path), runtime_root=tmp_path)
    assert proof["state"] == "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED"
    assert proof["boundary_stack"] == ["DEVICE_SYSTEM", "KV", "SKAP_VAULT", "KV", "DEVICE_SYSTEM"]
    assert proof["receipt_hash_chain_complete"] is True
    assert proof["exact_packet_hashes_verified"] is True
    assert proof["credential_authority"] == "TV/TVC"
    assert proof["authority_effect"] == "NONE_EVIDENCE_ONLY"


def test_detached_skap_return_fails_closed(tmp_path):
    manifest = build_manifest(tmp_path)
    intent_path = tmp_path / manifest["skap_kv"]["intent_path"]
    intent = json.loads(intent_path.read_text())
    intent["prior_transport_receipt_hash"] = None
    intent_path.write_text(json.dumps(intent), encoding="utf-8")
    with pytest.raises(RoundTripEvidenceError, match="skap_kv_intent_prior_hash_mismatch"):
        verify_manifest(manifest, runtime_root=tmp_path)


def test_mutated_exact_packet_bytes_fail_closed(tmp_path):
    manifest = build_manifest(tmp_path)
    (tmp_path / manifest["kv_skap"]["payload_path"]).write_bytes(b"changed")
    with pytest.raises(RoundTripEvidenceError, match="kv_skap_exact_packet_hash_mismatch"):
        verify_manifest(manifest, runtime_root=tmp_path)


def test_missing_exact_readback_fails_closed(tmp_path):
    manifest = build_manifest(tmp_path)
    manifest["readback"]["skap"]["exact_readback"] = False
    with pytest.raises(RoundTripEvidenceError, match="skap_exact_readback_not_observed"):
        verify_manifest(manifest, runtime_root=tmp_path)


def test_wrong_credential_authority_fails_closed(tmp_path):
    manifest = build_manifest(tmp_path)
    intent_path = tmp_path / manifest["device_kv"]["intent_path"]
    intent = json.loads(intent_path.read_text())
    intent["authority"]["credential_authority"] = "OTHER"
    intent_path.write_text(json.dumps(intent), encoding="utf-8")
    with pytest.raises(RoundTripEvidenceError, match="device_kv_credential_authority_invalid"):
        verify_manifest(manifest, runtime_root=tmp_path)
