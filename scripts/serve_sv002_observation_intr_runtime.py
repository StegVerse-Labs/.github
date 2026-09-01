#!/usr/bin/env python3
"""Sovereign read-only StegVerse-002 public observation Interlock/InTr runtime.

This runtime exposes only evidence-derived observation projections to a caller
that presents a valid StegVerse Node genesis receipt. It does not route observer
traffic into StegVerse-002 and grants no review, execution, custody, or authority.
"""
from __future__ import annotations
import argparse, hashlib, json, os, ssl, sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Mapping

HOSTED_ENV=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
CREDENTIAL_ENV=("GITHUB_TOKEN","GH_TOKEN","STEGVERSE_GITHUB_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN")
MAX_BODY=2*1024*1024
TASK_ID="SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001"
EXPERIMENT_ID="STEGVERSE-002-SELF-CHARACTERIZATION-001"
WORKER_RECEIPT_REL=Path("receipts/sv002-self-characterization/SHWP-SV002-SELF-CHARACTERIZATION-001.json")
MR_RECEIPT_REL=Path("receipts/sv002-self-characterization/master-records-reconstruction.latest.json")
MR_CANONICAL_RECEIPT_NAME="STEGVERSE_002_SELF_CHARACTERIZATION_RECONSTRUCTION_RECEIPT.json"
PROVENANCE_REL=Path("experiments/self-characterization-001/CONSTRUCTION_PROVENANCE.v0.1.json")

class ObservationRuntimeError(ValueError): pass

def now_iso()->str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def canonical(value:Any)->str:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)

def sha256_hex(value:Any)->str:
    data=value if isinstance(value,(bytes,bytearray)) else canonical(value).encode("utf-8")
    return hashlib.sha256(bytes(data)).hexdigest()

def _reject_hosted_or_secret_env()->None:
    for key in HOSTED_ENV:
        if str(os.environ.get(key,"")).strip().lower() not in {"","0","false","no"}:
            raise ObservationRuntimeError(f"hosted_runtime_forbidden:{key}")
    for key in CREDENTIAL_ENV:
        if os.environ.get(key):
            raise ObservationRuntimeError(f"credential_environment_forbidden:{key}")

def _load_json(path:Path)->dict[str,Any]|None:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value,dict) else None
    except Exception:
        return None

def _canonical_master_records_source()->Path:
    explicit=str(os.environ.get("STEGVERSE_SELF_CHAR_STATE_ROOT") or "").strip()
    root=Path(explicit).expanduser().resolve() if explicit else (Path.home()/".stegverse/self-characterization-001").resolve()
    return root/MR_CANONICAL_RECEIPT_NAME

def _validate_master_records_receipt(value:Mapping[str,Any])->bool:
    if value.get("schema")!="master-records.sv002-self-characterization-reconstruction/v0.2":
        return False
    if value.get("experiment_id")!=EXPERIMENT_ID:
        return False
    if value.get("status")!="PASS" or value.get("reconstruction")!="PASS":
        return False
    body=dict(value)
    claimed=str(body.pop("receipt_sha256",""))
    return bool(claimed) and claimed==sha256_hex(body)

def materialize_master_records_projection_receipt(runtime_root:Path)->dict[str,Any]:
    runtime=runtime_root.expanduser().resolve()
    target=runtime/MR_RECEIPT_REL
    source=_canonical_master_records_source()
    if not source.is_file():
        return {"state":"NOT_AVAILABLE","target":str(target),"source":str(source)}
    try:
        raw=source.read_bytes()
        value=json.loads(raw)
    except Exception as exc:
        raise ObservationRuntimeError("master_records_source_receipt_unreadable") from exc
    if not isinstance(value,dict) or not _validate_master_records_receipt(value):
        raise ObservationRuntimeError("master_records_source_receipt_invalid")
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        existing=target.read_bytes()
        if existing!=raw:
            raise ObservationRuntimeError("master_records_projection_receipt_collision")
        return {"state":"ALREADY_MATERIALIZED","target":str(target),"source":str(source),"receipt_sha256":value["receipt_sha256"]}
    tmp=target.with_suffix(target.suffix+".tmp")
    tmp.write_bytes(raw)
    tmp.replace(target)
    return {"state":"MATERIALIZED","target":str(target),"source":str(source),"receipt_sha256":value["receipt_sha256"]}

