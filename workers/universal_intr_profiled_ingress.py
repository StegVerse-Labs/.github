#!/usr/bin/env python3
"""Shared profiled Universal InTr materialization ingress.

HIL requests delegate to the already-validated HIL ingress unchanged. SV002
public-observation requests use a distinct validator and receipt namespace. The
shared listener grants no execution authority; it only admits exact durable
materialization requests for the existing downstream owners.
"""
from __future__ import annotations
import argparse, hashlib, json, ssl, sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT/"scripts") not in sys.path:sys.path.insert(0,str(ROOT/"scripts"))
import serve_hil_intr_materialization_ingress as hil  # noqa: E402
from consume_sv002_intr_materialization_request import DESTINATION as SV002_DESTINATION, DOWNSTREAM_OWNER as SV002_OWNER, validate_request as validate_sv002_request  # noqa: E402

PROFILE_PATH="/intr/profile"
INGRESS_PATH="/intr/materialization"
SV002_RECEIPT_SCHEMA="stegverse.sv002-intr-materialization-ingress/v1"
SV002_RECEIPT_DIR=Path("receipts/sovereign-network/sv002-intr-ingress")
SV002_LATEST=Path("receipts/sovereign-network/sv002-intr-ingress.latest.json")
AUTHORITY_EFFECT="NONE_INGRESS_ONLY"

