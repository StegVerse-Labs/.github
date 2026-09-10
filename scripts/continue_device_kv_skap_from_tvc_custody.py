#!/usr/bin/env python3
"""Continue Device->KV->SKAP->KV->Device from one authentic TVC custody event.

Inputs are the Gateway canonical first-hop sidecar and the terminal TVC stage-drain
receipt. TVC remains the only ciphertext custody writer. This continuation reads
back that already-persisted SKAP object exactly, uses the canonical StegOS `kv-skap`
REFERENCE profile to verify the existing custody across KV<->SKAP, persists/readbacks
the return at KV, emits the final device-kv response, and runs the existing fail-
closed four-leg verifier. It does not write credential custody or resolve secrets.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from workers.device_kv_skap_roundtrip_verifier import INPUT_SCHEMA,TASK_ID,verify_manifest

HOSTED_ENV=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
OUT_REL=Path("receipts/sovereign-host/device-kv-skap-roundtrip")

class TVCCustodyContinuationError(ValueError):pass

def canonical(value:Any)->bytes:return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")
def sha_uri(value:Any)->str:
    raw=value if isinstance(value,(bytes,bytearray)) else canonical(value);return "sha256:"+hashlib.sha256(bytes(raw)).hexdigest()
def now()->str:return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def load_json(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):raise TVCCustodyContinuationError("object_required:"+str(path))
    return value
def atomic_bytes(path:Path,raw:bytes)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=raw:raise TVCCustodyContinuationError("write_once_collision:"+str(path))
        return
    tmp=path.with_name("."+path.name+".tmp");tmp.write_bytes(raw);os.replace(tmp,path)
def atomic_json(path:Path,value:Mapping[str,Any])->None:atomic_bytes(path,(json.dumps(dict(value),indent=2,sort_keys=True)+"\n").encode())
def rel(root:Path,path:Path)->str:return str(path.resolve().relative_to(root.resolve()))

def _load_stegos(stegos_root:Path):
    root=stegos_root.expanduser().resolve();registry=root/"specs/universal-intr-connector-profiles.v1.json"
    if not registry.is_file():raise TVCCustodyContinuationError("canonical_stegos_registry_missing")
    text=str(root)
    if text not in sys.path:sys.path.insert(0,text)
    backbone=importlib.import_module("stegos.intr_backbone");transport=importlib.import_module("stegos.universal_intr_transport")
    if root not in Path(backbone.__file__).resolve().parents or root not in Path(transport.__file__).resolve().parents:raise TVCCustodyContinuationError("canonical_stegos_module_root_mismatch")
    return backbone.connector_from_registry(registry,"kv-skap"),backbone,transport

def _validate_first_hop(sidecar:Mapping[str,Any],backbone:Any,transport:Any)->tuple[dict[str,Any],bytes,dict[str,Any]]:
    if sidecar.get("schema")!="stegverse.service-gateway.device-kv-canonical-stage/v1" or sidecar.get("payload_schema")!="kv.interlock.request.v1":raise TVCCustodyContinuationError("gateway_canonical_sidecar_schema_invalid")
    if sidecar.get("credential_material_present") is not False or sidecar.get("authority_effect")!="NONE_EVIDENCE_ONLY":raise TVCCustodyContinuationError("gateway_canonical_sidecar_authority_invalid")
    payload=sidecar.get("payload");intent=sidecar.get("intent");receipt=sidecar.get("receipt")
    if not all(isinstance(v,dict) for v in (payload,intent,receipt)):raise TVCCustodyContinuationError("gateway_canonical_sidecar_components_missing")
    payload_bytes=canonical(payload)
    if backbone.payload_hash_uri(payload_bytes)!=intent.get("payload_hash"):raise TVCCustodyContinuationError("gateway_device_kv_payload_hash_mismatch")
    transport.validate_transport_intent(intent);transport.validate_receipt_chain(intent,[receipt])
    if intent.get("boundary_path")!=["DEVICE_SYSTEM","KV"] or receipt.get("transition_state")!="RECEIVED":raise TVCCustodyContinuationError("gateway_device_kv_first_hop_invalid")
    return dict(intent),payload_bytes,dict(receipt)

def _validate_tvc_outcome(outcome:Mapping[str,Any],sidecar:Mapping[str,Any])->tuple[Path,bytes,str]:
    body=dict(outcome);claimed=body.pop("receipt_digest",None)
    if claimed!=sha_uri(body):raise TVCCustodyContinuationError("tvc_drain_receipt_digest_invalid")
    if outcome.get("status")!="ADMITTED_TO_SKAP_VAULT_CUSTODY" or outcome.get("canonical_roundtrip_eligible") is not True:raise TVCCustodyContinuationError("tvc_custody_not_canonical_roundtrip_eligible")
    binding=outcome.get("canonical_device_kv_binding")
    if not isinstance(binding,dict) or binding.get("canonical_device_kv_receipt_hash")!=(sidecar.get("receipt") or {}).get("receipt_hash"):raise TVCCustodyContinuationError("tvc_custody_first_hop_binding_mismatch")
    custody=Path(str(outcome.get("credential_persistence_ref") or "")).expanduser().resolve()
    if not custody.is_file():raise TVCCustodyContinuationError("tvc_custody_object_missing")
    raw=custody.read_bytes();expected=(sidecar.get("payload") or {}).get("browser_ingress_digest")
    if sha_uri(raw)!=expected:raise TVCCustodyContinuationError("tvc_skap_exact_readback_mismatch")
    return custody,raw,claimed

def _final_device_return(*,runtime_root:Path,stegos_root:Path,materialization_id:str,skap_kv_intent:Mapping[str,Any],skap_kv_payload:bytes,skap_kv_receipt:Mapping[str,Any])->dict[str,Any]:
    path=ROOT/"scripts/materialize_kv_device_from_skap_return.py";spec=importlib.util.spec_from_file_location("stegverse_kv_device_from_tvc_custody",path)
    if spec is None or spec.loader is None:raise TVCCustodyContinuationError("kv_device_return_loader_unavailable")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.materialize(runtime_root=runtime_root,stegos_root=stegos_root,materialization_id=materialization_id,skap_kv_intent=skap_kv_intent,skap_kv_payload=skap_kv_payload,skap_kv_receipt=skap_kv_receipt)

def continue_roundtrip(*,runtime_root:Path,stegos_root:Path,gateway_sidecar_path:Path,tvc_drain_receipt_path:Path)->dict[str,Any]:
    if any(os.environ.get(k) for k in HOSTED_ENV):raise TVCCustodyContinuationError("hosted_runtime_forbidden")
    runtime=runtime_root.expanduser().resolve();sidecar=load_json(gateway_sidecar_path);outcome=load_json(tvc_drain_receipt_path)
    connector,backbone,transport=_load_stegos(stegos_root)
    d_intent,d_payload,d_receipt=_validate_first_hop(sidecar,backbone,transport)
    custody_path,custody_bytes,tvc_digest=_validate_tvc_outcome(outcome,sidecar)
    ingress_id=str(outcome.get("ingress_id") or "")
    if not ingress_id:raise TVCCustodyContinuationError("tvc_ingress_id_required")
    base=runtime/OUT_REL/ingress_id;base.mkdir(parents=True,exist_ok=True)
    d_intent_p=base/"device-to-kv.intent.json";d_payload_p=base/"device-to-kv.payload.bin";d_receipt_p=base/"device-to-kv.receipt.json"
    atomic_json(d_intent_p,d_intent);atomic_bytes(d_payload_p,d_payload);atomic_json(d_receipt_p,d_receipt)

    reference={"schema":"stegverse.skap.reference-request/v1","operation":"VERIFY_SESSION","ingress_id":ingress_id,"credential_ref":outcome.get("credential_ref"),"custody_ref":str(custody_path),"custody_object_sha256":sha_uri(custody_bytes),"tvc_drain_receipt_digest":tvc_digest,"canonical_device_kv_receipt_hash":d_receipt["receipt_hash"],"exact_ciphertext_readback_verified":True,"credential_material_present":False,"credential_authority":"TV/TVC","authority_effect":"NONE_REFERENCE_ONLY"}
    forward_packet=connector.prepare(reference,payload_schema="stegverse.skap.reference-request/v1",operation="VERIFY_SESSION",operation_id=ingress_id+":kv-skap-verify",prior_receipt_hash=d_receipt["receipt_hash"])
    forward_receipt=connector.accept_hop(forward_packet,hop_index=1,receipt_id="KV-SKAP-"+forward_packet.intent["packet_id"],boundary_identity_ref="tvc://SKAP_VAULT/custody-readback",recorded_at=now(),prior_receipt_hash=d_receipt["receipt_hash"],transition_state="RECEIVED")
    connector.validate_complete(forward_packet,[forward_receipt])
    response={"schema":"stegverse.skap.reference-result/v1","state":"SKAP_REFERENCE_VERIFIED","ingress_id":ingress_id,"credential_ref":outcome.get("credential_ref"),"custody_object_sha256":sha_uri(custody_bytes),"forward_terminal_receipt_hash":forward_receipt["receipt_hash"],"exact_ciphertext_readback_verified":True,"credential_material_present":False,"credential_authority":"TV/TVC","authority_effect":"NONE_EVIDENCE_ONLY"}
    reverse_packet=connector.prepare_response(forward_packet,[forward_receipt],response,payload_schema="stegverse.skap.reference-result/v1",operation_id=ingress_id+":skap-kv-return")
    reverse_receipt=connector.accept_hop(reverse_packet,hop_index=1,receipt_id="SKAP-KV-"+reverse_packet.intent["packet_id"],boundary_identity_ref="kv://KnowledgeVault:SKAPClient",recorded_at=now(),prior_receipt_hash=forward_receipt["receipt_hash"],transition_state="RECEIVED")
    connector.validate_complete(reverse_packet,[reverse_receipt])
    fk_i=base/"kv-to-skap.intent.json";fk_p=base/"kv-to-skap.payload.bin";fk_r=base/"kv-to-skap.receipt.json";sk_i=base/"skap-to-kv.intent.json";sk_p=base/"skap-to-kv.payload.bin";sk_r=base/"skap-to-kv.receipt.json"
    atomic_json(fk_i,forward_packet.intent);atomic_bytes(fk_p,forward_packet.payload_bytes);atomic_json(fk_r,forward_receipt);atomic_json(sk_i,reverse_packet.intent);atomic_bytes(sk_p,reverse_packet.payload_bytes);atomic_json(sk_r,reverse_receipt)
    device_return=_final_device_return(runtime_root=runtime,stegos_root=stegos_root,materialization_id=ingress_id,skap_kv_intent=reverse_packet.intent,skap_kv_payload=reverse_packet.payload_bytes,skap_kv_receipt=reverse_receipt)
    kv_i=Path(device_return["kv_device_intent_ref"]);kv_p=Path(device_return["kv_device_payload_ref"]);kv_r=Path(device_return["kv_device_receipt_ref"]);kv_readback=load_json(Path(device_return["kv_readback_ref"]))
    manifest={"schema":INPUT_SCHEMA,"task_id":TASK_ID,"current_device":True,"hosted_runtime_used":False,"second_user_operated_device_used":False,
      "device_kv":{"intent_path":rel(runtime,d_intent_p),"payload_path":rel(runtime,d_payload_p),"receipt_path":rel(runtime,d_receipt_p)},
      "kv_skap":{"intent_path":rel(runtime,fk_i),"payload_path":rel(runtime,fk_p),"receipt_path":rel(runtime,fk_r)},
      "skap_kv":{"intent_path":rel(runtime,sk_i),"payload_path":rel(runtime,sk_p),"receipt_path":rel(runtime,sk_r)},
      "kv_device":{"intent_path":rel(runtime,kv_i),"payload_path":rel(runtime,kv_p),"receipt_path":rel(runtime,kv_r)},
      "readback":{"skap":{"observed":True,"exact_readback":True,"source_receipt_hash":forward_receipt["receipt_hash"],"object_sha256":sha_uri(custody_bytes),"credential_material_present":False},"kv":{"observed":True,"exact_readback":True,"source_receipt_hash":reverse_receipt["receipt_hash"],"object_sha256":kv_readback["object_sha256"],"credential_material_present":False}}}
    manifest_path=base/"runtime-roundtrip-manifest.json";atomic_json(manifest_path,manifest)
    proof=verify_manifest(manifest,runtime_root=runtime);proof_path=base/"runtime-roundtrip-proof.json";atomic_json(proof_path,proof)
    result={"schema":"stegverse.device-kv-skap.tvc-custody-continuation/v1","state":"DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED","task_id":TASK_ID,"ingress_id":ingress_id,"gateway_sidecar_ref":str(gateway_sidecar_path),"tvc_drain_receipt_ref":str(tvc_drain_receipt_path),"tvc_single_custody_writer_preserved":True,"skap_exact_readback_verified":True,"kv_exact_readback_verified":True,"terminal_receipt_hash":device_return["kv_device_terminal_receipt_hash"],"manifest_ref":str(manifest_path),"proof_ref":str(proof_path),"proof_sha256":proof["proof_sha256"],"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_effect":"NONE_EVIDENCE_ONLY"}
    atomic_json(base/"tvc-custody-continuation.json",result);atomic_json(runtime/OUT_REL/"latest.json",result);return result

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--runtime-root",type=Path,required=True);p.add_argument("--stegos-root",type=Path,required=True);p.add_argument("--gateway-sidecar",type=Path,required=True);p.add_argument("--tvc-drain-receipt",type=Path,required=True);a=p.parse_args()
    try:r=continue_roundtrip(runtime_root=a.runtime_root,stegos_root=a.stegos_root,gateway_sidecar_path=a.gateway_sidecar,tvc_drain_receipt_path=a.tvc_drain_receipt)
    except Exception as exc:
        print(json.dumps({"state":"BLOCKED","reason":str(exc),"authority_effect":"NONE"},sort_keys=True));return 1
    print(json.dumps(r,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