def _validate_genesis(observer:Mapping[str,Any])->dict[str,Any]:
    genesis=observer.get("genesis_receipt")
    if not isinstance(genesis,Mapping):
        raise ObservationRuntimeError("observer_genesis_receipt_required")
    required={
        "schema":"stegos.node_handoff_receipt.v1",
        "receipt_number":1,
        "transition":"NODE_REGISTERED",
        "continuity_parent":"GENESIS",
        "authority_effect":"NONE",
        "credential_authority":"TV/TVC",
    }
    for key,value in required.items():
        if genesis.get(key)!=value:
            raise ObservationRuntimeError(f"observer_genesis_{key}_mismatch")
    body=dict(genesis)
    claimed=str(body.pop("receipt_sha256",""))
    actual=sha256_hex(body)
    if claimed!=actual:
        raise ObservationRuntimeError("observer_genesis_receipt_digest_mismatch")
    if observer.get("registration_receipt_sha256")!=claimed:
        raise ObservationRuntimeError("observer_registration_receipt_binding_mismatch")
    if observer.get("node_id")!=genesis.get("node_id"):
        raise ObservationRuntimeError("observer_node_id_binding_mismatch")
    if observer.get("interlock_id")!=genesis.get("interlock_id"):
        raise ObservationRuntimeError("observer_interlock_id_binding_mismatch")
    return dict(genesis)

def _validate_request(request:Mapping[str,Any],authorization_id:str)->dict[str,Any]:
    expected={
        "schema_version":"stegverse.sv002.public_observation.interlock_request.v1",
        "request_class":"SV002_PUBLIC_OBSERVE",
        "operation":"READ_OBSERVATION",
        "transport":"InTr",
        "authority_transfer":False,
    }
    for key,value in expected.items():
        if request.get(key)!=value:
            raise ObservationRuntimeError(f"request_{key}_mismatch")
    if request.get("authority_ref")!=authorization_id:
        raise ObservationRuntimeError("authorization_binding_mismatch")
    bindings=request.get("bindings")
    if not isinstance(bindings,Mapping) or bindings.get("experiment_id")!=EXPERIMENT_ID or bindings.get("observation_projection")!="PUBLIC_READ_ONLY":
        raise ObservationRuntimeError("experiment_projection_binding_mismatch")
    observer=request.get("observer")
    if not isinstance(observer,Mapping):
        raise ObservationRuntimeError("observer_binding_required")
    genesis=_validate_genesis(observer)
    body=dict(request)
    claimed=str(body.pop("request_sha256",""))
    if claimed!=sha256_hex(body):
        raise ObservationRuntimeError("request_sha256_mismatch")
    return genesis

def _load_stegos(stegos_root:Path):
    root=stegos_root.expanduser().resolve()
    if not (root/"stegos/universal_intr_transport.py").is_file():
        raise ObservationRuntimeError(f"stegos_source_missing:{root}")
    if str(root) not in sys.path:
        sys.path.insert(0,str(root))
    from stegos.universal_intr_transport import build_transport_intent, build_hop_receipt, sha256_uri
    return build_transport_intent,build_hop_receipt,sha256_uri

def _interaction_events(chain:Any)->list[Any]:
    if isinstance(chain,list):
        return chain
    if isinstance(chain,dict):
        for key in ("events","interactions","receipts","interaction_receipts"):
            value=chain.get(key)
            if isinstance(value,list):
                return value
    return []

