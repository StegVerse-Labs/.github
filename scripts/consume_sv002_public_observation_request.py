#!/usr/bin/env python3
"""Consume StegVerse-002 public observation resident request through targeted task control."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
REQUEST_REL=Path("control/resident-execution-request.d/sv002-public-observation-runtime-001.json")
CONSUMPTION_REL=Path("receipts/sovereign-host/sv002-public-observation-request-consumption.latest.json")
TARGET_TASK="SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001"
TARGET_MODE="TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT="scripts/refresh_and_execute_resident_task.py"
MATERIALIZER="scripts/materialize_sv002_observation_route_config.py"
NONSECRET_ENV={
 "PATH","HOME","LANG","LC_ALL","XDG_STATE_HOME","XDG_CONFIG_HOME","LOCALAPPDATA",
 "STEGVERSE_SOVEREIGN_NODE","STEGVERSE_HEARTBEAT_ROOT","STEGVERSE_HEARTBEAT_SOURCE_ROOT",
 "STEGVERSE_STEGOS_ROOT","STEGVERSE_MICRO_NODE_RUNTIME_ROOT","STEGVERSE_REPO_ROOTS_JSON",
 "STEGVERSE_SV002_OBSERVE_ROUTE_CONFIG","STEGVERSE_SV002_OBSERVE_PORT"
}
def load_json(path:Path)->dict[str,Any]:
    v=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise RuntimeError(f"expected JSON object: {path}")
    return v
def stable_hash(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def clean_env(source:dict[str,str]|None=None)->dict[str,str]:
    values=dict(os.environ if source is None else source)
    env={k:values[k] for k in NONSECRET_ENV if values.get(k)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"; env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"; return env
def validate_request(r:dict[str,Any])->None:
    expected={"schema":"stegverse.resident-execution-request/v1","state":"REQUESTED","task_id":TARGET_TASK,"mode":TARGET_MODE,"entrypoint":TARGET_ENTRYPOINT,"credential_authority":"TV/TVC","credential_requirement":"NONE_FOR_NODE_BOUND_PUBLIC_READ","github_token_required":False,"github_token_runtime_authority":"NONE","heartbeat_grants_execution_authority":False,"second_machine_required":False,"network_source_fetch_allowed":False,"request_granted_authority":False,"authority_effect":"NONE_REQUEST_ONLY"}
    for k,v in expected.items():
        if r.get(k)!=v: raise RuntimeError(f"SV002 observation resident request {k} mismatch")
    if not isinstance(r.get("request_id"),str) or not r["request_id"].strip(): raise RuntimeError("request_id missing")
def parse_last_json(stdout:str)->dict[str,Any]|None:
    for line in reversed([x.strip() for x in stdout.splitlines() if x.strip()]):
        try: v=json.loads(line)
        except Exception: continue
        if isinstance(v,dict): return v
    return None
def terminally_consumed(runtime:Path,request:dict[str,Any],request_hash:str)->bool:
    p=runtime/CONSUMPTION_REL
    if not p.is_file(): return False
    try: receipt=load_json(p)
    except Exception: return False
    return receipt.get("request_id")==request["request_id"] and receipt.get("request_sha256")==request_hash and receipt.get("terminal_round_trip_observed") is True
def consume(source_root:Path,runtime_root:Path,*,runner=subprocess.run,env:dict[str,str]|None=None)->dict[str,Any]:
    source=source_root.expanduser().resolve(); runtime=runtime_root.expanduser().resolve(); request_path=runtime/REQUEST_REL
    if not request_path.is_file(): return {"schema":"stegverse.sv002-public-observation-request-consumption/v1","state":"NO_REQUEST","runtime_execution_attempted":False,"authority_effect":"NONE"}
    request=load_json(request_path); validate_request(request); request_hash=stable_hash(request)
    if terminally_consumed(runtime,request,request_hash): return {"schema":"stegverse.sv002-public-observation-request-consumption/v1","state":"ALREADY_CONSUMED","request_id":request["request_id"],"request_sha256":request_hash,"runtime_execution_attempted":False,"authority_effect":"NONE"}
    safe=clean_env(env); materializer=runtime/MATERIALIZER
    if not materializer.is_file(): raise RuntimeError(f"SV002 observation route materializer missing: {materializer}")
    mat=runner([sys.executable,str(materializer)],cwd=runtime,capture_output=True,text=True,check=False,env=safe,timeout=30); mat_result=parse_last_json(mat.stdout)
    if not isinstance(mat_result,dict): raise RuntimeError("SV002 observation route materializer returned no machine result")
    if mat_result.get("state")=="PREDICATE_PENDING":
        receipt={"schema":"stegverse.sv002-public-observation-request-consumption/v1","state":"PREDICATE_PENDING","request_id":request["request_id"],"request_sha256":request_hash,"task_id":TARGET_TASK,"runtime_execution_attempted":False,"route_materialization":mat_result,"terminal_round_trip_observed":False,"request_granted_authority":False,"credential_authority":"TV/TVC","github_token_required":False,"second_machine_required":False,"authority_effect":"NONE_REQUEST_ONLY"}
    else:
        entrypoint=runtime/TARGET_ENTRYPOINT
        if not entrypoint.is_file(): raise RuntimeError(f"SV002 observation resident execution entrypoint missing: {entrypoint}")
        command=[sys.executable,str(entrypoint),"--source-root",str(source),"--runtime-root",str(runtime),"--task-id",TARGET_TASK]
        completed=runner(command,cwd=runtime,capture_output=True,text=True,check=False,env=safe,timeout=180); result=parse_last_json(completed.stdout)
        terminal=bool(isinstance(result,dict) and (result.get("transition_id")=="SV002_PUBLIC_OBSERVATION_ROUND_TRIP_OBSERVED" or (result.get("execution_result") or {}).get("transition_id")=="SV002_PUBLIC_OBSERVATION_ROUND_TRIP_OBSERVED"))
        receipt={"schema":"stegverse.sv002-public-observation-request-consumption/v1","state":"COMPLETED" if terminal else "ATTEMPT_RECORDED","request_id":request["request_id"],"request_sha256":request_hash,"task_id":TARGET_TASK,"mode":TARGET_MODE,"command":command,"execution_returncode":completed.returncode,"execution_result_observed":isinstance(result,dict),"execution_result":result,"runtime_execution_attempted":True,"route_materialization":mat_result,"terminal_round_trip_observed":terminal,"request_granted_authority":False,"heartbeat_grants_execution_authority":False,"github_token_required":False,"github_token_runtime_authority":"NONE","credential_authority":"TV/TVC","credential_requirement":"NONE_FOR_NODE_BOUND_PUBLIC_READ","second_machine_required":False,"network_source_fetch_performed":False,"authority_effect":"NONE_REQUEST_ONLY"}
    p=runtime/CONSUMPTION_REL; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return receipt
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--source-root",type=Path,default=ROOT); ap.add_argument("--runtime-root",type=Path,required=True); a=ap.parse_args(); r=consume(a.source_root,a.runtime_root); print(json.dumps(r,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
