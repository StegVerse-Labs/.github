#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
from typing import Mapping

ROOT=Path(__file__).resolve().parents[1]
REQUEST_REL=Path("control/resident-execution-request.d/kimi-intr-resident-activation-001.json")
CONSUMPTION_REL=Path("receipts/sovereign-host/kimi-intr-resident-activation-request-consumption.latest.json")
TARGET_TASK="KIMI-INTR-RESIDENT-ACTIVATION-001"
TARGET_MODE="TARGETED_INDEPENDENT_TASK_CONTROL"
TARGET_ENTRYPOINT="scripts/refresh_and_execute_kimi_intr_resident_task.py"
HOSTED_ENV=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","VERCEL_ENV","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","ACTIONS_RUNTIME_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","DEEPSEEK_API_KEY","MOONSHOT_API_KEY","KIMI_API_KEY","MASTER_RECORDS_AUTH_TOKEN","MASTER_RECORDS_RECEIPT_KEY","STEGVERSE_MASTER_RECORDS_TOKEN","PRIVATE_KEY","SEED","MNEMONIC")
FORWARD=("PATH","HOME","LANG","LC_ALL","XDG_STATE_HOME","XDG_CONFIG_HOME","LOCALAPPDATA","STEGVERSE_SOVEREIGN_NODE","STEGVERSE_HEARTBEAT_ROOT","STEGVERSE_HEARTBEAT_SOURCE_ROOT","STEGVERSE_LLM_ADAPTER_ROOT","STEGVERSE_TVC_ROOT","STEGVERSE_STEGOS_ROOT","STEGVERSE_GOVERNANCE_ROOT","STEGVERSE_STEGCORE_SOURCE_ROOT","STEGVERSE_TEST_LANES_ROOT","STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT","STEGVERSE_REPO_ROOTS_JSON","STEGVERSE_VAULT_BROKER_SOCKET","STEGVERSE_MASTER_RECORDS_PROVIDER_USAGE_SOCKET")

def truthy(v): return str(v or "").strip().lower() not in {"","0","false","no"}
def load(p):
    v=json.loads(Path(p).read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise RuntimeError("expected object")
    return v
def stable(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate_request(r):
    required={"schema":"stegverse.resident-execution-request/v1","state":"REQUESTED","task_id":TARGET_TASK,"mode":TARGET_MODE,"entrypoint":TARGET_ENTRYPOINT,"fresh_fence_minimum_exclusive":0,"credential_authority":"TV/TVC","github_token_required":False,"github_token_runtime_authority":"NONE","heartbeat_grants_execution_authority":False,"second_machine_required":False,"network_source_fetch_allowed":False,"request_granted_authority":False,"provider_credential_material_allowed":False,"master_records_credential_material_allowed":False,"authority_effect":"NONE_REQUEST_ONLY"}
    for k,e in required.items():
        if r.get(k)!=e: raise RuntimeError(f"Kimi resident request {k} mismatch")
    if not isinstance(r.get("request_id"),str) or not r["request_id"]: raise RuntimeError("request_id missing")
def clean_env(source: Mapping[str,str] | None=None):
    vals=dict(os.environ if source is None else source)
    hosted=[k for k in HOSTED_ENV if truthy(vals.get(k))]
    if hosted: raise RuntimeError("hosted environment may not consume Kimi resident request: "+",".join(sorted(hosted)))
    leaked=[k for k in FORBIDDEN if vals.get(k)]
    if leaked: raise RuntimeError("credential-bearing resident consumer environment prohibited: "+",".join(sorted(leaked)))
    env={k:vals[k] for k in FORWARD if vals.get(k)}
    env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"]="TV/TVC"
    env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]="NONE"
    return env
def consumed(runtime,r,h):
    p=runtime/CONSUMPTION_REL
    if not p.is_file(): return False
    try: x=load(p)
    except Exception: return False
    return x.get("request_id")==r.get("request_id") and x.get("request_sha256")==h and x.get("runtime_execution_attempted") is True
def last_json(s):
    for line in reversed([x.strip() for x in s.splitlines() if x.strip()]):
        try: v=json.loads(line)
        except Exception: continue
        if isinstance(v,dict): return v
    return None
def consume(source_root,runtime_root,*,runner=subprocess.run,env=None):
    source=Path(source_root).expanduser().resolve(); runtime=Path(runtime_root).expanduser().resolve(); p=runtime/REQUEST_REL
    if not p.is_file(): return {"schema":"stegverse.kimi-intr-resident-request-consumption/v1","state":"NO_REQUEST","runtime_execution_attempted":False,"authority_effect":"NONE"}
    r=load(p); validate_request(r); h=stable(r)
    if consumed(runtime,r,h): return {"schema":"stegverse.kimi-intr-resident-request-consumption/v1","state":"ALREADY_CONSUMED","request_id":r["request_id"],"request_sha256":h,"runtime_execution_attempted":False,"authority_effect":"NONE"}
    entry=runtime/TARGET_ENTRYPOINT
    if not entry.is_file(): raise RuntimeError("Kimi resident execution entrypoint missing")
    command=[sys.executable,str(entry),"--source-root",str(source),"--runtime-root",str(runtime)]
    done=runner(command,cwd=runtime,capture_output=True,text=True,check=False,env=clean_env(env),timeout=1800)
    result=last_json(done.stdout)
    valid=bool(isinstance(result,dict) and result.get("mode")==TARGET_MODE and result.get("task_id")==TARGET_TASK and result.get("runtime_execution_attempted") is True and result.get("network_fetch_performed") is False and result.get("github_token_runtime_authority")=="NONE" and result.get("credential_authority")=="TV/TVC" and result.get("authority_effect")=="EXISTING_ADMITTED_TASK_AUTHORITY_ONLY")
    receipt={"schema":"stegverse.kimi-intr-resident-request-consumption/v1","state":"ATTEMPT_RECORDED" if valid else "FAIL_CLOSED","request_id":r["request_id"],"request_sha256":h,"task_id":TARGET_TASK,"mode":TARGET_MODE,"command":command,"execution_returncode":done.returncode,"execution_result_observed":isinstance(result,dict),"execution_result":result,"bridge_contract_valid":valid,"runtime_execution_attempted":True,"request_granted_authority":False,"activation_claimed":False,"heartbeat_grants_execution_authority":False,"github_token_required":False,"github_token_runtime_authority":"NONE","credential_authority":"TV/TVC","network_source_fetch_performed":False,"authority_effect":"NONE_REQUEST_ONLY"}
    q=runtime/CONSUMPTION_REL; q.parent.mkdir(parents=True,exist_ok=True); q.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return receipt
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--source-root",type=Path,default=ROOT); ap.add_argument("--runtime-root",type=Path,required=True); a=ap.parse_args(); r=consume(a.source_root,a.runtime_root); print(json.dumps(r,sort_keys=True)); return 0 if r["state"] in {"NO_REQUEST","ALREADY_CONSUMED","ATTEMPT_RECORDED"} else 1
if __name__=="__main__": raise SystemExit(main())
