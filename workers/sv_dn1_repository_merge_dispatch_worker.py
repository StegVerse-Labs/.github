#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, json, os, tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

TASK_ID="SV-DN1-REPOSITORY-MERGE-DISPATCH-001"
WORKER_ID="sv-dn1-repository-merge-dispatch-worker"
PERSIST_DISPATCH_ENV="STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_DISPATCH_STATE_ROOT"
PACKAGE_ENV="STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT"
BOUND_ENV="STEGVERSE_TVC_SV_DN1_MERGE_SPOOL_ROOT"
DEFAULT_PERSIST_DISPATCH=Path.home()/".stegverse/transport/sv-dn1-repository-persistence"
DEFAULT_PACKAGE=Path.home()/".stegverse/state/sv-dn1-repository-persistence-package"
DEFAULT_BOUND=Path.home()/".stegverse/transport/sv-dn1-repository-merge"
TARGET_REPO="StegVerse-org/stegverse-demo-suite"
TARGET_REF="main"
TARGET_ROOT="public/sv-dn1"
FILES=("first-round-analysis.json","production-pipeline-observation.json","result-receipt.json","report.md","index.html")
REQUEST_SCHEMA="stegverse.tvc.sv-dn1-repository-merge-request/v1"
MERGE_RECEIPT_SCHEMA="stegverse.tvc.sv-dn1-repository-merge-receipt/v1"
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","TVC_EPHEMERAL_GITHUB_TOKEN","HF_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","OAUTH_TOKEN")
class Pending(RuntimeError): pass
class Conflict(RuntimeError): pass
def truthy(v): return str(v or "").strip().lower() not in {"","0","false","no"}
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def canonical_hash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def stable_package_bytes(v): return (json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
def resolve(name,default): return Path(os.environ.get(name,str(default))).expanduser().resolve()
def load(path,pending=False):
    if not path.is_file():
        if pending: raise Pending(f"required local object not present: {path}")
        raise RuntimeError(f"required JSON missing: {path}")
    value=json.loads(path.read_text())
    if not isinstance(value,dict): raise RuntimeError(f"expected JSON object: {path}")
    return value
def atomic(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h: json.dump(value,h,indent=2,sort_keys=True);h.write("\n")
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def write_once(path,value):
    if path.is_file():
        if load(path)!=value: raise Conflict(f"frozen request conflict: {path.name}")
    else: atomic(path,value)

def validate_package(pkg):
    if pkg.get("schema")!="stegverse.sv-dn1.repository-persistence-package/v1" or pkg.get("state")!="READY_FOR_ADMITTED_REPOSITORY_MUTATION":
        raise Pending("governed persistence package is not ready")
    if (pkg.get("target_repository"),pkg.get("target_ref"),pkg.get("target_root"))!=(TARGET_REPO,TARGET_REF,TARGET_ROOT):
        raise RuntimeError("persistence package target mismatch")
    body=dict(pkg);claimed=body.pop("package_sha256",None)
    if not isinstance(claimed,str) or claimed!=sha_bytes(stable_package_bytes(body)):
        raise RuntimeError("persistence package sha256 mismatch")
    rows=pkg.get("files")
    if not isinstance(rows,list) or len(rows)!=5: raise RuntimeError("persistence package file count mismatch")
    names=set()
    for row in rows:
        if not isinstance(row,Mapping): raise RuntimeError("persistence package row invalid")
        path=str(row.get("path") or "");name=PurePosixPath(path).name
        if path!=f"{TARGET_ROOT}/{name}" or name not in FILES or name in names: raise RuntimeError("persistence package exact path set mismatch")
        raw=base64.b64decode(str(row.get("content_base64") or "").encode(),validate=True)
        if row.get("sha256")!=sha_bytes(raw) or row.get("size")!=len(raw): raise RuntimeError(f"persistence package byte mismatch:{name}")
        names.add(name)
    if names!=set(FILES): raise RuntimeError("persistence package exact file set mismatch")
    return claimed

def validate_persistence_receipt(receipt,package_sha):
    expected={
      "schema":"stegverse.sv-dn1.repository-persistence-dispatch-receipt/v1",
      "state":"COMPLETE",
      "transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED",
      "package_sha256":package_sha,
      "credential_used":False,
      "consumer_credential_present":False,
      "repository_mutation_performed_by_worker":False,
      "merge_performed":False,
      "deployment_performed":False,
      "authority_effect":"NONE_REQUEST_STAGING_ONLY",
    }
    for k,v in expected.items():
        if receipt.get(k)!=v: raise Pending(f"persistence dispatch receipt {k} mismatch")
    base=receipt.get("base_sha");head=receipt.get("head_sha");branch=receipt.get("branch");pr=receipt.get("pull_request_number")
    if not isinstance(base,str) or len(base)!=40: raise RuntimeError("persistence base sha invalid")
    if not isinstance(head,str) or len(head)!=40: raise RuntimeError("persistence head sha invalid")
    if not isinstance(branch,str) or not branch.startswith("sv-dn1/publication-"): raise RuntimeError("persistence branch invalid")
    if not isinstance(pr,int) or pr<1: raise RuntimeError("persistence PR number invalid")
    return base,head,branch,pr

def merge_request(package_sha,base,head,branch,pr):
    payload={"repository":TARGET_REPO,"base_ref":TARGET_REF,"pull_request_number":pr,"expected_base_sha":base,"expected_head_sha":head,"expected_head_ref":branch,"package_sha256":package_sha}
    rid="svdn1-merge-"+canonical_hash(payload)[:20]
    return {
      "schema":REQUEST_SCHEMA,"request_id":rid,"repository":TARGET_REPO,"base_ref":TARGET_REF,
      "pull_request_number":pr,"expected_base_sha":base,"expected_head_sha":head,"expected_head_ref":branch,
      "package_sha256":package_sha,"credential_authority":"TV/TVC","consumer_credential_present":False,
      "secret_values_present":False,"merge_request_grants_authority":False,
      "authority_effect":"NONE_MERGE_REQUEST_ONLY"
    }

def validate_merge_receipt(request,receipt):
    expected={
      "schema":MERGE_RECEIPT_SCHEMA,"state":"COMPLETE","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PR_MERGED",
      "request_id":request["request_id"],"request_sha256":canonical_hash(request),
      "repository":TARGET_REPO,"base_ref":TARGET_REF,"pull_request_number":request["pull_request_number"],
      "base_sha":request["expected_base_sha"],"head_ref":request["expected_head_ref"],"head_sha":request["expected_head_sha"],
      "package_sha256":request["package_sha256"],"file_count":5,"exact_bytes_verified":True,
      "credential_authority":"TV/TVC","credential_value_exposed":False,"non_tv_tvc_secret_or_token_used":False,
      "scope_expanded":False,"deployment_performed":False,"publication_observed":False,
      "authority_effect":"BOUNDED_SV_DN1_REPOSITORY_MERGE_ONLY",
    }
    for k,v in expected.items():
        if receipt.get(k)!=v: raise Pending(f"merge receipt {k} mismatch")
    merge_sha=receipt.get("merge_commit_sha")
    if not isinstance(merge_sha,str) or len(merge_sha)!=40: raise RuntimeError("merge receipt merge sha invalid")
    return merge_sha

def execute(inv:Mapping[str,Any]):
    if any(truthy(os.getenv(x)) for x in HOSTED): raise RuntimeError("hosted environment cannot dispatch authentic repository merge")
    present=[x for x in FORBIDDEN if truthy(os.getenv(x))]
    if present: raise RuntimeError("credential-bearing environment forbidden: "+",".join(sorted(present)))
    task=inv.get("task") or {}
    if inv.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID or not task.get("claim_id"):
        raise RuntimeError("task invocation identity mismatch")

    pkg=load(resolve(PACKAGE_ENV,DEFAULT_PACKAGE)/"packages/latest.json",True)
    package_sha=validate_package(pkg)
    persistence=load(resolve(PERSIST_DISPATCH_ENV,DEFAULT_PERSIST_DISPATCH)/"receipts/latest.json",True)
    base,head,branch,pr=validate_persistence_receipt(persistence,package_sha)

    root=resolve(BOUND_ENV,DEFAULT_BOUND);outbox=root/"outbox";inbox=root/"inbox";staged=root/"staged"
    request=merge_request(package_sha,base,head,branch,pr)
    write_once(staged/"merge-request.json",request)
    write_once(outbox/f"{request['request_id']}.json",request)
    receipt_path=inbox/f"{request['request_id']}.json"
    if not receipt_path.is_file(): raise Pending("TVC SV-DN-1 merge receipt not yet observed")
    merge_sha=validate_merge_receipt(request,load(receipt_path))
    result={
      "schema":"stegverse.sv-dn1.repository-merge-dispatch-receipt/v1","state":"COMPLETE",
      "transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PR_MERGED","task_id":TASK_ID,"worker_id":WORKER_ID,
      "claim_id":task.get("claim_id"),"fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),
      "package_sha256":package_sha,"base_sha":base,"branch":branch,"head_sha":head,"pull_request_number":pr,
      "merge_commit_sha":merge_sha,"credential_used":False,"consumer_credential_present":False,
      "repository_merge_performed_by_worker":False,"deployment_performed":False,"publication_observed":False,
      "authority_effect":"NONE_MERGE_REQUEST_STAGING_ONLY"
    }
    write_once(root/"receipts/dispatcher.latest.json",result)
    return result

def main():
    try:
        execute(json.loads(input()))
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"COMPLETED","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PR_MERGED","transition_sequence":1,"expected_next_transition":"SV_DN1_AUTHENTIC_PUBLICATION_OBSERVED","checkpoint_ref":"receipts/dispatcher.latest.json","evidence_refs":["staged/merge-request.json","receipts/dispatcher.latest.json"],"authority_effect":"NONE_MERGE_REQUEST_STAGING_ONLY"},sort_keys=True));return 0
    except Pending as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"HANDOFF_READY","transition_id":"SV_DN1_REPOSITORY_MERGE_PENDING","error":str(e),"blocker":{"dependency_class":"TVC_REPOSITORY_MERGE","problem_statement":str(e),"solution_required":True,"may_remain_blocked":True,"physical_additional_machine_required":False,"third_party_runtime_required":False,"github_platform_required":True,"human_action_required":False},"authority_effect":"NONE"},sort_keys=True));return 0
    except Conflict as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"SV_DN1_REPOSITORY_MERGE_DISPATCH_CONFLICT","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
    except Exception as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"SV_DN1_REPOSITORY_MERGE_DISPATCH_BLOCKED","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
if __name__=="__main__": raise SystemExit(main())
