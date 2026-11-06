#!/usr/bin/env python3
"""Build and dispatch one KV -> SKAP Vault ciphertext custody request to the in-KV SKAP gate.

The SKAP Vault sits inside KV, so the KV -> SKAP Vault step is the in-KV SKAP gate, never an InTr hop
(StegVerse-org/.github#167 ruling c6393224851 (3); ruling C accepted, c6393756343). The round trip is two-leg
DEVICE_SYSTEM -> KV -> DEVICE_SYSTEM: Device -> KV is one InTr leg, and the KV -> Device return is the other.
This dispatcher builds no transport intent, no materialization request, no carrier binding and no relay
headers, and resolves no StegOS connector profile. It hands the gate request directly to the in-KV gate
admission. The legacy DEVICE->KV boundary-transition receipt remains for TVC double-Interlock compatibility.
A canonical DEVICE_SYSTEM->KV hop receipt anchors the round trip. The request carries the cvk layer-1
KV-access receipt of that hop and the layer-2 SKAP-access receipt chained to it; the gate re-derives both (C1, C2). Neither receipt grants execution or credential authority.
"""
from __future__ import annotations

import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CAPSULE_SCHEMA="stegverse.skap.browser_ingress/p256-ecdh-hkdf-sha256-aes256gcm/v1"
EGRESS_DIR_REL=Path("receipts/sovereign-network/kv-skap-gate-dispatch")
LATEST_REL=Path("receipts/sovereign-network/kv-skap-gate-dispatch.latest.json")

class KVSkapDispatchError(ValueError): pass

def canonical(value:Any)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
def sha_uri(value:Any)->str:
    raw=value if isinstance(value,bytes) else canonical(value)
    return "sha256:"+hashlib.sha256(raw).hexdigest()
