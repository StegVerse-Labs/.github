#!/usr/bin/env python3
"""Prepare exact production source roots from local/content-addressed StegVerse packages only."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
from typing import Any, Mapping

TASK_ID = "SV-DN1-PRODUCTION-SOURCE-PREP-001"
WORKER_ID = "sv-dn1-production-source-prep-worker"
BOUND_STATE_ENV = "STEGVERSE_BOUND_STATE_ROOT"
SOURCE_ROOT_ENV = "STEGVERSE_SOURCE_MATERIALIZATION_ROOT"
PACKAGE_ROOT_ENV = "STEGVERSE_SOURCE_PACKAGE_ROOT"

DEFAULT_BOUND_ROOT = Path.home() / ".stegverse" / "state" / "sv-dn1-production-source-prep"
DEFAULT_SOURCE_ROOT = Path("/var/lib/stegverse/source")
DEFAULT_PACKAGE_ROOT = Path.home() / ".stegverse" / "packages" / "source" / "v1"

HOSTED_ENV = ("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN","ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "TVC_EPHEMERAL_GITHUB_TOKEN","HF_TOKEN","HUGGINGFACE_TOKEN","HUGGING_FACE_HUB_TOKEN",
    "OPENAI_API_KEY","ANTHROPIC_API_KEY","GOOGLE_API_KEY","AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY","AZURE_CLIENT_SECRET","OAUTH_TOKEN",
)
NODE_MARKERS=(Path("/etc/stegverse/node.json"),Path.home()/".stegverse"/"node.json")
PACKAGE_SCHEMA="stegverse.source-package/v1"
PACKAGE_VERSION="1.0.0"

COMPONENTS={
    "StegVerse-org/StegVerse-SDK":{
        "root_rel":"StegVerse-org/StegVerse-SDK",
        "legacy_coordinate":{"kind":"git_commit","value":"4461a1edf83549c51189ca4217dd75752caf604e"},
        "anchors":{
            "stegverse/governance_ingress_runtime.py":"62c5ae4799ae018f6b100766215c3c68078c5b2e",
            "stegverse/sovereign_validation_runtime.py":"814d4cb607cc2cb4c7a605474fe845e13540898d",
        },
    },
    "Data-Continuation/core-lite":{
        "root_rel":"Data-Continuation/core-lite",
        "legacy_coordinate":{"kind":"git_commit","value":"284ddc21a352ee9c7decdd40dd499b7286710bc8"},
        "anchors":{"core_lite/transaction_route.py":"734923a86bfcd4d41d07e0fb8797de50f0fb9408"},
    },
    "StegVerse-Labs/StegCore":{
        "root_rel":"StegVerse-Labs/StegCore",
        "legacy_coordinate":{"kind":"git_commit","value":"eb2ef110d09328aa90bf1ed91c18b47a3ba32a71"},
        "anchors":{"src/stegcore/transaction_lifecycle.py":"81935669846fedd2867272810b090226b05780ab"},
    },
    "master-records/orchestration":{
        "root_rel":"master-records/orchestration",
        "legacy_coordinate":{"kind":"git_commit","value":"baf9272f89ebe515fc4c2413b5d951d28f1e4485"},
        "anchors":{"services/manifest_receipt_custody.py":"26a4c1e082ee91128648b2b9bd13cc32ce915f82"},
    },
}
ROOT_ENV_OUTPUT={
    "StegVerse-org/StegVerse-SDK":"STEGVERSE_SDK_SOURCE_ROOT",
    "StegVerse-Labs/StegCore":"STEGVERSE_STEGCORE_SOURCE_ROOT",
    "Data-Continuation/core-lite":"STEGVERSE_CORE_LITE_SOURCE_ROOT",
    "master-records/orchestration":"STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
}

class SourcePackagePending(RuntimeError): pass
class SourceIdentityDrift(RuntimeError): pass

def truthy(v: str|None)->bool:
    return str(v or "").strip().lower() not in {"","0","false","no"}

def canonical_bytes(v:Any)->bytes:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")

def sha256_bytes(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def git_blob_sha1(raw:bytes)->str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

def component_slug(component_id:str)->str:
    return component_id.lower().replace("/","--").replace("_","-").replace(".","-")

def source_root()->Path:
    return Path(os.environ.get(SOURCE_ROOT_ENV,str(DEFAULT_SOURCE_ROOT))).expanduser()

def package_root()->Path:
    return Path(os.environ.get(PACKAGE_ROOT_ENV,str(DEFAULT_PACKAGE_ROOT))).expanduser()

def bound_root()->Path:
    return Path(os.environ.get(BOUND_STATE_ENV,str(DEFAULT_BOUND_ROOT))).expanduser()

def repo_root(base:Path,component_id:str)->Path:
    return base / COMPONENTS[component_id]["root_rel"]

def find_node()->tuple[Path,dict[str,Any]]:
    for p in NODE_MARKERS:
        if p.is_file():
            try: v=json.loads(p.read_text())
            except Exception: continue
            if isinstance(v,dict): return p,v
    raise RuntimeError("sovereign StegVerse node declaration not observed")

def verify_migration_anchors(root:Path,component_id:str)->dict[str,str]:
    out={}
    for rel,expected in COMPONENTS[component_id]["anchors"].items():
        p=root/rel
        if not p.is_file(): raise SourceIdentityDrift(f"{component_id}: migration anchor missing: {rel}")
        actual=git_blob_sha1(p.read_bytes())
        if actual!=expected: raise SourceIdentityDrift(f"{component_id}: migration anchor drift {rel}")
        out[rel]=actual
    return out

def iter_source_files(root:Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file(): continue
        rel=p.relative_to(root)
        if rel.parts and rel.parts[0]==".git": continue
        yield rel,p

def compute_source_manifest(root:Path)->dict[str,Any]:
    rows=[]
    for rel,p in iter_source_files(root):
        raw=p.read_bytes()
        rows.append({"path":rel.as_posix(),"sha256":sha256_bytes(raw),"size":len(raw)})
    bundle=sha256_bytes(canonical_bytes(rows))
    return {"file_count":len(rows),"source_bundle_sha256":bundle,"files":rows}

def source_identity(manifest:Mapping[str,Any])->str:
    return "sha256:"+str(manifest["source_bundle_sha256"])

def observe_local_component(base:Path,component_id:str)->dict[str,Any]|None:
    root=repo_root(base,component_id)
    if not root.is_dir(): return None
    anchors=verify_migration_anchors(root,component_id)
    manifest=compute_source_manifest(root)
    return {
        "component_id":component_id,"root":str(root),"state":"LOCAL_PRESENT_VERIFIED",
        "source_identity":source_identity(manifest),"manifest":manifest,
        "migration_anchors":anchors,"network_fetch_performed":False,
        "legacy_coordinate":COMPONENTS[component_id]["legacy_coordinate"],
    }

def package_path(store:Path,component_id:str)->Path:
    return store/component_slug(component_id)/"package.json"

def load_package(store:Path,component_id:str)->dict[str,Any]|None:
    p=package_path(store,component_id)
    if not p.is_file(): return None
    v=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise SourceIdentityDrift(f"{component_id}: source package root must be object")
    return v

def validate_package(package:Mapping[str,Any],component_id:str)->dict[str,Any]:
    if package.get("schema")!=PACKAGE_SCHEMA or package.get("package_version")!=PACKAGE_VERSION:
        raise SourceIdentityDrift(f"{component_id}: package schema/version mismatch")
    if package.get("component_id")!=component_id:
        raise SourceIdentityDrift(f"{component_id}: package component mismatch")
    if package.get("credential_material_included") is not False:
        raise SourceIdentityDrift(f"{component_id}: package contains credential material")
    if package.get("authority_effect")!="NONE_SOURCE_TRANSPORT_ONLY":
        raise SourceIdentityDrift(f"{component_id}: package authority effect mismatch")
    files=package.get("files"); manifest=package.get("manifest")
    if not isinstance(files,list) or not isinstance(manifest,dict): raise SourceIdentityDrift(f"{component_id}: package files/manifest missing")
    mrows=manifest.get("files")
    if not isinstance(mrows,list) or manifest.get("file_count")!=len(files) or len(mrows)!=len(files):
        raise SourceIdentityDrift(f"{component_id}: package file count mismatch")
    rows=[]
    for i,f in enumerate(files):
        m=mrows[i]
        if not isinstance(f,dict) or not isinstance(m,dict): raise SourceIdentityDrift(f"{component_id}: package row malformed")
        rel=f.get("path")
        if rel!=m.get("path") or f.get("sha256")!=m.get("sha256") or f.get("size")!=m.get("size"):
            raise SourceIdentityDrift(f"{component_id}: package manifest/file mismatch")
        pure=PurePosixPath(str(rel))
        if not pure.parts or pure.is_absolute() or ".." in pure.parts:
            raise SourceIdentityDrift(f"{component_id}: unsafe package path")
        try: raw=base64.b64decode(f.get("content_base64",""),validate=True)
        except Exception as exc: raise SourceIdentityDrift(f"{component_id}: invalid base64 payload") from exc
        if len(raw)!=f["size"] or sha256_bytes(raw)!=f["sha256"]:
            raise SourceIdentityDrift(f"{component_id}: package file integrity mismatch: {rel}")
        rows.append({"path":rel,"sha256":f["sha256"],"size":f["size"]})
    digest=sha256_bytes(canonical_bytes(rows))
    if digest!=manifest.get("source_bundle_sha256"):
        raise SourceIdentityDrift(f"{component_id}: package source bundle digest mismatch")
    identity="sha256:"+digest
    if package.get("source_identity")!=identity:
        raise SourceIdentityDrift(f"{component_id}: package source identity mismatch")
    return {"source_identity":identity,"manifest":{"file_count":len(rows),"source_bundle_sha256":digest,"files":rows}}

def materialize_package(package:Mapping[str,Any],destination:Path,component_id:str)->dict[str,Any]:
    verified=validate_package(package,component_id)
    parent=destination.parent; parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix="."+destination.name+".stegverse-package-",dir=parent))
    old=None
    try:
        for f in package["files"]:
            pure=PurePosixPath(f["path"]); target=stage/Path(*pure.parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(base64.b64decode(f["content_base64"],validate=True))
        verify_migration_anchors(stage,component_id)
        observed=compute_source_manifest(stage)
        if source_identity(observed)!=verified["source_identity"]:
            raise SourceIdentityDrift(f"{component_id}: materialized identity mismatch")
        if destination.exists():
            old=parent/("."+destination.name+".previous-stegverse-package")
            if old.exists(): shutil.rmtree(old)
            os.replace(destination,old)
        os.replace(stage,destination); stage=None
        if old and old.exists(): shutil.rmtree(old)
        return {"component_id":component_id,"root":str(destination),"state":"PACKAGE_MATERIALIZED_VERIFIED",
                "source_identity":verified["source_identity"],"manifest":observed,
                "migration_anchors":verify_migration_anchors(destination,component_id),
                "network_fetch_performed":False,
                "legacy_coordinate":package.get("provenance",{}).get("legacy_coordinate")}
    finally:
        if stage and stage.exists(): shutil.rmtree(stage,ignore_errors=True)

def ensure_component(base:Path,store:Path,component_id:str)->dict[str,Any]:
    local=observe_local_component(base,component_id)
    if local is not None: return local
    package=load_package(store,component_id)
    if package is None:
        raise SourcePackagePending(f"{component_id}: content-addressed StegVerse source package not present in local package store")
    return materialize_package(package,repo_root(base,component_id),component_id)

def atomic_json(path:Path,value:Mapping[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h:
            json.dump(dict(value),h,indent=2,sort_keys=True); h.write("\n")
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def validate_invocation(invocation:Mapping[str,Any])->dict[str,Any]:
    if invocation.get("schema")!="stegverse.worker-invocation/v0.1": raise RuntimeError("worker invocation schema mismatch")
    task=invocation.get("task") or {}
    if task.get("task_id")!=TASK_ID: raise RuntimeError("task id mismatch")
    return dict(task)

def execute(invocation:Mapping[str,Any])->dict[str,Any]:
    if any(truthy(os.getenv(n)) for n in HOSTED_ENV): raise RuntimeError("hosted environments cannot execute sovereign production source preparation")
    present=[n for n in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(n))]
    if present: raise RuntimeError("credential-bearing environment forbidden: "+",".join(sorted(present)))
    node_path,_=find_node(); task=validate_invocation(invocation)
    base=source_root(); store=package_root(); bound=bound_root()
    rows={}
    pending=[]
    for component_id in COMPONENTS:
        try: rows[component_id]=ensure_component(base,store,component_id)
        except SourcePackagePending as exc:
            rows[component_id]={"component_id":component_id,"state":"SOURCE_PACKAGE_PENDING","error":str(exc),
                                "package_path":str(package_path(store,component_id)),
                                "network_fetch_performed":False,
                                "legacy_coordinate":COMPONENTS[component_id]["legacy_coordinate"]}
            pending.append(component_id)
    atomic_json(bound/"observed"/"source-roots.json",{
        "schema":"stegverse.sv-dn1.production-source-roots/v2","roots":rows,
        "source_identity_scheme":"sha256-content-manifest","network_source_fetch_performed":False,
        "github_platform_required":False,"authority_effect":"NONE"})
    atomic_json(bound/"requests"/"source-package-needs.json",{
        "schema":"stegverse.source-package-needs/v1",
        "needed":[{"component_id":c,"package_path":str(package_path(store,c)),
                   "migration_anchors":COMPONENTS[c]["anchors"],
                   "legacy_coordinate_optional_provenance":COMPONENTS[c]["legacy_coordinate"]}
                  for c in pending],
        "transport_requirements":{"github":False,"http":False,"specific_platform":False},
        "authority_effect":"NONE_REQUEST_ONLY"})
    if pending:
        raise SourcePackagePending("content-addressed StegVerse source packages pending: "+",".join(pending))
    roots={c:str(repo_root(base,c)) for c in COMPONENTS}
    identities={c:rows[c]["source_identity"] for c in COMPONENTS}
    receipt={
        "schema":"stegverse.sv-dn1.production-source-prep-receipt/v2","task_id":TASK_ID,"worker_id":WORKER_ID,
        "state":"COMPLETE","transition_id":"SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
        "claim_id":task.get("claim_id"),"fencing_token":(task.get("heartbeat_timing") or {}).get("fencing_token"),
        "node_declaration_ref":str(node_path),"source_roots":roots,
        "source_root_env":{ROOT_ENV_OUTPUT[c]:p for c,p in roots.items()},
        "source_identities":identities,"source_identity_scheme":"sha256-content-manifest",
        "migration_anchors_verified":True,"network_source_fetch_performed":False,
        "github_platform_required":False,"credential_used":False,"github_token_used":False,
        "repository_writeback_performed":False,"sdk_admitted":False,
        "authority_effect":"SOURCE_PREPARATION_ONLY_NO_NEW_AUTHORITY"}
    atomic_json(bound/"receipts"/"latest.json",receipt); return receipt

def completed_response(receipt:Mapping[str,Any])->dict[str,Any]:
    return {"schema":"stegverse.worker-response/v0.1","state":"COMPLETED",
            "transition_id":"SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE","transition_sequence":1,
            "expected_next_transition":"SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED","checkpoint_ref":"receipts/latest.json",
            "evidence_refs":["observed/source-roots.json","requests/source-package-needs.json","receipts/latest.json"],
            "source_root_env":receipt.get("source_root_env"),"source_identities":receipt.get("source_identities"),
            "github_platform_required":False,"github_token_used":False,"repository_writeback_performed":False}

def wait_response(exc:Exception,transition:str)->dict[str,Any]:
    return {"schema":"stegverse.worker-response/v0.1","state":"HANDOFF_READY","transition_id":transition,
            "transition_sequence":1,"expected_next_transition":"SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
            "error":str(exc),"github_platform_required":False,"github_token_used":False,
            "repository_writeback_performed":False,
            "blocker":{"dependency_class":"STEGVERSE_SOURCE_PACKAGE","problem_statement":str(exc),
                       "solution_required":True,"may_remain_blocked":False,
                       "next_solution_action":"Materialize the required content-addressed StegVerse source package into the local package store using any admitted transport; no specific external platform is required.",
                       "machine_observable_release_condition":"all four source roots are present with content-addressed identities and migration anchors verified",
                       "physical_additional_machine_required":False,"third_party_runtime_required":False,
                       "github_token_required":False,"github_platform_required":False,
                       "human_action_required":False}}

def main()->int:
    try:
        raw=sys.stdin.readline(); invocation=json.loads(raw)
        if not isinstance(invocation,dict): raise RuntimeError("worker invocation must be JSON object")
        receipt=execute(invocation); print(json.dumps(completed_response(receipt),sort_keys=True)); return 0
    except SourcePackagePending as exc:
        print(json.dumps(wait_response(exc,"SV_DN1_SOURCE_PACKAGE_MATERIALIZATION_PENDING"),sort_keys=True)); return 0
    except SourceIdentityDrift as exc:
        print(json.dumps(wait_response(exc,"SV_DN1_SOURCE_IDENTITY_RECONCILIATION_REQUIRED"),sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"schema":"stegverse.worker-response/v0.1","state":"BLOCKED",
                          "transition_id":"SV_DN1_PRODUCTION_SOURCE_PREP_BLOCKED","error":str(exc),
                          "github_platform_required":False,"github_token_used":False,
                          "repository_writeback_performed":False},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
