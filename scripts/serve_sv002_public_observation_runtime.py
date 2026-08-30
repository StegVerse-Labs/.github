#!/usr/bin/env python3
"""Read-only StegVerse-002 public observation Interlock/InTr receiver."""
from __future__ import annotations
import argparse, hashlib, json, os, ssl, sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN_CREDS=("GITHUB_TOKEN","GH_TOKEN","STEGVERSE_GITHUB_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN")
MAX_BODY=2*1024*1024
EXPERIMENT_ID="STEGVERSE-002-SELF-CHARACTERIZATION-001"

class ObservationError(ValueError): pass
def now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def canonical(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)
def sha256_hex(v): return hashlib.sha256((v if isinstance(v,bytes) else str(v).encode())).hexdigest()
def sha256_uri(v): return "sha256:"+hashlib.sha256((v if isinstance(v,bytes) else str(v).encode())).hexdigest()
def load_json(p:Path)->dict[str,Any]|None:
    try:
        v=json.loads(p.read_text(encoding="utf-8")); return v if isinstance(v,dict) else None
    except Exception: return None
def reject_hosted():
    for k in HOSTED:
        if str(os.getenv(k,"")).lower() in {"1","true","yes"}: raise ObservationError("hosted_runtime_forbidden:"+k)
    for k in FORBIDDEN_CREDS:
        if os.getenv(k): raise ObservationError("credential_environment_forbidden:"+k)

def load_transport(stegos_root:Path):
    root=stegos_root.expanduser().resolve()
    if not (root/"stegos/universal_intr_transport.py").is_file(): raise ObservationError("stegos_transport_missing")
    if str(root) not in sys.path: sys.path.insert(0,str(root))
    from stegos.universal_intr_transport import build_transport_intent, build_hop_receipt
    return build_transport_intent, build_hop_receipt

def validate_genesis(observer:dict[str,Any])->dict[str,Any]:
    g=observer.get("genesis_receipt")
    if not isinstance(g,dict): raise ObservationError("observer_genesis_receipt_required")
    if g.get("schema")!="stegos.node_handoff_receipt.v1" or g.get("receipt_number")!=1 or g.get("transition")!="NODE_REGISTERED":
        raise ObservationError("observer_genesis_schema_invalid")
    if g.get("continuity_parent")!="GENESIS" or g.get("authority_effect")!="NONE" or g.get("credential_authority")!="TV/TVC":
        raise ObservationError("observer_genesis_authority_invalid")
    body=dict(g); claimed=str(body.pop("receipt_sha256",""))
    actual=hashlib.sha256(canonical(body).encode()).hexdigest()
    if claimed!=actual: raise ObservationError("observer_genesis_digest_mismatch")
    if observer.get("registration_receipt_sha256")!=claimed: raise ObservationError("observer_registration_digest_mismatch")
    if observer.get("node_id")!=g.get("node_id") or observer.get("interlock_id")!=g.get("interlock_id"):
        raise ObservationError("observer_identity_binding_mismatch")
    return {"node_id":g["node_id"],"interlock_id":g["interlock_id"],"registration_receipt_sha256":claimed}

def validate_request(req:dict[str,Any])->dict[str,Any]:
    if req.get("schema_version")!="stegverse.sv002.public_observation.interlock_request.v1": raise ObservationError("request_schema_mismatch")
    if req.get("request_class")!="SV002_PUBLIC_OBSERVE" or req.get("operation")!="READ_OBSERVATION": raise ObservationError("operation_not_admitted")
    if req.get("transport")!="InTr" or req.get("authority_transfer") is not False: raise ObservationError("transport_authority_mismatch")
    bindings=req.get("bindings") or {}
    if bindings.get("experiment_id")!=EXPERIMENT_ID or bindings.get("observation_projection")!="PUBLIC_READ_ONLY": raise ObservationError("experiment_binding_mismatch")
    claimed=str(req.get("request_sha256") or "")
    body=dict(req); body.pop("request_sha256",None)
    if claimed!=hashlib.sha256(canonical(body).encode()).hexdigest(): raise ObservationError("request_sha256_mismatch")
    return validate_genesis(req.get("observer") or {})

