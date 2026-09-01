#!/usr/bin/env python3
"""Fenced launcher for the StegVerse-002 public observation InTr runtime."""
from __future__ import annotations
import hashlib, json, os, subprocess, sys, time, urllib.request
from pathlib import Path
from typing import Any, Mapping

TASK_ID="SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001"; WORKER_ID="sv002-public-observation-runtime-worker"
CONFIG_ENV="STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG"; DEFAULT_CONFIG=Path.home()/".stegverse/config/sv002-public-observation-runtime.json"
NODE_MARKERS=(Path("/etc/stegverse/node.json"),Path.home()/".stegverse/node.json")
HOSTED_ENV=("GITHUB_ACTIONS","CI","RENDER","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","STEGVERSE_GITHUB_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN")
class RoutePending(RuntimeError): pass

def truthy(v): return str(v or "").strip().lower() not in {"","0","false","no"}
def validate_invocation(inv:Mapping[str,Any])->dict[str,Any]:
    if inv.get("schema")!="stegverse.worker-invocation/v0.1": raise RuntimeError("unexpected invocation schema")
    task=inv.get("task") or {}
    if task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID: raise RuntimeError("task/worker identity mismatch")
    if not task.get("claim_id"): raise RuntimeError("canonical scheduler claim required")
    if not isinstance((task.get("heartbeat_timing") or {}).get("fencing_token"),int): raise RuntimeError("fresh fencing token required")
    auth=(inv.get("handoff") or {}).get("authority") or {}
    if auth.get("credential_authority")!="TV/TVC" or auth.get("github_token_required") is not False or auth.get("non_tv_tvc_secret_or_token_allowed") is not False: raise RuntimeError("authority boundary drift")
    return dict(task)
def find_node()->Path:
    for p in NODE_MARKERS:
        if p.is_file():
            v=json.loads(p.read_text())
            if v.get("declared") is not True: raise RoutePending("sovereign node not declared")
            return p
    raise RoutePending("no declared sovereign StegVerse node marker")
def load_config()->dict[str,Any]:
    p=Path(os.getenv(CONFIG_ENV) or DEFAULT_CONFIG).expanduser().resolve()
    if not p.is_file(): raise RoutePending(f"SV002 observation route config not present: {p}")
    c=json.loads(p.read_text())
    for k in ("stegos_root","micro_node_root","runtime_root","host","port","allowed_origin","boundary_identity_ref"):
        if c.get(k) in (None,""): raise RoutePending(f"route config missing {k}")
    if c.get("master_records_reconstruction_receipt") not in (None,""):
        c["master_records_reconstruction_receipt"]=str(Path(str(c["master_records_reconstruction_receipt"])).expanduser().resolve())
    if c.get("credential_authority")!="TV/TVC" or c.get("github_token_runtime_authority")!="NONE": raise RuntimeError("route authority drift")
    for k in ("stegos_root","micro_node_root","runtime_root"):
        if not Path(str(c[k])).expanduser().is_dir(): raise RoutePending(f"local root unavailable: {k}")
    return c
def paths(c):
    root=Path(str(c["runtime_root"])).expanduser().resolve()/"receipts/sovereign-network/sv002-public-observation"
    return root/"receiver.pid",root/"receiver.log",root/"receiver.latest.json"
def pid_alive(pid):
    try: os.kill(pid,0); return pid>1
    except OSError: return False
def read_pid(p):
    try:
        v=int(p.read_text().strip()); return v if pid_alive(v) else None
    except Exception: return None
def readiness(c):
    with urllib.request.urlopen(f"http://127.0.0.1:{int(c['port'])}/intr/sv002-observe/readiness",timeout=2) as response:
        value=json.loads(response.read().decode())
    if response.status!=200 or value.get("state")!="READY" or value.get("transport")!="InTr": raise RoutePending("SV002 observation receiver readiness not observed")
    return value
def _canonical(value:Any)->str:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)

def _sha256_uri(value:Any)->str:
    return "sha256:"+hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()

