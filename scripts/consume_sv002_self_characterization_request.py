#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

REQUEST_REL=Path("control/resident-execution-request.d/sv002-self-characterization-001.json")
RECEIPT_REL=Path("receipts/sovereign-host/sv002-self-characterization-request-consumption.latest.json")
TASK_ID="SHWP-SV002-SELF-CHARACTERIZATION-001"

def stable(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def load(p): return json.loads(p.read_text())
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--source-root",type=Path,required=True); ap.add_argument("--runtime-root",type=Path,required=True); a=ap.parse_args()
    source=a.source_root.resolve(); runtime=a.runtime_root.resolve(); rp=runtime/REQUEST_REL
    if not rp.is_file():
        print(json.dumps({"state":"NO_REQUEST","runtime_execution_attempted":False,"authority_effect":"NONE"})); return 0
    req=load(rp)
    if req.get("schema")!="stegverse.resident-execution-request/v1" or req.get("task_id")!=TASK_ID or req.get("state")!="REQUESTED": return 2
    h=stable(req); prior=runtime/RECEIPT_REL
    if prior.is_file():
        try: p=load(prior)
        except Exception: p={}
        if p.get("request_sha256")==h and p.get("runtime_execution_attempted") is True:
            print(json.dumps({"state":"ALREADY_CONSUMED","request_sha256":h,"runtime_execution_attempted":False,"authority_effect":"NONE"})); return 0
    cmd=[sys.executable,str(runtime/"scripts/refresh_and_execute_resident_task.py"),"--source-root",str(source),"--runtime-root",str(runtime),"--task-id",TASK_ID]
    cp=subprocess.run(cmd,cwd=runtime,capture_output=True,text=True,check=False,timeout=2000)
    result=None
    for line in reversed([x.strip() for x in cp.stdout.splitlines() if x.strip()]):
        try:
            q=json.loads(line)
            if isinstance(q,dict): result=q; break
        except Exception: pass
    rec={"schema":"stegverse.resident-execution-request-consumption/v1","state":"ATTEMPT_RECORDED","request_id":req.get("request_id"),"request_sha256":h,"task_id":TASK_ID,"runtime_execution_attempted":True,"execution_returncode":cp.returncode,"execution_result":result,"request_granted_authority":False,"network_source_fetch_performed":False,"second_machine_required":False,"authority_effect":"NONE_REQUEST_ONLY"}
    prior.parent.mkdir(parents=True,exist_ok=True); prior.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