def projection(runtime_root:Path)->dict[str,Any]:
    runtime=runtime_root.expanduser().resolve()
    state_root=Path(os.getenv("STEGVERSE_SELF_CHAR_STATE_ROOT",str(Path.home()/".stegverse/self-characterization-001"))).expanduser().resolve()
    worker=load_json(runtime/"receipts/sv002-self-characterization/SHWP-SV002-SELF-CHARACTERIZATION-001.json")
    execution=load_json(state_root/"EXPERIMENT_EXECUTION_RECEIPT.json")
    chain=load_json(state_root/"INTERACTION_RECEIPT_CHAIN.json")
    formal=load_json(state_root/"SELF_CHARACTERIZATION_FORMAL.json")
    human=(state_root/"SELF_CHARACTERIZATION.md").read_text(encoding="utf-8") if (state_root/"SELF_CHARACTERIZATION.md").is_file() else None
    completed=bool(worker and worker.get("state")=="COMPLETED" and execution and execution.get("state")=="COMPLETED")
    events=[]
    if worker: events.append({"event_class":"RESIDENT_WORKER_STATE","state":worker.get("state"),"transition":"SV002_SELF_CHARACTERIZATION_COMPLETED" if completed else "SV002_SELF_CHARACTERIZATION_NOT_COMPLETED"})
    if execution: events.append({"event_class":"PRINCIPAL_EXECUTION","state":execution.get("state")})
    if chain:
        rows=chain.get("receipts") if isinstance(chain.get("receipts"),list) else chain.get("interactions")
        if isinstance(rows,list):
            for i,row in enumerate(rows): events.append({"event_class":"INTERACTION_RECEIPT","index":i,"evidence":row})
    return {
      "schema":"stegverse.sv002.public_observation_projection.v1",
      "experiment_id":EXPERIMENT_ID,
      "state":{"principal_execution":"COMPLETED" if completed else "NOT_OBSERVED","worker_state":worker.get("state") if worker else "NOT_OBSERVED"},
      "topology":{"StegVerse-002_to_SDK":"OBSERVED" if chain else "NOT_OBSERVED","observer_to_StegVerse-002":"FORBIDDEN","observer_terminus":"PUBLIC_READ_ONLY_OBSERVATION_PROJECTION"},
      "knowledge":{"Admissible-Existence":{"availability":"KNOWN_AVAILABLE_FROM_CONSTRUCTION_PROVENANCE","interlock":"NOT_CONNECTED_UNLESS_EVIDENCED","mathematics_access":"UNKNOWN_UNLESS_EVIDENCED"}},
      "events":events,
      "self_characterization":{"human":human,"formal":formal} if completed else None,
      "reconstruction":{"master_records_state":"NOT_OBSERVED","claim":"No Master Records reconstruction is inferred from local experiment artifacts."},
      "generated_from":{"worker_receipt_present":worker is not None,"execution_receipt_present":execution is not None,"interaction_chain_present":chain is not None},
      "authority_effect":"NONE"
    }

