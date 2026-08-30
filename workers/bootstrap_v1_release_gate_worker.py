#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,sys,tempfile
from pathlib import Path
from typing import Any,Mapping

TASK_ID="BOOTSTRAP-V1-RELEASE-GATE-001"
WORKER_ID="bootstrap-v1-release-gate-worker"
COMPONENTS=("stegverse.sdk","stegverse.stegcore","stegverse.core-lite","stegverse.master-records")
RC_ENV="STEGVERSE_BOOTSTRAP_V1_RELEASE_CANDIDATE_STATE_ROOT"
BUNDLE_ENV="STEGVERSE_BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_STATE_ROOT"
PROOF_ENV="STEGVERSE_BOOTSTRAP_V1_MATERIALIZATION_PROOF"
BOUND_ENV="STEGVERSE_BOUND_STATE_ROOT"
DEFAULT_RC=Path.home()/".stegverse"/"state"/"bootstrap-v1-release-candidate-freeze"
DEFAULT_BUNDLE=Path.home()/".stegverse"/"state"/"bootstrap-v1-distributable-bundle"
DEFAULT_PROOF=Path.home()/".stegverse"/"state"/"bootstrap-v1-materialization-evidence-intake"/"receipts"/"latest.json"
DEFAULT_BOUND=Path.home()/".stegverse"/"state"/"bootstrap-v1-release-gate"
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","HF_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","OAUTH_TOKEN")

class Pending(RuntimeError): pass
class Conflict(RuntimeError): pass

