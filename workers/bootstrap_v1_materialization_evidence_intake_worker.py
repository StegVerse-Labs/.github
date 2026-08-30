#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,sys,tempfile
from pathlib import Path
from typing import Any,Mapping

TASK_ID="BOOTSTRAP-V1-MATERIALIZATION-EVIDENCE-INTAKE-001"
WORKER_ID="bootstrap-v1-materialization-evidence-intake-worker"
COMPONENTS=("stegverse.sdk","stegverse.stegcore","stegverse.core-lite","stegverse.master-records")
RC_ENV="STEGVERSE_BOOTSTRAP_V1_RELEASE_CANDIDATE_STATE_ROOT"
BUNDLE_ENV="STEGVERSE_BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_STATE_ROOT"
EVIDENCE_ENV="STEGVERSE_BOOTSTRAP_V1_DEVICE_EVIDENCE"
BOUND_ENV="STEGVERSE_BOUND_STATE_ROOT"
DEFAULT_RC=Path.home()/".stegverse"/"state"/"bootstrap-v1-release-candidate-freeze"
DEFAULT_BUNDLE=Path.home()/".stegverse"/"state"/"bootstrap-v1-distributable-bundle"
DEFAULT_BOUND=Path.home()/".stegverse"/"state"/"bootstrap-v1-materialization-evidence-intake"
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","HF_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","OAUTH_TOKEN")

class InputPending(RuntimeError): pass
class ProofConflict(RuntimeError): pass

