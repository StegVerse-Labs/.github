#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Mapping

TASK_ID = "SV-DN1-PUBLIC-PROMOTION-001"
WORKER_ID = "sv-dn1-public-promotion-worker"
BOUND_ENV = "STEGVERSE_BOUND_STATE_ROOT"
SDK_STATE_ENV = "STEGVERSE_SV_DN1_SDK_FIRST_ROUND_STATE_ROOT"
DEMO_ROOT_ENV = "STEGVERSE_SV_DN1_SOURCE_ROOT"
DEFAULT_BOUND = Path.home()/".stegverse"/"state"/"sv-dn1-public-promotion"
DEFAULT_SDK = Path.home()/".stegverse"/"state"/"sv-dn1-sdk-first-round"
DEFAULT_DEMO = Path.home()/".stegverse"/"source"/"stegverse-demo-suite"
PROMOTED = ("first-round-analysis.json","production-pipeline-observation.json","result-receipt.json","report.md","index.html")
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","TVC_EPHEMERAL_GITHUB_TOKEN","HF_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","OAUTH_TOKEN")

class Pending(RuntimeError): pass
class Conflict(RuntimeError): pass

def truthy(v:str|None)->bool:return str(v or "").strip().lower() not in {"","0","false","no"}
def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def load(path:Path,pending=False)->dict[str,Any]:
    if not path.is_file():
        if pending: raise Pending(f"required local object not present: {path}")
        raise RuntimeError(f"required JSON missing: {path}")
    v=json.loads(path.read_text())
    if not isinstance(v,dict): raise RuntimeError(f"expected JSON object: {path}")
    return v
