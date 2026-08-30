#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,json,os
from pathlib import Path,PurePosixPath
import sys,tempfile
from typing import Any,Mapping

TASK_ID="BOOTSTRAP-V1-DISTRIBUTABLE-BUNDLE-001"
WORKER_ID="bootstrap-v1-distributable-bundle-worker"
RC_ENV="STEGVERSE_BOOTSTRAP_V1_RELEASE_CANDIDATE_STATE_ROOT"
FREEZE_ENV="STEGVERSE_BOOTSTRAP_V1_SOURCE_IDENTITY_FREEZE_STATE_ROOT"
PACKAGE_ENV="STEGVERSE_SOURCE_PACKAGE_ROOT"
BOUND_ENV="STEGVERSE_BOUND_STATE_ROOT"
DEFAULT_RC=Path.home()/".stegverse"/"state"/"bootstrap-v1-release-candidate-freeze"
DEFAULT_FREEZE=Path.home()/".stegverse"/"state"/"bootstrap-v1-source-identity-freeze"
DEFAULT_PACKAGES=Path.home()/".stegverse"/"packages"/"source"/"v1"
DEFAULT_BOUND=Path.home()/".stegverse"/"state"/"bootstrap-v1-distributable-bundle"
COMPONENTS=("stegverse.sdk","stegverse.stegcore","stegverse.core-lite","stegverse.master-records")
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN","HF_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","OAUTH_TOKEN")

class UpstreamPending(RuntimeError):pass
class BundleConflict(RuntimeError):pass

