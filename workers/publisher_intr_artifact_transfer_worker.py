#!/usr/bin/env python3
"""WorkerCoordinator owner for canonical KV -> Publisher -> KV artifact transport."""
from __future__ import annotations
import hashlib, importlib.util, json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

TASK_ID="SHWP-PUBLISHER-INTR-ARTIFACT-TRANSFER-001"
WORKER_ID="publisher-intr-artifact-transfer-worker"
MID_ENV="STEGVERSE_PUBLISHER_INTR_MATERIALIZATION_ID"
HOSTED_ENV=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
CRED_ENV=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN","HF_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","GOOGLE_API_KEY")
TRANSFER_SCHEMA="stegverse.publisher.artifact-transfer/v1"
RETURN_SCHEMA="stegverse.publisher.artifact-return/v1"
DEST={"boundary":"STEGOS_ECOSYSTEM","subsystem":"Publisher:Ingress"}
OWNER="GCAT-BCAT-Engine/Publisher"

class Pending(RuntimeError): pass

def truthy(v): return str(v or "").strip().lower() not in {"","0","false","no"}
def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)
def sha_bytes(v:bytes): return "sha256:"+hashlib.sha256(v).hexdigest()
def load(path:Path):
    if not path.is_file(): raise Pending("required_local_object_missing:"+str(path))
    v=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise RuntimeError("json_object_required:"+str(path))
    return v
