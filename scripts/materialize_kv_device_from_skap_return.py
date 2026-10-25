#!/usr/bin/env python3
"""Materialize the KV->DEVICE_SYSTEM return leg from the in-KV SKAP gate exchange.

KV and the SKAP Vault are one organisation, so KV<->SKAP is the in-KV SKAP gate, not
an InTr hop (StegVerse-org/.github#167 ruling c6393224851 (3); ruling C accepted with conditions
C1-C3, c6393756343). The round trip has two InTr legs, DEVICE_SYSTEM->KV and KV->DEVICE_SYSTEM:

1. the DEVICE->KV terminal receipt is validated first;
2. the in-KV gate exchange is the continuity-vault-kit layer-2 SKAP-access receipt
   (SkapLayer2Gate.admit, KV_INTERNAL_SKAP_GATE), re-derived from its bytes, whose prior is the
   layer-1 KV-access receipt (KVInterlockRuntime.handle, INTR_DEVICE_KV) of that same DEVICE->KV hop.
   It is bound by the sha256 of its exact bytes (``kv_skap_gate_exchange_hash``). No SKAP->KV InTr
   packet is taken as input;
3. the return payload carries that hash. It is persisted and read back at KV, and
   only then is the device-kv response packet built, with
   prior_transport_receipt_hash equal to the DEVICE->KV terminal receipt.

This module has no credential, provider, transition-admission or hosted-runtime authority.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from workers.device_kv_skap_roundtrip_verifier import GATE_EXCHANGE_FIELD, Layer2BindingRefused, bind_layer2_skap_access_receipt

PROFILE_ID = "device-kv"
RETURN_SCHEMA = "stegverse.kv-skap.gate-return/v1"
OUT_REL = Path("receipts/sovereign-host/device-kv-skap-roundtrip")
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")


class KVDeviceReturnError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: bytes | Mapping[str, Any]) -> str:
    raw = value if isinstance(value, (bytes, bytearray)) else canonical(value)
    return "sha256:" + hashlib.sha256(bytes(raw)).hexdigest()


def atomic_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise KVDeviceReturnError("write_once_collision:" + str(path))
        return
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_bytes(raw); os.replace(tmp, path)


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    atomic_bytes(path, (json.dumps(dict(value), indent=2, sort_keys=True) + "\n").encode("utf-8"))


def _replace_json(path: Path, value: Mapping[str, Any]) -> None:
    """A latest pointer is replaced, never write-once (each round trip has its own write-once result)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_bytes((json.dumps(dict(value), indent=2, sort_keys=True) + "\n").encode("utf-8")); os.replace(tmp, path)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise KVDeviceReturnError("object_required:" + str(path))
    return value


def _load_stegos(stegos_root: Path):
    root = stegos_root.expanduser().resolve()
    registry = root / "specs/universal-intr-connector-profiles.v1.json"
    if not registry.is_file():
        raise KVDeviceReturnError("canonical_stegos_registry_missing")
    text = str(root)
    if text not in sys.path: sys.path.insert(0, text)
    backbone = importlib.import_module("stegos.intr_backbone")
    transport = importlib.import_module("stegos.universal_intr_transport")
    if root not in Path(backbone.__file__).resolve().parents or root not in Path(transport.__file__).resolve().parents:
        raise KVDeviceReturnError("canonical_stegos_module_root_mismatch")
    connector = backbone.connector_from_registry(registry, PROFILE_ID)
    return connector, backbone, transport


def validate_device_kv_receipt(receipt: Any) -> str:
    """Return the DEVICE_SYSTEM->KV terminal receipt hash, fail-closed."""
    if not isinstance(receipt, Mapping) or receipt.get("schema") != "stegverse.intr.hop_receipt/v1":
        raise KVDeviceReturnError("device_kv_receipt_schema_invalid")
    if receipt.get("from_role") != "DEVICE_SYSTEM" or receipt.get("to_role") != "KV":
        raise KVDeviceReturnError("device_kv_receipt_boundary_invalid")
    body = dict(receipt); claimed = body.pop("receipt_hash", None)
    if not isinstance(claimed, str) or not claimed.startswith("sha256:") or claimed != sha_uri(body):
        raise KVDeviceReturnError("device_kv_receipt_hash_invalid")
    return claimed


