#!/usr/bin/env python3
"""Verify one authentic two-leg DEVICE_SYSTEM -> KV -> DEVICE_SYSTEM lineage with its in-KV SKAP gate exchange.

KV and the SKAP Vault are one organisation, so KV<->SKAP is the in-KV SKAP gate, not an InTr hop
(StegVerse-org/.github#167 ruling c6393224851 (3); ruling C accepted with conditions C1-C3 in c6393756343).
The two InTr legs are:

- device_kv, DEVICE_SYSTEM -> KV;
- kv_device, KV -> DEVICE_SYSTEM, whose prior is the device_kv receipt.

The in-KV gate exchange in between is the continuity-vault-kit layer-2 SKAP-access receipt itself
(``SkapLayer2Gate.admit``, boundary KV_INTERNAL_SKAP_GATE, from KV), re-derived from its bytes and never taken
on a caller's word (C1). Its ``prior_receipt_hash`` must be the layer-1 KV-access receipt that
``KVInterlockRuntime.handle`` (INTR_DEVICE_KV) minted for this same device_kv hop (C2).
``kv_skap_gate_exchange_hash`` is the sha256 of the layer-2 receipt's exact canonical bytes, and the
kv_device payload must carry it. Any mismatch is a six-field FAIL_CLOSED, never a fallback. A manifest that
still carries kv_skap or skap_kv InTr legs fails closed (C3).

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
INPUT_SCHEMA = "stegverse.device-kv-skap.runtime-roundtrip-input/v2"
PROOF_SCHEMA = "stegverse.device-kv-skap.runtime-roundtrip-proof/v2"
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
    ("kv_device", "KV", "DEVICE_SYSTEM"),
)
RETIRED_KV_SKAP_LEGS = ("kv_skap", "skap_kv")
GATE_EXCHANGE_FIELD = "kv_skap_gate_exchange_hash"
# continuity-vault-kit runtime/kv_skap_layer2.py and runtime/kv_interlock_endpoint.py (StegVerse-Labs/continuity-vault-kit)
KV_ACCESS_RECEIPT_SCHEMA = "stegverse.kv-access-receipt/v1"
SKAP_ACCESS_RECEIPT_SCHEMA = "stegverse.skap-access-receipt/v1"
LAYER1_BOUNDARY = "INTR_DEVICE_KV"
LAYER2_BOUNDARY = "KV_INTERNAL_SKAP_GATE"
LAYER1_MINTED_BY = "KVInterlockRuntime.handle"
LAYER2_MINTED_BY = "SkapLayer2Gate.admit"
LAYER2_OPERATIONS = ("BIND_CUSTODY_KEY_REFERENCE", "SKAP_WRITE", "SKAP_READ", "RECONSTRUCT", "CONSENT_GRANT",
                     "CONSENT_REVOKE", "SKAP_SEALED_CREDENTIAL_APPEND", "SKAP_SEALED_CREDENTIAL_READ")
LAYER2_BINDING_FAILURE_CODE = "KV_SKAP_LAYER2_ACCESS_RECEIPT_BINDING_REFUSED"


class RoundTripEvidenceError(ValueError):
    pass


class Layer2BindingRefused(RoundTripEvidenceError):
    """A six-field FAIL_CLOSED (CODE, CLASS, OBSERVED, EXPECTED, BLOCKS, NEXT). There is no fallback leg."""

    def __init__(self, cause: str, failure_class: str, observed: str, expected: str) -> None:
        self.fail_closed = {
            "CODE": LAYER2_BINDING_FAILURE_CODE,
            "CLASS": failure_class,
            "OBSERVED": f"{cause}: {observed}",
            "EXPECTED": expected,
            "BLOCKS": "the KV->DEVICE_SYSTEM return leg and the round-trip proof",
            "NEXT": ("a new DEVICE->KV InTr transition admitted by KVInterlockRuntime.handle, then SkapLayer2Gate.admit "
                     "on that layer-1 receipt; the four-leg KV<->SKAP InTr path is retired and is never used"),
        }
        super().__init__(cause)


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


def _rederives(receipt: Any) -> bool:
    if not isinstance(receipt, Mapping):
        return False
    claimed = receipt.get("receipt_hash")
    return _valid_sha(claimed) and claimed == sha_uri({k: v for k, v in receipt.items() if k != "receipt_hash"})


def bind_layer2_skap_access_receipt(*, kv_access_receipt: Any, skap_access_receipt: Any, device_kv_terminal_receipt_hash: str) -> tuple[bytes, str]:
    """C1/C2: return (exact layer-2 receipt bytes, kv_skap_gate_exchange_hash), or raise a six-field Layer2BindingRefused.

    Both receipts are re-derived from their own bytes. No caller-supplied hash is accepted."""
    l1, l2 = kv_access_receipt, skap_access_receipt
    if not _rederives(l1):
        raise Layer2BindingRefused("layer1_kv_access_receipt_not_rederived", "C", "the layer-1 receipt_hash does not re-derive from its body",
                                   "a stegverse.kv-access-receipt/v1 whose receipt_hash is the sha256 of its canonical body")
    if (l1.get("schema"), l1.get("boundary"), l1.get("minted_by"), l1.get("layer"), l1.get("from_role"), l1.get("to_role")) != (
            KV_ACCESS_RECEIPT_SCHEMA, LAYER1_BOUNDARY, LAYER1_MINTED_BY, 1, "DEVICE", "KV"):
        raise Layer2BindingRefused("layer1_kv_access_receipt_invalid", "C", f"schema={l1.get('schema')!r} boundary={l1.get('boundary')!r} minted_by={l1.get('minted_by')!r}",
                                   "a layer-1 DEVICE->KV receipt minted by KVInterlockRuntime.handle at INTR_DEVICE_KV")
    if not isinstance(l1.get("healthy_node_receipt"), Mapping) or l1["healthy_node_receipt"].get("healthy_node_established") is not True:
        raise Layer2BindingRefused("layer1_healthy_node_not_established", "C", "healthy_node_receipt.healthy_node_established is not true",
                                   "layer 1 admits only a currently admitted healthy node")
    if l1.get("intr_receipt_ref") != device_kv_terminal_receipt_hash:
        raise Layer2BindingRefused("layer1_not_for_this_device_kv_hop", "C", f"intr_receipt_ref={l1.get('intr_receipt_ref')!r}",
                                   f"the layer-1 receipt of this DEVICE->KV hop, intr_receipt_ref={device_kv_terminal_receipt_hash}")
    if not _rederives(l2):
        raise Layer2BindingRefused("layer2_skap_access_receipt_not_rederived", "C", "the layer-2 receipt_hash does not re-derive from its body",
                                   "a stegverse.skap-access-receipt/v1 whose receipt_hash is the sha256 of its canonical body")
    if (l2.get("schema"), l2.get("boundary"), l2.get("minted_by"), l2.get("layer"), l2.get("from_role"), l2.get("to_role")) != (
            SKAP_ACCESS_RECEIPT_SCHEMA, LAYER2_BOUNDARY, LAYER2_MINTED_BY, 2, "KV", "SKAP_VAULT"):
        raise Layer2BindingRefused("layer2_skap_access_receipt_invalid", "C", f"schema={l2.get('schema')!r} boundary={l2.get('boundary')!r} minted_by={l2.get('minted_by')!r} from_role={l2.get('from_role')!r}",
                                   "a layer-2 KV->SKAP_VAULT receipt minted by SkapLayer2Gate.admit at KV_INTERNAL_SKAP_GATE")
    if l2.get("operation") not in LAYER2_OPERATIONS or l2.get("authority_effect") != "NONE":
        raise Layer2BindingRefused("layer2_skap_access_receipt_scope_invalid", "C", f"operation={l2.get('operation')!r} authority_effect={l2.get('authority_effect')!r}",
                                   "one cvk layer-2 operation and authority_effect NONE")
    if l2.get("prior_receipt_hash") != l1["receipt_hash"]:
        raise Layer2BindingRefused("layer2_not_chained_to_layer1", "C", f"prior_receipt_hash={l2.get('prior_receipt_hash')!r}",
                                   f"prior_receipt_hash={l1['receipt_hash']} (the layer-1 KV-access receipt)")
    if l2.get("layer1_intr_receipt_ref") != l1.get("intr_receipt_ref") or l2.get("layer1_requester_node_ref") != l1.get("requester_node_ref"):
        raise Layer2BindingRefused("layer2_layer1_reference_mismatch", "C", "layer1_intr_receipt_ref or layer1_requester_node_ref differs from the layer-1 receipt",
                                   "the layer-2 receipt names the same InTr receipt and requester node as its layer-1 receipt")
    raw = canonical(dict(l2))
    return raw, sha_uri(raw)


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


def _validate_readback(value: Any, *, label: str, gate_hash: str, expected_object: str) -> dict[str, Any]:
    require(isinstance(value, Mapping), f"{label}_readback_required")
    require(value.get("observed") is True and value.get("exact_readback") is True, f"{label}_exact_readback_not_observed")
    require(value.get(GATE_EXCHANGE_FIELD) == gate_hash, f"{label}_readback_gate_exchange_mismatch")
    require(_valid_sha(value.get("object_sha256")), f"{label}_readback_object_hash_invalid")
    require(value.get("object_sha256") == expected_object, f"{label}_readback_object_mismatch")
    require(value.get("credential_material_present") is False, f"{label}_credential_material_forbidden")
    return {
        GATE_EXCHANGE_FIELD: gate_hash,
        "object_sha256": value["object_sha256"],
        "exact_readback": True,
    }


def _validate_gate_exchange(manifest: Mapping[str, Any], *, runtime_root: Path, device_kv_receipt_hash: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
    entry = manifest.get("kv_skap_gate_exchange")
    require(isinstance(entry, Mapping), "kv_skap_gate_exchange_required")
    path = _resolve_file(runtime_root, entry.get("path"), "kv_skap_gate_exchange")
    raw = path.read_bytes()
    gate_hash = sha_uri(raw)
    require(entry.get(GATE_EXCHANGE_FIELD) == gate_hash, "kv_skap_gate_exchange_hash_mismatch")
    skap_access = _load_json(path, "kv_skap_gate_exchange")
    require(canonical(skap_access) == raw, "kv_skap_gate_exchange_not_canonical_bytes")
    kv_access = _load_json(_resolve_file(runtime_root, entry.get("kv_access_receipt_path"), "kv_access_receipt"), "kv_access_receipt")
    bound_raw, bound_hash = bind_layer2_skap_access_receipt(kv_access_receipt=kv_access, skap_access_receipt=skap_access, device_kv_terminal_receipt_hash=device_kv_receipt_hash)
    require(bound_raw == raw and bound_hash == gate_hash, "kv_skap_gate_exchange_not_the_layer2_receipt_bytes")
    return gate_hash, skap_access, kv_access


def verify_manifest(manifest: Mapping[str, Any], *, runtime_root: Path) -> dict[str, Any]:
    require(manifest.get("schema") == INPUT_SCHEMA, "roundtrip_input_schema_invalid")
    require(manifest.get("task_id") == TASK_ID, "roundtrip_task_id_invalid")
    require(manifest.get("current_device") is True, "current_device_evidence_required")
    require(manifest.get("hosted_runtime_used") is False, "hosted_runtime_forbidden")
    require(manifest.get("second_user_operated_device_used") is False, "second_user_device_forbidden")

    retired = [name for name in RETIRED_KV_SKAP_LEGS if name in manifest]
    require(not retired, "kv_skap_intr_leg_retired:" + ",".join(retired))

    previous: str | None = None
    payloads: dict[str, bytes] = {}
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
        payloads[name] = payload

    gate_hash, skap_access, kv_access = _validate_gate_exchange(manifest, runtime_root=runtime_root, device_kv_receipt_hash=receipt_hashes["device_kv"])
    try:
        returned = json.loads(payloads["kv_device"].decode("utf-8"))
    except Exception as exc:
        raise RoundTripEvidenceError("kv_device_payload_json_invalid") from exc
    require(isinstance(returned, Mapping), "kv_device_payload_object_required")
    require(returned.get(GATE_EXCHANGE_FIELD) == gate_hash, "kv_device_payload_gate_exchange_mismatch")
    require(returned.get("device_kv_terminal_receipt_hash") == receipt_hashes["device_kv"], "kv_device_payload_device_kv_binding_mismatch")
    require(returned.get("kv_skap_intr_hop") is False, "kv_device_payload_must_not_claim_kv_skap_intr")
    require(returned.get("skap_access_receipt_hash") == skap_access["receipt_hash"] and returned.get("kv_access_receipt_hash") == kv_access["receipt_hash"], "kv_device_payload_access_receipt_binding_mismatch")
    require(_valid_sha(returned.get("stored_object_sha256")), "kv_device_payload_stored_object_hash_invalid")

    readback = manifest.get("readback")
    require(isinstance(readback, Mapping), "roundtrip_readback_required")
    skap_readback = _validate_readback(readback.get("skap"), label="skap", gate_hash=gate_hash, expected_object=returned["stored_object_sha256"])
    kv_readback = _validate_readback(readback.get("kv"), label="kv", gate_hash=gate_hash, expected_object=sha_uri(payloads["kv_device"]))

    proof = {
        "schema": PROOF_SCHEMA,
        "task_id": TASK_ID,
        "state": "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED",
        "boundary_stack": ["DEVICE_SYSTEM", "KV", "DEVICE_SYSTEM"],
        "kv_skap_path": "IN_KV_GATE",
        "kv_skap_intr_hop": False,
        GATE_EXCHANGE_FIELD: gate_hash,
        "kv_skap_gate": LAYER2_BOUNDARY,
        "kv_access_receipt_hash": kv_access["receipt_hash"],
        "skap_access_receipt_hash": skap_access["receipt_hash"],
        "layer2_chained_to_layer1": True,
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