def _observed_interlock(chain:Any,target:str)->bool:
    if isinstance(chain,list):
        return any(_observed_interlock(item,target) for item in chain)
    if not isinstance(chain,dict):
        return False
    target_values={
        str(chain.get("counterpart") or ""),
        str(chain.get("counterpart_id") or ""),
        str(chain.get("destination_organization") or ""),
        str(chain.get("external_organization") or ""),
        str(chain.get("organization") or ""),
    }
    transition=str(chain.get("transition") or chain.get("transition_id") or "").upper()
    interlock_state=str(chain.get("interlock_state") or "").upper()
    state=str(chain.get("state") or "").upper()
    established=(
        interlock_state in {"CONNECTED","ESTABLISHED"}
        or transition in {"INTERLOCK_ESTABLISHED","INTERLOCK_CONNECTED","EXTERNAL_INTERLOCK_ESTABLISHED"}
        or state in {"INTERLOCK_ESTABLISHED","CONNECTED"} and "INTERLOCK" in transition
    )
    if target in target_values and established:
        return True
    return any(_observed_interlock(value,target) for value in chain.values() if isinstance(value,(dict,list)))


def build_projection(runtime_root:Path,micro_node_root:Path)->dict[str,Any]:
    runtime=runtime_root.expanduser().resolve()
    _=micro_node_root
    materialization=materialize_master_records_projection_receipt(runtime)
    master=_load_json(runtime/MR_RECEIPT_REL)
    if not master:
        return {
            "schema":"stegverse.sv002.public_observation.projection.v1",
            "experiment_id":EXPERIMENT_ID,
            "generated_from_evidence_at":now_iso(),
            "observation_source":"MASTER_RECORDS_ONLY",
            "state":{
                "master_records_reconstruction":"NOT_OBSERVED",
                "principal_execution":"NOT_OBSERVED",
                "final_self_characterization":"NOT_OBSERVED",
            },
            "topology":{
                "entities":[{"entity_id":"StegVerse-002","evidence_state":"KNOWN_SUBJECT"}],
                "relations":[],
                "observer_direct_relation_to_stegverse_002":False,
            },
            "events":[],
            "artifacts":{"reconstructed_artifact_sha256":{}},
            "reconstruction":{"state":"NOT_OBSERVED","master_records_required":True},
            "materialization":materialization,
            "authority_effect":"NONE",
            "observer_interaction_target":"READ_ONLY_MASTER_RECORDS_PROJECTION",
        }
    checks=master.get("checks") if isinstance(master.get("checks"),dict) else {}
    evidence=master.get("evidence") if isinstance(master.get("evidence"),dict) else {}
    artifact_hashes=evidence.get("artifact_sha256") if isinstance(evidence.get("artifact_sha256"),dict) else {}
    reconstruction_pass=master.get("status")=="PASS" and master.get("reconstruction")=="PASS"
    execution_reconstructed=bool(checks.get("execution_completed")) and reconstruction_pass
    self_char_reconstructed=("SELF_CHARACTERIZATION.md" in artifact_hashes) and reconstruction_pass
    return {
        "schema":"stegverse.sv002.public_observation.projection.v1",
        "experiment_id":EXPERIMENT_ID,
        "generated_from_evidence_at":now_iso(),
        "observation_source":"MASTER_RECORDS_ONLY",
        "state":{
            "master_records_reconstruction":"PASS" if reconstruction_pass else str(master.get("status") or "OBSERVED_NONPASS"),
            "principal_execution":"RECONSTRUCTED" if execution_reconstructed else "NOT_ESTABLISHED",
            "final_self_characterization":"HASH_RECONSTRUCTED" if self_char_reconstructed else "NOT_ESTABLISHED",
        },
        "topology":{
            "entities":[{"entity_id":"StegVerse-002","evidence_state":"KNOWN_SUBJECT"}],
            "relations":[],
            "observer_direct_relation_to_stegverse_002":False,
            "relationship_state_source":"MASTER_RECORDS_ONLY",
        },
        "events":[{
            "event":"MASTER_RECORDS_RECONSTRUCTION_RECEIPT_OBSERVED",
            "status":master.get("status"),
            "receipt_sha256":master.get("receipt_sha256"),
            "evidence_ref":MR_RECEIPT_REL.as_posix(),
        }],
        "artifacts":{
            "reconstructed_artifact_sha256":artifact_hashes,
            "subject_identity_sha256":evidence.get("subject_identity_sha256"),
            "capability_realizations":evidence.get("capability_realizations"),
            "ordered_transition_receipts":evidence.get("ordered_transition_receipts"),
            "repository_ledger_root":evidence.get("repository_ledger_root"),
            "organization_ledger_root":evidence.get("organization_ledger_root"),
        },
        "materialization":materialization,
        "reconstruction":master,
        "authority_effect":"NONE",
        "observer_interaction_target":"READ_ONLY_MASTER_RECORDS_PROJECTION",
    }

