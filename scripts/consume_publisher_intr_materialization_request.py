#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,subprocess,sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
TASK_ID="SHWP-PUBLISHER-ARTIFACT-TRANSFER-001"
EVENT_ENV="STEGVERSE_PUBLISHER_INTR_MATERIALIZATION_ID"

def load(path:Path)->dict[str,Any]:
    v=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise ValueError("object required")
    return v

def scrub(env=None):
    source=dict(os.environ if env is None else env)
    keep=("PATH","HOME","LANG","LC_ALL","XDG_STATE_HOME","XDG_CONFIG_HOME","LOCALAPPDATA","STEGVERSE_HEARTBEAT_ROOT","STEGVERSE_HEARTBEAT_SOURCE_ROOT","STEGVERSE_STEGOS_ROOT","STEGVERSE_PUBLISHER_ROOT")
    out={k:source[k] for k in keep if source.get(k)}
    out["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"; out["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    return out

def consume(source:Path,runtime:Path,mid:str,runner=subprocess.run,env=None)->dict[str,Any]:
    req=load(runtime/"intr-materialization"/f"{mid}.json"); ing=load(runtime/"receipts/sovereign-network/publisher-intr-ingress"/f"{mid}.json")
    if req.get("destination")!={"boundary":"STEGOS_ECOSYSTEM","subsystem":"Publisher:Ingress"} or req.get("downstream_owner_ref")!="GCAT-BCAT-Engine/Publisher": raise ValueError("not publisher materialization")
    if ing.get("state")!="INGRESS_ADMITTED" or ing.get("exact_payload_materialized") is not True: raise ValueError("publisher ingress not ready")
    child=scrub(env); child[EVENT_ENV]=mid
    cmd=[sys.executable,str(runtime/"scripts/refresh_and_execute_resident_task.py"),"--source-root",str(source),"--runtime-root",str(runtime),"--task-id",TASK_ID]
    cp=runner(cmd,cwd=runtime,env=child,check=False,capture_output=True,text=True,timeout=300)
    worker=load(runtime/"receipts/publisher-artifact-transfer"/f"{TASK_ID}.json") if (runtime/"receipts/publisher-artifact-transfer"/f"{TASK_ID}.json").is_file() else {}
    result={"schema":"stegverse.publisher-intr-materialization-consumption/v1","state":"RETURN_STAGED_TO_DEVICE" if cp.returncode==0 and worker.get("state")=="RETURN_STAGED_TO_DEVICE" else "MATERIALIZATION_EXECUTION_BLOCKED","materialization_id":mid,"request_hash":req.get("request_hash"),"target_task_id":TASK_ID,"targeted_executor_returncode":cp.returncode,"runtime_execution_attempted":True,"return_meta_ref":worker.get("return_meta_ref"),"request_grants_authority":False,"claim_or_fence_minted_by_consumer":False,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_effect":"NONE_REQUEST_ONLY"}
    p=runtime/"receipts/sovereign-host/publisher-intr-materialization-consumption.latest.json"; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--source-root",type=Path,default=ROOT); p.add_argument("--runtime-root",type=Path,required=True); p.add_argument("--materialization-id",required=True); a=p.parse_args()
    r=consume(a.source_root.resolve(),a.runtime_root.resolve(),a.materialization_id); print(json.dumps(r,sort_keys=True)); return 0 if r["state"]=="RETURN_STAGED_TO_DEVICE" else 1
if __name__=="__main__": raise SystemExit(main())
