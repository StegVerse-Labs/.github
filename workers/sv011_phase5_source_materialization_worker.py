#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, os, shutil, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

ROOT=Path.cwd().resolve()
TASK_ID="SHWP-SV011-PHASE5-SOURCE-MATERIALIZATION-001"
CAPABILITY="sv011_phase5_source_materialization"
BUNDLE_ROOT=ROOT/"source-bundles/sv011-phase5"
MANIFEST=BUNDLE_ROOT/"manifest.json"
DEFAULT_DEST=Path.home()/".stegverse/source/SV-011/.github"
DEST_ENV="STEGVERSE_SV011_MATERIALIZED_ROOT"
RECEIPT=ROOT/"receipts/sv011-phase5-source-materialization/SHWP-SV011-PHASE5-SOURCE-MATERIALIZATION-001.json"
IDENTITY_FILE=".stegverse-source-identity.json"
HOSTED_ENV=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","VERCEL_ENV","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN_ENV=("GITHUB_TOKEN","GH_TOKEN","GITHUB_PAT","ACTIONS_RUNTIME_TOKEN","OPENAI_API_KEY","ANTHROPIC_API_KEY","WALLET_PRIVATE_KEY","PRIVATE_KEY","SEED","MNEMONIC")

def truthy(v): return str(v or "").strip().lower() not in {"","0","false","no"}

def git_blob_sha1(raw:bytes)->str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

def load(path:Path)->dict[str,Any]:
    v=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise RuntimeError(f"expected JSON object: {path}")
    return v

def atomic_json(path:Path,value:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,delete=False) as h:
        json.dump(value,h,indent=2,sort_keys=True); h.write("\n"); tmp=h.name
    os.replace(tmp,path)

def validate_manifest()->dict[str,Any]:
    if not MANIFEST.is_file(): raise RuntimeError("SV-011 source bundle manifest not materialized")
    m=load(MANIFEST)
    if m.get("schema")!="stegverse.sv011-phase5-source-bundle/v0.1": raise RuntimeError("SV-011 source bundle schema mismatch")
    if m.get("repository")!="SV-011/.github": raise RuntimeError("SV-011 source bundle repository mismatch")
    if m.get("source_basis_commit")!="cf2777d9d21a97289f4ec7b0d9b0b21597047666": raise RuntimeError("SV-011 source bundle commit mismatch")
    if m.get("authority_effect")!="NONE_SOURCE_TRANSPORT_ONLY": raise RuntimeError("SV-011 source bundle authority mismatch")
    if m.get("credential_material_included") is not False or m.get("network_source_fetch_required") is not False:
        raise RuntimeError("SV-011 source bundle transport contract mismatch")
    rows=m.get("files")
    if not isinstance(rows,list) or len(rows)!=7: raise RuntimeError("SV-011 source bundle must contain exactly seven pinned files")
    seen=set()
    for row in rows:
        if not isinstance(row,dict): raise RuntimeError("SV-011 source bundle row malformed")
        rel=str(row.get("path") or "")
        expected=str(row.get("git_blob_sha1") or "")
        pure=PurePosixPath(rel)
        if not pure.parts or pure.is_absolute() or ".." in pure.parts or rel in seen: raise RuntimeError("unsafe/duplicate SV-011 bundle path")
        seen.add(rel)
        p=BUNDLE_ROOT/Path(*pure.parts)
        if not p.is_file(): raise RuntimeError(f"SV-011 bundle file missing: {rel}")
        if git_blob_sha1(p.read_bytes())!=expected: raise RuntimeError(f"SV-011 bundle identity mismatch: {rel}")
    return m

def verify_tree(root:Path,manifest:dict[str,Any],require_identity:bool)->dict[str,Any]:
    mismatches=[]
    for row in manifest["files"]:
        p=root/row["path"]
        actual=git_blob_sha1(p.read_bytes()) if p.is_file() else "MISSING"
        if actual!=row["git_blob_sha1"]:
            mismatches.append({"path":row["path"],"expected":row["git_blob_sha1"],"observed":actual})
    identity=None
    id_path=root/IDENTITY_FILE
    if id_path.is_file():
        try: identity=load(id_path)
        except Exception: identity=None
    identity_ok=bool(
        isinstance(identity,dict)
        and identity.get("schema")=="stegverse.sv011-materialized-source-identity/v0.1"
        and identity.get("repository")=="SV-011/.github"
        and identity.get("source_basis_commit")==manifest["source_basis_commit"]
        and identity.get("verified_git_blob_count")==7
        and identity.get("authority_effect")=="NONE_SOURCE_MATERIALIZATION_ONLY"
    )
    return {"root":str(root),"mismatches":mismatches,"identity_ok":identity_ok,"verified":not mismatches and (identity_ok if require_identity else True)}