def truthy(v:str|None)->bool:return str(v or "").strip().lower() not in {"","0","false","no"}
def canonical(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def digest(v:Any)->str:return hashlib.sha256(canonical(v)).hexdigest()
def load(path:Path,pending=False)->dict[str,Any]:
    if not path.is_file():
        if pending:raise Pending(f"required local object not present: {path}")
        raise RuntimeError(f"required JSON missing: {path}")
    v=json.loads(path.read_text())
    if not isinstance(v,dict):raise RuntimeError(f"expected JSON object: {path}")
    return v
def atomic(path:Path,v:Mapping[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(dict(v),h,indent=2,sort_keys=True);h.write("\n")
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def candidate_body(v:Mapping[str,Any])->dict[str,Any]:return {k:x for k,x in v.items() if k!="candidate_identity"}
def bundle_body(v:Mapping[str,Any])->dict[str,Any]:return {k:x for k,x in v.items() if k!="bundle_identity"}

def validate_candidate(c:Mapping[str,Any])->None:
    if c.get("schema")!="stegverse.bootstrap.release-candidate/v1" or c.get("candidate_version")!="1.0.0-rc.1" or c.get("state")!="FROZEN":raise Pending("frozen Bootstrap v1 rc.1 candidate required")
    if c.get("candidate_identity")!="sha256:"+digest(candidate_body(c)):raise RuntimeError("candidate identity mismatch")
    if c.get("release_activated") is not False or c.get("publication_performed") is not False or c.get("execution_authority")!="NONE":raise RuntimeError("candidate authority state invalid")

def validate_bundle(b:Mapping[str,Any],c:Mapping[str,Any])->list[dict[str,str]]:
    if b.get("schema")!="stegverse.bootstrap.bundle/v1" or b.get("bundle_version")!="1.0.0-rc.1" or b.get("state")!="BUILT":raise Pending("canonical Bootstrap v1 bundle required")
    if b.get("bundle_identity")!="sha256:"+digest(bundle_body(b)):raise RuntimeError("bundle identity mismatch")
    if b.get("release_candidate")!=c or b.get("component_count")!=4 or b.get("component_order")!=list(COMPONENTS):raise RuntimeError("bundle candidate/component binding mismatch")
    if any(b.get(k) is not False for k in ("github_platform_required","specific_external_platform_required","network_locator_required","credential_required","release_activated","publication_performed")) or b.get("execution_authority")!="NONE":raise RuntimeError("bundle authority boundary invalid")
    packages=b.get("packages")
    if not isinstance(packages,list) or len(packages)!=4:raise RuntimeError("bundle packages missing")
    out=[]
    for i,component in enumerate(COMPONENTS):
        p=packages[i]
        if not isinstance(p,dict) or p.get("component_id")!=component:raise RuntimeError("bundle package order mismatch")
        ident=p.get("source_identity")
        if not isinstance(ident,str) or not ident.startswith("sha256:") or len(ident)!=71:raise RuntimeError("bundle source identity invalid")
        out.append({"component_id":component,"source_identity":ident})
    return out

def validate_proof(p:Mapping[str,Any],c:Mapping[str,Any],b:Mapping[str,Any],ids:list[dict[str,str]])->None:
    if p.get("schema")!="stegverse.bootstrap.materialization-proof/v1" or p.get("state")!="COMPLETE" or p.get("transition_id")!="BOOTSTRAP_V1_DISTRIBUTION_MATERIALIZATION_PROVEN":raise Pending("terminal Bootstrap v1 materialization proof required")
    if p.get("candidate_identity")!=c.get("candidate_identity") or p.get("bundle_identity")!=b.get("bundle_identity"):raise RuntimeError("proof candidate/bundle binding mismatch")
    if p.get("component_order")!=list(COMPONENTS) or p.get("component_identities")!=ids:raise RuntimeError("proof component identity mismatch")
    if p.get("source_identity_set_sha256")!=(b.get("source_catalog") or {}).get("source_identity_set_sha256"):raise RuntimeError("proof source identity-set mismatch")
    required={"materialization_state":"MATERIALIZED_UNADMITTED","execution_authority":"NONE","release_activated":False,"publication_performed":False,"network_access_performed":False,"credential_used":False,"github_platform_required":False,"repository_writeback_performed":False,"authority_effect":"NONE_EVIDENCE_VALIDATION_ONLY"}
    for k,v in required.items():
        if p.get(k)!=v:raise RuntimeError(f"proof {k} mismatch")
    for k in ("node_id","device_continuity_id","journal_tail_sha256","device_evidence_sha256"):
        if not isinstance(p.get(k),str) or not p.get(k):raise RuntimeError(f"proof {k} missing")

def execute(inv:Mapping[str,Any])->dict[str,Any]:
    if any(truthy(os.getenv(x)) for x in HOSTED):raise RuntimeError("hosted environment cannot authorize Bootstrap release")
    present=[x for x in FORBIDDEN if truthy(os.getenv(x))]
    if present:raise RuntimeError("credential-bearing environment forbidden: "+",".join(sorted(present)))
    task=inv.get("task") or {}
    if inv.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID or not task.get("claim_id"):raise RuntimeError("task invocation identity mismatch")
    rc=Path(os.environ.get(RC_ENV,str(DEFAULT_RC))).expanduser().resolve()/"candidate"/"bootstrap-v1-1.0.0-rc.1.json"
    bp=Path(os.environ.get(BUNDLE_ENV,str(DEFAULT_BUNDLE))).expanduser().resolve()/"bundle"/"bootstrap-v1-1.0.0-rc.1.bundle.json"
    pp=Path(os.environ.get(PROOF_ENV,str(DEFAULT_PROOF))).expanduser().resolve()
    c=load(rc,True);b=load(bp,True);p=load(pp,True)
    validate_candidate(c);ids=validate_bundle(b,c);validate_proof(p,c,b,ids)
    auth={"schema":"stegverse.bootstrap.release-authorization/v1","task_id":TASK_ID,"worker_id":WORKER_ID,"state":"AUTHORIZED","transition_id":"BOOTSTRAP_V1_RELEASE_AUTHORIZED","claim_id":task.get("claim_id"),"fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),"candidate_version":"1.0.0-rc.1","candidate_identity":c["candidate_identity"],"bundle_identity":b["bundle_identity"],"source_identity_set_sha256":b["source_catalog"]["source_identity_set_sha256"],"component_order":list(COMPONENTS),"component_identities":ids,"materialization_proof_sha256":digest(p),"node_id":p["node_id"],"device_continuity_id":p["device_continuity_id"],"release_candidate_distribution_authorized":True,"repository_writeback_authority":False,"tag_mutation_authority":False,"publication_authority":False,"sdk_admission_authority":False,"execution_authority":"NONE","credential_used":False,"network_access_performed":False,"github_platform_required":False,"authority_effect":"NONE_RELEASE_GATE_EVALUATION_ONLY"}
    out=Path(os.environ.get(BOUND_ENV,str(DEFAULT_BOUND))).expanduser().resolve()/"receipts"/"latest.json"
    if out.is_file() and load(out)!=auth:raise Conflict("FROZEN_BOOTSTRAP_V1_RELEASE_AUTHORIZATION_CONFLICT")
    if not out.is_file():atomic(out,auth)
    return auth

def main()->int:
    try:
        inv=json.loads(sys.stdin.readline());a=execute(inv);print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"COMPLETED","transition_id":"BOOTSTRAP_V1_RELEASE_AUTHORIZED","transition_sequence":1,"expected_next_transition":"BOOTSTRAP_V1_RC1_RELEASE_PUBLICATION","checkpoint_ref":"receipts/latest.json","evidence_refs":["receipts/latest.json"],"candidate_identity":a["candidate_identity"],"bundle_identity":a["bundle_identity"],"authority_effect":"NONE_RELEASE_GATE_EVALUATION_ONLY"},sort_keys=True));return 0
    except Pending as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"HANDOFF_READY","transition_id":"BOOTSTRAP_V1_RELEASE_GATE_PENDING","transition_sequence":1,"expected_next_transition":"BOOTSTRAP_V1_RELEASE_AUTHORIZED","error":str(e),"blocker":{"dependency_class":"AUTHENTIC_BOOTSTRAP_V1_RELEASE_INPUT","problem_statement":str(e),"solution_required":True,"may_remain_blocked":False,"next_solution_action":"Wait for exact frozen rc.1 candidate, distributable bundle, and authentic materialization proof in local StegVerse state.","machine_observable_release_condition":"all three exact local immutable inputs are present and valid","physical_additional_machine_required":False,"third_party_runtime_required":False,"github_platform_required":False,"human_action_required":False},"authority_effect":"NONE"},sort_keys=True));return 0
    except Conflict as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"BOOTSTRAP_V1_RELEASE_AUTHORIZATION_CONFLICT","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
    except Exception as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"BOOTSTRAP_V1_RELEASE_GATE_BLOCKED","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
