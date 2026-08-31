#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT=Path.cwd().resolve()
TASK_ID="SHWP-PUBLISHER-ARTIFACT-TRANSFER-001"
EVENT_ENV="STEGVERSE_PUBLISHER_INTR_MATERIALIZATION_ID"
REQ_DIR=ROOT/"intr-materialization"
INGRESS_DIR=ROOT/"receipts/sovereign-network/publisher-intr-ingress"
PAYLOAD_DIR=ROOT/"intr-payload/publisher"
RECEIPT=ROOT/"receipts/publisher-artifact-transfer"/f"{TASK_ID}.json"
RETURN_DIR=ROOT/"intr-return/publisher"

def canon(v:Any)->str: return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)
def sha_bytes(v:bytes)->str: return "sha256:"+hashlib.sha256(v).hexdigest()
def sha_value(v:Any)->str: return sha_bytes(canon(v).encode())
def now()->str: return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise RuntimeError("object required: "+str(path))
    return value

def atomic(path:Path,value:Mapping[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,delete=False) as h:
        json.dump(dict(value),h,indent=2,sort_keys=True); h.write("\n"); tmp=Path(h.name)
    os.replace(tmp,path)

def source_root(env_name:str,repo_name:str,required:str)->Path|None:
    candidates=[]
    if os.environ.get(env_name): candidates.append(Path(os.environ[env_name]).expanduser())
    candidates += [ROOT.parent/repo_name,ROOT/repo_name,ROOT/"StegVerse-Labs"/repo_name,ROOT.parent.parent/repo_name]
    seen=set()
    for c in candidates:
        r=c.resolve()
        if r in seen: continue
        seen.add(r)
        if (r/required).is_file(): return r
    return None

def validate_materialization(req:Mapping[str,Any],ing:Mapping[str,Any])->None:
    expected={
      "schema":"stegverse.universal-intr-materialization-request/v1",
      "state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
      "transport_schema":"stegverse.universal-intr-transport/v1","transport_protocol":"InTr",
      "destination":{"boundary":"STEGOS_ECOSYSTEM","subsystem":"Publisher:Ingress"},
      "downstream_owner_ref":"GCAT-BCAT-Engine/Publisher",
      "event_triggered":True,"always_on_receiver_required":False,"second_user_device_required":False,
      "receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
      "exact_packet_transport_retry_allowed":True,"blind_consequence_retry_allowed":False,
      "interlock_required":True,"request_grants_execution_authority":False,"claim_or_fence_minted":False,
      "transport_grants_execution_authority":False,"credential_authority":"TV/TVC",
      "github_token_runtime_authority":"NONE","authority_transfer":False,"authority_effect":"NONE_REQUEST_ONLY"}
    for k,v in expected.items():
        if req.get(k)!=v: raise RuntimeError("materialization mismatch: "+k)
    if req.get("boundary_path")!=["KV","DEVICE_SYSTEM","STEGOS_ECOSYSTEM"]: raise RuntimeError("publisher boundary path invalid")
    body=dict(req); claimed=body.pop("request_hash",None)
    if claimed!=sha_value(body): raise RuntimeError("materialization request hash mismatch")
    if ing.get("schema")!="stegverse.publisher-intr-materialization-ingress/v1" or ing.get("state")!="INGRESS_ADMITTED":
        raise RuntimeError("publisher ingress not admitted")
    for k in ("materialization_id","request_hash","transport_intent_hash","payload_hash","operation_id","packet_id"):
        if ing.get(k)!=req.get(k): raise RuntimeError("publisher ingress binding mismatch: "+k)
    if ing.get("exact_payload_materialized") is not True or ing.get("claim_or_fence_minted") is not False:
        raise RuntimeError("publisher ingress payload/authority invalid")
    if ing.get("credential_authority")!="TV/TVC": raise RuntimeError("publisher ingress credential authority invalid")

def main()->int:
    invocation=json.load(sys.stdin); task=invocation.get("task") or {}; epoch=invocation.get("heartbeat_epoch")
    if invocation.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK_ID or not isinstance(epoch,int): return 2
    claim=task.get("claim_id"); fence=(task.get("heartbeat_timing") or {}).get("fencing_token")
    if not isinstance(claim,str) or not claim or not isinstance(fence,int): return 3
    mid=os.environ.get(EVENT_ENV)
    if not mid:
        atomic(RECEIPT,{"schema":"stegverse.publisher-artifact-transfer-runtime/v1","state":"ACTIVE","transition_id":"PUBLISHER_INTR_EVENT_REQUIRED","task_id":TASK_ID,"claim_id":claim,"fencing_token":fence,"credential_authority":"TV/TVC","authority_effect":"NONE"})
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"ACTIVE","transition_id":"PUBLISHER_INTR_EVENT_REQUIRED","transition_sequence":1,"expected_next_transition":"PUBLISHER_ARTIFACT_RETURN_STAGED","expected_next_earliest_epoch":epoch+1,"expected_next_latest_epoch":epoch+8,"checkpoint_ref":str(RECEIPT.relative_to(ROOT)),"evidence_refs":[str(RECEIPT.relative_to(ROOT))],"cost_observation":{"hb_transition_count":1,"compute_units":1,"external_cost_usd":0,"task_class":"publisher_artifact_transfer"}})); return 0

    req=load(REQ_DIR/f"{mid}.json"); ing=load(INGRESS_DIR/f"{mid}.json"); validate_materialization(req,ing)
    payload_path=PAYLOAD_DIR/f"{mid}.bin"
    if not payload_path.is_file(): raise RuntimeError("publisher exact payload missing")
    payload=payload_path.read_bytes()
    if sha_bytes(payload)!=req.get("payload_hash") or sha_bytes(payload)!=ing.get("payload_hash"):
        raise RuntimeError("publisher exact payload hash mismatch")

    stegos=source_root("STEGVERSE_STEGOS_ROOT","StegOS","stegos/intr_backbone.py")
    publisher=source_root("STEGVERSE_PUBLISHER_ROOT","Publisher","publisher/intr_artifact_transfer.py")
    if stegos is None or publisher is None: raise RuntimeError("current StegOS and Publisher source must already be local")
    for root in (stegos,publisher):
        if str(root) not in sys.path: sys.path.insert(0,str(root))
    intr=importlib.import_module("stegos.intr_backbone")
    pub=importlib.import_module("publisher.intr_artifact_transfer")
    connector=intr.connector_from_registry(stegos/"specs/universal-intr-connector-profiles.v1.json","publisher-artifact-transfer")
    transfer=pub.parse_transfer_bytes(payload)
    packet=connector.prepare(payload,payload_schema=pub.TRANSFER_SCHEMA,operation=str(transfer["operation"]),operation_id=str(req["operation_id"]))
    if sha_value(packet.intent)!=req.get("transport_intent_hash") or packet.intent.get("packet_id")!=req.get("packet_id") or packet.payload_hash!=req.get("payload_hash"):
        raise RuntimeError("publisher canonical intent reconstruction mismatch")

    prior=packet.intent.get("prior_transport_receipt_hash"); forward=[]
    node_id=str(ing.get("node_id")); interlock_id=str(ing.get("interlock_id"))
    identities=[f"stegos-node://{node_id}/{interlock_id}",f"publisher-ingress://{mid}"]
    for i,identity in enumerate(identities,1):
        receipt=connector.accept_hop(packet,hop_index=i,receipt_id=f"PUB-FWD-{mid}-{i}",boundary_identity_ref=identity,recorded_at=now(),prior_receipt_hash=prior)
        forward.append(receipt); prior=receipt["receipt_hash"]
    transport=connector.validate_complete(packet,forward)

    render_dir=ROOT/"publisher-render"/mid
    result,return_bytes=pub.process_artifact_transfer(payload,render_dir)
    response=connector.prepare_response(packet,forward,return_bytes,payload_schema=pub.RETURN_SCHEMA,operation_id=str(req["operation_id"])+"-RETURN")
    response_first=connector.accept_hop(response,hop_index=1,receipt_id=f"PUB-RET-{mid}-1",boundary_identity_ref=f"stegos-node://{node_id}/{interlock_id}",recorded_at=now(),prior_receipt_hash=response.intent.get("prior_transport_receipt_hash"))

    RETURN_DIR.mkdir(parents=True,exist_ok=True)
    return_packet=RETURN_DIR/f"{mid}.bin"; return_packet.write_bytes(return_bytes)
    return_meta={
      "schema":"stegverse.publisher-artifact-return-staged/v1","state":"RETURN_STAGED_TO_DEVICE",
      "materialization_id":mid,"request_hash":req["request_hash"],"forward_transport":transport,
      "forward_receipts":forward,"response_intent":response.intent,"response_first_hop_receipt":response_first,
      "return_payload_sha256":sha_bytes(return_bytes),"return_packet_ref":str(return_packet.relative_to(ROOT)),
      "return_requires_kv_terminal_hop":True,"publication_authorized":False,"release_authorized":False,
      "execution_authorized":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE",
      "authority_effect":"NONE_RUNTIME_OBSERVATION_ONLY"}
    atomic(RETURN_DIR/f"{mid}.json",return_meta)
    evidence={
      "schema":"stegverse.publisher-artifact-transfer-runtime/v1","state":"RETURN_STAGED_TO_DEVICE",
      "transition_id":"PUBLISHER_ARTIFACT_RETURN_STAGED","task_id":TASK_ID,"heartbeat_epoch":epoch,
      "claim_id":claim,"fencing_token":fence,"materialization_id":mid,"request_hash":req["request_hash"],
      "payload_hash":req["payload_hash"],"forward_transport_complete":True,
      "publisher_render_result":result["rendering_receipt"]["result"],"return_payload_sha256":sha_bytes(return_bytes),
      "return_terminal_kv_hop_observed":False,"publication_authorized":False,"release_authorized":False,
      "execution_authorized":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE",
      "heartbeat_grants_execution_authority":False,"authority_effect":"NONE_RUNTIME_OBSERVATION_ONLY",
      "return_meta_ref":str((RETURN_DIR/f"{mid}.json").relative_to(ROOT))}
    atomic(RECEIPT,evidence)
    print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"COMPLETED","transition_id":"PUBLISHER_ARTIFACT_RETURN_STAGED","transition_sequence":1,"expected_next_transition":None,"expected_next_earliest_epoch":None,"expected_next_latest_epoch":None,"checkpoint_ref":str(RECEIPT.relative_to(ROOT)),"evidence_refs":[str(RECEIPT.relative_to(ROOT)),str((RETURN_DIR/f"{mid}.json").relative_to(ROOT))],"cost_observation":{"hb_transition_count":1,"compute_units":2,"external_cost_usd":0,"task_class":"publisher_artifact_transfer"}}))
    return 0
if __name__=="__main__": raise SystemExit(main())
