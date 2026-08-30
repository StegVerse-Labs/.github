#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, json, os, tempfile
from pathlib import Path
from typing import Any, Mapping

TASK_ID="SV-DN1-REPOSITORY-PERSISTENCE-PACKAGE-001"
WORKER_ID="sv-dn1-repository-persistence-package-worker"
PROMOTION_ENV="STEGVERSE_SV_DN1_PUBLIC_PROMOTION_STATE_ROOT"
DEMO_ENV="STEGVERSE_SV_DN1_SOURCE_ROOT"
BOUND_ENV="STEGVERSE_BOUND_STATE_ROOT"
DEFAULT_PROMOTION=Path.home()/".stegverse/state/sv-dn1-public-promotion"
DEFAULT_DEMO=Path.home()/".stegverse/source/stegverse-demo-suite"
DEFAULT_BOUND=Path.home()/".stegverse/state/sv-dn1-repository-persistence-package"
FILES=("first-round-analysis.json","production-pipeline-observation.json","result-receipt.json","report.md","index.html")
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","TVC_EPHEMERAL_GITHUB_TOKEN","HF_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","OAUTH_TOKEN")

class Pending(RuntimeError): pass
class Conflict(RuntimeError): pass

def truthy(v:str|None)->bool:return str(v or "").strip().lower() not in {"","0","false","no"}
def stable_bytes(v:Mapping[str,Any])->bytes:return (json.dumps(dict(v),sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def load(path:Path,pending:bool=False)->dict[str,Any]:
    if not path.is_file():
        if pending: raise Pending(f"required local object not present: {path}")
        raise RuntimeError(f"required JSON missing: {path}")
    v=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise RuntimeError(f"expected JSON object: {path}")
    return v
def atomic(path:Path,v:Mapping[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h: json.dump(dict(v),h,indent=2,sort_keys=True);h.write("\n")
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def resolve(name:str,default:Path)->Path:return Path(os.environ.get(name,str(default))).expanduser().resolve()

def validate_promotion(r:Mapping[str,Any])->None:
    expected={
      "schema":"stegverse.sv-dn1.public-promotion-worker-receipt/v1","state":"COMPLETE",
      "transition_id":"SV_DN1_PUBLIC_PROMOTION_READY","observation_class":"LIVE",
      "exact_bytes_preserved":True,"semantic_rewrite_performed":False,"network_fetch_performed":False,
      "credential_used":False,"repository_writeback_performed":False,"deployment_performed":False,
      "release_performed":False,"certification_claimed":False,"authority_effect":"NONE_STATIC_PROJECTION_ONLY"}
    for k,v in expected.items():
        if r.get(k)!=v: raise Pending(f"promotion receipt {k} mismatch")
    if r.get("publication_state") not in {"PUBLIC_OBSERVED","PUBLIC_WITH_LIMITATIONS"}: raise Pending("promotion publication_state is not public-observable")
    hashes=r.get("destination_artifact_sha256")
    if not isinstance(hashes,dict) or set(hashes)!=set(FILES): raise Pending("promotion destination hash map mismatch")

def execute(inv:Mapping[str,Any])->dict[str,Any]:
    if any(truthy(os.getenv(x)) for x in HOSTED): raise RuntimeError("hosted environment cannot create repository persistence package")
    present=[x for x in FORBIDDEN if truthy(os.getenv(x))]
    if present: raise RuntimeError("credential-bearing environment forbidden: "+",".join(sorted(present)))
    task=inv.get("task") or {}
    if inv.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID or not task.get("claim_id"):
        raise RuntimeError("task invocation identity mismatch")

    promotion_root=resolve(PROMOTION_ENV,DEFAULT_PROMOTION)
    demo=resolve(DEMO_ENV,DEFAULT_DEMO)
    bound=resolve(BOUND_ENV,DEFAULT_BOUND)
    promotion=load(promotion_root/"receipts/latest.json",True); validate_promotion(promotion)
    public=demo/"public/sv-dn1"
    expected_hashes=promotion["destination_artifact_sha256"]
    rows=[]
    for name in FILES:
        p=public/name
        if not p.is_file(): raise Pending(f"promoted public artifact missing: {name}")
        b=p.read_bytes(); digest=sha_bytes(b)
        if digest!=expected_hashes.get(name): raise RuntimeError(f"promoted artifact hash mismatch: {name}")
        rows.append({"path":f"public/sv-dn1/{name}","sha256":digest,"size":len(b),"content_base64":base64.b64encode(b).decode("ascii")})
    body={
      "schema":"stegverse.sv-dn1.repository-persistence-package/v1",
      "state":"READY_FOR_ADMITTED_REPOSITORY_MUTATION",
      "target_repository":"StegVerse-org/stegverse-demo-suite","target_ref":"main","target_root":"public/sv-dn1",
      "exchange_id":promotion.get("exchange_id"),"manifest_receipt_id":promotion.get("manifest_receipt_id"),
      "publication_state":promotion.get("publication_state"),"observation_class":"LIVE","files":rows,
      "exact_bytes_preserved":True,"semantic_rewrite_performed":False,"network_fetch_performed":False,
      "credential_used":False,"repository_writeback_performed":False,"deployment_performed":False,
      "authority_effect":"NONE_PERSISTENCE_PACKAGE_ONLY"}
    package=dict(body); package["package_sha256"]=sha_bytes(stable_bytes(body))
    package_path=bound/"packages/latest.json"
    if package_path.is_file() and load(package_path)!=package: raise Conflict("SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_FROZEN_CONFLICT")
    if not package_path.is_file(): atomic(package_path,package)
    receipt={
      "schema":"stegverse.sv-dn1.repository-persistence-package-worker-receipt/v1","task_id":TASK_ID,"worker_id":WORKER_ID,
      "state":"COMPLETE","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_READY",
      "claim_id":task.get("claim_id"),"fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),
      "package_sha256":package["package_sha256"],"target_repository":package["target_repository"],"target_ref":"main",
      "file_sha256":{Path(r["path"]).name:r["sha256"] for r in rows},"exact_bytes_preserved":True,
      "network_fetch_performed":False,"credential_used":False,"repository_writeback_performed":False,
      "deployment_performed":False,"authority_effect":"NONE_PERSISTENCE_PACKAGE_ONLY"}
    receipt_path=bound/"receipts/latest.json"
    if receipt_path.is_file() and load(receipt_path)!=receipt: raise Conflict("SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_RECEIPT_FROZEN_CONFLICT")
    if not receipt_path.is_file(): atomic(receipt_path,receipt)
    return receipt

def main()->int:
    try:
        inv=json.loads(input()); execute(inv)
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"COMPLETED","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_READY","transition_sequence":1,"expected_next_transition":"SV_DN1_AUTHENTIC_RESULT_REPOSITORY_PERSISTED","checkpoint_ref":"receipts/latest.json","evidence_refs":["packages/latest.json","receipts/latest.json"],"authority_effect":"NONE_PERSISTENCE_PACKAGE_ONLY"},sort_keys=True)); return 0
    except Pending as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"HANDOFF_READY","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_PENDING","error":str(e),"blocker":{"dependency_class":"AUTHENTIC_PUBLIC_PROMOTION","problem_statement":str(e),"solution_required":True,"may_remain_blocked":False,"physical_additional_machine_required":False,"third_party_runtime_required":False,"github_platform_required":False,"human_action_required":False},"authority_effect":"NONE"},sort_keys=True)); return 0
    except Conflict as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_CONFLICT","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True)); return 0
    except Exception as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_BLOCKED","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