def materialize(destination:Path)->dict[str,Any]:
    manifest=validate_manifest()
    dest=destination.expanduser().resolve()
    existing=verify_tree(dest,manifest,True) if dest.is_dir() else {"verified":False}
    if existing.get("verified"):
        return {"state":"ALREADY_MATERIALIZED_VERIFIED","destination":str(dest),"source_basis_commit":manifest["source_basis_commit"],"verified_git_blob_count":7,"filesystem_mutated":False}
    dest.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix=".sv011-phase5-source-",dir=dest.parent))
    backup=None
    try:
        for row in manifest["files"]:
            pure=PurePosixPath(row["path"])
            src=BUNDLE_ROOT/Path(*pure.parts)
            target=stage/Path(*pure.parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(src.read_bytes())
        pre=verify_tree(stage,manifest,False)
        if not pre["verified"]: raise RuntimeError("SV-011 staged source failed exact-byte verification")
        atomic_json(stage/IDENTITY_FILE,{
          "schema":"stegverse.sv011-materialized-source-identity/v0.1",
          "repository":"SV-011/.github",
          "source_basis_commit":manifest["source_basis_commit"],
          "verified_git_blob_count":7,
          "network_source_fetch_performed":False,
          "credential_used":False,
          "repository_writeback_performed":False,
          "authority_effect":"NONE_SOURCE_MATERIALIZATION_ONLY"
        })
        post_stage=verify_tree(stage,manifest,True)
        if not post_stage["verified"]: raise RuntimeError("SV-011 staged identity record failed verification")
        if dest.exists():
            backup=dest.parent/(".sv011-phase5-source.previous")
            if backup.exists(): shutil.rmtree(backup)
            os.replace(dest,backup)
        os.replace(stage,dest); stage=None
        post=verify_tree(dest,manifest,True)
        if not post["verified"]: raise RuntimeError("SV-011 post-write source verification failed")
        if backup and backup.exists(): shutil.rmtree(backup)
        return {"state":"MATERIALIZED_VERIFIED","destination":str(dest),"source_basis_commit":manifest["source_basis_commit"],"verified_git_blob_count":7,"filesystem_mutated":True}
    finally:
        if stage is not None and stage.exists(): shutil.rmtree(stage,ignore_errors=True)

def main()->int:
    try: invocation=json.load(sys.stdin)
    except Exception: return 2
    if invocation.get("schema")!="stegverse.worker-invocation/v0.1": return 3
    task=invocation.get("task") or {}; handoff=invocation.get("handoff") or {}
    if task.get("task_id")!=TASK_ID: return 4
    execution=handoff.get("execution") or {}
    if CAPABILITY not in set(execution.get("required_capabilities") or []): return 5
    if "receipts/sv011-phase5-source-materialization/**" not in set(execution.get("allowed_paths") or []): return 6

    hosted=[k for k in HOSTED_ENV if truthy(os.environ.get(k))]
    forbidden=[k for k in FORBIDDEN_ENV if truthy(os.environ.get(k))]
    now=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    if hosted:
        state="BLOCKED"; result={"reason":"HOSTED_RUNTIME_PROHIBITED","hosted_markers":hosted}
    elif forbidden:
        state="BLOCKED"; result={"reason":"FORBIDDEN_CREDENTIAL_ENVIRONMENT","forbidden_names":sorted(forbidden)}
    else:
        try:
            dest=Path(os.environ.get(DEST_ENV,str(DEFAULT_DEST)))
            materialized=materialize(dest)
            state="COMPLETED"
            result={"reason":"SV011_PHASE5_SOURCE_MATERIALIZED","materialization":materialized}
        except Exception as exc:
            state="BLOCKED"; result={"reason":"SV011_PHASE5_SOURCE_MATERIALIZATION_FAILED","error_type":type(exc).__name__,"error":str(exc)}

    result.update({
      "network_source_fetch_performed":False,"credential_authority":"TV/TVC","credential_used":False,
      "github_token_runtime_authority":"NONE","repository_writeback_performed":False,
      "heartbeat_grants_execution_authority":False,"boundary_execution_performed":False,
      "publication_authorized":False,"proofs_accepted":False
    })
    receipt={"schema":"stegverse.sv011-phase5-source-materialization-worker-receipt/v0.1","task_id":TASK_ID,"generated_at":now,"state":state,"result":result,"authority_effect":"NONE_SOURCE_MATERIALIZATION_ONLY"}
    atomic_json(RECEIPT,receipt)
    blocker=None if state=="COMPLETED" else {
      "dependency_class":"INTERNAL_SOURCE_MATERIALIZATION","problem_statement":result["reason"],"solution_required":True,"may_remain_blocked":True,
      "next_solution_action":"RECHECK_LOCAL_WORKER_SOURCE_BUNDLE_AND_DESTINATION",
      "machine_observable_release_condition":"seven pinned SV-011 Phase-5 source files are atomically materialized and post-write verified"
    }
    response={
      "schema":"stegverse.worker-response/v0.1","state":state,
      "transition_id":"SV011_PHASE5_SOURCE_MATERIALIZATION_COMPLETE" if state=="COMPLETED" else "SV011_PHASE5_SOURCE_MATERIALIZATION_BLOCKED",
      "transition_sequence":1,
      "expected_next_transition":"SV011_PHASE5_BOUNDARY_COMPLETED" if state=="COMPLETED" else "SV011_PHASE5_SOURCE_MATERIALIZATION_RECHECK",
      "expected_next_earliest_epoch":None,"expected_next_latest_epoch":None,
      "recheck_policy":None if state=="COMPLETED" else "SEPARATE_TASK_CONTROL_EVALUATION",
      "checkpoint_ref":"receipts/sv011-phase5-source-materialization/SHWP-SV011-PHASE5-SOURCE-MATERIALIZATION-001.json",
      "evidence_refs":["docs/SV011_PHASE5_SOURCE_MATERIALIZATION_MIRROR_HANDOFF.md","source-bundles/sv011-phase5/manifest.json","receipts/sv011-phase5-source-materialization/SHWP-SV011-PHASE5-SOURCE-MATERIALIZATION-001.json"],
      "blocker":blocker,
      "cost_observation":{"task_control_evaluations":1,"compute_units":1,"external_cost_usd":0,"task_class":"sv011_phase5_source_materialization"}
    }
    json.dump(response,sys.stdout,sort_keys=True); sys.stdout.write("\n"); return 0
if __name__=="__main__": raise SystemExit(main())