def _plain_sha256(value:Any)->bool:
    return isinstance(value,str) and len(value)==64 and all(ch in "0123456789abcdef" for ch in value)

def _valid_hop(receipt:Any, *, transition:str, from_role:str, to_role:str, prefix:str)->bool:
    if not isinstance(receipt,dict): return False
    required={
      "schema":"stegverse.intr.hop_receipt/v1",
      "boundary_verification":"VERIFIED",
      "transition_state":transition,
      "from_role":from_role,
      "to_role":to_role,
      "secret_plaintext_present":False,
      "authority_transfer":False,
    }
    if any(receipt.get(k)!=v for k,v in required.items()): return False
    if not str(receipt.get("receipt_id") or "").startswith(prefix): return False
    claimed=receipt.get("receipt_hash")
    if not isinstance(claimed,str) or not claimed.startswith("sha256:") or len(claimed)!=71: return False
    body=dict(receipt); body.pop("receipt_hash",None)
    return claimed==_sha256_uri(body)

def validate_round_bundle(bundle:Any)->None:
    if not isinstance(bundle,dict): raise RuntimeError("SV002 observation round-trip bundle must be an object")
    expected={
      "schema":"stegverse.sv002-public-observation-runtime-receipt-bundle/v1",
      "state":"SV002_PUBLIC_OBSERVATION_ROUND_TRIP_FORWARDED",
      "observer_direct_relation_to_stegverse_002":False,
      "credential_authority":"TV/TVC",
      "authority_effect":"NONE",
    }
    for k,v in expected.items():
        if bundle.get(k)!=v: raise RuntimeError(f"SV002 observation round-trip bundle {k} mismatch")
    if not _plain_sha256(bundle.get("request_sha256")): raise RuntimeError("SV002 observation request digest invalid")
    observer=bundle.get("observer_binding")
    if not isinstance(observer,dict): raise RuntimeError("SV002 observation observer binding missing")
    if not all(isinstance(observer.get(k),str) and observer.get(k) for k in ("node_id","interlock_id")):
        raise RuntimeError("SV002 observation observer identity incomplete")
    if not _plain_sha256(observer.get("registration_receipt_sha256")):
        raise RuntimeError("SV002 observation registration receipt digest invalid")
    ingress=bundle.get("ingress_receipt"); egress=bundle.get("egress_receipt")
    if not _valid_hop(ingress,transition="RECEIVED",from_role="DEVICE_SYSTEM",to_role="STEGOS_ECOSYSTEM",prefix="SV002-OBS-IN-"):
        raise RuntimeError("SV002 observation ingress receipt integrity invalid")
    if not _valid_hop(egress,transition="FORWARDED",from_role="STEGOS_ECOSYSTEM",to_role="DEVICE_SYSTEM",prefix="SV002-OBS-OUT-"):
        raise RuntimeError("SV002 observation egress receipt integrity invalid")
    if egress.get("prior_receipt_hash")!=ingress.get("receipt_hash"):
        raise RuntimeError("SV002 observation egress lineage does not bind ingress receipt")

def existing_round(c):
    root=Path(str(c["runtime_root"])).expanduser().resolve()/"receipts/sovereign-network/sv002-public-observation"
    if not root.is_dir(): return None
    for p in sorted(root.glob("SV002-OBS-IN-*.json")):
        try: v=json.loads(p.read_text())
        except Exception: continue
        if not isinstance(v,dict) or v.get("state")!="SV002_PUBLIC_OBSERVATION_ROUND_TRIP_FORWARDED": continue
        validate_round_bundle(v)
        return str(p)
    return None