def truthy(v:str|None)->bool:return str(v or "").strip().lower() not in {"","0","false","no"}
def canonical(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
def digest(v:Any)->str:return hashlib.sha256(canonical(v)).hexdigest()
def load(path:Path,pending=False)->dict[str,Any]:
    if not path.is_file():
        if pending:raise InputPending(f"required local object not present: {path}")
        raise RuntimeError(f"required JSON missing: {path}")
    v=json.loads(path.read_text(encoding="utf-8"))
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
    if c.get("schema")!="stegverse.bootstrap.release-candidate/v1" or c.get("candidate_version")!="1.0.0-rc.1" or c.get("state")!="FROZEN":raise InputPending("frozen Bootstrap v1 rc.1 candidate required")
    if c.get("candidate_identity")!="sha256:"+digest(candidate_body(c)):raise RuntimeError("candidate identity mismatch")
    if c.get("release_activated") is not False or c.get("publication_performed") is not False or c.get("execution_authority")!="NONE":raise RuntimeError("candidate authority state invalid")

def validate_bundle(b:Mapping[str,Any],candidate:Mapping[str,Any])->dict[str,str]:
    if b.get("schema")!="stegverse.bootstrap.bundle/v1" or b.get("bundle_version")!="1.0.0-rc.1" or b.get("state")!="BUILT":raise InputPending("canonical Bootstrap v1 bundle required")
    if b.get("bundle_identity")!="sha256:"+digest(bundle_body(b)):raise RuntimeError("bundle identity mismatch")
    if b.get("component_count")!=4 or b.get("component_order")!=list(COMPONENTS):raise RuntimeError("bundle component order/count mismatch")
    if b.get("release_candidate")!=candidate:raise RuntimeError("bundle/candidate object mismatch")
    if b.get("github_platform_required") is not False or b.get("specific_external_platform_required") is not False or b.get("network_locator_required") is not False or b.get("credential_required") is not False:raise RuntimeError("bundle platform/credential boundary invalid")
    if b.get("release_activated") is not False or b.get("publication_performed") is not False or b.get("execution_authority")!="NONE":raise RuntimeError("bundle authority state invalid")
    packages=b.get("packages");catalog=b.get("source_catalog") or {}
    if not isinstance(packages,list) or len(packages)!=4 or catalog.get("source_identity_set_sha256") is None:raise RuntimeError("bundle packages/catalog missing")
    ids={}
    for i,c in enumerate(COMPONENTS):
        p=packages[i]
        if not isinstance(p,dict) or p.get("component_id")!=c:raise RuntimeError("bundle package component order mismatch")
        ident=p.get("source_identity")
        if not isinstance(ident,str) or not ident.startswith("sha256:") or len(ident)!=71:raise RuntimeError("bundle source identity invalid")
        ids[c]=ident
    return ids

def replay(rows:list[Any])->dict[str,Any]:
    prev=None
    for i,row in enumerate(rows,1):
        if not isinstance(row,dict) or row.get("schema")!="stegos.web_bootstrap_journal_entry.v1" or row.get("sequence")!=i or row.get("previous_entry_sha256")!=prev:raise RuntimeError(f"journal chain mismatch at sequence {i}")
        receipt=row.get("receipt")
        rh=digest(receipt)
        if row.get("receipt_sha256")!=rh:raise RuntimeError(f"journal receipt hash mismatch at sequence {i}")
        body={"schema":row["schema"],"sequence":row["sequence"],"previous_entry_sha256":row["previous_entry_sha256"],"receipt":receipt,"receipt_sha256":rh}
        eh=digest(body)
        if row.get("entry_sha256")!=eh:raise RuntimeError(f"journal entry hash mismatch at sequence {i}")
        prev=eh
    return {"state":"PASS","entries":len(rows),"tail_sha256":prev}

def validate_materialization_entry(entry:Mapping[str,Any],node:str,device:str,component:str,identity:str)->None:
    r=entry.get("receipt") if isinstance(entry,dict) else None
    if not isinstance(r,dict) or r.get("schema")!="stegos.web_source_package_materialization_receipt.v1":raise RuntimeError(f"{component}: package materialization receipt missing")
    if r.get("node_id")!=node or r.get("device_continuity_id")!=device or r.get("component_id")!=component or r.get("source_identity")!=identity:raise RuntimeError(f"{component}: package materialization identity mismatch")
    required={"materialization_state":"MATERIALIZED","admission_state":"UNADMITTED","execution_authority":"NONE","credential_material_observed":False,"github_platform_required":False,"specific_external_platform_required":False,"new_node_identity_minted":False,"authority_effect":"NONE_SOURCE_MATERIALIZATION_ONLY"}
    for k,v in required.items():
        if r.get(k)!=v:raise RuntimeError(f"{component}: package receipt {k} mismatch")

def validate_evidence(e:Mapping[str,Any],candidate:Mapping[str,Any],bundle:Mapping[str,Any],ids:Mapping[str,str])->dict[str,Any]:
    if e.get("schema")!="stegverse.device-node-bootstrap-bundle-evidence/v1" or e.get("state")!="MATERIALIZED_UNADMITTED":raise RuntimeError("device bundle evidence schema/state mismatch")
    node=e.get("node_id");device=e.get("device_continuity_id")
    if not isinstance(node,str) or not node or not isinstance(device,str) or not device:raise RuntimeError("established node/device identity missing")
    if e.get("continuity_source") not in {"LIVE_EXISTING_WEB_BOOTSTRAP","VERIFIED_IMPORTED_WEB_BOOTSTRAP_EVIDENCE"}:raise RuntimeError("continuity source not established/replayed")
    if e.get("bundle_identity")!=bundle.get("bundle_identity") or e.get("candidate_identity")!=candidate.get("candidate_identity"):raise RuntimeError("evidence bundle/candidate binding mismatch")
    catalog=bundle.get("source_catalog") or {}
    if e.get("source_identity_set_sha256")!=catalog.get("source_identity_set_sha256"):raise RuntimeError("evidence source identity-set mismatch")
    if e.get("component_count")!=4 or e.get("component_order")!=list(COMPONENTS):raise RuntimeError("evidence component order/count mismatch")
    expected=[{"component_id":c,"source_identity":ids[c]} for c in COMPONENTS]
    if e.get("component_identities")!=expected:raise RuntimeError("evidence component identities mismatch")
    required={"all_components_materialized":True,"admission_state":"UNADMITTED","credential_material_observed":False,"github_platform_required":False,"specific_external_platform_required":False,"new_node_identity_minted":False,"release_activated":False,"publication_performed":False,"execution_authority":"NONE","authority_effect":"NONE"}
    for k,v in required.items():
        if e.get(k)!=v:raise RuntimeError(f"evidence {k} mismatch")
    entries=e.get("package_materialization_entries")
    if not isinstance(entries,list) or len(entries)!=4:raise RuntimeError("exactly four package materialization entries required")
    for i,c in enumerate(COMPONENTS):validate_materialization_entry(entries[i],node,device,c,ids[c])
    agg=e.get("bundle_materialization_entry");r=agg.get("receipt") if isinstance(agg,dict) else None
    if not isinstance(r,dict) or r.get("schema")!="stegos.web_bootstrap_bundle_materialization_receipt.v1":raise RuntimeError("aggregate bundle materialization receipt missing")
    if r.get("node_id")!=node or r.get("device_continuity_id")!=device or r.get("bundle_identity")!=bundle.get("bundle_identity") or r.get("candidate_identity")!=candidate.get("candidate_identity"):raise RuntimeError("aggregate receipt identity mismatch")
    if r.get("source_identity_set_sha256")!=catalog.get("source_identity_set_sha256") or r.get("component_order")!=list(COMPONENTS) or r.get("component_identities")!=expected or r.get("component_count")!=4:raise RuntimeError("aggregate receipt component binding mismatch")
    for k,v in {"all_components_materialized":True,"bundle_state":"MATERIALIZED_UNADMITTED","admission_state":"UNADMITTED","execution_authority":"NONE","release_activated":False,"publication_performed":False,"github_platform_required":False,"specific_external_platform_required":False,"new_node_identity_minted":False,"authority_effect":"NONE_BUNDLE_MATERIALIZATION_ONLY"}.items():
        if r.get(k)!=v:raise RuntimeError(f"aggregate receipt {k} mismatch")
    rows=e.get("continued_receipts")
    if not isinstance(rows,list) or len(rows)<5:raise RuntimeError("continued receipt journal missing")
    rep=replay(rows);decl=e.get("journal_replay")
    if not isinstance(decl,dict) or decl.get("state")!="PASS" or decl.get("entries")!=rep["entries"] or decl.get("tail_sha256")!=rep["tail_sha256"]:raise RuntimeError("declared journal replay mismatch")
    if entries!=rows[-5:-1] or agg!=rows[-1]:raise RuntimeError("materialization entries are not the terminal journal suffix")
    pre_materialization=rows[:-5]
    binding_ok=any(
        isinstance(row,dict)
        and isinstance(row.get("receipt"),dict)
        and row["receipt"].get("schema")=="stegos.web_device_node_binding_receipt.v1"
        and row["receipt"].get("node_id")==node
        and row["receipt"].get("device_continuity_id")==device
        for row in pre_materialization
    )
    if not binding_ok:raise RuntimeError("established node/device binding receipt missing")
    return {"node_id":node,"device_continuity_id":device,"journal_tail":rep["tail_sha256"],"journal_entries":rep["entries"]}

def execute(inv:Mapping[str,Any])->dict[str,Any]:
    if any(truthy(os.getenv(x)) for x in HOSTED):raise RuntimeError("hosted environment cannot validate authentic Bootstrap materialization evidence")
    present=[x for x in FORBIDDEN if truthy(os.getenv(x))]
    if present:raise RuntimeError("credential-bearing environment forbidden: "+",".join(sorted(present)))
    task=inv.get("task") or {}
    if inv.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID or not task.get("claim_id"):raise RuntimeError("task invocation identity mismatch")
    rc=Path(os.environ.get(RC_ENV,str(DEFAULT_RC))).expanduser().resolve()/"candidate"/"bootstrap-v1-1.0.0-rc.1.json"
    bp=Path(os.environ.get(BUNDLE_ENV,str(DEFAULT_BUNDLE))).expanduser().resolve()/"bundle"/"bootstrap-v1-1.0.0-rc.1.bundle.json"
    ep_raw=os.environ.get(EVIDENCE_ENV,"").strip()
    if not ep_raw:raise InputPending(f"{EVIDENCE_ENV} is not set")
    ep=Path(ep_raw).expanduser().resolve()
    candidate=load(rc,pending=True);bundle=load(bp,pending=True);evidence=load(ep,pending=True)
    validate_candidate(candidate);ids=validate_bundle(bundle,candidate);obs=validate_evidence(evidence,candidate,bundle,ids)
    proof={"schema":"stegverse.bootstrap.materialization-proof/v1","task_id":TASK_ID,"worker_id":WORKER_ID,"state":"COMPLETE","transition_id":"BOOTSTRAP_V1_DISTRIBUTION_MATERIALIZATION_PROVEN","claim_id":task.get("claim_id"),"fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),"candidate_identity":candidate["candidate_identity"],"bundle_identity":bundle["bundle_identity"],"source_identity_set_sha256":bundle["source_catalog"]["source_identity_set_sha256"],"component_order":list(COMPONENTS),"component_identities":[{"component_id":c,"source_identity":ids[c]} for c in COMPONENTS],"node_id":obs["node_id"],"device_continuity_id":obs["device_continuity_id"],"journal_entries":obs["journal_entries"],"journal_tail_sha256":obs["journal_tail"],"device_evidence_sha256":digest(evidence),"materialization_state":"MATERIALIZED_UNADMITTED","execution_authority":"NONE","release_activated":False,"publication_performed":False,"network_access_performed":False,"credential_used":False,"github_platform_required":False,"repository_writeback_performed":False,"authority_effect":"NONE_EVIDENCE_VALIDATION_ONLY"}
    bound=Path(os.environ.get(BOUND_ENV,str(DEFAULT_BOUND))).expanduser().resolve();out=bound/"receipts"/"latest.json"
    if out.is_file() and load(out)!=proof:raise ProofConflict("FROZEN_BOOTSTRAP_V1_MATERIALIZATION_PROOF_CONFLICT")
    if not out.is_file():atomic(out,proof)
    return proof

def main()->int:
    try:
        inv=json.loads(sys.stdin.readline());p=execute(inv);print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"COMPLETED","transition_id":"BOOTSTRAP_V1_DISTRIBUTION_MATERIALIZATION_PROVEN","transition_sequence":1,"expected_next_transition":"BOOTSTRAP_V1_RELEASE_GATE_EVALUATION","checkpoint_ref":"receipts/latest.json","evidence_refs":["receipts/latest.json"],"bundle_identity":p["bundle_identity"],"node_id":p["node_id"],"authority_effect":"NONE_EVIDENCE_VALIDATION_ONLY"},sort_keys=True));return 0
    except InputPending as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"HANDOFF_READY","transition_id":"BOOTSTRAP_V1_MATERIALIZATION_EVIDENCE_PENDING","transition_sequence":1,"expected_next_transition":"BOOTSTRAP_V1_DISTRIBUTION_MATERIALIZATION_PROVEN","error":str(e),"blocker":{"dependency_class":"AUTHENTIC_DEVICE_BUNDLE_EVIDENCE","problem_statement":str(e),"solution_required":True,"may_remain_blocked":False,"next_solution_action":"Supply the authentic established-node Bootstrap v1 bundle evidence after the canonical frozen bundle exists.","machine_observable_release_condition":"exact frozen candidate + bundle + valid device bundle evidence are locally present","physical_additional_machine_required":False,"third_party_runtime_required":False,"github_platform_required":False,"human_action_required":False},"authority_effect":"NONE"},sort_keys=True));return 0
    except ProofConflict as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"BOOTSTRAP_V1_MATERIALIZATION_PROOF_CONFLICT","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
    except Exception as e:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"BOOTSTRAP_V1_MATERIALIZATION_EVIDENCE_BLOCKED","error":str(e),"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())