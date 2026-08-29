#!/usr/bin/env python3
"""Fenced launcher for the evaluator READ_REVIEW Universal InTr runtime."""
from __future__ import annotations
import json, os, ssl, subprocess, sys, time, urllib.request
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

def _service_paths(c: Mapping[str,Any])->tuple[Path,Path,Path]:
    root=Path(str(c["runtime_root"])).expanduser().resolve()/ "receipts" / "sovereign-network" / "evaluator-intr"
    return root/"receiver.pid", root/"receiver.log", root/"receiver.latest.json"

def _pid_alive(pid:int)->bool:
    if pid <= 1: return False
    try:
        os.kill(pid,0); return True
    except OSError:
        return False

def _read_pid(path:Path)->int|None:
    try:
        value=int(path.read_text(encoding="utf-8").strip())
        return value if _pid_alive(value) else None
    except Exception:
        return None

def _round_trip_bundle(c: Mapping[str,Any])->dict[str,Any]|None:
    root=Path(str(c["runtime_root"])).expanduser().resolve()/ "receipts" / "sovereign-network" / "evaluator-intr"
    if not root.is_dir(): return None
    for path in sorted(root.glob("*.json")):
        if path.name=="receiver.latest.json": continue
        try: value=json.loads(path.read_text(encoding="utf-8"))
        except Exception: continue
        if isinstance(value,dict) and value.get("state")=="READ_REVIEW_ROUND_TRIP_FORWARDED":
            return {"path":str(path),"value":value}
    return None

def _readiness(c: Mapping[str,Any])->dict[str,Any]:
    host=str(c["host"]); port=int(c["port"])
    tls=host not in {"127.0.0.1","::1","localhost"}
    scheme="https" if tls else "http"
    context=ssl._create_unverified_context() if tls else None
    with urllib.request.urlopen(f"{scheme}://127.0.0.1:{port}/intr/evaluator/readiness",timeout=2,context=context) as response:
        value=json.loads(response.read().decode("utf-8"))
    if response.status != 200 or value.get("state")!="READY" or value.get("transport")!="InTr":
        raise RoutePending("evaluator receiver readiness not observed")
    if value.get("credential_authority")!="TV/TVC" or value.get("github_token_runtime_authority")!="NONE":
        raise RuntimeError("evaluator receiver readiness authority drift")
    return value

def ensure_receiver(c: Mapping[str,Any], server:Path)->dict[str,Any]:
    observed=_round_trip_bundle(c)
    if observed is not None:
        return {
            "schema":"stegverse.evaluator-intr-runtime-worker-completion/v2",
            "state":"COMPLETE",
            "transition_id":"EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED",
            "receipt_bundle_ref":observed["path"],
            "credential_authority":"TV/TVC",
            "github_token_used":False,
            "authority_effect":"NONE",
        }

    pid_file,log_file,ready_file=_service_paths(c)
    pid_file.parent.mkdir(parents=True,exist_ok=True)
    pid=_read_pid(pid_file)
    if pid is None:
        cmd=[sys.executable,str(server),"--site-root",str(c["site_root"]),"--stegos-root",str(c["stegos_root"]),"--runtime-root",str(c["runtime_root"]),"--host",str(c["host"]),"--port",str(c["port"]),"--max-requests","0","--allowed-origin",str(c["allowed_origin"]),"--boundary-identity-ref",str(c["boundary_identity_ref"])]
        if c.get("tls_cert"): cmd += ["--tls-cert",str(c["tls_cert"])]
        if c.get("tls_key"): cmd += ["--tls-key",str(c["tls_key"])]
        log=log_file.open("ab",buffering=0)
        proc=subprocess.Popen(cmd,cwd=server.parent.parent,env={"PATH":os.getenv("PATH",""),"HOME":os.getenv("HOME",""),"STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY":"TV/TVC","STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY":"NONE"},stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
        pid=proc.pid
        pid_file.write_text(str(pid)+"\n",encoding="utf-8")

    readiness=None
    last=None
    for _ in range(40):
        if not _pid_alive(pid):
            raise RuntimeError("evaluator receiver exited before readiness")
        try:
            readiness=_readiness(c); break
        except Exception as exc:
            last=exc; time.sleep(0.1)
    if readiness is None:
        raise RoutePending("evaluator receiver readiness unavailable: "+type(last).__name__)

    receipt={
        "schema":"stegverse.evaluator-intr-resident-receiver-readiness/v1",
        "state":"READY",
        "transition_id":"EVALUATOR_INTR_RECEIVER_READY",
        "pid":pid,
        "host":c["host"],
        "port":c["port"],
        "readiness":readiness,
        "persistent_receiver":True,
        "round_trip_observed":False,
        "credential_authority":"TV/TVC",
        "github_token_runtime_authority":"NONE",
        "public_tls_terminated_by":c.get("public_tls_terminated_by"),
        "authority_effect":"NONE",
    }
    ready_file.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt

def execute(inv: Mapping[str,Any])->dict[str,Any]:
    if any(truthy(os.getenv(k)) for k in HOSTED_ENV): raise RuntimeError("hosted runtime forbidden")
    present=[k for k in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(k))]
    if present: raise RuntimeError("credential-bearing environment forbidden: "+",".join(present))
    task=validate_invocation(inv)
    node_path,_=find_node()
    config=load_config()
    server=Path(__file__).resolve().parents[1]/"scripts/serve_evaluator_intr_runtime.py"
    result=ensure_receiver(config,server)
    result["task_id"]=TASK_ID
    result["worker_id"]=WORKER_ID
    result["claim_id"]=task.get("claim_id")
    result["fencing_token"]=(task.get("heartbeat_timing") or {}).get("fencing_token")
    result["node_declaration_ref"]=str(node_path)
    return result

def response(state,transition,**extra):
    base={"schema":"stegverse.worker-response/v0.1","state":state,"transition_id":transition,"transition_sequence":1,"credential_authority":"TV/TVC","github_token_used":False,"repository_writeback_performed":False}
    base.update(extra); return base

def main():
    try:
        inv=json.loads(sys.stdin.readline())
        result=execute(inv)
        if result.get("state")=="COMPLETE":
            print(json.dumps(response("COMPLETED","EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED",evidence_refs=[result.get("receipt_bundle_ref")],result=result),sort_keys=True)); return 0
        print(json.dumps(response("ACTIVE","EVALUATOR_INTR_RECEIVER_READY",evidence_refs=[str(Path(str(load_config()["runtime_root"]))/ "receipts" / "sovereign-network" / "evaluator-intr" / "receiver.latest.json")],result=result),sort_keys=True)); return 0
    except RoutePending as exc:
        print(json.dumps(response("HANDOFF_READY","EVALUATOR_INTR_ROUTE_PENDING",blocker={"dependency_class":"SOVEREIGN_ROUTE_RUNTIME","problem_statement":str(exc),"solution_required":True,"may_remain_blocked":False,"machine_observable_release_condition":"declared node + local Site/StegOS roots + admitted evaluator route configuration/TLS identity exist","physical_additional_machine_required":False,"third_party_runtime_required":False,"github_token_required":False,"non_tv_tvc_secret_or_token_required":False,"human_action_required":False}),sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps(response("BLOCKED","EVALUATOR_INTR_RUNTIME_BLOCKED",error=str(exc)),sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