def ensure_receiver(c,server):
    observed=existing_round(c)
    if observed: return {"state":"COMPLETE","transition_id":"SV002_PUBLIC_OBSERVATION_ROUND_TRIP_OBSERVED","receipt_bundle_ref":observed}
    pid_file,log_file,ready_file=paths(c); pid_file.parent.mkdir(parents=True,exist_ok=True); pid=read_pid(pid_file)
    if pid is None:
        cmd=[sys.executable,str(server),"--stegos-root",str(c["stegos_root"]),"--micro-node-root",str(c["micro_node_root"]),"--runtime-root",str(c["runtime_root"]),"--host",str(c["host"]),"--port",str(c["port"]),"--max-requests","0","--allowed-origin",str(c["allowed_origin"]),"--boundary-identity-ref",str(c["boundary_identity_ref"])]
        log=log_file.open("ab",buffering=0)
        child_env={"PATH":os.getenv("PATH",""),"HOME":os.getenv("HOME",""),"STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY":"TV/TVC","STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY":"NONE"}
        if c.get("master_records_reconstruction_receipt"):
            child_env["STEGVERSE_SV002_MASTER_RECORDS_RECONSTRUCTION_RECEIPT"]=str(c["master_records_reconstruction_receipt"])
        proc=subprocess.Popen(cmd,cwd=server.parent.parent,env=child_env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
        pid=proc.pid; pid_file.write_text(str(pid)+"\n")
    ready=None; last=None
    for _ in range(40):
        if not pid_alive(pid): raise RuntimeError("SV002 observation receiver exited before readiness")
        try: ready=readiness(c); break
        except Exception as exc: last=exc; time.sleep(.1)
    if ready is None: raise RoutePending("SV002 observation receiver readiness unavailable: "+type(last).__name__)
    receipt={"schema":"stegverse.sv002-public-observation-resident-receiver-readiness/v1","state":"READY","transition_id":"SV002_PUBLIC_OBSERVATION_RECEIVER_READY","pid":pid,"host":c["host"],"port":c["port"],"readiness":ready,"persistent_receiver":True,"round_trip_observed":False,"credential_authority":"TV/TVC","authority_effect":"NONE"}
    ready_file.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n"); return receipt
def response(state,transition,**extra):
    x={"schema":"stegverse.worker-response/v0.1","state":state,"transition_id":transition,"transition_sequence":1,"credential_authority":"TV/TVC","github_token_used":False,"repository_writeback_performed":False}; x.update(extra); return x
def main():
    try:
        inv=json.loads(sys.stdin.readline())
        if any(truthy(os.getenv(k)) for k in HOSTED_ENV): raise RuntimeError("hosted runtime forbidden")
        if any(truthy(os.getenv(k)) for k in FORBIDDEN): raise RuntimeError("credential-bearing environment forbidden")
        task=validate_invocation(inv); node=find_node(); c=load_config(); server=Path(__file__).resolve().parents[1]/"scripts/serve_sv002_observation_intr_runtime.py"; result=ensure_receiver(c,server)
        result.update({"task_id":TASK_ID,"worker_id":WORKER_ID,"claim_id":task.get("claim_id"),"fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),"node_declaration_ref":str(node),"credential_authority":"TV/TVC","authority_effect":"NONE"})
        if result.get("state")=="COMPLETE": print(json.dumps(response("COMPLETED","SV002_PUBLIC_OBSERVATION_ROUND_TRIP_OBSERVED",evidence_refs=[result.get("receipt_bundle_ref")],result=result),sort_keys=True)); return 0
        print(json.dumps(response("ACTIVE","SV002_PUBLIC_OBSERVATION_RECEIVER_READY",evidence_refs=[str(paths(c)[2])],result=result),sort_keys=True)); return 0
    except RoutePending as exc:
        print(json.dumps(response("HANDOFF_READY","SV002_PUBLIC_OBSERVATION_ROUTE_PENDING",blocker={"dependency_class":"SOVEREIGN_ROUTE_RUNTIME","problem_statement":str(exc),"solution_required":True,"may_remain_blocked":False,"physical_additional_machine_required":False,"third_party_runtime_required":False,"github_token_required":False,"human_action_required":False}),sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps(response("BLOCKED","SV002_PUBLIC_OBSERVATION_RUNTIME_BLOCKED",error=str(exc)),sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
