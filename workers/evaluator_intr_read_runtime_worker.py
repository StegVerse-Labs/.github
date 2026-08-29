#!/usr/bin/env python3
"""Fenced launcher for the evaluator READ_REVIEW Universal InTr runtime."""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
from typing import Any, Mapping

TASK_ID="SHWP-EVALUATOR-INTR-READ-RUNTIME-001"
WORKER_ID="evaluator-intr-read-runtime-worker"
CONFIG_ENV="STEGVERSE_EVALUATOR_INTR_ROUTE_CONFIG"
DEFAULT_CONFIG=Path.home()/".stegverse/config/evaluator-intr-runtime.json"
NODE_MARKERS=(Path("/etc/stegverse/node.json"),Path.home()/".stegverse/node.json")
HOSTED_ENV=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN_CREDENTIAL_ENV=("GITHUB_TOKEN","GH_TOKEN","STEGVERSE_GITHUB_TOKEN","ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN")

class RoutePending(RuntimeError): pass

def truthy(v): return str(v or "").strip().lower() not in {"","0","false","no"}

def validate_invocation(inv: Mapping[str,Any])->dict[str,Any]:
    if inv.get("schema")!="stegverse.worker-invocation/v0.1": raise RuntimeError("unexpected invocation schema")
    task=inv.get("task") or {}
    if task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID: raise RuntimeError("task/worker identity mismatch")
    if not task.get("claim_id"): raise RuntimeError("canonical scheduler claim required")
    if not isinstance((task.get("heartbeat_timing") or {}).get("fencing_token"),int): raise RuntimeError("fresh fencing token required")
    auth=(inv.get("handoff") or {}).get("authority") or {}
    if auth.get("credential_authority")!="TV/TVC": raise RuntimeError("credential authority drift")
    if auth.get("github_token_required") is not False or auth.get("non_tv_tvc_secret_or_token_allowed") is not False: raise RuntimeError("credential boundary drift")
    if auth.get("heartbeat_grants_execution_authority") is not False: raise RuntimeError("heartbeat authority drift")
    return dict(task)

def find_node()->tuple[Path,dict[str,Any]]:
    for p in NODE_MARKERS:
        if p.is_file():
            v=json.loads(p.read_text())
            if v.get("declared") is not True: raise RoutePending("sovereign node is not declared")
            if v.get("credential_authority")!="TV/TVC": raise RuntimeError("node credential authority drift")
            if v.get("github_token_required") is not False: raise RuntimeError("node requires GitHub token")
            return p,v
    raise RoutePending("no declared sovereign StegVerse node marker")

def config_path()->Path:
    raw=str(os.getenv(CONFIG_ENV) or "").strip()
    return Path(raw).expanduser().resolve() if raw else DEFAULT_CONFIG.expanduser().resolve()

def load_config()->dict[str,Any]:
    p=config_path()
    if not p.is_file(): raise RoutePending(f"evaluator InTr route config not present: {p}")
    c=json.loads(p.read_text())
    required=("site_root","stegos_root","runtime_root","host","port","allowed_origin","boundary_identity_ref")
    for k in required:
        if c.get(k) in (None,""): raise RoutePending(f"route config missing {k}")
    if c.get("credential_authority")!="TV/TVC" or c.get("github_token_runtime_authority")!="NONE": raise RuntimeError("route authority drift")
    host=str(c["host"])
    if host not in {"127.0.0.1","::1","localhost"}:
        for k in ("tls_cert","tls_key"):
            if not c.get(k): raise RoutePending(f"public evaluator route requires {k}")
            if not Path(str(c[k])).expanduser().is_file(): raise RoutePending(f"public evaluator route {k} not materialized")
    for k in ("site_root","stegos_root","runtime_root"):
        if not Path(str(c[k])).expanduser().is_dir(): raise RoutePending(f"local source/runtime root unavailable: {k}")
    return c

def execute(inv: Mapping[str,Any])->dict[str,Any]:
    if any(truthy(os.getenv(k)) for k in HOSTED_ENV): raise RuntimeError("hosted runtime forbidden")
    present=[k for k in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(k))]
    if present: raise RuntimeError("credential-bearing environment forbidden: "+",".join(present))
    task=validate_invocation(inv)
    node_path,_=find_node()
    c=load_config()
    server=Path(__file__).resolve().parents[1]/"scripts/serve_evaluator_intr_runtime.py"
    cmd=[sys.executable,str(server),"--site-root",str(c["site_root"]),"--stegos-root",str(c["stegos_root"]),"--runtime-root",str(c["runtime_root"]),"--host",str(c["host"]),"--port",str(c["port"]),"--max-requests","1","--allowed-origin",str(c["allowed_origin"]),"--boundary-identity-ref",str(c["boundary_identity_ref"])]
    if c.get("tls_cert"): cmd += ["--tls-cert",str(c["tls_cert"])]
    if c.get("tls_key"): cmd += ["--tls-key",str(c["tls_key"])]
    timeout=int(c.get("window_seconds",300))
    try:
        completed=subprocess.run(cmd,cwd=server.parent.parent,env={"PATH":os.getenv("PATH",""),"HOME":os.getenv("HOME",""),"STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY":"TV/TVC","STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY":"NONE"},capture_output=True,text=True,check=False,timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RoutePending("bounded evaluator listener window elapsed without admitted browser request")
    if completed.returncode!=0: raise RuntimeError("evaluator listener failed: "+completed.stderr[-1000:])
    return {"schema":"stegverse.evaluator-intr-runtime-worker-completion/v1","state":"COMPLETE","transition_id":"EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED","task_id":TASK_ID,"worker_id":WORKER_ID,"claim_id":task.get("claim_id"),"fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),"node_declaration_ref":str(node_path),"route_host":c["host"],"route_port":c["port"],"credential_authority":"TV/TVC","github_token_used":False,"authority_effect":"NONE"}

def response(state,transition,**extra):
    base={"schema":"stegverse.worker-response/v0.1","state":state,"transition_id":transition,"transition_sequence":1,"credential_authority":"TV/TVC","github_token_used":False,"repository_writeback_performed":False}
    base.update(extra); return base

def main():
    try:
        inv=json.loads(sys.stdin.readline())
        result=execute(inv)
        print(json.dumps(response("COMPLETED","EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED",evidence_refs=["receipts/sovereign-network/evaluator-intr/**"],result=result),sort_keys=True)); return 0
    except RoutePending as exc:
        print(json.dumps(response("HANDOFF_READY","EVALUATOR_INTR_ROUTE_PENDING",blocker={"dependency_class":"SOVEREIGN_ROUTE_RUNTIME","problem_statement":str(exc),"solution_required":True,"may_remain_blocked":False,"machine_observable_release_condition":"declared node + local Site/StegOS roots + admitted evaluator route configuration/TLS identity exist","physical_additional_machine_required":False,"third_party_runtime_required":False,"github_token_required":False,"non_tv_tvc_secret_or_token_required":False,"human_action_required":False}),sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps(response("BLOCKED","EVALUATOR_INTR_RUNTIME_BLOCKED",error=str(exc)),sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