def process_observation(request:dict[str,Any],*,runtime_root:Path,micro_node_root:Path,stegos_root:Path,authorization_id:str,boundary_identity_ref:str)->dict[str,Any]:
    genesis=_validate_request(request,authorization_id)
    build_transport_intent,build_hop_receipt,sha256_uri=_load_stegos(stegos_root)
    ingress_intent=build_transport_intent(
        operation_id="SV002_PUBLIC_OBSERVE:"+request["request_sha256"][:24],
        payload_hash=sha256_uri(request),
        source_boundary="DEVICE_SYSTEM",
        source_subsystem="STEGVERSE_OBSERVER_NODE",
        destination_boundary="STEGOS_ECOSYSTEM",
        destination_subsystem="SV002_PUBLIC_OBSERVATION_PROJECTION",
    )
    ingress=build_hop_receipt(
        ingress_intent,hop_index=1,receipt_id="SV002-OBS-IN-"+ingress_intent["packet_id"][5:],
        boundary_identity_ref=boundary_identity_ref,recorded_at=now_iso(),prior_receipt_hash=None,transition_state="RECEIVED")
    projection=build_projection(runtime_root,micro_node_root)
    response={
        "schema_version":"stegverse.sv002.public_observation.interlock_response.v1",
        "operation":"READ_OBSERVATION",
        "decision":"ALLOW_READ_ONLY_OBSERVATION",
        "authority_effect":"NONE",
        "authority_transfer":False,
        "observer_binding":{
            "node_id":genesis["node_id"],
            "interlock_id":genesis["interlock_id"],
            "registration_receipt_sha256":genesis["receipt_sha256"],
        },
        "bindings":dict(request["bindings"]),
        "projection":projection,
    }
    egress_intent=build_transport_intent(
        operation_id="SV002_PUBLIC_OBSERVE_RESPONSE:"+request["request_sha256"][:24],
        payload_hash=sha256_uri(response),
        source_boundary="STEGOS_ECOSYSTEM",
        source_subsystem="SV002_PUBLIC_OBSERVATION_PROJECTION",
        destination_boundary="DEVICE_SYSTEM",
        destination_subsystem="STEGVERSE_OBSERVER_NODE",
        prior_transport_receipt_hash=ingress["receipt_hash"],
    )
    egress=build_hop_receipt(
        egress_intent,hop_index=1,receipt_id="SV002-OBS-OUT-"+egress_intent["packet_id"][5:],
        boundary_identity_ref=boundary_identity_ref,recorded_at=now_iso(),prior_receipt_hash=ingress["receipt_hash"],transition_state="FORWARDED")
    response["transport_receipts"]={"ingress":ingress,"egress":egress}
    receipt_dir=runtime_root.expanduser().resolve()/"receipts/sovereign-network/sv002-public-observation"
    receipt_dir.mkdir(parents=True,exist_ok=True)
    bundle={
        "schema":"stegverse.sv002-public-observation-runtime-receipt-bundle/v1",
        "state":"SV002_PUBLIC_OBSERVATION_ROUND_TRIP_FORWARDED",
        "observer_binding":response["observer_binding"],
        "request_sha256":request["request_sha256"],
        "ingress_receipt":ingress,
        "egress_receipt":egress,
        "observer_direct_relation_to_stegverse_002":False,
        "authority_effect":"NONE",
        "credential_authority":"TV/TVC",
        "recorded_at":now_iso(),
    }
    path=receipt_dir/(ingress["receipt_id"]+".json")
    if not path.exists():
        path.write_text(json.dumps(bundle,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return response

def make_handler(args):
    class Handler(BaseHTTPRequestHandler):
        server_version="StegVerseSV002ObservationInTr/1"
        def _cors(self):
            origin=self.headers.get("Origin")
            if origin==args.allowed_origin:
                self.send_header("Access-Control-Allow-Origin",origin); self.send_header("Vary","Origin")
        def do_GET(self):
            if self.path!="/intr/sv002-observe/readiness":
                self.send_response(404); self.end_headers(); return
            raw=json.dumps({"schema":"stegverse.sv002-public-observation-runtime-readiness/v1","state":"READY","transport":"InTr","credential_authority":"TV/TVC","authority_effect":"NONE"},sort_keys=True,separators=(",",":")).encode()
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
        def do_OPTIONS(self):
            if self.headers.get("Origin")!=args.allowed_origin:
                self.send_response(403); self.end_headers(); return
            self.send_response(204); self._cors(); self.send_header("Access-Control-Allow-Methods","POST, OPTIONS"); self.send_header("Access-Control-Allow-Headers","content-type,x-stegverse-transport,x-stegverse-authorization-id,x-stegverse-payload-sha256"); self.end_headers()
        def do_POST(self):
            if self.path!="/intr/sv002-observe":
                self.send_response(404); self.end_headers(); return
            try:
                if self.headers.get("Origin")!=args.allowed_origin: raise ObservationRuntimeError("origin_not_admitted")
                if self.headers.get("X-StegVerse-Transport")!="InTr": raise ObservationRuntimeError("transport_header_mismatch")
                authorization_id=str(self.headers.get("X-StegVerse-Authorization-Id") or "").strip()
                if not authorization_id: raise ObservationRuntimeError("authorization_id_required")
                length=int(self.headers.get("Content-Length") or "0")
                if length<=0 or length>MAX_BODY: raise ObservationRuntimeError("request_size_invalid")
                body=self.rfile.read(length)
                if str(self.headers.get("X-StegVerse-Payload-SHA256") or "")!=hashlib.sha256(body).hexdigest(): raise ObservationRuntimeError("request_payload_hash_mismatch")
                request=json.loads(body.decode("utf-8"))
                if not isinstance(request,dict): raise ObservationRuntimeError("request_object_required")
                response=process_observation(request,runtime_root=args.runtime_root,micro_node_root=args.micro_node_root,stegos_root=args.stegos_root,authorization_id=authorization_id,boundary_identity_ref=args.boundary_identity_ref)
                raw=(json.dumps(response,sort_keys=True,separators=(",",":"))+"\n").encode()
                self.send_response(200); self._cors(); self.send_header("Content-Type","application/json"); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw); self.server.processed_requests+=1
            except Exception as exc:
                raw=json.dumps({"schema":"stegverse.sv002-public-observation-runtime-error/v1","state":"FAIL_CLOSED","reason":str(exc),"authority_effect":"NONE"}).encode()
                self.send_response(400); self._cors(); self.send_header("Content-Type","application/json"); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
        def log_message(self,fmt,*values): return
    return Handler

class BoundedHTTPServer(HTTPServer):
    processed_requests=0

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--stegos-root",type=Path,required=True); ap.add_argument("--micro-node-root",type=Path,required=True); ap.add_argument("--runtime-root",type=Path,required=True)
    ap.add_argument("--host",default="127.0.0.1"); ap.add_argument("--port",type=int,default=8766); ap.add_argument("--max-requests",type=int,default=0)
    ap.add_argument("--allowed-origin",default="https://stegverse.org"); ap.add_argument("--boundary-identity-ref",required=True); ap.add_argument("--tls-cert",type=Path); ap.add_argument("--tls-key",type=Path)
    args=ap.parse_args(); _reject_hosted_or_secret_env()
    if args.host not in {"127.0.0.1","::1","localhost"} and (not args.tls_cert or not args.tls_key): raise ObservationRuntimeError("non_loopback_requires_tls")
    server=BoundedHTTPServer((args.host,args.port),make_handler(args))
    if args.tls_cert and args.tls_key:
        ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(args.tls_cert,args.tls_key); server.socket=ctx.wrap_socket(server.socket,server_side=True)
    if args.max_requests<=0: server.serve_forever(poll_interval=0.5)
    else:
        while server.processed_requests<args.max_requests: server.handle_request()
    return 0
if __name__=="__main__": raise SystemExit(main())
