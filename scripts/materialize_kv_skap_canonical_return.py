#!/usr/bin/env python3
"""Materialize the canonical DEVICE->KV->DEVICE return around the in-KV SKAP gate.

KV and the SKAP Vault are one organisation, so KV<->SKAP is the in-KV SKAP gate, not
an InTr hop (StegVerse-org/.github#167 ruling c6393224851 (3); PROVISIONAL_ON_RULING_C).
No KV->SKAP or SKAP->KV InTr packet is prepared, and no retired StegOS connector profile
(kv-skap, kv-skap-custody or kv-skap-account-metadata) is resolved. Only the genuine
cross-boundary device-kv profile is used, for the KV->DEVICE return leg.

This bridge keeps the TVC double-Interlock custody admission as it is. Once that
admission has persisted the ciphertext, it:

1. requires an exact readback of the SKAP Vault object;
2. binds the in-KV gate exchange to the canonical DEVICE->KV terminal receipt, by the
   sha256 of the exchange's exact bytes;
3. emits the final KV->DEVICE leg carrying that hash.

No plaintext, credential resolution, provider operation or execution authority is introduced.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Mapping

PROFILE_ID = "device-kv"
CAPSULE_SCHEMA = "stegverse.skap.browser_ingress/p256-ecdh-hkdf-sha256-aes256gcm/v1"
OUT_REL = Path("receipts/sovereign-host/kv-skap-gate-roundtrip")


class CanonicalKVSkapReturnError(ValueError): pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
def sha_uri(raw: bytes) -> str: return "sha256:" + hashlib.sha256(raw).hexdigest()
def atomic_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw: raise CanonicalKVSkapReturnError("write_once_collision:" + str(path))
        return
    tmp = path.with_name("." + path.name + ".tmp"); tmp.write_bytes(raw); os.replace(tmp, path)
def atomic_json(path: Path, value: Mapping[str, Any]) -> None: atomic_bytes(path, (json.dumps(dict(value), indent=2, sort_keys=True) + "\n").encode("utf-8"))


def _device_return_module():
    path = Path(__file__).resolve().parent / "materialize_kv_device_from_skap_return.py"
    spec = importlib.util.spec_from_file_location("stegverse_kv_device_from_skap_gate", path)
    if spec is None or spec.loader is None: raise CanonicalKVSkapReturnError("kv_device_return_loader_unavailable")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    if getattr(mod, "PROFILE_ID", None) != PROFILE_ID: raise CanonicalKVSkapReturnError("kv_device_return_profile_mismatch")
    return mod


def materialize(*, request: Mapping[str, Any], persisted: Mapping[str, Any], runtime_root: Path, stegos_root: Path) -> dict[str, Any]:
    canonical_device = request.get("canonical_device_kv_receipt")
    if not isinstance(canonical_device, Mapping): raise CanonicalKVSkapReturnError("canonical_device_kv_receipt_required")
    capsule = request.get("sealed_capsule")
    if not isinstance(capsule, Mapping) or capsule.get("schema") != CAPSULE_SCHEMA: raise CanonicalKVSkapReturnError("sealed_capsule_invalid")
    device_return = _device_return_module()
    try:
        device_hash = device_return.validate_device_kv_receipt(canonical_device)
    except device_return.KVDeviceReturnError as exc:
        raise CanonicalKVSkapReturnError("canonical_" + str(exc)) from exc
    credential_path = Path(str(persisted.get("credential_path") or ""))
    if not credential_path.is_file(): raise CanonicalKVSkapReturnError("skap_exact_readback_object_missing")
    stored = credential_path.read_bytes()
    if stored != canonical(dict(capsule)): raise CanonicalKVSkapReturnError("skap_exact_readback_mismatch")
    if sha_uri(stored) != request.get("payload_hash"): raise CanonicalKVSkapReturnError("skap_exact_readback_payload_hash_mismatch")
    gate_exchange = device_return.build_gate_exchange(
        operation_id=str(request["operation_id"]), credential_ref=capsule.get("credential_ref"),
        device_kv_terminal=device_hash, stored_object_sha256=sha_uri(stored),
        custody_evidence={"gate_request_hash": request.get("request_hash"), "custody_receipt_ref": str(persisted.get("custody_receipt_path") or ""), "skap_vault_storage_backend": persisted.get("backend_id")},
    )
    returned = device_return.materialize(runtime_root=runtime_root, stegos_root=stegos_root, materialization_id=str(request["materialization_id"]), device_kv_receipt=canonical_device, gate_exchange_bytes=gate_exchange, operation_id=str(request["operation_id"]))
    result = {
        "schema": "stegverse.kv-skap.gate-roundtrip/v1", "state": "KV_TO_DEVICE_RETURN_PERSISTED",
        "materialization_id": request["materialization_id"], "operation_id": request["operation_id"],
        "canonical_device_kv_receipt_hash": device_hash,
        "kv_skap_gate_exchange_hash": returned["kv_skap_gate_exchange_hash"],
        "kv_device_terminal_receipt_hash": returned["kv_device_terminal_receipt_hash"],
        "boundary_stack": ["DEVICE_SYSTEM", "KV", "DEVICE_SYSTEM"], "kv_skap_path": "IN_KV_GATE", "kv_skap_intr_hop": False,
        "exact_ciphertext_readback_verified": True, "kv_exact_readback_verified": returned["kv_exact_readback_verified"],
        "kv_skap_gate_exchange_ref": returned["kv_skap_gate_exchange_ref"],
        "kv_device_intent_ref": returned["kv_device_intent_ref"], "kv_device_payload_ref": returned["kv_device_payload_ref"],
        "kv_device_receipt_ref": returned["kv_device_receipt_ref"], "kv_readback_ref": returned["kv_readback_ref"],
        "credential_authority": "TV/TVC", "github_token_runtime_authority": "NONE", "secret_plaintext_present": False,
        "authority_effect": "NONE_CUSTODY_TRANSITION_ONLY",
    }
    base = runtime_root.expanduser().resolve() / OUT_REL / str(request["materialization_id"])
    atomic_json(base / "roundtrip.json", result); atomic_json(runtime_root.expanduser().resolve() / OUT_REL / "latest.json", result)
    return result
