#!/usr/bin/env python3
"""Fenced launcher for the StegVerse-002 public observation InTr receiver."""
from __future__ import annotations
import json, os, ssl, subprocess, sys, time, urllib.request
from pathlib import Path
from typing import Any, Mapping

TASK_ID="SHWP-SV002-PUBLIC-OBSERVATION-001"
WORKER_ID="sv002-public-observation-worker"
CONFIG_ENV="STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG"
DEFAULT_CONFIG=Path.home()/".stegverse/config/sv002-public-observe-runtime.json"
NODE_MARKERS=(Path("/etc/stegverse/node.json"),Path.home()/".stegverse/node.json")
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
CREDS=("GITHUB_TOKEN","GH_TOKEN","STEGVERSE_GITHUB_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN")
class Pending(RuntimeError): pass
def truthy(v): return str(v or "").strip().lower() not in {"","0","false","no"}
def validate_invocation(inv:Mapping[str,Any]):
    if inv.get("schema")!="stegverse.worker-invocation/v0.1": raise RuntimeError("unexpected invocation schema")
    task=inv.get("task") or {}
    if task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID: raise RuntimeError("task/worker identity mismatch")
    if not task.get("claim_id"): raise RuntimeError("scheduler claim required")
    if not isinstance((task.get("heartbeat_timing") or {}).get("fencing_token"),int): raise RuntimeError("fresh fencing token required")
    auth=(inv.get("handoff") or {}).get("authority") or {}
    if auth.get("credential_authority")!="TV/TVC" or auth.get("github_token_required") is not False or auth.get("non_tv_tvc_secret_or_token_allowed") is not False: raise RuntimeError("authority drift")
    if auth.get("heartbeat_grants_execution_authority") is not False: raise RuntimeError("heartbeat authority drift")
    return task
def find_node():
    for p in NODE_MARKERS:
        if p.is_file():
            v=json.loads(p.read_text())
            if v.get("declared") is not True: raise Pending("sovereign node is not declared")
            if v.get("credential_authority")!="TV/TVC": raise RuntimeError("node credential authority drift")
            return p
    raise Pending("no declared sovereign StegVerse node marker")
def load_config():
    p=Path(os.getenv(CONFIG_ENV,"") or DEFAULT_CONFIG).expanduser().resolve()
    if not p.is_file(): raise Pending("SV002 observation route config unavailable")
    c=json.loads(p.read_text())
    for k in ("stegos_root","runtime_root","host","port","allowed_origin","boundary_identity_ref"):
        if c.get(k) in (None,""): raise Pending("route config missing "+k)
    if c.get("credential_authority")!="TV/TVC" or c.get("github_token_runtime_authority")!="NONE": raise RuntimeError("route authority drift")
    if not Path(c["stegos_root"]).expanduser().is_dir() or not Path(c["runtime_root"]).expanduser().is_dir(): raise Pending("local route roots unavailable")
    return c
def paths(c):
    root=Path(c["runtime_root"]).expanduser().resolve()/"receipts/sovereign-network/sv002-public-observe"
    return root/"receiver.pid",root/"receiver.log",root/"receiver.latest.json"
def alive(pid):
    try: os.kill(pid,0); return pid>1
    except OSError: return False
def read_pid(p):
    try:
        v=int(p.read_text().strip()); return v if alive(v) else None
    except Exception: return None
def completion(c):
    root=Path(c["runtime_root"]).expanduser().resolve()/"receipts/sovereign-network/sv002-public-observe"
    if not root.is_dir(): return None
    for p in sorted(root.glob("SV002-OBS-IN-*.json")):
        try: v=json.loads(p.read_text())
        except Exception: continue
        if v.get("state")=="SV002_PUBLIC_OBSERVATION_FORWARDED": return str(p)
    return None
def readiness(c):
    host=str(c["host"]); port=int(c["port"]); tls=host not in {"127.0.0.1","::1","localhost"}
    ctx=ssl._create_unverified_context() if tls else None
    with urllib.request.urlopen(("https" if tls else "http")+f"://127.0.0.1:{port}/intr/sv002-observe/readiness",timeout=2,context=ctx) as r:
        v=json.loads(r.read().decode())
    if r.status!=200 or v.get("state")!="READY" or v.get("transport")!="InTr": raise Pending("receiver readiness not observed")
    return v
