#!/usr/bin/env python3
"""Consume a transport-complete Publisher artifact-transfer materialization.

Materialization intent is non-authorizing. Publisher execution occurs only after
the exact queued payload and the complete canonical forward InTr receipt chain
validate against the canonical StegOS publisher-artifact-transfer profile.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
REQUEST_DIR=Path("intr-materialization")
INGRESS_DIR=Path("receipts/sovereign-network/publisher-intr-ingress")
PAYLOAD_DIR=Path("intr-payloads/publisher-artifact-transfer")
RECEIPT_DIR=Path("receipts/sovereign-host/publisher-artifact-transfer")
DESTINATION={"boundary":"STEGOS_ECOSYSTEM","subsystem":"Publisher:Ingress"}
DOWNSTREAM_OWNER="GCAT-BCAT-Engine/Publisher"
OWNER=DOWNSTREAM_OWNER
PROFILE_ID="publisher-artifact-transfer"
TRANSFER_SCHEMA="stegverse.publisher.artifact-transfer/v1"
RETURN_SCHEMA="stegverse.publisher.artifact-return/v1"

HOSTED_ENV=("GITHUB_ACTIONS","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
CREDENTIAL_ENV=("GITHUB_TOKEN","GH_TOKEN","STEGVERSE_GITHUB_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN")
class PublisherInTrConsumerError(ValueError): pass
def scrubbed_env(env=None):
    child=dict(os.environ if env is None else env)
    for k in HOSTED_ENV+CREDENTIAL_ENV: child.pop(k,None)
    child["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"
    child["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    return child

def canon(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
def sha(v:Any)->str:return "sha256:"+hashlib.sha256(v if isinstance(v,bytes) else canon(v)).hexdigest()
def load(p:Path)->Any:return json.loads(p.read_text(encoding="utf-8"))
def source_root(env_name:str,repo_name:str,required:str)->Path|None:
    values=[]
    if os.environ.get(env_name): values.append(Path(os.environ[env_name]).expanduser())
    values += [ROOT.parent/repo_name,ROOT/repo_name,ROOT/"StegVerse-Labs"/repo_name,ROOT.parent.parent/repo_name]
    for p in values:
        r=p.resolve()
        if (r/required).is_file(): return r
    return None
def validate_request(r:dict[str,Any])->None:
    expected={"schema":"stegverse.universal-intr-materialization-request/v1","state":"QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION","transport_schema":"stegverse.universal-intr-transport/v1","transport_protocol":"InTr","destination":DESTINATION,"downstream_owner_ref":OWNER,"event_triggered":True,"always_on_receiver_required":False,"second_user_device_required":False,"receiver_unavailable_disposition":"DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION","exact_packet_transport_retry_allowed":True,"blind_consequence_retry_allowed":False,"interlock_required":True,"request_grants_execution_authority":False,"claim_or_fence_minted":False,"transport_grants_execution_authority":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_transfer":False,"authority_effect":"NONE_REQUEST_ONLY"}
    for k,v in expected.items():
        if r.get(k)!=v: raise PublisherInTrConsumerError("materialization_"+k+"_mismatch")
    if r.get("boundary_path")!=["KV","DEVICE_SYSTEM","STEGOS_ECOSYSTEM"]: raise PublisherInTrConsumerError("boundary_path_invalid")
    mid=str(r.get("materialization_id") or "")
    expected_payload_ref="runtime://"+str(PAYLOAD_DIR/f"{mid}.bin")
    if r.get("payload_ref")!=expected_payload_ref: raise PublisherInTrConsumerError("payload_ref_mismatch")
    body=dict(r); claimed=body.pop("request_hash",None)
    if claimed!=sha(body): raise PublisherInTrConsumerError("request_hash_mismatch")
def import_file(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise PublisherInTrConsumerError("module_load_failed:"+str(path))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def consume(runtime:Path,mid:str)->dict[str,Any]:
    req=load(runtime/REQUEST_DIR/f"{mid}.json"); validate_request(req)
    prior_path=runtime/RECEIPT_DIR/f"{mid}.json"
    if prior_path.is_file():
        prior=load(prior_path)
        if prior.get("state") in {"RENDERED_RETURN_PACKET_PREPARED_NOT_TRANSPORTED","RETURN_MATERIALIZATION_QUEUED_NOT_TRANSPORTED"} and prior.get("materialization_id")==mid and prior.get("request_hash")==req.get("request_hash"):
            return prior
    ingress=load(runtime/INGRESS_DIR/f"{mid}.json")
    if ingress.get("schema")!="stegverse.publisher-intr-materialization-ingress/v1" or ingress.get("state")!="INGRESS_ADMITTED": raise PublisherInTrConsumerError("ingress_not_admitted")
    for k in ("materialization_id","request_hash","transport_intent_hash","payload_hash","operation_id","packet_id"):
        if ingress.get(k)!=req.get(k): raise PublisherInTrConsumerError("ingress_binding_mismatch:"+k)
    payload_path=runtime/PAYLOAD_DIR/f"{mid}.bin"
    receipts_path=runtime/PAYLOAD_DIR/f"{mid}.forward-receipts.json"
    if not payload_path.is_file(): raise PublisherInTrConsumerError("exact_payload_sidecar_missing")
    if not receipts_path.is_file(): raise PublisherInTrConsumerError("forward_receipt_chain_missing")
    raw=payload_path.read_bytes()
    if sha(raw)!=req["payload_hash"]: raise PublisherInTrConsumerError("queued_payload_hash_mismatch")
    stegos=source_root("STEGVERSE_STEGOS_ROOT","StegOS","stegos/intr_backbone.py")
    publisher=source_root("STEGVERSE_PUBLISHER_ROOT","Publisher","publisher/intr_artifact_transfer.py")
    if stegos is None or publisher is None: raise PublisherInTrConsumerError("local_source_materialization_required")
    if str(stegos) not in sys.path: sys.path.insert(0,str(stegos))
    if str(publisher) not in sys.path: sys.path.insert(0,str(publisher))
    from stegos.intr_backbone import CanonicalInTrConnector, load_connector_registry
    from stegos.universal_intr_transport import sha256_uri
    from stegos.universal_intr_materialization import build_materialization_request, persist_materialization_request
    profiles=load_connector_registry(stegos/"specs/universal-intr-connector-profiles.v1.json")
    connector=CanonicalInTrConnector(profiles[PROFILE_ID])
    packet=connector.prepare(raw,payload_schema=TRANSFER_SCHEMA,operation="TRANSFER",operation_id=req["operation_id"])
    if sha256_uri(dict(packet.intent))!=req["transport_intent_hash"] or packet.intent["packet_id"]!=req["packet_id"]: raise PublisherInTrConsumerError("canonical_intent_binding_mismatch")
    receipts=load(receipts_path)
    if not isinstance(receipts,list): raise PublisherInTrConsumerError("forward_receipt_chain_invalid")
    forward=connector.validate_complete(packet,receipts)
    from publisher.intr_artifact_transfer import process_artifact_transfer, verify_artifact_return
    out=runtime/"publisher-artifacts"/mid
    result,return_bytes=process_artifact_transfer(raw,out)
    verify_artifact_return(return_bytes)
    response=connector.prepare_response(packet,receipts,result,payload_schema=RETURN_SCHEMA,operation_id=req["operation_id"]+":return")
    response_path=runtime/PAYLOAD_DIR/f"{mid}.return.bin"; response_path.parent.mkdir(parents=True,exist_ok=True); response_path.write_bytes(response.payload_bytes)
    response_intent_path=runtime/PAYLOAD_DIR/f"{mid}.return-intent.json"
    response_intent_path.write_text(json.dumps(response.intent,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return_request=build_materialization_request(response.intent,payload_ref="runtime://"+str(response_path.relative_to(runtime)),downstream_owner_ref="StegVerse-Labs/continuity-vault-kit")
    return_request_path=persist_materialization_request(runtime,return_request)
    receipt={"schema":"stegverse.publisher-intr-materialization-consumption/v1","state":"RETURN_MATERIALIZATION_QUEUED_NOT_TRANSPORTED","materialization_id":mid,"request_hash":req["request_hash"],"transport_intent_hash":req["transport_intent_hash"],"payload_hash":req["payload_hash"],"forward_transport_state":forward["state"],"forward_terminal_receipt_hash":forward["terminal_receipt_hash"],"publisher_result_schema":result["schema"],"publisher_generation_id":result["generation_id"],"return_payload_hash":response.payload_hash,"return_packet_id":response.intent["packet_id"],"return_intent_hash":sha256_uri(dict(response.intent)),"return_payload_ref":"runtime://"+str(response_path.relative_to(runtime)),"return_intent_ref":"runtime://"+str(response_intent_path.relative_to(runtime)),"return_materialization_id":return_request["materialization_id"],"return_materialization_request_hash":return_request["request_hash"],"return_materialization_request_ref":"runtime://"+str(return_request_path.relative_to(runtime)),"return_transport_observed":False,"publication_authorized":False,"release_authorized":False,"execution_authorized":False,"request_grants_authority":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_effect":"NONE","observed_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")}
    p=runtime/RECEIPT_DIR/f"{mid}.json";p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--runtime-root",type=Path,required=True);ap.add_argument("--materialization-id",required=True);a=ap.parse_args()
    try:r=consume(a.runtime_root.expanduser().resolve(),a.materialization_id)
    except Exception as exc:r={"schema":"stegverse.publisher-intr-materialization-consumption/v1","state":"BLOCKED","reason":str(exc),"runtime_execution_attempted":False,"publication_authorized":False,"authority_effect":"NONE"}
    print(json.dumps(r,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