def import_from(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if not spec or not spec.loader: raise Pending("module_unavailable:"+str(path))
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def validate_invocation(inv:Mapping[str,Any])->dict[str,Any]:
    if inv.get("schema")!="stegverse.worker-invocation/v0.1": raise RuntimeError("invocation_schema_invalid")
    task=inv.get("task") or {}
    if task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID: raise RuntimeError("task_worker_mismatch")
    if not task.get("claim_id"): raise RuntimeError("worker_claim_required")
    fence=(task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(fence,int) or fence<=22: raise RuntimeError("fresh_fence_gt_22_required")
    auth=(inv.get("handoff") or {}).get("authority") or {}
    if auth.get("credential_authority")!="TV/TVC" or auth.get("github_token_required") is not False or auth.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("authority_boundary_drift")
    return dict(task)

def roots()->tuple[Path,Path,Path]:
    runtime=Path(os.getenv("STEGVERSE_HEARTBEAT_ROOT") or Path(__file__).resolve().parents[1]).expanduser().resolve()
    stegos=Path(os.getenv("STEGVERSE_STEGOS_ROOT") or "").expanduser()
    publisher=Path(os.getenv("STEGVERSE_PUBLISHER_ROOT") or "").expanduser()
    if not str(stegos) or not stegos.is_dir(): raise Pending("already_local_StegOS_root_required")
    if not str(publisher) or not publisher.is_dir(): raise Pending("already_local_Publisher_root_required")
    return runtime,stegos.resolve(),publisher.resolve()

def validate_request(req:dict[str,Any], payload:bytes, transport)->tuple[Any,list[dict[str,Any]]]:
    if req.get("schema")!="stegverse.universal-intr-materialization-request/v1" or req.get("state")!="QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION":
        raise RuntimeError("materialization_request_invalid")
    expected={"boundary":"STEGOS_ECOSYSTEM","subsystem":"Publisher:Ingress"}
    if req.get("destination")!=expected or req.get("downstream_owner_ref")!=OWNER: raise RuntimeError("publisher_destination_binding_invalid")
    if req.get("boundary_path")!=["KV","DEVICE_SYSTEM","STEGOS_ECOSYSTEM"]: raise RuntimeError("publisher_boundary_path_invalid")
    if req.get("credential_authority")!="TV/TVC" or req.get("request_grants_execution_authority") is not False or req.get("claim_or_fence_minted") is not False:
        raise RuntimeError("materialization_authority_invalid")
    if sha_bytes(payload)!=req.get("payload_hash"): raise RuntimeError("queued_payload_hash_mismatch")
    return expected,[]

def execute(inv:Mapping[str,Any])->dict[str,Any]:
    if any(truthy(os.getenv(k)) for k in HOSTED_ENV): raise RuntimeError("hosted_runtime_forbidden")
    present=[k for k in CRED_ENV if truthy(os.getenv(k))]
    if present: raise RuntimeError("credential_environment_forbidden:"+",".join(sorted(present)))
    task=validate_invocation(inv)
    mid=str(os.getenv(MID_ENV) or "").strip()
    if not mid: raise Pending("publisher_materialization_id_required")
    runtime,stegos,publisher=roots()
    request_path=runtime/"intr-materialization"/f"{mid}.json"
    qroot=runtime/"intr-packet-queue"/mid
    payload_path=qroot/"payload.bin"
    prior_path=qroot/"forward-receipts.json"
    req=load(request_path)
    payload=payload_path.read_bytes() if payload_path.is_file() else (_ for _ in ()).throw(Pending("queued_exact_payload_missing"))
    transport=import_from(stegos/"stegos/universal_intr_transport.py","publisher_intr_transport")
    backbone=import_from(stegos/"stegos/intr_backbone.py","publisher_intr_backbone")
    validate_request(req,payload,transport)
    connector=backbone.connector_from_registry(stegos/"specs/universal-intr-connector-profiles.v1.json","publisher-artifact-transfer")
    packet=connector.prepare(payload,payload_schema=TRANSFER_SCHEMA,operation="TRANSFER",operation_id=req["operation_id"])
    materialization=import_from(stegos/"stegos/universal_intr_materialization.py","publisher_intr_materialization")
    expected_req=materialization.build_materialization_request(packet.intent,payload_ref=req["payload_ref"],downstream_owner_ref=OWNER)
    if expected_req!=req: raise RuntimeError("materialization_request_exact_binding_mismatch")
    prior=load(prior_path).get("receipts")
    if not isinstance(prior,list) or len(prior)!=1: raise Pending("authentic_KV_to_DEVICE_first_hop_receipt_required")
    transport.validate_receipt_chain(packet.intent,prior)
    first=prior[0]
    if first.get("from_role")!="KV" or first.get("to_role")!="DEVICE_SYSTEM" or first.get("hop_index")!=1: raise RuntimeError("first_hop_not_KV_to_DEVICE")
    second=connector.accept_hop(packet,hop_index=2,receipt_id="PUB-IN-"+mid[-24:],boundary_identity_ref="publisher://"+mid,recorded_at=now(),prior_receipt_hash=first["receipt_hash"],transition_state="RECEIVED")
    forward=[first,second]
    connector.validate_complete(packet,forward)

    state=runtime/"publisher-artifact-transfer"/mid
    render=state/"render"; ret=state/"artifact-return.json"
    state.mkdir(parents=True,exist_ok=True)
    if not ret.is_file():
        cli=publisher/"tools/process_intr_artifact_transfer.py"
        if not cli.is_file(): raise Pending("Publisher_intr_artifact_transfer_source_not_materialized")
        env={"PATH":os.getenv("PATH",""),"PYTHONPATH":str(publisher),"HOME":os.getenv("HOME","")}
        cp=subprocess.run([sys.executable,str(cli),str(payload_path),"--output-dir",str(render),"--return-packet",str(ret)],cwd=publisher,env=env,capture_output=True,text=True,check=False,timeout=180)
        if cp.returncode!=0: raise RuntimeError("Publisher_render_failed")
    return_bytes=ret.read_bytes()
    pub=import_from(publisher/"publisher/intr_artifact_transfer.py","publisher_intr_adapter")
    returned=pub.verify_artifact_return(return_bytes)
    response=connector.prepare_response(packet,forward,return_bytes,payload_schema=RETURN_SCHEMA,operation_id=req["operation_id"]+"-return")
    response_first=connector.accept_hop(response,hop_index=1,receipt_id="PUB-OUT-"+mid[-24:],boundary_identity_ref="stegos-publisher://"+mid,recorded_at=now(),prior_receipt_hash=response.intent["prior_transport_receipt_hash"],transition_state="FORWARDED")
    response_queue={
      "schema":"stegverse.publisher.artifact-return-queue/v1","state":"RETURN_QUEUED_FOR_DEVICE_KV",
      "materialization_id":mid,"request_hash":req["request_hash"],"forward_intent":packet.intent,
      "forward_receipts":forward,"return_intent":response.intent,"return_first_hop_receipt":response_first,
      "return_payload_ref":str(ret),"return_payload_hash":sha_bytes(return_bytes),
      "generation_id":returned["generation_id"],"manifest_sha256":returned["manifest"]["manifest_sha256"],
      "publication_authorized":False,"release_authorized":False,"execution_authorized":False,
      "credential_authority":"TV/TVC","authority_effect":"NONE_TRANSPORT_ONLY"}
    queue_path=state/"return-queue.json"; queue_path.write_text(json.dumps(response_queue,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    final_path=state/"return-final-receipt.json"
    if not final_path.is_file():
        return {"state":"ACTIVE","transition_id":"PUBLISHER_ARTIFACT_RETURN_QUEUED_FOR_DEVICE_KV","queue_ref":str(queue_path),"materialization_id":mid,"claim_id":task["claim_id"],"fencing_token":task["heartbeat_timing"]["fencing_token"]}
    final=load(final_path); connector.validate_complete(response,[response_first,final])
    return {"state":"COMPLETE","transition_id":"PUBLISHER_INTR_ARTIFACT_TRANSFER_ROUND_TRIP_OBSERVED","queue_ref":str(queue_path),"final_receipt_ref":str(final_path),"materialization_id":mid,"claim_id":task["claim_id"],"fencing_token":task["heartbeat_timing"]["fencing_token"]}

def response(state,transition,**extra):
    v={"schema":"stegverse.worker-response/v0.1","state":state,"transition_id":transition,"transition_sequence":1,"credential_authority":"TV/TVC","github_token_used":False,"repository_writeback_performed":False,"publication_authorized":False,"release_authorized":False,"authority_effect":"NONE_TRANSPORT_ONLY"}; v.update(extra); return v

def main():
    try:
        inv=json.loads(sys.stdin.readline()); result=execute(inv)
        terminal=result.pop("state"); transition=result.pop("transition_id")
        print(json.dumps(response("COMPLETED" if terminal=="COMPLETE" else "ACTIVE",transition,result=result,evidence_refs=[x for x in (result.get("queue_ref"),result.get("final_receipt_ref")) if x]),sort_keys=True)); return 0
    except Pending as exc:
        print(json.dumps(response("HANDOFF_READY","PUBLISHER_INTR_MATERIALIZATION_PENDING",blocker={"dependency_class":"PUBLISHER_INTR_EVENT_MATERIALIZATION","problem_statement":str(exc),"solution_required":True,"may_remain_blocked":False,"human_action_required":False,"second_user_machine_required":False}),sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps(response("BLOCKED","PUBLISHER_INTR_ARTIFACT_TRANSFER_BLOCKED",error=str(exc)),sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
