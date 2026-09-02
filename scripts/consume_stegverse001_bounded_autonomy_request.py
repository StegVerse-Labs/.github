#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from typing import Any, Callable

REQUEST_REL=Path("control/resident-execution-request.d/stegverse001-bounded-autonomy-runtime-001.json")
RECEIPT_REL=Path("receipts/sovereign-host/stegverse001-bounded-autonomy-request-consumption.latest.json")
TASK_ID="SHWP-STEGVERSE001-BOUNDED-AUTONOMY-RUNTIME-001"
Runner=Callable[...,subprocess.CompletedProcess[str]]

def stable(v:Any)->str: return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise RuntimeError("expected JSON object")
    return v
def parse_last_json(s:str):
    for line in reversed([x.strip() for x in s.splitlines() if x.strip()]):
        try: v=json.loads(line)
        except Exception: continue
        if isinstance(v,dict): return v
    return None
def terminal(v:Any)->bool:
    if isinstance(v,list): return any(terminal(x) for x in v)
    if not isinstance(v,dict): return False
    if v.get("state")=="COMPLETED" and v.get("transition_id")=="SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED": return True
    return any(terminal(x) for x in v.values() if isinstance(x,(dict,list)))

def consume(source_root:Path,runtime_root:Path,runner:Runner=subprocess.run)->dict[str,Any]:
    source=source_root.resolve(); runtime=runtime_root.resolve(); rp=runtime/REQUEST_REL
    if not rp.is_file(): return {"schema":"stegverse.resident-execution-request-consumption/v1","state":"NO_REQUEST","runtime_execution_attempted":False,"authority_effect":"NONE"}
    req=load(rp)
    if req.get("schema")!="stegverse.resident-execution-request/v1" or req.get("task_id")!=TASK_ID or req.get("state")!="REQUESTED":
        raise RuntimeError("SV001 autonomy resident request contract mismatch")
    rh=stable(req); receipt_path=runtime/RECEIPT_REL
    if receipt_path.is_file():
        old=load(receipt_path)
        if old.get("request_sha256")==rh and old.get("terminal_execution_observed") is True:
            return {"schema":"stegverse.resident-execution-request-consumption/v1","state":"ALREADY_CONSUMED",
                    "request_id":req.get("request_id"),"request_sha256":rh,"task_id":TASK_ID,
                    "runtime_execution_attempted":False,"terminal_execution_observed":True,
                    "request_granted_authority":False,"authority_effect":"NONE_REQUEST_ONLY"}
    cmd=[sys.executable,str(runtime/"scripts/refresh_and_execute_resident_task.py"),"--source-root",str(source),"--runtime-root",str(runtime),"--task-id",TASK_ID]
    c=runner(cmd,cwd=runtime,capture_output=True,text=True,check=False,timeout=600)
    result=parse_last_json(c.stdout); done=terminal(result)
    out={"schema":"stegverse.resident-execution-request-consumption/v1","state":"COMPLETED" if done else "ATTEMPT_RECORDED",
         "request_id":req.get("request_id"),"request_sha256":rh,"task_id":TASK_ID,
         "runtime_execution_attempted":True,"execution_returncode":c.returncode,"execution_result":result,
         "terminal_execution_observed":done,"retry_allowed":not done,"exactly_once_after_terminal":True,
         "request_granted_authority":False,"network_source_fetch_performed":False,"second_machine_required":False,
         "authority_effect":"NONE_REQUEST_ONLY"}
    receipt_path.parent.mkdir(parents=True,exist_ok=True); receipt_path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    return out

def main():
    p=argparse.ArgumentParser(); p.add_argument("--source-root",type=Path,required=True); p.add_argument("--runtime-root",type=Path,required=True); a=p.parse_args()
    try: out=consume(a.source_root,a.runtime_root)
    except Exception as exc:
        print(json.dumps({"schema":"stegverse.resident-execution-request-consumption/v1","state":"BLOCKED","reason":str(exc),"runtime_execution_attempted":False,"authority_effect":"NONE"},sort_keys=True)); return 2
    print(json.dumps(out,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
