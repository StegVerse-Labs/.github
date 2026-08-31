#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

ROOT=Path(__file__).resolve().parents[1]
REQUEST_REL=Path("control/resident-execution-request.d/sv-dn1-publication-001.json")
CONSUMPTION_REL=Path("receipts/sovereign-host/sv-dn1-publication-resident-request-consumption.latest.json")
TARGET_TASK="SV-DN1-PUBLICATION-RESIDENT-CONTINUATION-001"
TARGET_MODE="SV_DN1_PUBLICATION_CONTINUATION"
TARGET_ENTRYPOINT="scripts/run_sv_dn1_publication_continuation.py"
MINIMUM_FENCE_EXCLUSIVE=22
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","TVC_EPHEMERAL_GITHUB_TOKEN","HF_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","OAUTH_TOKEN")
NONSECRET=(
 "PATH","HOME","LANG","LC_ALL","SSL_CERT_FILE","SSL_CERT_DIR","XDG_STATE_HOME","XDG_CONFIG_HOME",
 "STEGVERSE_HEARTBEAT_ROOT","STEGVERSE_SV_DN1_SOURCE_ROOT",
 "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT","STEGVERSE_TVC_SV_DN1_REPOSITORY_PERSISTENCE_ADMISSION",
 "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_DISPATCH_STATE_ROOT","STEGVERSE_TVC_SV_DN1_MERGE_SPOOL_ROOT"
)

def truthy(v): return str(v or "").strip().lower() not in {"","0","false","no"}
def load(path):
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise RuntimeError(f"expected JSON object: {path}")
    return value
def stable_hash(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def validate_request(r):
    expected={"schema":"stegverse.resident-execution-request/v1","state":"REQUESTED","task_id":TARGET_TASK,"mode":TARGET_MODE,"entrypoint":TARGET_ENTRYPOINT,"credential_authority":"TV/TVC","github_token_runtime_authority":"NONE","authority_effect":"NONE_REQUEST_ONLY"}
    for k,v in expected.items():
        if r.get(k)!=v: raise RuntimeError(f"publication resident request {k} mismatch")
    if r.get("fresh_fence_minimum_exclusive")!=MINIMUM_FENCE_EXCLUSIVE: raise RuntimeError("publication resident request fence floor mismatch")
    for k in ("heartbeat_grants_execution_authority","github_token_required","second_machine_required","network_source_fetch_allowed","request_granted_authority"):
        if r.get(k) is not False: raise RuntimeError(f"publication resident request forbidden grant: {k}")
    if not isinstance(r.get("request_id"),str) or not r["request_id"]: raise RuntimeError("publication resident request id missing")
def clean_env(source=None):
    values=dict(os.environ if source is None else source)
    bad=[n for n in HOSTED+FORBIDDEN if truthy(values.get(n))]
    if bad: raise RuntimeError("hosted/credential-bearing environment forbidden: "+",".join(sorted(bad)))
    env={n:values[n] for n in NONSECRET if values.get(n)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC";env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    return env
def atomic(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name("."+path.name+".tmp");tmp.write_text(json.dumps(dict(value),indent=2,sort_keys=True)+"\n");os.replace(tmp,path)
def previously_consumed(runtime,request,request_hash):
    path=runtime/CONSUMPTION_REL
    if not path.is_file(): return False
    receipt=load(path); result=receipt.get("execution_result")
    return receipt.get("request_id")==request.get("request_id") and receipt.get("request_sha256")==request_hash and isinstance(result,dict) and result.get("state")=="COMPLETE" and result.get("transition_id")=="SV_DN1_PUBLICATION_CONTINUATION_COMPLETE"
def consume(source_root:Path,runtime_root:Path,*,runner=subprocess.run,env:Mapping[str,str]|None=None):
    source=source_root.expanduser().resolve();runtime=runtime_root.expanduser().resolve();request_path=runtime/REQUEST_REL
    if not request_path.is_file(): return {"schema":"stegverse.sv-dn1.publication-resident-request-consumption/v1","state":"NO_REQUEST","runtime_execution_attempted":False,"authority_effect":"NONE"}
    request=load(request_path);validate_request(request);rh=stable_hash(request)
    if previously_consumed(runtime,request,rh): return {"schema":"stegverse.sv-dn1.publication-resident-request-consumption/v1","state":"ALREADY_CONSUMED","request_id":request["request_id"],"request_sha256":rh,"runtime_execution_attempted":False,"authority_effect":"NONE"}
    entry=runtime/TARGET_ENTRYPOINT
    if not entry.is_file(): raise RuntimeError(f"publication continuation entrypoint missing: {entry}")
    command=[sys.executable,str(entry),"--runtime-root",str(runtime)]
    proc=runner(command,cwd=runtime,capture_output=True,text=True,check=False,env=clean_env(env),timeout=1800)
    result=None
    for line in reversed([x.strip() for x in proc.stdout.splitlines() if x.strip()]):
        try: candidate=json.loads(line)
        except Exception: continue
        if isinstance(candidate,dict): result=candidate;break
    receipt={"schema":"stegverse.sv-dn1.publication-resident-request-consumption/v1","state":"ATTEMPT_RECORDED","request_id":request["request_id"],"request_sha256":rh,"task_id":TARGET_TASK,"mode":TARGET_MODE,"command":command,"execution_returncode":proc.returncode,"execution_result_observed":isinstance(result,dict),"execution_result":result,"runtime_execution_attempted":True,"request_granted_authority":False,"heartbeat_grants_execution_authority":False,"github_token_required":False,"github_token_runtime_authority":"NONE","credential_authority":"TV/TVC","second_machine_required":False,"repository_writeback_authority":False,"merge_authority":False,"deployment_authority":False,"authority_effect":"NONE_REQUEST_ONLY"}
    atomic(runtime/CONSUMPTION_REL,receipt);return receipt
def main():
    parser=argparse.ArgumentParser(description="Consume the bounded SV-DN-1 publication continuation request.");parser.add_argument("--source-root",type=Path,default=ROOT);parser.add_argument("--runtime-root",type=Path,required=True);args=parser.parse_args()
    receipt=consume(args.source_root,args.runtime_root);print(json.dumps(receipt,sort_keys=True));return 0 if receipt.get("execution_result_observed") is not False else 1
if __name__=="__main__": raise SystemExit(main())