def canonical(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
def sha_uri(v:Any)->str:
    raw=v if isinstance(v,bytes) else canonical(v);return "sha256:"+hashlib.sha256(raw).hexdigest()
def require(ok:bool,reason:str)->None:
    if not ok:raise ValueError(reason)
def now()->str:return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def safe_id(v:str)->str:
    require(v.startswith("INTR-MAT-") and len(v)==33 and all(c in "0123456789abcdef" for c in v[9:]),"materialization_id_invalid");return v

def _sv002_request_from_payload(payload:Any,transport:Mapping[str,str|None])->tuple[dict[str,Any],dict[str,Any]]:
    origin=transport["origin"]
    if origin==hil.ORIGIN_RELAY:
        require(isinstance(payload,dict),"request_object_required");validate_sv002_request(payload)
        return dict(payload),{"transport_origin":origin,"transport_authorization_id":transport["authorization_id"],"node_id":None,"interlock_id":None,"outbox_entry_hash":None}
    require(isinstance(payload,dict) and payload.get("schema")==hil.NODE_TRIGGER_SCHEMA,"node_trigger_schema_invalid")
    require(payload.get("transport_origin")==hil.ORIGIN_NODE,"node_trigger_origin_invalid")
    require(payload.get("authority_effect")=="NONE_TRIGGER_ONLY","node_trigger_authority_effect_invalid")
    require(payload.get("request_grants_execution_authority") is False and payload.get("claim_or_fence_minted") is False,"node_trigger_authority_forbidden")
    entry=payload.get("node_outbox_entry");require(isinstance(entry,dict),"node_outbox_entry_required")
    require(entry.get("schema")==hil.NODE_OUTBOX_SCHEMA and entry.get("state")=="LOCAL_OUTBOX_PENDING_NETWORK_DELIVERY","node_outbox_state_invalid")
    require(entry.get("network_delivery_observed") is False and entry.get("runtime_materialization_observed") is False and entry.get("receiver_receipt_observed") is False and entry.get("tvc_receipt_observed") is False,"node_outbox_promoted_evidence_forbidden")
    require(entry.get("request_grants_execution_authority") is False and entry.get("claim_or_fence_minted") is False,"node_outbox_authority_forbidden")
    require(entry.get("credential_authority")=="TV/TVC" and entry.get("github_token_runtime_authority")=="NONE" and entry.get("authority_effect")=="NONE_LOCAL_CONTINUITY_ONLY","node_outbox_credential_boundary_invalid")
    body=dict(entry);claimed=body.pop("outbox_entry_hash",None);require(claimed==sha_uri(body),"node_outbox_entry_hash_mismatch")
    request=entry.get("materialization_request");require(isinstance(request,dict),"node_outbox_materialization_request_required");validate_sv002_request(request)
    for key in ("materialization_id","request_hash","transport_intent_hash","payload_hash","destination","downstream_owner_ref"):
        require(entry.get(key)==request.get(key),"node_outbox_binding_mismatch:"+key)
    require(payload.get("node_id")==entry.get("node_id") and payload.get("interlock_id")==entry.get("interlock_id") and payload.get("outbox_entry_hash")==entry.get("outbox_entry_hash"),"node_trigger_binding_mismatch")
    trigger=dict(payload);trigger_claim=trigger.pop("trigger_sha256",None);require(trigger_claim==sha_uri(trigger),"node_trigger_hash_mismatch")
    return dict(request),{"transport_origin":origin,"transport_authorization_id":None,"node_id":entry.get("node_id"),"interlock_id":entry.get("interlock_id"),"outbox_entry_hash":entry.get("outbox_entry_hash")}

def _is_sv002(payload:Any)->bool:
    if isinstance(payload,dict) and payload.get("destination")==SV002_DESTINATION and payload.get("downstream_owner_ref")==SV002_OWNER:return True
    if isinstance(payload,dict):
        entry=payload.get("node_outbox_entry")
        if isinstance(entry,dict):
            req=entry.get("materialization_request")
            return isinstance(req,dict) and req.get("destination")==SV002_DESTINATION and req.get("downstream_owner_ref")==SV002_OWNER
    return False

def admit_sv002(*,runtime_root:Path,body:bytes,headers:Mapping[str,str])->dict[str,Any]:
    transport=hil.validate_transport_headers(headers,body)
    try:payload=json.loads(body.decode())
    except Exception as exc:raise ValueError("request_json_invalid") from exc
    request,source=_sv002_request_from_payload(payload,transport);mid=safe_id(str(request["materialization_id"]))
    request_path=runtime_root/hil.REQUEST_DIR_REL/(mid+".json");request_raw=json.dumps(request,sort_keys=True,indent=2).encode()+b"\n";hil._write_once(request_path,request_raw)
    receipt_path=runtime_root/SV002_RECEIPT_DIR/(mid+".json")
    if receipt_path.exists():
        existing=json.loads(receipt_path.read_text());require(existing.get("request_hash")==request.get("request_hash") and existing.get("state")=="INGRESS_ADMITTED","write_once_collision");return existing
    receipt={"schema":SV002_RECEIPT_SCHEMA,"state":"INGRESS_ADMITTED","materialization_id":mid,"request_hash":request["request_hash"],"transport_intent_hash":request["transport_intent_hash"],"payload_hash":request["payload_hash"],"operation_id":request["operation_id"],"packet_id":request["packet_id"],"transport_origin":source["transport_origin"],"transport_authorization_id":source["transport_authorization_id"],"node_id":source["node_id"],"interlock_id":source["interlock_id"],"outbox_entry_hash":source["outbox_entry_hash"],"transport_payload_sha256":transport["payload_sha256"],"queue_ref":str(request_path),"exact_request_validated":True,"write_once_persisted":True,"runtime_execution_attempted":False,"receiver_readiness_claimed":False,"observation_round_trip_claimed":False,"observer_direct_relation_to_stegverse_002":False,"claim_or_fence_minted":False,"g18_required":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_effect":AUTHORITY_EFFECT,"admitted_at":now()}
    raw=json.dumps(receipt,sort_keys=True,indent=2).encode()+b"\n";hil._write_once(receipt_path,raw);latest=runtime_root/SV002_LATEST;latest.parent.mkdir(parents=True,exist_ok=True);latest.write_bytes(raw);return receipt

def profile(tls_enabled:bool)->dict[str,Any]:
    return {"schema":"stegverse.universal-intr-profiled-ingress/v1","state":"ACTIVE_SOVEREIGN_INTR_INGRESS","protocol":"InTr","profile_path":PROFILE_PATH,"materialization_path":INGRESS_PATH,"profiles":["HIL:Ingress","SV002:PublicObservation"],"supported_origins":[hil.ORIGIN_NODE,hil.ORIGIN_RELAY],"event_triggered":True,"always_on_application_receiver_required":False,"second_user_device_required":False,"g18_required":False,"tls_enabled":tls_enabled,"public_tls_terminated_by":"STEGVERSE_SHARED_SERVICE_GATEWAY","credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","execution_authority":"NONE","authority_effect":"NONE_DISCOVERY_EVIDENCE_ONLY"}

class Handler(BaseHTTPRequestHandler):
    server:"Server"
    def log_message(self,_fmt,*_args):return
    def send_json(self,status:int,v:Mapping[str,Any]):
        raw=json.dumps(dict(v),sort_keys=True).encode()+b"\n";self.send_response(status);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        if self.path!=PROFILE_PATH:self.send_json(404,{"state":"NOT_FOUND","authority_effect":"NONE"});return
        self.send_json(200,profile(self.server.tls_enabled))
    def do_POST(self):
        if self.path!=INGRESS_PATH:self.send_json(404,{"state":"NOT_FOUND","authority_effect":AUTHORITY_EFFECT});return
        try:length=int(self.headers.get("Content-Length",""))
        except ValueError:self.send_json(411,{"state":"REJECTED","reason":"content_length_invalid","authority_effect":AUTHORITY_EFFECT});return
        if length<0 or length>hil.MAX_REQUEST_BYTES:self.send_json(413,{"state":"REJECTED","reason":"request_body_too_large","authority_effect":AUTHORITY_EFFECT});return
        body=self.rfile.read(length)
        try:
            payload=json.loads(body.decode())
            receipt=admit_sv002(runtime_root=self.server.runtime_root,body=body,headers=self.headers) if _is_sv002(payload) else hil.admit_materialization(runtime_root=self.server.runtime_root,body=body,headers=self.headers)
        except Exception as exc:self.send_json(400,{"state":"REJECTED","reason":str(exc),"authority_effect":AUTHORITY_EFFECT});return
        self.server.handled_requests+=1;self.send_json(202,receipt)

class Server(ThreadingHTTPServer):
    def __init__(self,address,runtime_root:Path,max_requests:int):super().__init__(address,Handler);self.runtime_root=runtime_root;self.max_requests=max_requests;self.handled_requests=0;self.tls_enabled=False

def serve(*,runtime_root:Path,bind_host:str,bind_port:int,max_requests:int,tls_cert:Path|None=None,tls_key:Path|None=None):
    runtime=runtime_root.expanduser().resolve();runtime.mkdir(parents=True,exist_ok=True);server=Server((bind_host,bind_port),runtime,max_requests)
    if tls_cert or tls_key:
        require(tls_cert is not None and tls_key is not None,"tls_cert_and_key_required_together");ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.load_cert_chain(str(tls_cert),str(tls_key));server.socket=ctx.wrap_socket(server.socket,server_side=True);server.tls_enabled=True
    elif bind_host not in {"127.0.0.1","::1","localhost"}:server.server_close();raise ValueError("non_loopback_ingress_requires_tls")
    bound=server.server_address
    try:
        while not max_requests or server.handled_requests<max_requests:server.handle_request()
    finally:server.server_close()
    return str(bound[0]),int(bound[1])

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--runtime-root",type=Path,required=True);p.add_argument("--bind-host",default="127.0.0.1");p.add_argument("--bind-port",type=int,default=0);p.add_argument("--max-requests",type=int,default=1);p.add_argument("--tls-cert",type=Path);p.add_argument("--tls-key",type=Path);a=p.parse_args();host,port=serve(runtime_root=a.runtime_root,bind_host=a.bind_host,bind_port=a.bind_port,max_requests=a.max_requests,tls_cert=a.tls_cert,tls_key=a.tls_key);print(json.dumps({"schema":"stegverse.universal-intr-profiled-ingress-listener/v1","state":"STOPPED_AFTER_BOUND","bound_host":host,"bound_port":port,"profile_path":PROFILE_PATH,"materialization_path":INGRESS_PATH,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","execution_authority":"NONE","authority_effect":"NONE_DISCOVERY_EVIDENCE_ONLY"},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