def ensure(c,server):
    done=completion(c)
    if done:
        return {"schema":"stegverse.sv002-public-observation-worker-completion/v1","state":"COMPLETE","transition_id":"SV002_PUBLIC_OBSERVATION_ROUND_TRIP_OBSERVED","receipt_bundle_ref":done,"authority_effect":"NONE","credential_authority":"TV/TVC","github_token_used":False}
    pidf,logf,readyf=paths(c); pidf.parent.mkdir(parents=True,exist_ok=True); pid=read_pid(pidf)
    if pid is None:
        cmd=[sys.executable,str(server),"--stegos-root",str(c["stegos_root"]),"--runtime-root",str(c["runtime_root"]),"--host",str(c["host"]),"--port",str(c["port"]),"--max-requests","0","--allowed-origin",str(c["allowed_origin"]),"--boundary-identity-ref",str(c["boundary_identity_ref"])]
        if c.get("tls_cert"): cmd+=["--tls-cert",str(c["tls_cert"])]
        if c.get("tls_key"): cmd+=["--tls-key",str(c["tls_key"])]
        log=logf.open("ab",buffering=0)
        proc=subprocess.Popen(cmd,cwd=server.parent.parent,env={"PATH":os.getenv("PATH",""),"HOME":os.getenv("HOME",""),"STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY":"TV/TVC","STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY":"NONE"},stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
        pid=proc.pid; pidf.write_text(str(pid)+"\n")
    ready=None
    for _ in range(40):
        if not alive(pid): raise RuntimeError("SV002 observation receiver exited before readiness")
        try: ready=readiness(c); break
        except Exception: time.sleep(.1)
    if ready is None: raise Pending("SV002 observation receiver readiness unavailable")
    receipt={"schema":"stegverse.sv002-public-observation-receiver-readiness/v1","state":"READY","transition_id":"SV002_PUBLIC_OBSERVATION_RECEIVER_READY","pid":pid,"host":c["host"],"port":c["port"],"readiness":ready,"persistent_receiver":True,"round_trip_observed":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_effect":"NONE"}
    readyf.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n"); return receipt
def response(state,transition,**extra):
    v={"schema":"stegverse.worker-response/v0.1","state":state,"transition_id":transition,"transition_sequence":1,"credential_authority":"TV/TVC","github_token_used":False,"repository_writeback_performed":False}; v.update(extra); return v
def main():
    try:
        inv=json.loads(sys.stdin.readline())
        if any(truthy(os.getenv(k)) for k in HOSTED): raise RuntimeError("hosted runtime forbidden")
        if any(truthy(os.getenv(k)) for k in CREDS): raise RuntimeError("credential-bearing environment forbidden")
        task=validate_invocation(inv); node=find_node(); c=load_config(); server=Path(__file__).resolve().parents[1]/"scripts/serve_sv002_public_observation_runtime.py"; result=ensure(c,server)
        result.update({"task_id":TASK_ID,"worker_id":WORKER_ID,"claim_id":task.get("claim_id"),"fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),"node_declaration_ref":str(node)})
        if result["state"]=="COMPLETE": print(json.dumps(response("COMPLETED","SV002_PUBLIC_OBSERVATION_ROUND_TRIP_OBSERVED",evidence_refs=[result["receipt_bundle_ref"]],result=result),sort_keys=True))
        else: print(json.dumps(response("ACTIVE","SV002_PUBLIC_OBSERVATION_RECEIVER_READY",evidence_refs=[str(paths(c)[2])],result=result),sort_keys=True))
        return 0
    except Pending as exc:
        print(json.dumps(response("HANDOFF_READY","SV002_PUBLIC_OBSERVATION_ROUTE_PENDING",blocker={"dependency_class":"SOVEREIGN_ROUTE_RUNTIME","problem_statement":str(exc),"solution_required":True,"may_remain_blocked":False,"machine_observable_release_condition":"declared node + local StegOS root + admitted observation route config exist","physical_additional_machine_required":False,"third_party_runtime_required":False,"github_token_required":False,"human_action_required":False}),sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps(response("BLOCKED","SV002_PUBLIC_OBSERVATION_RUNTIME_BLOCKED",error=str(exc)),sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