def atomic(path:Path,v:Mapping[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(dict(v),h,indent=2,sort_keys=True);h.write("\n")
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def resolve(env:str,default:Path)->Path:return Path(os.environ.get(env,str(default))).expanduser().resolve()

def validate_sdk(receipt:Mapping[str,Any])->None:
    expected={
      "schema":"stegverse.sv-dn1.sdk-first-round-worker-receipt/v1",
      "state":"COMPLETE","transition_id":"SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED",
      "first_round_analysis":"ANALYZED","dashboard_generated":True,"dashboard_publicly_hosted":False,
      "repository_writeback_performed":False,"credential_used":False,"github_token_used":False,"authority_effect":"NONE"}
    for k,v in expected.items():
        if receipt.get(k)!=v: raise Pending(f"SDK first-round receipt {k} mismatch")

def execute(inv:Mapping[str,Any])->dict[str,Any]:
    if any(truthy(os.getenv(x)) for x in HOSTED): raise RuntimeError("hosted environment cannot promote authentic public result")
    present=[x for x in FORBIDDEN if truthy(os.getenv(x))]
    if present: raise RuntimeError("credential-bearing environment forbidden: "+",".join(sorted(present)))
    task=inv.get("task") or {}
    if inv.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID or not task.get("claim_id"): raise RuntimeError("task invocation identity mismatch")
    sdk=resolve(SDK_STATE_ENV,DEFAULT_SDK);demo=resolve(DEMO_ROOT_ENV,DEFAULT_DEMO)
    sdk_receipt=load(sdk/"receipts"/"latest.json",True);validate_sdk(sdk_receipt)
    finalized=sdk/"round"
    for name in PROMOTED:
        if not (finalized/name).is_file(): raise Pending(f"finalized SDK artifact missing: {name}")
    promoter=demo/"scripts"/"promote_sv_dn1_public_result.py"
    handoff=demo/"docs"/"SV_DN1_AUTHENTIC_PUBLIC_PROMOTION_MIRROR_HANDOFF.md"
    if not promoter.is_file() or not handoff.is_file(): raise Pending(f"canonical demo-suite promoter unavailable: {demo}")
    public=demo/"public"/"sv-dn1"; local_receipt=resolve(BOUND_ENV,DEFAULT_BOUND)/"promoter"/"latest.json"
    env={k:v for k,v in os.environ.items() if k not in FORBIDDEN and k not in HOSTED}
    completed=subprocess.run([sys.executable,str(promoter),"--finalized-dir",str(finalized),"--public-dir",str(public),"--receipt",str(local_receipt)],cwd=demo,capture_output=True,text=True,check=False,env=env,timeout=180)
    if completed.returncode!=0: raise RuntimeError("canonical public promoter failed: "+(completed.stderr or completed.stdout)[-2000:])
    promoted=load(local_receipt)
    expected={"schema":"stegverse.sv-dn1.public-promotion-receipt/v1","state":"PROMOTION_READY_FOR_REPOSITORY_MUTATION","observation_class":"LIVE","exact_bytes_preserved":True,"semantic_rewrite_performed":False,"network_fetch_performed":False,"credential_used":False,"repository_writeback_performed":False,"deployment_performed":False,"authority_effect":"NONE_STATIC_PROJECTION_ONLY"}
    for k,v in expected.items():
        if promoted.get(k)!=v: raise RuntimeError(f"promoter receipt {k} mismatch")
    if promoted.get("publication_state") not in {"PUBLIC_OBSERVED","PUBLIC_WITH_LIMITATIONS"}: raise RuntimeError("promoter publication state invalid")
    src={n:sha(finalized/n) for n in PROMOTED};dst={n:sha(public/n) for n in PROMOTED}
    if src!=dst or promoted.get("source_artifact_sha256")!=src or promoted.get("destination_artifact_sha256")!=dst: raise RuntimeError("promotion exact-byte verification failed")
    receipt={"schema":"stegverse.sv-dn1.public-promotion-worker-receipt/v1","task_id":TASK_ID,"worker_id":WORKER_ID,"state":"COMPLETE","transition_id":"SV_DN1_PUBLIC_PROMOTION_READY","claim_id":task.get("claim_id"),"fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),"exchange_id":promoted.get("exchange_id"),"manifest_receipt_id":promoted.get("manifest_receipt_id"),"publication_state":promoted.get("publication_state"),"observation_class":"LIVE","source_artifact_sha256":src,"destination_artifact_sha256":dst,"exact_bytes_preserved":True,"semantic_rewrite_performed":False,"network_fetch_performed":False,"credential_used":False,"repository_writeback_performed":False,"deployment_performed":False,"release_performed":False,"certification_claimed":False,"authority_effect":"NONE_STATIC_PROJECTION_ONLY"}
    out=resolve(BOUND_ENV,DEFAULT_BOUND)/"receipts"/"latest.json"
    if out.is_file() and load(out)!=receipt: raise Conflict("SV_DN1_PUBLIC_PROMOTION_FROZEN_CONFLICT")
    if not out.is_file(): atomic(out,receipt)
    return receipt

def main()->int:
    try:
      inv=json.loads(sys.stdin.readline());r=execute(inv);print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"COMPLETED","transition_id":"SV_DN1_PUBLIC_PROMOTION_READY","transition_sequence":1,"expected_next_transition":"SV_DN1_PUBLIC_AUTHENTIC_DASHBOARD_PUBLISHED","checkpoint_ref":"receipts/latest.json","evidence_refs":["receipts/latest.json"],"authority_effect":"NONE_STATIC_PROJECTION_ONLY"},sort_keys=True));return 0
    except Pending as e:
      print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"HANDOFF_READY","transition_id":"SV_DN1_PUBLIC_PROMOTION_PENDING","error":str(e),"blocker":{"dependency_class":"AUTHENTIC_ANALYZED_RESULT_OR_LOCAL_PROMOTER","problem_statement":str(e),"solution_required":True,"may_remain_blocked":False,"physical_additional_machine_required":False,"third_party_runtime_required":False,"github_platform_required":False,"human_action_required":False},"authority_effect":"NONE"},sort_keys=True));return 0
    except Conflict as e:
      print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"SV_DN1_PUBLIC_PROMOTION_CONFLICT","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
    except Exception as e:
      print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"SV_DN1_PUBLIC_PROMOTION_BLOCKED","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
