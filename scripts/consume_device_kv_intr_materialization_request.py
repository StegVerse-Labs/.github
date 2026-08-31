#!/usr/bin/env python3
"""Consume admitted DEVICE_KV Universal InTr materialization requests.

The request is non-authorizing. This consumer only binds an admitted device-kv
materialization event to the already-authorized DEVICE_KV_INTR observation task.
WorkerCoordinator remains the sole claim/fence authority.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
REQUEST_DIR_REL = Path("intr-materialization")
INGRESS_DIR_REL = Path("receipts/sovereign-network/device-kv-intr-ingress")
RECEIPT_DIR_REL = Path("receipts/sovereign-host/device-kv-intr-materialization")
LATEST_REL = Path("receipts/sovereign-host/device-kv-intr-materialization-consumption.latest.json")
TARGET_TASK = "SHWP-DEVICE-KV-INTR-OBSERVATION-001"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
PORTABLE_PAYLOAD_SCHEMA = "stegverse.kv.portable-direct-source-inline-payload/v1"
KV_SOURCE_ROOT_ENV = "STEGVERSE_KV_SOURCE_ROOT"
KV_DATA_ROOT_ENV = "STEGVERSE_KV_DATA_ROOT"
CVK_PORTABLE_INGRESS_REL = Path("runtime/portable_direct_source_ingress.py")
DESTINATION = {"boundary":"KV","subsystem":"KnowledgeVault:Interlock"}
DOWNSTREAM_OWNER = "StegVerse-Labs/continuity-vault-kit#79"
Runner = Callable[..., subprocess.CompletedProcess[Any]]
HOSTED_ENV=("GITHUB_ACTIONS","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
CREDENTIAL_ENV=("GITHUB_TOKEN","GH_TOKEN","STEGVERSE_GITHUB_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN")

class DeviceKVMaterializationError(ValueError): pass
def canon(v:Any)->bytes: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
def sha(v:Any)->str: return "sha256:"+hashlib.sha256(v if isinstance(v,bytes) else canon(v)).hexdigest()
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise DeviceKVMaterializationError("object_required")
    return v
def scrubbed_env(env=None):
    child=dict(os.environ if env is None else env)
    for k in HOSTED_ENV+CREDENTIAL_ENV: child.pop(k,None)
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"
    child["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    return child

def validate_request(r:dict[str,Any])->None:
    expected={"schema":"stegverse.universal-intr-materialization-request/v1","state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION","transport_schema":"stegverse.universal-intr-transport/v1","transport_protocol":"InTr","destination":DESTINATION,"downstream_owner_ref":DOWNSTREAM_OWNER,"event_triggered":True,"always_on_receiver_required":False,"second_user_device_required":False,"receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION","exact_packet_transport_retry_allowed":True,"blind_consequence_retry_allowed":False,"interlock_required":True,"request_grants_execution_authority":False,"claim_or_fence_minted":False,"transport_grants_execution_authority":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_transfer":False,"authority_effect":"NONE_REQUEST_ONLY"}
    for k,v in expected.items():
        if r.get(k)!=v: raise DeviceKVMaterializationError("materialization_"+k+"_mismatch")
    if r.get("boundary_path")!=["DEVICE_SYSTEM","KV"]: raise DeviceKVMaterializationError("boundary_path_invalid")
    for k in ("materialization_id","operation_id","packet_id","payload_ref"):
        if not isinstance(r.get(k),str) or not r[k]: raise DeviceKVMaterializationError(k+"_required")
    for k in ("transport_intent_hash","payload_hash","request_hash"):
        v=r.get(k)
        if not isinstance(v,str) or len(v)!=71 or not v.startswith("sha256:"): raise DeviceKVMaterializationError(k+"_invalid")
    body=dict(r); claimed=body.pop("request_hash")
    if claimed!=sha(body): raise DeviceKVMaterializationError("request_hash_mismatch")

def portable_payload_present(request:dict[str,Any])->bool:
    payload=request.get("portable_payload")
    return isinstance(payload,dict) and payload.get("schema")==PORTABLE_PAYLOAD_SCHEMA

def _load_cvk_portable_module(source_root:Path):
    module_path=source_root/CVK_PORTABLE_INGRESS_REL
    if not module_path.is_file():
        raise DeviceKVMaterializationError("portable_cvk_ingress_source_missing")
    spec=importlib.util.spec_from_file_location("stegverse_cvk_portable_direct_source_ingress",module_path)
    if spec is None or spec.loader is None:
        raise DeviceKVMaterializationError("portable_cvk_ingress_loader_unavailable")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module,"admit_portable_direct_source"):
        raise DeviceKVMaterializationError("portable_cvk_ingress_entrypoint_missing")
    return module

def stage_portable_payload(req:dict[str,Any],ing:dict[str,Any],env:dict[str,str])->dict[str,Any]:
    source_value=env.get(KV_SOURCE_ROOT_ENV)
    data_value=env.get(KV_DATA_ROOT_ENV)
    if not source_value:
        raise DeviceKVMaterializationError("portable_kv_source_root_missing")
    if not data_value:
        raise DeviceKVMaterializationError("portable_kv_data_root_missing")
    source_root=Path(source_value).expanduser().resolve()
    data_root=Path(data_value).expanduser().resolve()
    module=_load_cvk_portable_module(source_root)
    try:
        receipt=module.admit_portable_direct_source(req,ing,kv_data_root=data_root)
    except Exception as exc:
        raise DeviceKVMaterializationError("portable_kv_staging_failed:"+type(exc).__name__+":"+str(exc)) from exc
    if not isinstance(receipt,dict) or receipt.get("schema")!="stegverse.kv.portable-direct-source-admission/v1":
        raise DeviceKVMaterializationError("portable_kv_staging_receipt_invalid")
    if receipt.get("state")!="STAGED_UNTRUSTED" or receipt.get("exact_readback_verified") is not True:
        raise DeviceKVMaterializationError("portable_kv_staging_not_verified")
    if receipt.get("trusted_semantic_admission") is not False or receipt.get("credential_authority")!="TV/TVC":
        raise DeviceKVMaterializationError("portable_kv_staging_authority_invalid")
    return receipt

def consume_one(source:Path,runtime:Path,mid:str,runner:Runner=subprocess.run,env=None)->dict[str,Any]:
    req=load(runtime/REQUEST_DIR_REL/(mid+".json")); validate_request(req)
    ing=load(runtime/INGRESS_DIR_REL/(mid+".json"))
    if ing.get("schema")!="stegverse.device-kv-intr-materialization-ingress/v1" or ing.get("state")!="INGRESS_ADMITTED": raise DeviceKVMaterializationError("ingress_not_admitted")
    for k in ("materialization_id","request_hash","transport_intent_hash","payload_hash","operation_id","packet_id"):
        if ing.get(k)!=req.get(k): raise DeviceKVMaterializationError("ingress_binding_mismatch:"+k)
    if ing.get("claim_or_fence_minted") is not False or ing.get("credential_authority")!="TV/TVC": raise DeviceKVMaterializationError("ingress_authority_invalid")
    child=scrubbed_env(env); child["STEGVERSE_DEVICE_KV_INTR_MATERIALIZATION_ID"]=mid
    completed=runner([sys.executable,str(runtime/TARGET_ENTRYPOINT),"--source-root",str(source),"--runtime-root",str(runtime),"--task-id",TARGET_TASK],cwd=runtime,env=child,check=False,capture_output=True,text=True,timeout=240)

    portable=portable_payload_present(req)
    staging_receipt=None
    staging_error=None
    staging_attempted=False
    if portable and completed.returncode==0:
        staging_attempted=True
        try:
            staging_receipt=stage_portable_payload(req,ing,child)
        except DeviceKVMaterializationError as exc:
            staging_error=str(exc)

    observation_ok=completed.returncode==0
    staging_ok=(not portable) or (staging_receipt is not None and staging_receipt.get("state")=="STAGED_UNTRUSTED")
    state="MATERIALIZATION_EXECUTION_ATTEMPTED" if observation_ok and staging_ok else "MATERIALIZATION_EXECUTION_BLOCKED"
    body={
        "schema":"stegverse.device-kv-intr-materialization-consumption/v1",
        "state":state,
        "materialization_id":mid,
        "request_hash":req["request_hash"],
        "transport_intent_hash":req["transport_intent_hash"],
        "payload_hash":req["payload_hash"],
        "target_task_id":TARGET_TASK,
        "targeted_executor_returncode":completed.returncode,
        "runtime_execution_attempted":True,
        "portable_payload_present":portable,
        "portable_kv_staging_attempted":staging_attempted,
        "portable_kv_staging_state":staging_receipt.get("state") if staging_receipt else ("BLOCKED" if portable else "NOT_APPLICABLE"),
        "portable_kv_staging_receipt_sha256":staging_receipt.get("receipt_sha256") if staging_receipt else None,
        "portable_kv_staging_path":staging_receipt.get("staging_path") if staging_receipt else None,
        "portable_kv_exact_readback_verified":staging_receipt.get("exact_readback_verified") if staging_receipt else False,
        "portable_kv_staging_error":staging_error,
        "trusted_semantic_admission":False,
        "request_grants_authority":False,
        "claim_or_fence_minted_by_consumer":False,
        "heartbeat_grants_execution_authority":False,
        "credential_authority":"TV/TVC",
        "github_token_runtime_authority":"NONE",
        "authority_effect":"NONE_REQUEST_ONLY",
        "consumed_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    }
    p=runtime/RECEIPT_DIR_REL/(mid+".json"); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(body,indent=2,sort_keys=True)+"\n")
    latest=runtime/LATEST_REL; latest.parent.mkdir(parents=True,exist_ok=True); latest.write_text(json.dumps(body,indent=2,sort_keys=True)+"\n")
    return body

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--source-root",type=Path,default=ROOT); ap.add_argument("--runtime-root",type=Path,required=True); ap.add_argument("--materialization-id",required=True); a=ap.parse_args()
    r=consume_one(a.source_root.expanduser().resolve(),a.runtime_root.expanduser().resolve(),a.materialization_id)
    print(json.dumps(r,sort_keys=True)); return 0 if r.get("state")=="MATERIALIZATION_EXECUTION_ATTEMPTED" else 1
if __name__=="__main__": raise SystemExit(main())
