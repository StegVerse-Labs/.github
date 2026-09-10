#!/usr/bin/env python3
"""Materialize canonical KV->SKAP->KV->DEVICE Universal InTr custody return.

This compatibility bridge preserves the existing TVC double-Interlock custody
admission. It binds that admitted operation to a canonical Device->KV hop,
emits KV->SKAP, requires exact SKAP ciphertext readback, emits SKAP->KV, then
requires KV readback before emitting the final KV->DEVICE leg. No plaintext,
credential resolution, provider operation, or execution authority is introduced.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

PROFILE_ID = "kv-skap-custody"
CAPSULE_SCHEMA = "stegverse.skap.browser_ingress/p256-ecdh-hkdf-sha256-aes256gcm/v1"
RETURN_SCHEMA = "stegverse.skap.custody-return/v1"
OUT_REL = Path("receipts/sovereign-host/kv-skap-canonical")

class CanonicalKVSkapReturnError(ValueError): pass

def now() -> str:return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
def atomic_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:raise CanonicalKVSkapReturnError("write_once_collision:" + str(path))
        return
    tmp=path.with_name("."+path.name+".tmp");tmp.write_bytes(raw);os.replace(tmp,path)
def atomic_json(path: Path, value: Mapping[str, Any]) -> None:atomic_bytes(path,(json.dumps(dict(value),indent=2,sort_keys=True)+"\n").encode("utf-8"))

def _load_connector(stegos_root: Path):
    root=stegos_root.expanduser().resolve();registry=root/"specs/universal-intr-connector-profiles.v1.json"
    if not registry.is_file() or not (root/"stegos/intr_backbone.py").is_file():raise CanonicalKVSkapReturnError("canonical_stegos_source_missing")
    text=str(root)
    if text not in sys.path:sys.path.insert(0,text)
    module=importlib.import_module("stegos.intr_backbone");origin=Path(module.__file__).resolve()
    if root not in origin.parents:raise CanonicalKVSkapReturnError("canonical_stegos_module_root_mismatch")
    return module.connector_from_registry(registry,PROFILE_ID),module

def _final_device_return(*,runtime_root:Path,stegos_root:Path,materialization_id:str,skap_kv_intent:Mapping[str,Any],skap_kv_payload:bytes,skap_kv_receipt:Mapping[str,Any])->dict[str,Any]:
    path=Path(__file__).resolve().parent/"materialize_kv_device_from_skap_return.py"
    spec=importlib.util.spec_from_file_location("stegverse_kv_device_from_skap_return",path)
    if spec is None or spec.loader is None:raise CanonicalKVSkapReturnError("kv_device_return_loader_unavailable")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.materialize(runtime_root=runtime_root,stegos_root=stegos_root,materialization_id=materialization_id,skap_kv_intent=skap_kv_intent,skap_kv_payload=skap_kv_payload,skap_kv_receipt=skap_kv_receipt)

def materialize(*,request:Mapping[str,Any],persisted:Mapping[str,Any],runtime_root:Path,stegos_root:Path)->dict[str,Any]:
    canonical_device=request.get("canonical_device_kv_receipt")
    if not isinstance(canonical_device,Mapping):raise CanonicalKVSkapReturnError("canonical_device_kv_receipt_required")
    if canonical_device.get("schema")!="stegverse.intr.hop_receipt/v1":raise CanonicalKVSkapReturnError("canonical_device_kv_receipt_schema_invalid")
    if canonical_device.get("from_role")!="DEVICE_SYSTEM" or canonical_device.get("to_role")!="KV":raise CanonicalKVSkapReturnError("canonical_device_kv_boundary_invalid")
    device_hash=canonical_device.get("receipt_hash")
    if not isinstance(device_hash,str) or not device_hash.startswith("sha256:"):raise CanonicalKVSkapReturnError("canonical_device_kv_receipt_hash_invalid")
    capsule=request.get("sealed_capsule")
    if not isinstance(capsule,Mapping) or capsule.get("schema")!=CAPSULE_SCHEMA:raise CanonicalKVSkapReturnError("sealed_capsule_invalid")
    connector,backbone=_load_connector(stegos_root)
    packet=connector.prepare(dict(capsule),payload_schema=CAPSULE_SCHEMA,operation="ADMIT_CIPHERTEXT",operation_id=str(request.get("operation_id") or ""),prior_receipt_hash=device_hash)
    if backbone.sha256_uri(packet.intent)!=request.get("transport_intent_hash"):raise CanonicalKVSkapReturnError("canonical_kv_skap_intent_binding_mismatch")
    if packet.payload_hash!=request.get("payload_hash"):raise CanonicalKVSkapReturnError("canonical_kv_skap_payload_hash_mismatch")
    forward=connector.accept_hop(packet,hop_index=1,receipt_id="KV-SKAP-"+packet.intent["packet_id"],boundary_identity_ref="tvc://SKAP_VAULT",recorded_at=now(),prior_receipt_hash=device_hash,transition_state="RECEIVED")
    forward_result=connector.validate_complete(packet,[forward])
    credential_path=Path(str(persisted.get("credential_path") or ""))
    if not credential_path.is_file():raise CanonicalKVSkapReturnError("skap_exact_readback_object_missing")
    stored=credential_path.read_bytes()
    if stored!=packet.payload_bytes:raise CanonicalKVSkapReturnError("skap_exact_readback_mismatch")
    return_payload={"schema":RETURN_SCHEMA,"state":"SKAP_CIPHERTEXT_CUSTODY_VERIFIED","operation_id":request["operation_id"],"credential_ref":capsule.get("credential_ref"),"forward_terminal_receipt_hash":forward["receipt_hash"],"stored_object_sha256":backbone.sha256_uri(stored),"exact_ciphertext_readback_verified":True,"secret_plaintext_present":False,"credential_material_present":False,"credential_authority":"TV/TVC","authority_effect":"NONE_EVIDENCE_ONLY"}
    response_packet=connector.prepare_response(packet,[forward],return_payload,payload_schema=RETURN_SCHEMA,operation_id=str(request["operation_id"])+":return")
    reverse=connector.accept_hop(response_packet,hop_index=1,receipt_id="SKAP-KV-"+response_packet.intent["packet_id"],boundary_identity_ref="kv://KnowledgeVault:SKAPClient",recorded_at=now(),prior_receipt_hash=forward["receipt_hash"],transition_state="RECEIVED")
    reverse_result=connector.validate_complete(response_packet,[reverse])
    base=runtime_root.expanduser().resolve()/OUT_REL/str(request["materialization_id"])
    atomic_json(base/"kv-to-skap.intent.json",packet.intent);atomic_bytes(base/"kv-to-skap.payload.bin",packet.payload_bytes);atomic_json(base/"kv-to-skap.receipt.json",forward)
    atomic_json(base/"skap-to-kv.intent.json",response_packet.intent);atomic_bytes(base/"skap-to-kv.payload.bin",response_packet.payload_bytes);atomic_json(base/"skap-to-kv.receipt.json",reverse)
    device_return=_final_device_return(runtime_root=runtime_root,stegos_root=stegos_root,materialization_id=str(request["materialization_id"]),skap_kv_intent=response_packet.intent,skap_kv_payload=response_packet.payload_bytes,skap_kv_receipt=reverse)
    result={"schema":"stegverse.kv-skap.canonical-roundtrip/v1","state":"SKAP_TO_KV_RETURN_PERSISTED","four_leg_state":"KV_TO_DEVICE_RETURN_PERSISTED","materialization_id":request["materialization_id"],"operation_id":request["operation_id"],"canonical_device_kv_receipt_hash":device_hash,"kv_skap_terminal_receipt_hash":forward["receipt_hash"],"skap_kv_terminal_receipt_hash":reverse["receipt_hash"],"kv_device_terminal_receipt_hash":device_return["kv_device_terminal_receipt_hash"],"kv_skap_transport_state":forward_result["state"],"skap_kv_transport_state":reverse_result["state"],"exact_ciphertext_readback_verified":True,"kv_exact_readback_verified":device_return["kv_exact_readback_verified"],"kv_skap_intent_ref":str(base/"kv-to-skap.intent.json"),"kv_skap_payload_ref":str(base/"kv-to-skap.payload.bin"),"kv_skap_receipt_ref":str(base/"kv-to-skap.receipt.json"),"skap_kv_intent_ref":str(base/"skap-to-kv.intent.json"),"skap_kv_payload_ref":str(base/"skap-to-kv.payload.bin"),"skap_kv_receipt_ref":str(base/"skap-to-kv.receipt.json"),"kv_device_intent_ref":device_return["kv_device_intent_ref"],"kv_device_payload_ref":device_return["kv_device_payload_ref"],"kv_device_receipt_ref":device_return["kv_device_receipt_ref"],"kv_readback_ref":device_return["kv_readback_ref"],"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","secret_plaintext_present":False,"authority_effect":"NONE_CUSTODY_TRANSITION_ONLY"}
    atomic_json(base/"roundtrip.json",result);atomic_json(runtime_root.expanduser().resolve()/OUT_REL/"latest.json",result);return result