def load_json(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise KVSkapDispatchError("object_required:"+str(path))
    return value

def _gate():
    path=ROOT/"scripts/consume_kv_skap_custody_materialization_request.py"
    spec=importlib.util.spec_from_file_location("stegverse_kv_skap_gate_consumer",path)
    if spec is None or spec.loader is None: raise KVSkapDispatchError("kv_skap_gate_loader_unavailable")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def _validate_canonical_device_receipt(value:dict[str,Any])->None:
    if value.get("schema")!="stegverse.intr.hop_receipt/v1": raise KVSkapDispatchError("canonical_device_kv_receipt_schema_invalid")
    if value.get("from_role")!="DEVICE_SYSTEM" or value.get("to_role")!="KV": raise KVSkapDispatchError("canonical_device_kv_receipt_boundary_invalid")
    receipt_hash=value.get("receipt_hash")
    if not isinstance(receipt_hash,str) or not receipt_hash.startswith("sha256:"): raise KVSkapDispatchError("canonical_device_kv_receipt_hash_invalid")
    body=dict(value); body.pop("receipt_hash",None)
    if sha_uri(body)!=receipt_hash: raise KVSkapDispatchError("canonical_device_kv_receipt_hash_mismatch")

def build_request(*,capsule:dict[str,Any],device_kv_receipt:dict[str,Any],canonical_device_kv_receipt:dict[str,Any],kv_access_receipt:dict[str,Any],skap_access_receipt:dict[str,Any])->dict[str,Any]:
    gate=_gate()
    if capsule.get("schema")!=CAPSULE_SCHEMA: raise KVSkapDispatchError("sealed_capsule_schema_invalid")
    ingress_id=str(capsule.get("ingress_id") or "")
    if not ingress_id: raise KVSkapDispatchError("sealed_capsule_ingress_id_required")
    if not isinstance(device_kv_receipt,dict) or device_kv_receipt.get("schema")!="stegverse.intr.boundary_transition_receipt/v1": raise KVSkapDispatchError("device_kv_receipt_invalid")
    _validate_canonical_device_receipt(canonical_device_kv_receipt)
    payload_hash=sha_uri(capsule)
    seed=canonical({"operation_id":ingress_id,"payload_hash":payload_hash,"canonical_device_kv_receipt_hash":canonical_device_kv_receipt["receipt_hash"]})
    body={
        "schema":gate.GATE_REQUEST_SCHEMA,"state":"QUEUED_FOR_IN_KV_SKAP_GATE","gate":dict(gate.GATE),
        "kv_skap_path":"IN_KV_GATE","kv_skap_intr_hop":False,"downstream_owner_ref":gate.DOWNSTREAM_OWNER,
        "interlock_required":True,"request_grants_execution_authority":False,"claim_or_fence_minted":False,
        "credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_transfer":False,"authority_effect":"NONE_REQUEST_ONLY",
        "materialization_id":"KV-SKAP-GATE-"+hashlib.sha256(seed).hexdigest()[:24],"operation_id":ingress_id,"payload_hash":payload_hash,
        "sealed_capsule":capsule,"device_kv_receipt":device_kv_receipt,"canonical_device_kv_receipt":canonical_device_kv_receipt,
        "kv_access_receipt":kv_access_receipt,"skap_access_receipt":skap_access_receipt,
    }
    request={**body,"request_hash":sha_uri(body)}
    gate.validate_request(request)
    return request

def dispatch(*,runtime_root:Path,capsule:dict[str,Any],device_kv_receipt:dict[str,Any],canonical_device_kv_receipt:dict[str,Any],kv_access_receipt:dict[str,Any],skap_access_receipt:dict[str,Any],consumer_dispatch:bool=True)->dict[str,Any]:
    request=build_request(capsule=capsule,device_kv_receipt=device_kv_receipt,canonical_device_kv_receipt=canonical_device_kv_receipt,kv_access_receipt=kv_access_receipt,skap_access_receipt=skap_access_receipt)
    admitted=_gate().admit(runtime_root=runtime_root.expanduser().resolve(),request=request,dispatch=consumer_dispatch)
    if admitted.get("state")!="GATE_ADMITTED": raise KVSkapDispatchError("kv_skap_gate_not_admitted")
    body={
        "schema":"stegverse.kv-skap-gate.dispatch/v1","state":"DISPATCHED_TO_IN_KV_SKAP_GATE",
        "materialization_id":request["materialization_id"],"request_hash":request["request_hash"],"payload_hash":request["payload_hash"],
        "device_kv_receipt_hash":device_kv_receipt["receipt_hash"],
        "canonical_device_kv_receipt_hash":canonical_device_kv_receipt["receipt_hash"],
        "kv_access_receipt_hash":kv_access_receipt["receipt_hash"],"skap_access_receipt_hash":skap_access_receipt["receipt_hash"],
        "kv_skap_path":"IN_KV_GATE","kv_skap_intr_hop":False,
        "gate_admission_state":admitted["state"],"gate_admission_authority_effect":admitted["authority_effect"],
        "consumer_dispatch_attempted":bool((admitted.get("dispatch") or {}).get("consumer_dispatch_attempted")),
        "credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","dispatch_grants_execution_authority":False,"authority_effect":"NONE_GATE_DISPATCH_ONLY",
    }
    receipt={**body,"receipt_hash":sha_uri(body)}
    target=runtime_root.expanduser().resolve()/EGRESS_DIR_REL/f"{request['materialization_id']}.json";target.parent.mkdir(parents=True,exist_ok=True)
    serialized=json.dumps(receipt,sort_keys=True,indent=2)+"\n"
    if target.exists() and target.read_text()!=serialized: raise KVSkapDispatchError("kv_skap_gate_dispatch_receipt_collision")
    target.write_text(serialized,encoding="utf-8")
    latest=runtime_root.expanduser().resolve()/LATEST_REL;latest.parent.mkdir(parents=True,exist_ok=True);latest.write_text(serialized,encoding="utf-8")
    return {"request":request,"gate_admission":admitted,"dispatch_receipt":receipt}

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--runtime-root",type=Path,required=True);p.add_argument("--sealed-capsule",type=Path,required=True);p.add_argument("--device-kv-receipt",type=Path,required=True);p.add_argument("--canonical-device-kv-receipt",type=Path,required=True);p.add_argument("--kv-access-receipt",type=Path,required=True);p.add_argument("--skap-access-receipt",type=Path,required=True);a=p.parse_args()
    try:
        result=dispatch(runtime_root=a.runtime_root,capsule=load_json(a.sealed_capsule),device_kv_receipt=load_json(a.device_kv_receipt),canonical_device_kv_receipt=load_json(a.canonical_device_kv_receipt),kv_access_receipt=load_json(a.kv_access_receipt),skap_access_receipt=load_json(a.skap_access_receipt))
    except Exception as exc:
        print(json.dumps({"state":"BLOCKED","reason":str(exc),"fail_closed":getattr(exc,"fail_closed",None),"authority_effect":"NONE"},sort_keys=True));return 1
    print(json.dumps(result["dispatch_receipt"],sort_keys=True));return 0
if __name__=="__main__": raise SystemExit(main())