def process(req:dict[str,Any],*,stegos_root:Path,runtime_root:Path,boundary_identity_ref:str,authorization_id:str)->dict[str,Any]:
    observer=validate_request(req)
    if req.get("authority_ref")!=authorization_id: raise ObservationError("authorization_binding_mismatch")
    build_intent,build_receipt=load_transport(stegos_root)
    req_payload=sha256_uri(canonical(req))
    ingress_intent=build_intent(operation_id="SV002_PUBLIC_OBSERVE_INGRESS",payload_hash=req_payload,source_boundary="DEVICE_SYSTEM",source_subsystem=observer["node_id"],destination_boundary="STEGOS_ECOSYSTEM",destination_subsystem="sv002-public-observation")
    ingress=build_receipt(ingress_intent,hop_index=1,receipt_id="SV002-OBS-IN-"+hashlib.sha256(canonical(req).encode()).hexdigest()[:24],boundary_identity_ref=boundary_identity_ref,recorded_at=now_iso(),prior_receipt_hash=None,transition_state="RECEIVED")
    p=projection(runtime_root)
    base={"schema_version":"stegverse.sv002.public_observation.interlock_response.v1","operation":"READ_OBSERVATION","decision":"ALLOW_BOUNDED_CONTEXT","authority_effect":"NONE","authority_transfer":False,"observer_binding":observer,"projection":p}
    egress_payload=sha256_uri(canonical(base))
    egress_intent=build_intent(operation_id="SV002_PUBLIC_OBSERVE_EGRESS",payload_hash=egress_payload,source_boundary="STEGOS_ECOSYSTEM",source_subsystem="sv002-public-observation",destination_boundary="DEVICE_SYSTEM",destination_subsystem=observer["node_id"],prior_transport_receipt_hash=ingress["receipt_hash"])
    egress=build_receipt(egress_intent,hop_index=1,receipt_id="SV002-OBS-OUT-"+hashlib.sha256(canonical(base).encode()).hexdigest()[:24],boundary_identity_ref=boundary_identity_ref,recorded_at=now_iso(),prior_receipt_hash=ingress["receipt_hash"],transition_state="FORWARDED")
    response={**base,"transport_receipts":{"ingress":ingress,"egress":egress}}
    root=runtime_root.expanduser().resolve()/"receipts/sovereign-network/sv002-public-observe"; root.mkdir(parents=True,exist_ok=True)
    bundle={"schema":"stegverse.sv002-public-observation-runtime-receipt/v1","state":"SV002_PUBLIC_OBSERVATION_FORWARDED","observer_binding":observer,"ingress_receipt":ingress,"egress_receipt":egress,"projection_state":p["state"],"authority_effect":"NONE","recorded_at":now_iso()}
    (root/(ingress["receipt_id"]+".json")).write_text(json.dumps(bundle,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return response

def handler(args):
    class H(BaseHTTPRequestHandler):
        server_version="StegVerseSV002Observe/1"
        def cors(self):
            if self.headers.get("Origin")==args.allowed_origin:
                self.send_header("Access-Control-Allow-Origin",args.allowed_origin); self.send_header("Vary","Origin")
        def do_GET(self):
            if self.path!="/intr/sv002-observe/readiness": self.send_response(404); self.end_headers(); return
            raw=json.dumps({"schema":"stegverse.sv002-public-observation-readiness/v1","state":"READY","transport":"InTr","credential_authority":"TV/TVC","authority_effect":"NONE"}).encode()
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
        def do_OPTIONS(self):
            if self.headers.get("Origin")!=args.allowed_origin: self.send_response(403); self.end_headers(); return
            self.send_response(204); self.cors(); self.send_header("Access-Control-Allow-Methods","POST, OPTIONS"); self.send_header("Access-Control-Allow-Headers","content-type,x-stegverse-transport,x-stegverse-authorization-id,x-stegverse-payload-sha256"); self.end_headers()
        def do_POST(self):
            if self.path!="/intr/sv002-observe": self.send_response(404); self.end_headers(); return
            try:
                if self.headers.get("Origin")!=args.allowed_origin: raise ObservationError("origin_not_admitted")
                if self.headers.get("X-StegVerse-Transport")!="InTr": raise ObservationError("transport_header_mismatch")
                auth=str(self.headers.get("X-StegVerse-Authorization-Id") or "").strip()
                if not auth: raise ObservationError("authorization_id_required")
                n=int(self.headers.get("Content-Length") or "0")
                if n<=0 or n>MAX_BODY: raise ObservationError("request_size_invalid")
                body=self.rfile.read(n)
                if self.headers.get("X-StegVerse-Payload-SHA256")!=hashlib.sha256(body).hexdigest(): raise ObservationError("payload_hash_mismatch")
                req=json.loads(body.decode()); response=process(req,stegos_root=args.stegos_root,runtime_root=args.runtime_root,boundary_identity_ref=args.boundary_identity_ref,authorization_id=auth)
                raw=(json.dumps(response,sort_keys=True,separators=(",",":"))+"\n").encode()
                self.send_response(200); self.cors(); self.send_header("Content-Type","application/json"); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw); self.server.processed_requests+=1
            except Exception as exc:
                raw=json.dumps({"schema":"stegverse.sv002-public-observation-error/v1","state":"FAIL_CLOSED","reason":str(exc),"authority_effect":"NONE"}).encode()
                self.send_response(400); self.cors(); self.send_header("Content-Type","application/json"); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
        def log_message(self,*_): return
    return H

class S(HTTPServer): processed_requests=0
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--stegos-root",type=Path,required=True); ap.add_argument("--runtime-root",type=Path,required=True); ap.add_argument("--host",default="127.0.0.1"); ap.add_argument("--port",type=int,default=8766); ap.add_argument("--max-requests",type=int,default=0); ap.add_argument("--allowed-origin",default="https://stegverse.org"); ap.add_argument("--boundary-identity-ref",required=True); ap.add_argument("--tls-cert",type=Path); ap.add_argument("--tls-key",type=Path); a=ap.parse_args()
    reject_hosted()
    if a.host not in {"127.0.0.1","::1","localhost"} and (not a.tls_cert or not a.tls_key): raise ObservationError("non_loopback_requires_tls")
    s=S((a.host,a.port),handler(a))
    if a.tls_cert and a.tls_key:
        c=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); c.load_cert_chain(a.tls_cert,a.tls_key); s.socket=c.wrap_socket(s.socket,server_side=True)
    if a.max_requests<=0: s.serve_forever(poll_interval=.5)
    else:
        while s.processed_requests<a.max_requests: s.handle_request()
    return 0
if __name__=="__main__": raise SystemExit(main())
