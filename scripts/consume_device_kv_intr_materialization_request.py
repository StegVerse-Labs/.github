#!/usr/bin/env python3
"""Consume admitted DEVICE_KV Universal InTr materialization requests.

The request is non-authorizing. This consumer only binds an admitted device-kv
materialization event to the already-authorized DEVICE_KV_INTR observation task.
WorkerCoordinator remains the sole claim/fence authority.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from heartbeat_runtime.intr_subsignal_runtime import (
    default_heartbeat_runtime_root,
    propagate_local_intr_subsignal,
)

ROOT = Path(__file__).resolve().parents[1]
REQUEST_DIR_REL = Path("intr-materialization")
INGRESS_DIR_REL = Path("receipts/sovereign-network/device-kv-intr-ingress")
RECEIPT_DIR_REL = Path("receipts/sovereign-host/device-kv-intr-materialization")
LATEST_REL = Path("receipts/sovereign-host/device-kv-intr-materialization-consumption.latest.json")
TARGET_TASK = "SHWP-DEVICE-KV-INTR-OBSERVATION-001"
TARGET_ENTRYPOINT = "scripts/refresh_and_execute_resident_task.py"
PORTABLE_PAYLOAD_SCHEMA = "stegverse.kv.portable-direct-source-inline-payload/v1"
KV_SOURCE_ROOT_ENV = "STEGVERSE_KV_SOURCE_ROOT"
KV_DATA_ROOT_ENV = "STEGVERSE_KV_ROOT"
CVK_PORTABLE_INGRESS_REL = Path("runtime/portable_direct_source_ingress.py")
CVK_DIRECTORY_PROJECTION_REL = Path("runtime/portable_directory_projection.py")
QUERY_RESPONSE_DIR_REL = Path("receipts/sovereign-host/device-kv-query-response")
QUERY_RESPONSE_LATEST_REL = Path("receipts/sovereign-host/device-kv-query-response.latest.json")
KV_QUERY_SCHEMA = "kv.interlock.request.v1"
KV_DIRECTORY_RECORD_CLASS = "MY_KV_DIRECTORY_PROJECTION"
KV_HEALTH_RECORD_CLASS = "MY_KV_CONNECTION_HEALTH"
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

def kv_query_present(request:dict[str,Any])->bool:
    return isinstance(request.get("kv_request"),dict)

def _load_cvk_projection_module(source_root:Path):
    module_path=source_root/CVK_DIRECTORY_PROJECTION_REL
    if not module_path.is_file():
        raise DeviceKVMaterializationError("portable_cvk_directory_projection_source_missing")
    spec=importlib.util.spec_from_file_location("stegverse_cvk_portable_directory_projection",module_path)
    if spec is None or spec.loader is None:
        raise DeviceKVMaterializationError("portable_cvk_directory_projection_loader_unavailable")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module,"list_admitted_directory") or not hasattr(module,"get_directory_health"):
        raise DeviceKVMaterializationError("portable_cvk_directory_projection_entrypoint_missing")
    return module

def validate_kv_query(req:dict[str,Any],ing:dict[str,Any])->dict[str,Any]:
    query=req.get("kv_request")
    if not isinstance(query,dict):
        raise DeviceKVMaterializationError("kv_query_object_required")
    if portable_payload_present(req):
        raise DeviceKVMaterializationError("device_kv_extension_ambiguity_forbidden")
    allowed={
        "schema_version","operation","request_id","requester","purpose","record_class",
        "requested_scope","minimum_necessary_justification","authority_ref",
        "disclosure_mode","selector"
    }
    if set(query)!=allowed:
        raise DeviceKVMaterializationError("kv_query_field_set_invalid")
    if query.get("schema_version")!=KV_QUERY_SCHEMA or query.get("operation")!="REQUEST":
        raise DeviceKVMaterializationError("kv_query_schema_or_operation_invalid")
    requester=query.get("requester")
    if requester!={"module":"Site","component":"MyKVDirectory"}:
        raise DeviceKVMaterializationError("kv_query_requester_invalid")
    if not isinstance(query.get("request_id"),str) or not query["request_id"]:
        raise DeviceKVMaterializationError("kv_query_request_id_required")
    if not isinstance(query.get("purpose"),str) or not query["purpose"]:
        raise DeviceKVMaterializationError("kv_query_purpose_required")
    if not isinstance(query.get("minimum_necessary_justification"),str) or not query["minimum_necessary_justification"]:
        raise DeviceKVMaterializationError("kv_query_minimum_necessary_required")
    if query.get("disclosure_mode")!="BOUNDED_CONTEXT":
        raise DeviceKVMaterializationError("kv_query_disclosure_mode_invalid")
    selector=query.get("selector")
    if not isinstance(selector,dict) or set(selector)!={"directory_id","canonical_path"}:
        raise DeviceKVMaterializationError("kv_query_selector_invalid")
    if not all(isinstance(selector.get(key),str) and selector.get(key) for key in ("directory_id","canonical_path")):
        raise DeviceKVMaterializationError("kv_query_selector_invalid")
    node_id=ing.get("node_id")
    if ing.get("transport_origin")!="STEGOS_NODE_OUTBOX" or not isinstance(node_id,str) or not node_id:
        raise DeviceKVMaterializationError("kv_query_requires_node_origin")
    if query.get("authority_ref")!="stegos-node://"+node_id:
        raise DeviceKVMaterializationError("kv_query_node_authority_binding_mismatch")
    record_class=query.get("record_class")
    scopes=query.get("requested_scope")
    if record_class==KV_DIRECTORY_RECORD_CLASS:
        if scopes!=["entries","connection_health"]:
            raise DeviceKVMaterializationError("kv_directory_query_scope_invalid")
    elif record_class==KV_HEALTH_RECORD_CLASS:
        if scopes!=["connection_health"]:
            raise DeviceKVMaterializationError("kv_health_query_scope_invalid")
    else:
        raise DeviceKVMaterializationError("kv_query_record_class_invalid")
    if req.get("payload_ref")!="inline://materialization_request.kv_request":
        raise DeviceKVMaterializationError("kv_query_payload_ref_invalid")
    if req.get("payload_hash")!=sha(query):
        raise DeviceKVMaterializationError("kv_query_payload_hash_mismatch")
    return query

def execute_kv_query(req:dict[str,Any],ing:dict[str,Any],env:dict[str,str],runtime:Path)->dict[str,Any]:
    query=validate_kv_query(req,ing)
    target=runtime/QUERY_RESPONSE_DIR_REL/(req["materialization_id"]+".json")
    if target.exists():
        existing=load(target)
        if (
            existing.get("state")!="RESPONSE_PERSISTED"
            or existing.get("materialization_id")!=req["materialization_id"]
            or existing.get("request_hash")!=req["request_hash"]
            or existing.get("node_id")!=ing.get("node_id")
            or existing.get("query_request_hash")!=sha(query)
            or existing.get("response_transported_on_hb_derived_carrier") is not True
            or existing.get("exact_response_packet_recovered") is not True
        ):
            raise DeviceKVMaterializationError("kv_query_response_existing_binding_invalid")
        return existing
    source_value=env.get(KV_SOURCE_ROOT_ENV)
    data_value=env.get(KV_DATA_ROOT_ENV)
    if not source_value:
        raise DeviceKVMaterializationError("portable_kv_source_root_missing")
    if not data_value:
        raise DeviceKVMaterializationError("portable_kv_data_root_missing")
    source_root=Path(source_value).expanduser().resolve()
    data_root=Path(data_value).expanduser().resolve()
    module=_load_cvk_projection_module(source_root)
    selector=query["selector"]
    try:
        if query["record_class"]==KV_DIRECTORY_RECORD_CLASS:
            projection=module.list_admitted_directory(
                kv_data_root=data_root,
                directory_id=selector["directory_id"],
                canonical_path=selector["canonical_path"],
            )
        else:
            projection=module.get_directory_health(
                kv_data_root=data_root,
                directory_id=selector["directory_id"],
                canonical_path=selector["canonical_path"],
            )
    except Exception as exc:
        raise DeviceKVMaterializationError("kv_query_projection_failed:"+type(exc).__name__+":"+str(exc)) from exc
    if not isinstance(projection,dict):
        raise DeviceKVMaterializationError("kv_query_projection_result_invalid")
    if projection.get("credential_material_present") is not False or projection.get("provider_operation_authorized") is not False:
        raise DeviceKVMaterializationError("kv_query_projection_authority_invalid")
    if projection.get("authority_effect")!="NONE":
        raise DeviceKVMaterializationError("kv_query_projection_authority_invalid")

    response={
        "schema":"stegverse.device-kv.query-response/v1",
        "state":"QUERY_COMPLETE",
        "materialization_id":req["materialization_id"],
        "request_hash":req["request_hash"],
        "transport_intent_hash":req["transport_intent_hash"],
        "request_payload_hash":req["payload_hash"],
        "query_request_hash":sha(query),
        "query_request_id":query["request_id"],
        "record_class":query["record_class"],
        "directory_id":selector["directory_id"],
        "canonical_path":selector["canonical_path"],
        "node_id":ing["node_id"],
        "projection":projection,
        "credential_material_present":False,
        "provider_operation_authorized":False,
        "request_grants_authority":False,
        "response_grants_authority":False,
        "authority_effect":"NONE",
        "observed_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }
    response_bytes=canon(response)
    response_payload_hash=sha(response_bytes)
    receipt_body={
        "schema":"stegverse.device-kv.query-response-receipt/v1",
        "state":"RESPONSE_PERSISTED",
        "materialization_id":req["materialization_id"],
        "request_hash":req["request_hash"],
        "query_request_hash":sha(query),
        "response_payload_hash":response_payload_hash,
        "node_id":ing["node_id"],
        "credential_authority":"TV/TVC",
        "github_token_runtime_authority":"NONE",
        "credential_material_present":False,
        "provider_operation_authorized":False,
        "authority_effect":"NONE",
        "recorded_at":response["observed_at"],
    }
    receipt_hash=sha(receipt_body)
    packet_id=req["packet_id"]+"-RETURN"
    heartbeat_root=default_heartbeat_runtime_root(env)
    try:
        carrier=propagate_local_intr_subsignal(
            root=heartbeat_root,
            packet_id=packet_id,
            payload_hash=response_payload_hash,
            sampled_unix_ms=int(time.time()*1000),
            packet_bytes=response_bytes,
            intr_transport_profile="DEVICE_KV_QUERY_RETURN",
            boundary_from="KV",
            boundary_to="DEVICE_SYSTEM",
            packet_receipt_hash=receipt_hash,
        )
    except Exception as exc:
        raise DeviceKVMaterializationError("kv_query_response_carrier_failed:"+type(exc).__name__+":"+str(exc)) from exc
    result={
        **receipt_body,
        "receipt_hash":receipt_hash,
        "response":response,
        "response_payload_hash":response_payload_hash,
        "response_packet_id":packet_id,
        "response_transported_on_hb_derived_carrier":True,
        "response_shared_hb_signal_ref":carrier["signal_ref"],
        "response_shared_hb_signal_sha256":carrier["signal_sha256"],
        "response_carrier_channel_id":carrier["carrier_channel_id"],
        "response_carrier_heartbeat_epoch":carrier["heartbeat_epoch"],
        "exact_response_packet_recovered":carrier["exact_packet_recovered"],
    }
    target.parent.mkdir(parents=True,exist_ok=True)
    serialized=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if target.exists():
        existing=target.read_text(encoding="utf-8")
        if existing!=serialized:
            raise DeviceKVMaterializationError("kv_query_response_write_once_collision")
    else:
        target.write_text(serialized,encoding="utf-8")
    latest=runtime/QUERY_RESPONSE_LATEST_REL
    latest.parent.mkdir(parents=True,exist_ok=True)
    latest.write_text(serialized,encoding="utf-8")
    return result

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
    if not hasattr(module,"promote_portable_direct_source"):
        raise DeviceKVMaterializationError("portable_cvk_canonical_admission_entrypoint_missing")
    return module

def stage_and_promote_portable_payload(req:dict[str,Any],ing:dict[str,Any],env:dict[str,str])->dict[str,Any]:
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
        staging=module.admit_portable_direct_source(req,ing,kv_data_root=data_root)
    except Exception as exc:
        raise DeviceKVMaterializationError("portable_kv_staging_failed:"+type(exc).__name__+":"+str(exc)) from exc
    if not isinstance(staging,dict) or staging.get("schema")!="stegverse.kv.portable-direct-source-admission/v1":
        raise DeviceKVMaterializationError("portable_kv_staging_receipt_invalid")
    if staging.get("state")!="STAGED_UNTRUSTED" or staging.get("exact_readback_verified") is not True:
        raise DeviceKVMaterializationError("portable_kv_staging_not_verified")
    if staging.get("trusted_semantic_admission") is not False or staging.get("credential_authority")!="TV/TVC":
        raise DeviceKVMaterializationError("portable_kv_staging_authority_invalid")
    try:
        promoted=module.promote_portable_direct_source(req,staging,kv_data_root=data_root)
    except Exception as exc:
        raise DeviceKVMaterializationError("portable_kv_canonical_admission_failed:"+type(exc).__name__+":"+str(exc)) from exc
    if not isinstance(promoted,dict):
        raise DeviceKVMaterializationError("portable_kv_canonical_admission_result_invalid")
    admission=promoted.get("admission_receipt")
    health=promoted.get("connection_health")
    if not isinstance(admission,dict) or admission.get("schema")!="stegverse.kv.portable-direct-source-canonical-admission/v1":
        raise DeviceKVMaterializationError("portable_kv_canonical_admission_receipt_invalid")
    if admission.get("state")!="CANONICAL_ADMITTED" or admission.get("canonical_kv_persistence_observed") is not True:
        raise DeviceKVMaterializationError("portable_kv_canonical_persistence_not_verified")
    if admission.get("exact_canonical_readback_verified") is not True or admission.get("trusted_semantic_admission") is not True:
        raise DeviceKVMaterializationError("portable_kv_canonical_readback_not_verified")
    if admission.get("provider_session_required") is not False or admission.get("credential_authority")!="TV/TVC":
        raise DeviceKVMaterializationError("portable_kv_canonical_authority_invalid")
    if admission.get("provider_operation_authorized") is not False or admission.get("authority_effect")!="NONE":
        raise DeviceKVMaterializationError("portable_kv_canonical_authority_invalid")
    if not isinstance(health,dict) or health.get("compatibility_state")!="VERIFIED":
        raise DeviceKVMaterializationError("portable_kv_connection_health_not_verified")
    if health.get("credential_material_present") is not False or health.get("provider_operation_authorized") is not False:
        raise DeviceKVMaterializationError("portable_kv_connection_health_authority_invalid")
    return {"staging_receipt":staging,"admission_receipt":admission,"connection_health":health}

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
    query_present=kv_query_present(req)
    if portable and query_present:
        raise DeviceKVMaterializationError("device_kv_extension_ambiguity_forbidden")
    staging_receipt=None
    admission_receipt=None
    connection_health=None
    staging_error=None
    admission_error=None
    staging_attempted=False
    admission_attempted=False
    if portable and completed.returncode==0:
        staging_attempted=True
        admission_attempted=True
        try:
            promoted=stage_and_promote_portable_payload(req,ing,child)
            staging_receipt=promoted["staging_receipt"]
            admission_receipt=promoted["admission_receipt"]
            connection_health=promoted["connection_health"]
        except DeviceKVMaterializationError as exc:
            message=str(exc)
            if "canonical_admission" in message or "canonical_" in message or "connection_health" in message:
                admission_error=message
            else:
                staging_error=message

    query_result=None
    query_error=None
    query_attempted=False
    if query_present and completed.returncode==0:
        query_attempted=True
        try:
            query_result=execute_kv_query(req,ing,child,runtime)
        except DeviceKVMaterializationError as exc:
            query_error=str(exc)

    observation_ok=completed.returncode==0
    staging_ok=(not portable) or (staging_receipt is not None and staging_receipt.get("state")=="STAGED_UNTRUSTED")
    admission_ok=(not portable) or (
        admission_receipt is not None
        and admission_receipt.get("state")=="CANONICAL_ADMITTED"
        and admission_receipt.get("exact_canonical_readback_verified") is True
        and admission_receipt.get("trusted_semantic_admission") is True
    )
    query_ok=(not query_present) or (
        query_result is not None
        and query_result.get("state")=="RESPONSE_PERSISTED"
        and query_result.get("response_transported_on_hb_derived_carrier") is True
        and query_result.get("exact_response_packet_recovered") is True
    )
    state="MATERIALIZATION_EXECUTION_ATTEMPTED" if observation_ok and staging_ok and admission_ok and query_ok else "MATERIALIZATION_EXECUTION_BLOCKED"
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
        "kv_query_present":query_present,
        "kv_query_attempted":query_attempted,
        "kv_query_state":query_result.get("response",{}).get("state") if query_result else ("BLOCKED" if query_present else "NOT_APPLICABLE"),
        "kv_query_response_receipt_hash":query_result.get("receipt_hash") if query_result else None,
        "kv_query_response_payload_hash":query_result.get("response_payload_hash") if query_result else None,
        "kv_query_response_shared_hb_signal_ref":query_result.get("response_shared_hb_signal_ref") if query_result else None,
        "kv_query_response_shared_hb_signal_sha256":query_result.get("response_shared_hb_signal_sha256") if query_result else None,
        "kv_query_response_transported_on_hb_derived_carrier":query_result.get("response_transported_on_hb_derived_carrier") if query_result else False,
        "kv_query_exact_response_packet_recovered":query_result.get("exact_response_packet_recovered") if query_result else False,
        "kv_query_error":query_error,
        "portable_kv_staging_attempted":staging_attempted,
        "portable_kv_staging_state":staging_receipt.get("state") if staging_receipt else ("BLOCKED" if portable else "NOT_APPLICABLE"),
        "portable_kv_staging_receipt_sha256":staging_receipt.get("receipt_sha256") if staging_receipt else None,
        "portable_kv_staging_path":staging_receipt.get("staging_path") if staging_receipt else None,
        "portable_kv_exact_readback_verified":staging_receipt.get("exact_readback_verified") if staging_receipt else False,
        "portable_kv_staging_error":staging_error,
        "portable_kv_canonical_admission_attempted":admission_attempted,
        "portable_kv_canonical_admission_state":admission_receipt.get("state") if admission_receipt else ("BLOCKED" if portable else "NOT_APPLICABLE"),
        "portable_kv_canonical_admission_receipt_sha256":admission_receipt.get("receipt_sha256") if admission_receipt else None,
        "portable_kv_canonical_batch_path":admission_receipt.get("canonical_batch_path") if admission_receipt else None,
        "portable_kv_exact_canonical_readback_verified":admission_receipt.get("exact_canonical_readback_verified") if admission_receipt else False,
        "portable_kv_connection_health_state":connection_health.get("compatibility_state") if connection_health else None,
        "portable_kv_canonical_admission_error":admission_error,
        "trusted_semantic_admission":admission_receipt.get("trusted_semantic_admission") if admission_receipt else False,
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
