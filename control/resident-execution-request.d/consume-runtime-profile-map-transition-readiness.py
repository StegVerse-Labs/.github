#!/usr/bin/env python3
"""Consume post-reconciliation transition-readiness request without granting authority."""
from __future__ import annotations
import argparse, hashlib, json, shutil, sys
from pathlib import Path
from typing import Any

REQUEST_REL=Path("control/resident-execution-request.d/runtime-profile-map-transition-readiness-001.json")
RECON_CONSUMPTION_REL=Path("receipts/sovereign-host/runtime-profile-map-reconciliation-request-consumption.latest.json")
REGISTRY_REL=Path("data/canonical-task-registry.json")
WORKER_REL=Path("control/worker-registry.json")
READY_DIR=Path("receipts/runtime-profile-map/routing-readiness")
RECON_DIR=Path("receipts/runtime-profile-map/reconciliation/tasks")
OUT_DIR=Path("receipts/runtime-profile-map/transition-readiness")
CONSUMPTION_REL=Path("receipts/sovereign-host/runtime-profile-map-transition-readiness-request-consumption.latest.json")
EVALUATOR_REL=Path("scripts/evaluate_runtime_profile_map_transition_readiness.py")
TARGET="STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001"
MODE="RUNTIME_PROFILE_MAP_TRANSITION_READINESS"
ENTRY="control/resident-execution-request.d/consume-runtime-profile-map-transition-readiness.py"

def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text());
    if not isinstance(v,dict): raise RuntimeError(f"object required:{p}")
    return v

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p:Path,v:dict[str,Any]):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_name('.'+p.name+'.tmp'); t.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n'); t.replace(p)
def require(x:bool,m:str):
    if not x: raise RuntimeError(m)
def validate(r:dict[str,Any]):
    e={"schema":"stegverse.resident-execution-request/v1","state":"REQUESTED","task_id":TARGET,"mode":MODE,"entrypoint":ENTRY,"credential_authority":"TV/TVC","github_token_required":False,"github_token_runtime_authority":"NONE","heartbeat_grants_execution_authority":False,"oscillator_grants_execution_authority":False,"second_machine_required":False,"network_source_fetch_allowed":False,"request_granted_authority":False,"authority_effect":"NONE_REQUEST_ONLY"}
    for k,w in e.items(): require(r.get(k)==w,f"transition readiness request {k} mismatch")

def consume(source:Path,runtime:Path)->dict[str,Any]:
    reqp=runtime/REQUEST_REL
    if not reqp.is_file(): return {"schema":"stegverse.runtime-profile-map-transition-readiness-consumption/v1","state":"NO_REQUEST","authority_effect":"NONE"}
    req=load(reqp); validate(req)
    reconp=runtime/RECON_CONSUMPTION_REL
    if not reconp.is_file() or load(reconp).get("state")!="COMPLETED": return {"schema":"stegverse.runtime-profile-map-transition-readiness-consumption/v1","state":"WAITING_FOR_RECONCILIATION","task_id":TARGET,"authority_effect":"NONE_WAIT_ONLY"}
    evsrc=source/EVALUATOR_REL; evdst=runtime/EVALUATOR_REL; require(evsrc.is_file(),"transition evaluator source missing"); evdst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(evsrc,evdst); require(sha(evsrc)==sha(evdst),"transition evaluator copy mismatch")
    registry=load(runtime/REGISTRY_REL); tasks=[t for t in registry.get("tasks",[]) if isinstance(t.get("runtime_requirements"),dict)]
    rows=[]
    for task in tasks:
        tid=task.get("task_id"); ready=runtime/READY_DIR/f"{tid}.json"; recon=runtime/RECON_DIR/f"{tid}.json"; require(ready.is_file() and recon.is_file(),f"required transition inputs missing:{tid}")
        out=runtime/OUT_DIR/f"{tid}.json"; out.parent.mkdir(parents=True,exist_ok=True)
        import subprocess
        c=subprocess.run([sys.executable,str(evdst),tid,"--registry",str(runtime/REGISTRY_REL),"--worker-registry",str(runtime/WORKER_REL),"--routing-readiness",str(ready),"--reconciliation",str(recon),"--output",str(out)],cwd=runtime,capture_output=True,text=True,check=False,timeout=1200)
        rows.append({"task_id":tid,"returncode":c.returncode,"receipt_ref":str(out),"receipt_sha256":sha(out) if out.is_file() else None,"disposition":load(out).get("disposition") if out.is_file() else None})
    ok=bool(rows) and all(r["returncode"]==0 and r["receipt_sha256"] for r in rows)
    receipt={"schema":"stegverse.runtime-profile-map-transition-readiness-consumption/v1","state":"COMPLETED" if ok else "ATTEMPT_RECORDED","task_id":TARGET,"request_id":req.get("request_id"),"reconciliation_consumption_ref":str(reconp),"task_transition_readiness":rows,"task_transition_readiness_count":len(rows),"task_state_changed":False,"claim_or_fence_minted":False,"execution_authority_granted":False,"interlock_intr_admission_granted":False,"heartbeat_or_oscillator_advanced":False,"authority_effect":"NONE_TRANSITION_READINESS_ONLY"}
    atomic(runtime/CONSUMPTION_REL,receipt); return receipt

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--source-root",type=Path,required=True); p.add_argument("--runtime-root",type=Path,required=True); a=p.parse_args(); r=consume(a.source_root.resolve(),a.runtime_root.resolve()); print(json.dumps(r,sort_keys=True)); return 0 if r.get("state") in {"NO_REQUEST","WAITING_FOR_RECONCILIATION","COMPLETED","ATTEMPT_RECORDED"} else 1
if __name__=="__main__": raise SystemExit(main())
