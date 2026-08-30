#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os
from pathlib import Path
import sys,tempfile
from typing import Any,Mapping

TASK_ID="BOOTSTRAP-V1-RELEASE-CANDIDATE-FREEZE-001"
WORKER_ID="bootstrap-v1-release-candidate-freeze-worker"
SOURCE_FREEZE_ENV="STEGVERSE_BOOTSTRAP_V1_SOURCE_IDENTITY_FREEZE_STATE_ROOT"
BOUND_ENV="STEGVERSE_BOUND_STATE_ROOT"
DEFAULT_SOURCE_FREEZE=Path.home()/".stegverse"/"state"/"bootstrap-v1-source-identity-freeze"
DEFAULT_BOUND=Path.home()/".stegverse"/"state"/"bootstrap-v1-release-candidate-freeze"
CANDIDATE_VERSION="1.0.0-rc.1"
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","HF_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","OAUTH_TOKEN")

class UpstreamPending(RuntimeError): pass
class FrozenCandidateConflict(RuntimeError): pass

def truthy(v:str|None)->bool:return str(v or "").strip().lower() not in {"","0","false","no"}
def canonical_bytes(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def digest(v:Any)->str:return hashlib.sha256(canonical_bytes(v)).hexdigest()

def load(path:Path,pending=False)->dict[str,Any]:
    if not path.is_file():
        if pending: raise UpstreamPending(f"required upstream object not present: {path}")
        raise RuntimeError(f"required JSON missing: {path}")
    v=json.loads(path.read_text())
    if not isinstance(v,dict):raise RuntimeError(f"expected JSON object: {path}")
    return v

def atomic_json(path:Path,v:Mapping[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(dict(v),h,indent=2,sort_keys=True);h.write("\n")
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def upstream_root()->Path:return Path(os.environ.get(SOURCE_FREEZE_ENV,str(DEFAULT_SOURCE_FREEZE))).expanduser().resolve()
def bound_root()->Path:return Path(os.environ.get(BOUND_ENV,str(DEFAULT_BOUND))).expanduser().resolve()

def validate_upstream(catalog:Mapping[str,Any],receipt:Mapping[str,Any])->None:
    if catalog.get("schema")!="stegverse.bootstrap.source-catalog/v1" or catalog.get("catalog_version")!="1.0.0" or catalog.get("state")!="FROZEN":
        raise UpstreamPending("frozen Bootstrap v1 source catalog is required")
    if catalog.get("source_identity_scheme")!="sha256-content-manifest" or catalog.get("component_count")!=4:
        raise RuntimeError("source catalog identity/count drift")
    comps=catalog.get("components")
    if not isinstance(comps,list) or len(comps)!=4:raise RuntimeError("source catalog components invalid")
    for row in comps:
        if not isinstance(row,dict):raise RuntimeError("source catalog component row invalid")
        ident=row.get("source_identity")
        if not isinstance(ident,str) or len(ident)!=71 or not ident.startswith("sha256:"):raise RuntimeError("source catalog identity invalid")
    if catalog.get("github_platform_required") is not False or catalog.get("specific_external_platform_required") is not False or catalog.get("network_locator_required") is not False:
        raise RuntimeError("source catalog retains platform/locator dependency")
    if receipt.get("schema")!="stegverse.bootstrap.source-identity-freeze-receipt/v1" or receipt.get("state")!="COMPLETE" or receipt.get("transition_id")!="BOOTSTRAP_V1_SOURCE_IDENTITIES_FROZEN":
        raise UpstreamPending("source identity freeze receipt is not COMPLETE")
    if receipt.get("catalog_sha256")!=digest(catalog):raise RuntimeError("source freeze receipt/catalog digest mismatch")
    if receipt.get("source_identity_set_sha256")!=catalog.get("source_identity_set_sha256"):raise RuntimeError("source identity set digest mismatch")
    if receipt.get("github_platform_required") is not False or receipt.get("network_access_performed") is not False:raise RuntimeError("source freeze receipt retains platform/network dependency")

def build_candidate(catalog:Mapping[str,Any],freeze_receipt:Mapping[str,Any])->dict[str,Any]:
    body={
      "schema":"stegverse.bootstrap.release-candidate/v1",
      "candidate_version":CANDIDATE_VERSION,
      "state":"FROZEN",
      "source_identity_scheme":"sha256-content-manifest",
      "source_catalog":{"schema":"stegverse.bootstrap.source-catalog/v1","version":"1.0.0","sha256":digest(catalog),"source_identity_set_sha256":catalog["source_identity_set_sha256"]},
      "source_package_contract":{"schema":"stegverse.source-package/v1","version":"1.0.0"},
      "device_materialization_contract":{"evidence_schema":"stegverse.device-node-source-package-bootstrap-evidence/v1","required_state":"MATERIALIZED_UNADMITTED","execution_authority_before_admission":"NONE"},
      "source_freeze_receipt_sha256":digest(freeze_receipt),
      "github_platform_required":False,
      "specific_external_platform_required":False,
      "network_locator_required":False,
      "transport_implementation_required":False,
      "credential_required":False,
      "package_integrity_confers_execution_authority":False,
      "release_activated":False,
      "publication_performed":False,
      "execution_authority":"NONE",
      "authority_effect":"NONE_RELEASE_CANDIDATE_FREEZE_ONLY",
    }
    return {**body,"candidate_identity":"sha256:"+digest(body)}

def execute(invocation:Mapping[str,Any])->dict[str,Any]:
    if any(truthy(os.getenv(x)) for x in HOSTED):raise RuntimeError("hosted environment cannot freeze sovereign Bootstrap v1 release candidate")
    present=[x for x in FORBIDDEN if truthy(os.getenv(x))]
    if present:raise RuntimeError("credential-bearing environment forbidden: "+",".join(sorted(present)))
    if invocation.get("schema")!="stegverse.worker-invocation/v0.1":raise RuntimeError("worker invocation schema mismatch")
    task=invocation.get("task") or {}
    if task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID or not task.get("claim_id"):raise RuntimeError("task/worker/claim identity mismatch")
    up=upstream_root();catalog=load(up/"catalog"/"bootstrap-v1-source-catalog.json",pending=True);freeze=load(up/"receipts"/"latest.json",pending=True)
    validate_upstream(catalog,freeze);candidate=build_candidate(catalog,freeze)
    bound=bound_root();path=bound/"candidate"/"bootstrap-v1-1.0.0-rc.1.json"
    if path.is_file():
        if load(path)!=candidate:raise FrozenCandidateConflict("FROZEN_BOOTSTRAP_V1_RC1_CONFLICT")
    else:atomic_json(path,candidate)
    receipt={
      "schema":"stegverse.bootstrap.release-candidate-freeze-receipt/v1","task_id":TASK_ID,"worker_id":WORKER_ID,
      "state":"COMPLETE","transition_id":"BOOTSTRAP_V1_RELEASE_CANDIDATE_FROZEN","claim_id":task.get("claim_id"),
      "fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),"candidate_version":CANDIDATE_VERSION,
      "candidate_identity":candidate["candidate_identity"],"candidate_sha256":digest(candidate),"source_catalog_sha256":candidate["source_catalog"]["sha256"],
      "source_identity_set_sha256":candidate["source_catalog"]["source_identity_set_sha256"],"github_platform_required":False,
      "network_access_performed":False,"credential_used":False,"repository_writeback_performed":False,"release_activated":False,
      "publication_performed":False,"execution_authority":"NONE","authority_effect":"NONE_RELEASE_CANDIDATE_FREEZE_ONLY"
    }
    atomic_json(bound/"receipts"/"latest.json",receipt);return receipt

def main()->int:
    try:
      inv=json.loads(sys.stdin.readline());r=execute(inv);print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"COMPLETED","transition_id":"BOOTSTRAP_V1_RELEASE_CANDIDATE_FROZEN","transition_sequence":1,"expected_next_transition":"BOOTSTRAP_V1_DISTRIBUTION_MATERIALIZATION_PROVEN","checkpoint_ref":"receipts/latest.json","evidence_refs":["candidate/bootstrap-v1-1.0.0-rc.1.json","receipts/latest.json"],"candidate_identity":r["candidate_identity"],"github_platform_required":False,"authority_effect":"NONE_RELEASE_CANDIDATE_FREEZE_ONLY"},sort_keys=True));return 0
    except UpstreamPending as e:
      print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"HANDOFF_READY","transition_id":"BOOTSTRAP_V1_SOURCE_IDENTITY_FREEZE_PENDING","transition_sequence":1,"expected_next_transition":"BOOTSTRAP_V1_RELEASE_CANDIDATE_FROZEN","error":str(e),"github_platform_required":False,"blocker":{"dependency_class":"SOURCE_IDENTITY_FREEZE","problem_statement":str(e),"solution_required":True,"may_remain_blocked":False,"next_solution_action":"Wait for the machine-owned source identity freeze; do not substitute repository or platform coordinates.","machine_observable_release_condition":"frozen source catalog and matching source-identity-freeze receipt exist","physical_additional_machine_required":False,"third_party_runtime_required":False,"github_platform_required":False,"human_action_required":False}},sort_keys=True));return 0
    except FrozenCandidateConflict as e:
      print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"BOOTSTRAP_V1_RC1_FROZEN_CONFLICT","error":str(e),"github_platform_required":False,"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
    except Exception as e:
      print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"BOOTSTRAP_V1_RELEASE_CANDIDATE_FREEZE_BLOCKED","error":str(e),"github_platform_required":False,"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
