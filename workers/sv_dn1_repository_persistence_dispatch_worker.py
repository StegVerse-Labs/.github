#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, json, os, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

TASK_ID="SV-DN1-REPOSITORY-PERSISTENCE-DISPATCH-001"
WORKER_ID="sv-dn1-repository-persistence-dispatch-worker"
PERSIST_ENV="STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT"
BOUND_ENV="STEGVERSE_BOUND_STATE_ROOT"
ADMISSION_ENV="STEGVERSE_TVC_SV_DN1_REPOSITORY_PERSISTENCE_ADMISSION"
DEFAULT_PERSIST=Path.home()/".stegverse/state/sv-dn1-repository-persistence-package"
DEFAULT_BOUND=Path.home()/".stegverse/transport/sv-dn1-repository-persistence"
DEFAULT_ADMISSION=Path.home()/".stegverse/state/tvc/sv-dn1-repository-persistence-admission/latest.json"
FILES=("first-round-analysis.json","production-pipeline-observation.json","result-receipt.json","report.md","index.html")
TARGET_REPO="StegVerse-org/stegverse-demo-suite"; TARGET_REF="main"; TARGET_ROOT="public/sv-dn1"
INSPECT_SCHEMA="stegverse.tvc-github-repository-inspection-request/v0.1"
INSPECT_RECEIPT_SCHEMA="stegverse.tvc-github-repository-inspection-receipt/v0.1"
WARRANT_SCHEMA="stegverse.tvc-github-repository-operation-warrant/v0.1"
OP_RECEIPT_SCHEMA="stegverse.tvc-github-repository-operation-receipt/v0.1"
ADMISSION_SCHEMA="stegverse.tvc.sv-dn1-repository-persistence-admission/v1"
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","TVC_EPHEMERAL_GITHUB_TOKEN","HF_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","OAUTH_TOKEN")
class Pending(RuntimeError): pass
class Conflict(RuntimeError): pass
def truthy(v): return str(v or "").strip().lower() not in {"","0","false","no"}
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def canonical_hash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def stable_package_bytes(v): return (json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
def load(path,pending=False):
    if not path.is_file():
        if pending: raise Pending(f"required local object not present: {path}")
        raise RuntimeError(f"required JSON missing: {path}")
    v=json.loads(path.read_text())
    if not isinstance(v,dict): raise RuntimeError(f"expected JSON object: {path}")
    return v
def atomic(path,v):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h: json.dump(v,h,indent=2,sort_keys=True);h.write("\n")
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def resolve(name,default): return Path(os.environ.get(name,str(default))).expanduser().resolve()
def now_iso(dt): return dt.astimezone(timezone.utc).isoformat().replace("+00:00","Z")

def validate_package(pkg):
    if pkg.get("schema")!="stegverse.sv-dn1.repository-persistence-package/v1" or pkg.get("state")!="READY_FOR_ADMITTED_REPOSITORY_MUTATION": raise Pending("governed persistence package is not ready")
    if (pkg.get("target_repository"),pkg.get("target_ref"),pkg.get("target_root"))!=(TARGET_REPO,TARGET_REF,TARGET_ROOT): raise RuntimeError("persistence package target mismatch")
    body=dict(pkg); claimed=body.pop("package_sha256",None)
    if not isinstance(claimed,str) or claimed!=sha_bytes(stable_package_bytes(body)): raise RuntimeError("persistence package sha256 mismatch")
    rows=pkg.get("files")
    if not isinstance(rows,list) or len(rows)!=5: raise RuntimeError("persistence package file count mismatch")
    result={}
    for row in rows:
        path=row.get("path"); name=Path(str(path)).name
        if path!=f"{TARGET_ROOT}/{name}" or name not in FILES or name in result: raise RuntimeError("persistence package path set mismatch")
        raw=base64.b64decode(str(row.get("content_base64") or "").encode(),validate=True)
        if row.get("sha256")!=sha_bytes(raw) or row.get("size")!=len(raw): raise RuntimeError(f"persistence package byte identity mismatch: {name}")
        try: text=raw.decode("utf-8")
        except UnicodeDecodeError as e: raise RuntimeError(f"persistence package artifact is not UTF-8: {name}") from e
        result[name]={"path":path,"sha256":row["sha256"],"size":len(raw),"content_utf8":text}
    if set(result)!=set(FILES): raise RuntimeError("persistence package exact file set mismatch")
    return claimed,result

def write_once(path,value):
    if path.is_file():
        if load(path)!=value: raise Conflict(f"frozen request conflict: {path.name}")
    else: atomic(path,value)

def inspect_request(package_sha,now):
    paths=[f"{TARGET_ROOT}/{n}" for n in FILES]
    payload={"repository":TARGET_REPO,"base_ref":TARGET_REF,"paths":paths,"package_sha256":package_sha}
    rid="svdn1-inspect-"+canonical_hash(payload)[:20]
    return {"schema":INSPECT_SCHEMA,"request_id":rid,"operation_class":"INSPECT_REPOSITORY_STATE","repository":TARGET_REPO,"base_ref":TARGET_REF,"paths":paths,
      "credential_authority":"TV/TVC","consumer_credential_present":False,"secret_values_present":False,
      "issued_at":now_iso(now),"expires_at":now_iso(now+timedelta(hours=6)),"source_package_sha256":package_sha,"authority_effect":"NONE_REQUEST_ONLY"}

def validate_inspection(req,receipt):
    if receipt.get("schema")!=INSPECT_RECEIPT_SCHEMA or receipt.get("request_id")!=req["request_id"] or receipt.get("request_sha256")!=canonical_hash(req): raise Pending("matching TVC inspection receipt not yet observed")
    if receipt.get("repository")!=TARGET_REPO or receipt.get("base_ref")!=TARGET_REF: raise RuntimeError("inspection repository/ref mismatch")
    if receipt.get("credential_authority")!="TV/TVC" or receipt.get("credential_value_exposed") is not False or receipt.get("consumer_credential_present") is not False or receipt.get("non_tv_tvc_secret_or_token_used") is not False: raise RuntimeError("inspection credential boundary mismatch")
    base=receipt.get("base_sha")
    if not isinstance(base,str) or len(base)!=40: raise RuntimeError("inspection base sha invalid")
    rows=receipt.get("paths")
    if not isinstance(rows,list): raise RuntimeError("inspection paths missing")
    by={r.get("path"):r for r in rows if isinstance(r,dict)}
    expected=set(req["paths"])
    if set(by)!=expected: raise RuntimeError("inspection path set mismatch")
    for p,r in by.items():
        if r.get("state") not in {"PRESENT","ABSENT"}: raise RuntimeError(f"inspection state invalid: {p}")
        if r.get("state")=="PRESENT" and (not isinstance(r.get("sha256"),str) or len(r["sha256"])!=64): raise RuntimeError(f"inspection sha invalid: {p}")
        if r.get("state")=="ABSENT" and r.get("sha256") is not None: raise RuntimeError(f"inspection absent path has sha: {p}")
    return base,by

def apply_warrant(package_sha,files,base,inspected,now):
    branch=f"sv-dn1/publication-{package_sha[:12]}"
    rows=[]
    for name in FILES:
        src=inspected[files[name]["path"]]
        rows.append({"path":files[name]["path"],"content_utf8":files[name]["content_utf8"],"expected_source_sha256":src.get("sha256")})
    payload={"repository":TARGET_REPO,"base_ref":TARGET_REF,"expected_base_sha":base,"new_branch":branch,"package_sha256":package_sha,"file_hashes":{n:files[n]["sha256"] for n in FILES}}
    op="svdn1-apply-"+canonical_hash(payload)[:20]
    return {"schema":WARRANT_SCHEMA,"operation_id":op,"operation_class":"APPLY_BOUNDED_FILE_SET","repository":TARGET_REPO,"base_ref":TARGET_REF,"expected_base_sha":base,
      "new_branch":branch,"maximum_file_count":5,"maximum_total_bytes":sum(x["size"] for x in files.values()),"commit_message":"Publish authentic governed SV-DN-1 first round","files":rows,
      "credential_authority":"TV/TVC","consumer_credential_present":False,"secret_values_present":False,"single_use":True,
      "issued_at":now_iso(now),"expires_at":now_iso(now+timedelta(hours=6)),"nonce":canonical_hash(payload)[:24],"authorization_ref":f"tvc://sv-dn1/{op}",
      "source_package_sha256":package_sha,"authority_effect":"NONE_REQUEST_ONLY_TVC_AUTHORIZATION_REQUIRED"}

def mutation_admitted(path):
    if not path.is_file(): return False
    a=load(path)
    return a.get("schema")==ADMISSION_SCHEMA and a.get("state")=="ADMITTED" and a.get("issue")==264 and a.get("repository")==TARGET_REPO and a.get("credential_authority")=="TV/TVC" and a.get("consumer_credential_allowed") is False and set(a.get("allowed_operation_classes") or [])=={"APPLY_BOUNDED_FILE_SET","OPEN_PULL_REQUEST"}

def validate_apply_receipt(warrant,r):
    if r.get("schema")!=OP_RECEIPT_SCHEMA or r.get("operation_id")!=warrant["operation_id"] or r.get("operation_class")!="APPLY_BOUNDED_FILE_SET" or r.get("warrant_sha256")!=canonical_hash(warrant): raise Pending("matching TVC apply receipt not yet observed")
    if r.get("credential_authority")!="TV/TVC" or r.get("credential_value_exposed") is not False or r.get("non_tv_tvc_secret_or_token_used") is not False or r.get("merge_performed") is not False: raise RuntimeError("apply receipt authority mismatch")
    x=r.get("result") or {}
    if x.get("status")!="BRANCH_COMMIT_CREATED" or x.get("repository")!=TARGET_REPO or x.get("base_ref")!=TARGET_REF or x.get("base_sha")!=warrant["expected_base_sha"] or x.get("branch")!=warrant["new_branch"] or x.get("file_count")!=5: raise RuntimeError("apply receipt result mismatch")
    sha=x.get("commit_sha")
    if not isinstance(sha,str) or len(sha)!=40: raise RuntimeError("apply receipt commit sha invalid")
    return sha

def pr_warrant(package_sha,apply,head_sha,now):
    payload={"repository":TARGET_REPO,"base_ref":TARGET_REF,"base_sha":apply["expected_base_sha"],"head_ref":apply["new_branch"],"head_sha":head_sha,"package_sha256":package_sha}
    op="svdn1-pr-"+canonical_hash(payload)[:20]
    return {"schema":WARRANT_SCHEMA,"operation_id":op,"operation_class":"OPEN_PULL_REQUEST","repository":TARGET_REPO,"base_ref":TARGET_REF,"expected_base_sha":apply["expected_base_sha"],
      "head_ref":apply["new_branch"],"expected_head_sha":head_sha,"title":"Publish authentic governed SV-DN-1 first round",
      "body":f"Exact governed SV-DN-1 persistence package: {package_sha}\n\nNo semantic rewrite; five exact public artifacts only.","draft":False,
      "credential_authority":"TV/TVC","consumer_credential_present":False,"secret_values_present":False,"single_use":True,
      "issued_at":now_iso(now),"expires_at":now_iso(now+timedelta(hours=6)),"nonce":canonical_hash(payload)[:24],"authorization_ref":f"tvc://sv-dn1/{op}",
      "source_package_sha256":package_sha,"authority_effect":"NONE_REQUEST_ONLY_TVC_AUTHORIZATION_REQUIRED"}

def execute(inv:Mapping[str,Any]):
    if any(truthy(os.getenv(x)) for x in HOSTED): raise RuntimeError("hosted environment cannot dispatch authentic repository persistence")
    present=[x for x in FORBIDDEN if truthy(os.getenv(x))]
    if present: raise RuntimeError("credential-bearing environment forbidden: "+",".join(sorted(present)))
    task=inv.get("task") or {}
    if inv.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID or not task.get("claim_id"): raise RuntimeError("task invocation identity mismatch")
    root=resolve(BOUND_ENV,DEFAULT_BOUND); outbox=root/"outbox"; inbox=root/"inbox"; staged=root/"staged"
    pkg=load(resolve(PERSIST_ENV,DEFAULT_PERSIST)/"packages/latest.json",True)
    package_sha,files=validate_package(pkg); now=datetime.now(timezone.utc)
    req_path=staged/"inspection-request.json"
    if req_path.is_file(): req=load(req_path)
    else:
        req=inspect_request(package_sha,now); write_once(req_path,req)
    write_once(outbox/f"{req['request_id']}.json",req)
    ir_path=inbox/f"{req['request_id']}.json"
    if not ir_path.is_file(): raise Pending("TVC repository inspection receipt not yet observed")
    base,inspected=validate_inspection(req,load(ir_path))
    apply=apply_warrant(package_sha,files,base,inspected,now)
    write_once(staged/"apply-warrant.json",apply)
    admission=resolve(ADMISSION_ENV,DEFAULT_ADMISSION)
    if not mutation_admitted(admission): raise Pending("TVC SV-DN-1 repository mutation admission not yet observed (TVC#264)")
    write_once(outbox/f"{apply['operation_id']}.json",apply)
    ar_path=inbox/f"{apply['operation_id']}.json"
    if not ar_path.is_file(): raise Pending("TVC bounded file-set receipt not yet observed")
    head=validate_apply_receipt(apply,load(ar_path))
    pr=pr_warrant(package_sha,apply,head,now); write_once(staged/"pr-warrant.json",pr); write_once(outbox/f"{pr['operation_id']}.json",pr)
    rr_path=inbox/f"{pr['operation_id']}.json"
    if not rr_path.is_file(): raise Pending("TVC pull-request receipt not yet observed")
    rr=load(rr_path)
    if rr.get("schema")!=OP_RECEIPT_SCHEMA or rr.get("operation_id")!=pr["operation_id"] or rr.get("operation_class")!="OPEN_PULL_REQUEST" or rr.get("warrant_sha256")!=canonical_hash(pr): raise RuntimeError("pull-request receipt identity mismatch")
    if rr.get("credential_value_exposed") is not False or rr.get("non_tv_tvc_secret_or_token_used") is not False or rr.get("merge_performed") is not False: raise RuntimeError("pull-request receipt authority mismatch")
    x=rr.get("result") or {}
    if x.get("status")!="PULL_REQUEST_CREATED" or x.get("repository")!=TARGET_REPO or x.get("head_ref")!=pr["head_ref"] or x.get("head_sha")!=head or x.get("base_ref")!=TARGET_REF or x.get("base_sha")!=base: raise RuntimeError("pull-request result mismatch")
    if not isinstance(x.get("number"),int): raise RuntimeError("pull-request number missing")
    receipt={"schema":"stegverse.sv-dn1.repository-persistence-dispatch-receipt/v1","state":"COMPLETE","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED",
      "task_id":TASK_ID,"worker_id":WORKER_ID,"claim_id":task.get("claim_id"),"fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),
      "package_sha256":package_sha,"base_sha":base,"branch":pr["head_ref"],"head_sha":head,"pull_request_number":x["number"],"pull_request_url":x.get("html_url"),
      "credential_used":False,"consumer_credential_present":False,"repository_mutation_performed_by_worker":False,"merge_performed":False,"deployment_performed":False,"authority_effect":"NONE_REQUEST_STAGING_ONLY"}
    write_once(root/"receipts/latest.json",receipt); return receipt

def main():
    try:
        execute(json.loads(input()))
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"COMPLETED","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED","transition_sequence":1,"expected_next_transition":"SV_DN1_REPOSITORY_PERSISTENCE_PR_MERGED","checkpoint_ref":"receipts/latest.json","evidence_refs":["staged/inspection-request.json","staged/apply-warrant.json","staged/pr-warrant.json","receipts/latest.json"],"authority_effect":"NONE_REQUEST_STAGING_ONLY"},sort_keys=True));return 0
    except Pending as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"HANDOFF_READY","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_DISPATCH_PENDING","error":str(e),"blocker":{"dependency_class":"TVC_REPOSITORY_TRANSPORT","problem_statement":str(e),"solution_required":True,"may_remain_blocked":True,"physical_additional_machine_required":False,"third_party_runtime_required":False,"github_platform_required":True,"human_action_required":False},"authority_effect":"NONE"},sort_keys=True));return 0
    except Conflict as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_DISPATCH_CONFLICT","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
    except Exception as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"SV_DN1_REPOSITORY_PERSISTENCE_DISPATCH_BLOCKED","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
if __name__=="__main__": raise SystemExit(main())