def truthy(v:str|None)->bool:return str(v or "").strip().lower() not in {"","0","false","no"}
def canonical_bytes(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def digest(v:Any)->str:return hashlib.sha256(canonical_bytes(v)).hexdigest()
def bytes_digest(v:bytes)->str:return hashlib.sha256(v).hexdigest()
def slug(c:str)->str:return c.lower().replace("/","--").replace("_","-").replace(".","-")

def load(path:Path,pending=False)->dict[str,Any]:
    if not path.is_file():
        if pending:raise UpstreamPending(f"required local object not present: {path}")
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

def root(env:str,default:Path)->Path:return Path(os.environ.get(env,str(default))).expanduser().resolve()

def candidate_body(candidate:Mapping[str,Any])->dict[str,Any]:
    return {k:v for k,v in candidate.items() if k!="candidate_identity"}

def validate_candidate(candidate:Mapping[str,Any],catalog:Mapping[str,Any])->None:
    if candidate.get("schema")!="stegverse.bootstrap.release-candidate/v1" or candidate.get("candidate_version")!="1.0.0-rc.1" or candidate.get("state")!="FROZEN":
        raise UpstreamPending("frozen Bootstrap v1 rc.1 candidate required")
    if candidate.get("candidate_identity")!="sha256:"+digest(candidate_body(candidate)):raise RuntimeError("candidate identity mismatch")
    if candidate.get("release_activated") is not False or candidate.get("publication_performed") is not False or candidate.get("execution_authority")!="NONE":
        raise RuntimeError("candidate authority state invalid")
    if candidate.get("github_platform_required") is not False or candidate.get("specific_external_platform_required") is not False or candidate.get("network_locator_required") is not False:
        raise RuntimeError("candidate retains platform/locator dependency")
    sc=candidate.get("source_catalog") or {}
    if sc.get("sha256")!=digest(catalog) or sc.get("source_identity_set_sha256")!=catalog.get("source_identity_set_sha256"):
        raise RuntimeError("candidate/source catalog binding mismatch")

def validate_catalog(catalog:Mapping[str,Any])->dict[str,str]:
    if catalog.get("schema")!="stegverse.bootstrap.source-catalog/v1" or catalog.get("catalog_version")!="1.0.0" or catalog.get("state")!="FROZEN":
        raise UpstreamPending("frozen source catalog required")
    if catalog.get("source_identity_scheme")!="sha256-content-manifest" or catalog.get("component_count")!=4:raise RuntimeError("catalog identity/count drift")
    if catalog.get("github_platform_required") is not False or catalog.get("specific_external_platform_required") is not False or catalog.get("network_locator_required") is not False:raise RuntimeError("catalog platform dependency")
    rows=catalog.get("components")
    if not isinstance(rows,list) or len(rows)!=4:raise RuntimeError("catalog components invalid")
    out={}
    for row in rows:
        c=row.get("component_id") if isinstance(row,dict) else None;ident=row.get("source_identity") if isinstance(row,dict) else None
        if c not in COMPONENTS or c in out:raise RuntimeError("catalog component identity invalid")
        if not isinstance(ident,str) or len(ident)!=71 or not ident.startswith("sha256:"):raise RuntimeError("catalog source identity invalid")
        out[c]=ident
    if set(out)!=set(COMPONENTS):raise RuntimeError("catalog component set mismatch")
    return out

def validate_package(p:Mapping[str,Any],component:str,expected_identity:str)->None:
    if p.get("schema")!="stegverse.source-package/v1" or p.get("package_version")!="1.0.0" or p.get("component_id")!=component:raise RuntimeError(f"{component}: package contract mismatch")
    if p.get("source_identity")!=expected_identity:raise RuntimeError(f"{component}: source identity mismatch")
    if p.get("credential_material_included") is not False or p.get("authority_effect")!="NONE_SOURCE_TRANSPORT_ONLY":raise RuntimeError(f"{component}: package authority boundary invalid")
    manifest=p.get("manifest");files=p.get("files")
    if not isinstance(manifest,dict) or not isinstance(files,list) or not isinstance(manifest.get("files"),list):raise RuntimeError(f"{component}: package manifest missing")
    if manifest.get("file_count")!=len(files) or len(manifest["files"])!=len(files):raise RuntimeError(f"{component}: package file count mismatch")
    rows=[]
    for i,f in enumerate(files):
        m=manifest["files"][i]
        if not isinstance(f,dict) or not isinstance(m,dict) or f.get("path")!=m.get("path") or f.get("sha256")!=m.get("sha256") or f.get("size")!=m.get("size"):raise RuntimeError(f"{component}: package manifest/file mismatch")
        pp=PurePosixPath(str(f["path"]))
        if not pp.parts or pp.is_absolute() or ".." in pp.parts:raise RuntimeError(f"{component}: unsafe package path")
        try:raw=base64.b64decode(f.get("content_base64",""),validate=True)
        except Exception as exc:raise RuntimeError(f"{component}: invalid package base64") from exc
        if len(raw)!=f["size"] or bytes_digest(raw)!=f["sha256"]:raise RuntimeError(f"{component}: package file integrity mismatch")
        rows.append({"path":f["path"],"sha256":f["sha256"],"size":f["size"]})
    md=digest(rows)
    if md!=manifest.get("source_bundle_sha256") or "sha256:"+md!=expected_identity:raise RuntimeError(f"{component}: package manifest identity mismatch")

def build_bundle(candidate:Mapping[str,Any],catalog:Mapping[str,Any],packages:Mapping[str,Mapping[str,Any]])->dict[str,Any]:
    body={
      "schema":"stegverse.bootstrap.bundle/v1","bundle_version":"1.0.0-rc.1","state":"BUILT",
      "release_candidate":candidate,"source_catalog":catalog,
      "packages":[packages[c] for c in COMPONENTS],"component_order":list(COMPONENTS),"component_count":4,
      "source_identity_scheme":"sha256-content-manifest",
      "device_materialization_contract":{"evidence_schema":"stegverse.device-node-source-package-bootstrap-evidence/v1","required_state":"MATERIALIZED_UNADMITTED","execution_authority_before_admission":"NONE"},
      "github_platform_required":False,"specific_external_platform_required":False,"network_locator_required":False,"transport_implementation_required":False,
      "credential_required":False,"bundle_integrity_confers_execution_authority":False,"release_activated":False,"publication_performed":False,
      "execution_authority":"NONE","authority_effect":"NONE_BUNDLE_BUILD_ONLY"
    }
    return {**body,"bundle_identity":"sha256:"+digest(body)}

def execute(invocation:Mapping[str,Any])->dict[str,Any]:
    if any(truthy(os.getenv(x)) for x in HOSTED):raise RuntimeError("hosted environment cannot build sovereign Bootstrap bundle")
    present=[x for x in FORBIDDEN if truthy(os.getenv(x))]
    if present:raise RuntimeError("credential-bearing environment forbidden: "+",".join(sorted(present)))
    task=invocation.get("task") or {}
    if invocation.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK_ID or task.get("worker_id")!=WORKER_ID or not task.get("claim_id"):raise RuntimeError("task invocation identity mismatch")
    rr=root(RC_ENV,DEFAULT_RC);fr=root(FREEZE_ENV,DEFAULT_FREEZE);pr=root(PACKAGE_ENV,DEFAULT_PACKAGES)
    candidate=load(rr/"candidate"/"bootstrap-v1-1.0.0-rc.1.json",pending=True);catalog=load(fr/"catalog"/"bootstrap-v1-source-catalog.json",pending=True)
    identities=validate_catalog(catalog);validate_candidate(candidate,catalog)
    packages={}
    for c in COMPONENTS:
        p=load(pr/slug(c)/"package.json",pending=True);validate_package(p,c,identities[c]);packages[c]=p
    bundle=build_bundle(candidate,catalog,packages);bound=root(BOUND_ENV,DEFAULT_BOUND);path=bound/"bundle"/"bootstrap-v1-1.0.0-rc.1.bundle.json"
    if path.is_file():
        if load(path)!=bundle:raise BundleConflict("FROZEN_BOOTSTRAP_V1_BUNDLE_CONFLICT")
    else:atomic_json(path,bundle)
    receipt={"schema":"stegverse.bootstrap.distributable-bundle-build-receipt/v1","task_id":TASK_ID,"worker_id":WORKER_ID,"state":"COMPLETE",
      "transition_id":"BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_BUILT","claim_id":task.get("claim_id"),"fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),
      "bundle_version":"1.0.0-rc.1","bundle_identity":bundle["bundle_identity"],"bundle_sha256":digest(bundle),"candidate_identity":candidate["candidate_identity"],
      "source_identity_set_sha256":catalog["source_identity_set_sha256"],"component_count":4,"github_platform_required":False,"network_access_performed":False,
      "credential_used":False,"repository_writeback_performed":False,"release_activated":False,"publication_performed":False,"execution_authority":"NONE","authority_effect":"NONE_BUNDLE_BUILD_ONLY"}
    atomic_json(bound/"receipts"/"latest.json",receipt);return receipt

def main()->int:
    try:
      inv=json.loads(sys.stdin.readline());r=execute(inv);print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"COMPLETED","transition_id":"BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_BUILT","transition_sequence":1,"expected_next_transition":"BOOTSTRAP_V1_DISTRIBUTION_MATERIALIZATION_PROVEN","checkpoint_ref":"receipts/latest.json","evidence_refs":["bundle/bootstrap-v1-1.0.0-rc.1.bundle.json","receipts/latest.json"],"bundle_identity":r["bundle_identity"],"github_platform_required":False,"authority_effect":"NONE_BUNDLE_BUILD_ONLY"},sort_keys=True));return 0
    except UpstreamPending as e:
      print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"HANDOFF_READY","transition_id":"BOOTSTRAP_V1_BUNDLE_INPUT_PENDING","transition_sequence":1,"expected_next_transition":"BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_BUILT","error":str(e),"github_platform_required":False,"blocker":{"dependency_class":"LOCAL_BOOTSTRAP_BUNDLE_INPUT","problem_statement":str(e),"solution_required":True,"may_remain_blocked":False,"next_solution_action":"Wait for the machine-owned rc.1/catalog/package inputs in local StegVerse state; do not use a platform-specific acquisition fallback.","machine_observable_release_condition":"frozen rc.1, frozen catalog, and all four matching local source packages are present","physical_additional_machine_required":False,"third_party_runtime_required":False,"github_platform_required":False,"human_action_required":False}},sort_keys=True));return 0
    except BundleConflict as e:
      print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_CONFLICT","error":str(e),"github_platform_required":False,"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
    except Exception as e:
      print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED","transition_id":"BOOTSTRAP_V1_DISTRIBUTABLE_BUNDLE_BLOCKED","error":str(e),"github_platform_required":False,"authority_effect":"NONE_FAIL_CLOSED"},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
