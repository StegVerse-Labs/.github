#!/usr/bin/env python3
"""Materialize the final KV->DEVICE_SYSTEM leg from an authentic SKAP->KV receipt.

The SKAP return payload is first persisted/read back at the KV boundary. Only
then is a device-kv response packet built with prior_transport_receipt_hash equal
to the terminal SKAP->KV canonical receipt. This module has no credential,
provider, transition-admission, or hosted-runtime authority.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

PROFILE_ID = "device-kv"
OUT_REL = Path("receipts/sovereign-host/device-kv-skap-roundtrip")
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")

class KVDeviceReturnError(ValueError):
    pass

def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

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

def _valid_receipt(receipt: Mapping[str, Any], *, source: str, destination: str) -> str:
    if receipt.get("schema") != "stegverse.intr.hop_receipt/v1":
        raise KVDeviceReturnError("receipt_schema_invalid")
    if receipt.get("from_role") != source or receipt.get("to_role") != destination:
        raise KVDeviceReturnError("receipt_boundary_invalid")
    body = dict(receipt); claimed = body.pop("receipt_hash", None)
    if not isinstance(claimed, str) or not claimed.startswith("sha256:"):
        raise KVDeviceReturnError("receipt_hash_invalid")
    return claimed

def materialize(*, runtime_root: Path, stegos_root: Path, materialization_id: str, skap_kv_intent: Mapping[str, Any], skap_kv_payload: bytes, skap_kv_receipt: Mapping[str, Any]) -> dict[str, Any]:
    if any(os.environ.get(name) for name in HOSTED_ENV):
        raise KVDeviceReturnError("hosted_runtime_forbidden")
    connector, backbone, transport = _load_stegos(stegos_root)
    terminal = _valid_receipt(skap_kv_receipt, source="SKAP_VAULT", destination="KV")
    if skap_kv_intent.get("payload_hash") != backbone.sha256_uri(skap_kv_payload):
        raise KVDeviceReturnError("skap_kv_exact_packet_hash_mismatch")
    if skap_kv_receipt.get("packet_id") != skap_kv_intent.get("packet_id") or skap_kv_receipt.get("payload_hash") != skap_kv_intent.get("payload_hash"):
        raise KVDeviceReturnError("skap_kv_receipt_binding_mismatch")

    base = runtime_root.expanduser().resolve() / OUT_REL / materialization_id
    kv_object = base / "kv-return-object.bin"
    atomic_bytes(kv_object, skap_kv_payload)
    kv_readback = kv_object.read_bytes()
    if kv_readback != skap_kv_payload:
        raise KVDeviceReturnError("kv_exact_readback_mismatch")

    response = connector.profile.response
    if response is None:
        raise KVDeviceReturnError("device_kv_response_not_supported")
    source, destination = response
    intent = transport.build_transport_intent(
        operation_id=str(skap_kv_intent.get("operation_id") or materialization_id) + ":device-return",
        payload_hash=backbone.sha256_uri(kv_readback),
        source_boundary=source["boundary"], source_subsystem=source["subsystem"],
        destination_boundary=destination["boundary"], destination_subsystem=destination["subsystem"],
        prior_transport_receipt_hash=terminal,
    )
    packet = backbone.PreparedPacket(connector.profile, "RESPONSE", "stegverse.skap.custody-return/v1", kv_readback, intent)
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
        "schema": "stegverse.device-kv-skap.kv-readback/v1",
        "observed": True,
        "exact_readback": True,
        "source_receipt_hash": terminal,
        "object_sha256": backbone.sha256_uri(kv_readback),
        "credential_material_present": False,
        "authority_effect": "NONE_EVIDENCE_ONLY",
    }
    atomic_json(base / "kv-readback.json", readback)
    result = {
        "schema": "stegverse.device-kv-skap.kv-device-return/v1",
        "state": "KV_TO_DEVICE_RETURN_PERSISTED",
        "materialization_id": materialization_id,
        "skap_kv_terminal_receipt_hash": terminal,
        "kv_device_terminal_receipt_hash": receipt["receipt_hash"],
        "kv_exact_readback_verified": True,
        "kv_object_sha256": readback["object_sha256"],
        "kv_device_intent_ref": str(base / "kv-to-device.intent.json"),
        "kv_device_payload_ref": str(base / "kv-to-device.payload.bin"),
        "kv_device_receipt_ref": str(base / "kv-to-device.receipt.json"),
        "kv_readback_ref": str(base / "kv-readback.json"),
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "secret_plaintext_present": False,
        "authority_effect": "NONE_EVIDENCE_ONLY",
    }
    atomic_json(base / "kv-to-device.result.json", result)
    atomic_json(runtime_root.expanduser().resolve() / OUT_REL / "latest.json", result)
    return result

def main() -> int:
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--runtime-root",type=Path,required=True);p.add_argument("--stegos-root",type=Path,required=True);p.add_argument("--materialization-id",required=True);p.add_argument("--skap-kv-intent",type=Path,required=True);p.add_argument("--skap-kv-payload",type=Path,required=True);p.add_argument("--skap-kv-receipt",type=Path,required=True);a=p.parse_args()
    try:
        result=materialize(runtime_root=a.runtime_root,stegos_root=a.stegos_root,materialization_id=a.materialization_id,skap_kv_intent=load_json(a.skap_kv_intent),skap_kv_payload=a.skap_kv_payload.read_bytes(),skap_kv_receipt=load_json(a.skap_kv_receipt))
    except Exception as exc:
        print(json.dumps({"state":"BLOCKED","reason":str(exc),"authority_effect":"NONE"},sort_keys=True));return 1
    print(json.dumps(result,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