def bind_gate_exchange(*, kv_access_receipt: Any, skap_access_receipt: Any, device_kv_terminal: str) -> tuple[bytes, str]:
    """C1/C2: the exact layer-2 SKAP-access receipt bytes and their hash, or KVDeviceReturnError carrying the six-field FAIL_CLOSED."""
    try:
        return bind_layer2_skap_access_receipt(kv_access_receipt=kv_access_receipt, skap_access_receipt=skap_access_receipt, device_kv_terminal_receipt_hash=device_kv_terminal)
    except Layer2BindingRefused as exc:
        err = KVDeviceReturnError(str(exc)); err.fail_closed = exc.fail_closed
        raise err from exc


def materialize(*, runtime_root: Path, stegos_root: Path, materialization_id: str, device_kv_receipt: Mapping[str, Any], kv_access_receipt: Mapping[str, Any], skap_access_receipt: Mapping[str, Any], stored_object_sha256: str, operation_id: str | None = None) -> dict[str, Any]:
    if any(os.environ.get(name) for name in HOSTED_ENV):
        raise KVDeviceReturnError("hosted_runtime_forbidden")
    terminal = validate_device_kv_receipt(device_kv_receipt)
    gate_bytes, gate_hash = bind_gate_exchange(kv_access_receipt=kv_access_receipt, skap_access_receipt=skap_access_receipt, device_kv_terminal=terminal)
    if not isinstance(stored_object_sha256, str) or not stored_object_sha256.startswith("sha256:") or len(stored_object_sha256) != 71:
        raise KVDeviceReturnError("kv_skap_gate_stored_object_hash_invalid")
    connector, backbone, transport = _load_stegos(stegos_root)

    base = runtime_root.expanduser().resolve() / OUT_REL / materialization_id
    atomic_bytes(base / "kv-skap-gate-exchange.json", gate_bytes)
    atomic_bytes(base / "kv-access-receipt.json", canonical(dict(kv_access_receipt)))
    op = str(operation_id or materialization_id)
    return_payload = {
        "schema": RETURN_SCHEMA,
        "state": "KV_SKAP_GATE_EXCHANGE_BOUND",
        "operation_id": op,
        GATE_EXCHANGE_FIELD: gate_hash,
        "device_kv_terminal_receipt_hash": terminal,
        "kv_access_receipt_hash": kv_access_receipt["receipt_hash"],
        "skap_access_receipt_hash": skap_access_receipt["receipt_hash"],
        "stored_object_sha256": stored_object_sha256,
        "exact_ciphertext_readback_verified": True,
        "kv_skap_path": "IN_KV_GATE",
        "kv_skap_intr_hop": False,
        "secret_plaintext_present": False,
        "credential_material_present": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_EVIDENCE_ONLY",
    }
    raw_return = canonical(return_payload)
    kv_object = base / "kv-return-object.bin"
    atomic_bytes(kv_object, raw_return)
    kv_readback = kv_object.read_bytes()
    if kv_readback != raw_return:
        raise KVDeviceReturnError("kv_exact_readback_mismatch")

    response = connector.profile.response
    if response is None:
        raise KVDeviceReturnError("device_kv_response_not_supported")
    source, destination = response
    intent = transport.build_transport_intent(
        operation_id=op + ":device-return",
        payload_hash=backbone.sha256_uri(kv_readback),
        source_boundary=source["boundary"], source_subsystem=source["subsystem"],
        destination_boundary=destination["boundary"], destination_subsystem=destination["subsystem"],
        prior_transport_receipt_hash=terminal,
    )
    packet = backbone.PreparedPacket(connector.profile, "RESPONSE", RETURN_SCHEMA, kv_readback, intent)
    receipt = connector.accept_hop(
        packet, hop_index=1,
        receipt_id="KV-DEVICE-" + intent["packet_id"],
        boundary_identity_ref="device://current/KnowledgeVaultClient",
        recorded_at=now(), prior_receipt_hash=terminal, transition_state="RECEIVED",
    )
    completed = connector.validate_complete(packet, [receipt])
    if completed.get("terminal_receipt_hash") != receipt.get("receipt_hash"):
        raise KVDeviceReturnError("kv_device_terminal_receipt_mismatch")

    atomic_json(base / "kv-to-device.intent.json", intent)
    atomic_bytes(base / "kv-to-device.payload.bin", kv_readback)
    atomic_json(base / "kv-to-device.receipt.json", receipt)
    readback = {
        "schema": "stegverse.device-kv-skap.kv-readback/v2",
        "observed": True,
        "exact_readback": True,
        GATE_EXCHANGE_FIELD: gate_hash,
        "object_sha256": backbone.sha256_uri(kv_readback),
        "credential_material_present": False,
        "authority_effect": "NONE_EVIDENCE_ONLY",
    }
    atomic_json(base / "kv-readback.json", readback)
    result = {
        "schema": "stegverse.device-kv-skap.kv-device-return/v2",
        "state": "KV_TO_DEVICE_RETURN_PERSISTED",
        "materialization_id": materialization_id,
        "device_kv_terminal_receipt_hash": terminal,
        GATE_EXCHANGE_FIELD: gate_hash,
        "kv_device_terminal_receipt_hash": receipt["receipt_hash"],
        "kv_exact_readback_verified": True,
        "kv_object_sha256": readback["object_sha256"],
        "kv_skap_gate_exchange_ref": str(base / "kv-skap-gate-exchange.json"),
        "kv_access_receipt_ref": str(base / "kv-access-receipt.json"),
        "kv_access_receipt_hash": kv_access_receipt["receipt_hash"],
        "skap_access_receipt_hash": skap_access_receipt["receipt_hash"],
        "kv_device_intent_ref": str(base / "kv-to-device.intent.json"),
        "kv_device_payload_ref": str(base / "kv-to-device.payload.bin"),
        "kv_device_receipt_ref": str(base / "kv-to-device.receipt.json"),
        "kv_readback_ref": str(base / "kv-readback.json"),
        "boundary_stack": ["DEVICE_SYSTEM", "KV", "DEVICE_SYSTEM"],
        "kv_skap_path": "IN_KV_GATE",
        "kv_skap_intr_hop": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "secret_plaintext_present": False,
        "authority_effect": "NONE_EVIDENCE_ONLY",
    }
    atomic_json(base / "kv-to-device.result.json", result)
    _replace_json(runtime_root.expanduser().resolve() / OUT_REL / "kv-to-device.latest.json", result)
    return result


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--runtime-root", type=Path, required=True); p.add_argument("--stegos-root", type=Path, required=True)
    p.add_argument("--materialization-id", required=True); p.add_argument("--device-kv-receipt", type=Path, required=True)
    p.add_argument("--kv-access-receipt", type=Path, required=True); p.add_argument("--skap-access-receipt", type=Path, required=True)
    p.add_argument("--stored-object-sha256", required=True)
    a = p.parse_args()
    try:
        result = materialize(runtime_root=a.runtime_root, stegos_root=a.stegos_root, materialization_id=a.materialization_id, device_kv_receipt=load_json(a.device_kv_receipt), kv_access_receipt=load_json(a.kv_access_receipt), skap_access_receipt=load_json(a.skap_access_receipt), stored_object_sha256=a.stored_object_sha256)
    except Exception as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc), "fail_closed": getattr(exc, "fail_closed", None), "authority_effect": "NONE"}, sort_keys=True)); return 1
    print(json.dumps(result, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
