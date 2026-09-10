#!/usr/bin/env python3
"""Verify one authentic DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM lineage.

This worker consumes existing canonical InTr evidence only. It cannot mint hop
receipts, grant transition/credential authority, or convert CI/source state into
runtime evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

TASK_ID = "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001"
INPUT_SCHEMA = "stegverse.device-kv-skap.runtime-roundtrip-input/v1"
PROOF_SCHEMA = "stegverse.device-kv-skap.runtime-roundtrip-proof/v1"
INTENT_SCHEMA = "stegverse.universal-intr-transport/v1"
RECEIPT_SCHEMA = "stegverse.intr.hop_receipt/v1"
HOSTED_ENV = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
RECEIPT_FIELDS = {
    "schema", "receipt_id", "packet_id", "hop_index", "direction", "from_role", "to_role",
    "operation_hash", "payload_hash", "prior_receipt_hash", "boundary_identity_ref",
    "boundary_verification", "transition_state", "secret_plaintext_present", "authority_transfer",
    "recorded_at", "receipt_hash",
}
LEG_ORDER = (
    ("device_kv", "DEVICE_SYSTEM", "KV"),
    ("kv_skap", "KV", "SKAP_VAULT"),
    ("skap_kv", "SKAP_VAULT", "KV"),
    ("kv_device", "KV", "DEVICE_SYSTEM"),
)


class RoundTripEvidenceError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: bytes | Mapping[str, Any]) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RoundTripEvidenceError(reason)


def _valid_sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 71 and value.startswith("sha256:") and all(c in "0123456789abcdef" for c in value[7:])


def _resolve_file(root: Path, value: Any, label: str) -> Path:
    require(isinstance(value, str) and value, f"{label}_path_required")
    path = (root / value).resolve()
    root_resolved = root.resolve()
    require(path == root_resolved or root_resolved in path.parents, f"{label}_path_escape")
    require(path.is_file(), f"{label}_file_missing")
    return path


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RoundTripEvidenceError(f"{label}_json_invalid") from exc
    require(isinstance(value, dict), f"{label}_object_required")
    return value


def _validate_leg(*, name: str, expected_from: str, expected_to: str, intent: Mapping[str, Any], receipt: Mapping[str, Any], payload: bytes, expected_prior: str | None) -> str:
    require(intent.get("schema") == INTENT_SCHEMA and intent.get("protocol") == "InTr", f"{name}_intent_schema_invalid")
    require(intent.get("boundary_path") == [expected_from, expected_to], f"{name}_boundary_path_invalid")
    require((intent.get("source") or {}).get("boundary") == expected_from, f"{name}_source_boundary_invalid")
    require((intent.get("destination") or {}).get("boundary") == expected_to, f"{name}_destination_boundary_invalid")
    require(bool((intent.get("source") or {}).get("subsystem")) and bool((intent.get("destination") or {}).get("subsystem")), f"{name}_subsystem_identity_required")
    require(intent.get("interlock_required") is True, f"{name}_interlock_required")
    require(intent.get("prior_transport_receipt_hash") == expected_prior, f"{name}_intent_prior_hash_mismatch")
    require(intent.get("payload_hash") == sha_uri(payload), f"{name}_exact_packet_hash_mismatch")
    require(isinstance(intent.get("operation_id"), str) and bool(intent.get("operation_id")), f"{name}_operation_id_required")
    require(isinstance(intent.get("packet_id"), str) and intent.get("packet_id", "").startswith("INTR-"), f"{name}_packet_id_invalid")
    authority = intent.get("authority") or {}
    require(authority.get("authority_transfer") is False, f"{name}_intent_authority_transfer_forbidden")
    require(authority.get("transport_grants_execution_authority") is False, f"{name}_intent_execution_authority_forbidden")
    require(authority.get("credential_authority") == "TV/TVC", f"{name}_credential_authority_invalid")

    require(set(receipt) == RECEIPT_FIELDS, f"{name}_receipt_field_set_invalid")
    require(receipt.get("schema") == RECEIPT_SCHEMA, f"{name}_receipt_schema_invalid")
    require(receipt.get("packet_id") == intent.get("packet_id"), f"{name}_receipt_packet_mismatch")
    require(receipt.get("hop_index") == 1 and receipt.get("direction") == "FORWARD", f"{name}_receipt_hop_invalid")
    require(receipt.get("from_role") == expected_from and receipt.get("to_role") == expected_to, f"{name}_receipt_boundary_invalid")
    expected_operation_hash = sha_uri({
        "operation_id": intent["operation_id"],
        "packet_id": intent["packet_id"],
        "payload_hash": intent["payload_hash"],
    })
    require(receipt.get("operation_hash") == expected_operation_hash, f"{name}_receipt_operation_hash_mismatch")
    require(receipt.get("payload_hash") == intent.get("payload_hash"), f"{name}_receipt_payload_mismatch")
    require(receipt.get("prior_receipt_hash") == expected_prior, f"{name}_receipt_prior_hash_mismatch")
    require(isinstance(receipt.get("boundary_identity_ref"), str) and bool(receipt.get("boundary_identity_ref")), f"{name}_boundary_identity_required")
    require(receipt.get("boundary_verification") == "VERIFIED", f"{name}_boundary_not_verified")
    require(receipt.get("transition_state") == "RECEIVED", f"{name}_transition_not_received")
    require(receipt.get("secret_plaintext_present") is False, f"{name}_secret_plaintext_forbidden")
    require(receipt.get("authority_transfer") is False, f"{name}_receipt_authority_transfer_forbidden")
    require(isinstance(receipt.get("recorded_at"), str) and bool(receipt.get("recorded_at")), f"{name}_recorded_at_required")
    body = dict(receipt)
    claimed = body.pop("receipt_hash", None)
    require(_valid_sha(claimed) and claimed == sha_uri(body), f"{name}_receipt_hash_invalid")
    return claimed


def _validate_readback(value: Any, *, label: str, expected_receipt: str) -> dict[str, Any]:
    require(isinstance(value, Mapping), f"{label}_readback_required")
    require(value.get("observed") is True and value.get("exact_readback") is True, f"{label}_exact_readback_not_observed")
    require(value.get("source_receipt_hash") == expected_receipt, f"{label}_readback_receipt_mismatch")
    require(_valid_sha(value.get("object_sha256")), f"{label}_readback_object_hash_invalid")
    require(value.get("credential_material_present") is False, f"{label}_credential_material_forbidden")
    return {
        "source_receipt_hash": value["source_receipt_hash"],
        "object_sha256": value["object_sha256"],
        "exact_readback": True,
    }


def verify_manifest(manifest: Mapping[str, Any], *, runtime_root: Path) -> dict[str, Any]:
    require(manifest.get("schema") == INPUT_SCHEMA, "roundtrip_input_schema_invalid")
    require(manifest.get("task_id") == TASK_ID, "roundtrip_task_id_invalid")
    require(manifest.get("current_device") is True, "current_device_evidence_required")
    require(manifest.get("hosted_runtime_used") is False, "hosted_runtime_forbidden")
    require(manifest.get("second_user_operated_device_used") is False, "second_user_device_forbidden")

    previous: str | None = None
    receipt_hashes: dict[str, str] = {}
    packet_hashes: dict[str, str] = {}
    for name, expected_from, expected_to in LEG_ORDER:
        leg = manifest.get(name)
        require(isinstance(leg, Mapping), f"{name}_leg_required")
        intent_path = _resolve_file(runtime_root, leg.get("intent_path"), f"{name}_intent")
        payload_path = _resolve_file(runtime_root, leg.get("payload_path"), f"{name}_payload")
        receipt_path = _resolve_file(runtime_root, leg.get("receipt_path"), f"{name}_receipt")
        intent = _load_json(intent_path, f"{name}_intent")
        receipt = _load_json(receipt_path, f"{name}_receipt")
        payload = payload_path.read_bytes()
        previous = _validate_leg(
            name=name,
            expected_from=expected_from,
            expected_to=expected_to,
            intent=intent,
            receipt=receipt,
            payload=payload,
            expected_prior=previous,
        )
        receipt_hashes[name] = previous
        packet_hashes[name] = intent["payload_hash"]

    readback = manifest.get("readback")
    require(isinstance(readback, Mapping), "roundtrip_readback_required")
    skap_readback = _validate_readback(readback.get("skap"), label="skap", expected_receipt=receipt_hashes["kv_skap"])
    kv_readback = _validate_readback(readback.get("kv"), label="kv", expected_receipt=receipt_hashes["skap_kv"])

    proof = {
        "schema": PROOF_SCHEMA,
        "task_id": TASK_ID,
        "state": "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED",
        "boundary_stack": ["DEVICE_SYSTEM", "KV", "SKAP_VAULT", "KV", "DEVICE_SYSTEM"],
        "receipt_hashes": receipt_hashes,
        "packet_hashes": packet_hashes,
        "skap_readback": skap_readback,
        "kv_readback": kv_readback,
        "receipt_hash_chain_complete": True,
        "exact_packet_hashes_verified": True,
        "interlock_verified_per_hop": True,
        "credential_authority": "TV/TVC",
        "secret_plaintext_present": False,
        "authority_transfer": False,
        "github_runtime_authority": "NONE",
        "hosted_runtime_used": False,
        "second_user_operated_device_used": False,
        "authority_effect": "NONE_EVIDENCE_ONLY",
    }
    proof["proof_sha256"] = sha_uri(proof)
    return proof


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if any(os.environ.get(name) for name in HOSTED_ENV):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:hosted_runtime_forbidden")
    manifest = _load_json(args.manifest, "manifest")
    proof = verify_manifest(manifest, runtime_root=args.runtime_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(proof, sort_keys=True, indent=2) + "\n"
    if args.output.exists() and args.output.read_text(encoding="utf-8") != raw:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:write_once_collision")
    args.output.write_text(raw, encoding="utf-8")
    print(json.dumps(proof, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
