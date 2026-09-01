#!/usr/bin/env python3
"""DEVICE_KV consumer entrypoint with bounded Workspace query extension.

The preserved base consumer owns all existing DEVICE_KV behavior. This wrapper adds
only WORKSPACE_PERSONAL_PROJECTION and delegates every other request unchanged.
"""
from __future__ import annotations
import argparse,importlib.util,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

def _load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError("module_loader_unavailable:"+name)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

BASE=_load(ROOT/"scripts/consume_device_kv_intr_materialization_request_base.py","stegverse_device_kv_consumer_base")
WORKSPACE=_load(ROOT/"scripts/workspace_device_kv_query_extension.py","stegverse_workspace_device_kv_extension")
ORIGINAL_EXECUTE=BASE.execute_kv_query
for _name in dir(BASE):
    if _name not in globals() and not _name.startswith("__"): globals()[_name]=getattr(BASE,_name)

def _workspace_query_present(req:dict[str,Any])->bool:
    q=req.get("kv_request")
    return isinstance(q,dict) and q.get("record_class")==WORKSPACE.RECORD_CLASS

def _validate_outer_workspace_binding(req:dict[str,Any],ing:dict[str,Any])->dict[str,Any]:
    q=req.get("kv_request")
    if BASE.portable_payload_present(req): raise BASE.DeviceKVMaterializationError("device_kv_extension_ambiguity_forbidden")
    node_id=ing.get("node_id")
    if ing.get("transport_origin")!="STEGOS_NODE_OUTBOX" or not isinstance(node_id,str) or not node_id: raise BASE.DeviceKVMaterializationError("kv_query_requires_node_origin")
    try: WORKSPACE.validate_workspace_query(q,node_id=node_id)
    except Exception as exc: raise BASE.DeviceKVMaterializationError("workspace_kv_query_invalid:"+str(exc)) from exc
    if req.get("payload_ref")!="inline://materialization_request.kv_request": raise BASE.DeviceKVMaterializationError("kv_query_payload_ref_invalid")
    if req.get("payload_hash")!=BASE.sha(q): raise BASE.DeviceKVMaterializationError("kv_query_payload_hash_mismatch")
    return q

def execute_kv_query(req:dict[str,Any],ing:dict[str,Any],env:dict[str,str],runtime:Path)->dict[str,Any]:
    if not _workspace_query_present(req): return ORIGINAL_EXECUTE(req,ing,env,runtime)
    query=_validate_outer_workspace_binding(req,ing)
    target=runtime/BASE.QUERY_RESPONSE_DIR_REL/(req["materialization_id"]+".json")
    if target.exists():
        existing=BASE.load(target)
        if existing.get("state")!="RESPONSE_PERSISTED" or existing.get("materialization_id")!=req["materialization_id"] or existing.get("request_hash")!=req["request_hash"] or existing.get("node_id")!=ing.get("node_id") or existing.get("query_request_hash")!=BASE.sha(query) or existing.get("response_transported_on_hb_derived_carrier") is not True or existing.get("exact_response_packet_recovered") is not True: raise BASE.DeviceKVMaterializationError("kv_query_response_existing_binding_invalid")
        return existing
    source_value=env.get(BASE.KV_SOURCE_ROOT_ENV);data_value=env.get(BASE.KV_DATA_ROOT_ENV)
    if not source_value: raise BASE.DeviceKVMaterializationError("portable_kv_source_root_missing")
    if not data_value: raise BASE.DeviceKVMaterializationError("portable_kv_data_root_missing")
    try: projection=WORKSPACE.execute_workspace_query(query=query,node_id=ing["node_id"],kv_source_root=Path(source_value).expanduser().resolve(),kv_data_root=Path(data_value).expanduser().resolve())
    except Exception as exc: raise BASE.DeviceKVMaterializationError("kv_query_projection_failed:"+type(exc).__name__+":"+str(exc)) from exc
    response={"schema":"stegverse.device-kv.query-response/v1","state":"QUERY_COMPLETE","materialization_id":req["materialization_id"],"request_hash":req["request_hash"],"transport_intent_hash":req["transport_intent_hash"],"request_payload_hash":req["payload_hash"],"query_request_hash":BASE.sha(query),"query_request_id":query["request_id"],"record_class":query["record_class"],"selector":query["selector"],"directory_id":None,"canonical_path":None,"receipt_path":None,"node_id":ing["node_id"],"projection":projection,"credential_material_present":False,"provider_operation_authorized":False,"request_grants_authority":False,"response_grants_authority":False,"authority_effect":"NONE","observed_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")}
    response_bytes=BASE.canon(response);response_payload_hash=BASE.sha(response_bytes)
    receipt_body={"schema":"stegverse.device-kv.query-response-receipt/v1","state":"RESPONSE_PERSISTED","materialization_id":req["materialization_id"],"request_hash":req["request_hash"],"query_request_hash":BASE.sha(query),"response_payload_hash":response_payload_hash,"node_id":ing["node_id"],"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","credential_material_present":False,"provider_operation_authorized":False,"authority_effect":"NONE","recorded_at":response["observed_at"]}
    receipt_hash=BASE.sha(receipt_body);packet_id=req["packet_id"]+"-RETURN"
    try: carrier=BASE.propagate_local_intr_subsignal(root=BASE.default_heartbeat_runtime_root(env),packet_id=packet_id,payload_hash=response_payload_hash,sampled_unix_ms=int(time.time()*1000),packet_bytes=response_bytes,intr_transport_profile="DEVICE_KV_QUERY_RETURN",boundary_from="KV",boundary_to="DEVICE_SYSTEM",packet_receipt_hash=receipt_hash)
    except Exception as exc: raise BASE.DeviceKVMaterializationError("kv_query_response_carrier_failed:"+type(exc).__name__+":"+str(exc)) from exc
    result={**receipt_body,"receipt_hash":receipt_hash,"response":response,"response_payload_hash":response_payload_hash,"response_packet_id":packet_id,"response_transported_on_hb_derived_carrier":True,"response_shared_hb_signal_ref":carrier["signal_ref"],"response_shared_hb_signal_sha256":carrier["signal_sha256"],"response_carrier_channel_id":carrier["carrier_channel_id"],"response_carrier_heartbeat_epoch":carrier["heartbeat_epoch"],"exact_response_packet_recovered":carrier["exact_packet_recovered"]}
    target.parent.mkdir(parents=True,exist_ok=True);serialized=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if target.exists() and target.read_text(encoding="utf-8")!=serialized: raise BASE.DeviceKVMaterializationError("kv_query_response_write_once_collision")
    if not target.exists(): target.write_text(serialized,encoding="utf-8")
    latest=runtime/BASE.QUERY_RESPONSE_LATEST_REL;latest.parent.mkdir(parents=True,exist_ok=True);latest.write_text(serialized,encoding="utf-8")
    return result

BASE.execute_kv_query=execute_kv_query

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--source-root",type=Path,default=ROOT);ap.add_argument("--runtime-root",type=Path,required=True);ap.add_argument("--materialization-id",required=True);a=ap.parse_args()
    r=BASE.consume_one(a.source_root.expanduser().resolve(),a.runtime_root.expanduser().resolve(),a.materialization_id)
    print(json.dumps(r,sort_keys=True));return 0 if r.get("state")=="MATERIALIZATION_EXECUTION_ATTEMPTED" else 1

if __name__=="__main__": raise SystemExit(main())
