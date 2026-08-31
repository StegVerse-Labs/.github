#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys, tempfile
from pathlib import Path
from typing import Any, Mapping

TASK_ID="SV-DN1-PUBLICATION-OBSERVER-001"
WORKER_ID="sv-dn1-publication-observer-worker"
BOUND_ENV="STEGVERSE_BOUND_STATE_ROOT"
PERSIST_ENV="STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT"
DEMO_ENV="STEGVERSE_SV_DN1_SOURCE_ROOT"
DEFAULT_BOUND=Path.home()/".stegverse/state/sv-dn1-publication-observer"
DEFAULT_PERSIST=Path.home()/".stegverse/state/sv-dn1-repository-persistence-package"
DEFAULT_DEMO=Path.home()/".stegverse/source/stegverse-demo-suite"
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","HF_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","OAUTH_TOKEN")

class Pending(RuntimeError): pass
class Conflict(RuntimeError): pass
def truthy(v): return str(v or "").strip().lower() not in {"","0","false","no"}
def resolve(name,default): return Path(os.environ.get(name,str(default))).expanduser().resolve()
def load(path):
    if not path.is_file(): raise Pending(f"required local object not present: {path}")
    v=json.loads(path.read_text())
    if not isinstance(v,dict): raise RuntimeError(f"expected JSON object: {path}")
    return v
def atomic(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h: json.dump(dict(value),h,indent=2,sort_keys=True);h.write("\n")
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def execute(inv:Mapping[str,Any])->dict[str,Any]:
    if any(truthy(os.getenv(x)) for x in HOSTED): raise RuntimeError("hosted environment cannot perform authentic publication observation")
    present=[x for x in FORBIDDEN if truthy(os.getenv(x))]
    if present: raise RuntimeError("credential-bearing environment forbidden: "+",".join(sorted(present)))
    task=inv.get("task") or {}
    if inv.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID or not task.get("claim_id"):
        raise RuntimeError("task invocation identity mismatch")
    persistence=resolve(PERSIST_ENV,DEFAULT_PERSIST)
    package=persistence/"packages/latest.json"
    pkg=load(package)
    if pkg.get("schema")!="stegverse.sv-dn1.repository-persistence-package/v1" or pkg.get("state")!="READY_FOR_ADMITTED_REPOSITORY_MUTATION":
        raise Pending("governed persistence package is not ready")
    demo=resolve(DEMO_ENV,DEFAULT_DEMO)
    observer=demo/"scripts/verify_sv_dn1_public_publication.py"
    if not observer.is_file(): raise Pending(f"canonical product observer unavailable: {observer}")
    bound=resolve(BOUND_ENV,DEFAULT_BOUND)
    product_receipt=bound/"product-observation/latest.json"
    env={k:v for k,v in os.environ.items() if k not in FORBIDDEN and k not in HOSTED}
    completed=subprocess.run([sys.executable,str(observer),"--persistence-package",str(package),"--receipt",str(product_receipt)],
        cwd=demo,capture_output=True,text=True,check=False,env=env,timeout=180)
    if completed.returncode!=0:
        raise Pending("public governed bytes are not yet exactly observable: "+(completed.stderr or completed.stdout)[-1200:])
    observed=load(product_receipt)
    expected={"schema":"stegverse.sv-dn1.publication-observation/v1","state":"COMPLETE",
      "transition_id":"SV_DN1_AUTHENTIC_PUBLICATION_OBSERVED","all_public_artifacts_observed":True,
      "exact_bytes_preserved":True,"credential_used":False,"authorization_header_sent":False,
      "repository_writeback_performed":False,"deployment_performed":False,"governance_executed":False,
      "sdk_execution_performed":False,"authority_effect":"NONE_PUBLICATION_OBSERVATION_ONLY"}
    for k,v in expected.items():
        if observed.get(k)!=v: raise RuntimeError(f"publication observation {k} mismatch")
    receipt={**expected,"task_id":TASK_ID,"worker_id":WORKER_ID,"claim_id":task.get("claim_id"),
      "fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),
      "exchange_id":observed.get("exchange_id"),"manifest_receipt_id":observed.get("manifest_receipt_id"),
      "publication_state":observed.get("publication_state"),"public_base_url":observed.get("public_base_url"),
      "artifact_sha256":{k:v["sha256"] for k,v in (observed.get("artifacts") or {}).items()}}
    out=bound/"receipts/latest.json"
    if out.is_file() and json.loads(out.read_text())!=receipt: raise Conflict("SV_DN1_PUBLICATION_OBSERVATION_FROZEN_CONFLICT")
    if not out.is_file(): atomic(out,receipt)
    return receipt

def main():
    try:
        execute(json.loads(input()))
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"COMPLETED","transition_id":"SV_DN1_AUTHENTIC_PUBLICATION_OBSERVED","transition_sequence":1,"expected_next_transition":None,"checkpoint_ref":"receipts/latest.json","evidence_refs":["product-observation/latest.json","receipts/latest.json"],"authority_effect":"NONE_PUBLICATION_OBSERVATION_ONLY"},sort_keys=True)); return 0
    except Pending as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"HANDOFF_READY","transition_id":"SV_DN1_PUBLICATION_NOT_YET_OBSERVED","error":str(e),"blocker":{"dependency_class":"REPOSITORY_PERSISTENCE_OR_PUBLIC_DEPLOYMENT","problem_statement":str(e),"solution_required":True,"may_remain_blocked":False,"physical_additional_machine_required":False,"third_party_runtime_required":False,"github_platform_required":True,"human_action_required":False},"authority_effect":"NONE"},sort_keys=True)); return 0
    except Conflict as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"SV_DN1_PUBLICATION_OBSERVATION_CONFLICT","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True)); return 0
    except Exception as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"SV_DN1_PUBLICATION_OBSERVATION_BLOCKED","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
