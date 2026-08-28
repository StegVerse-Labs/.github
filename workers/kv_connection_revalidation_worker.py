#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

TASK_ID="KV-CONNECTION-REVALIDATION-001"
HOSTED_ENV=("GITHUB_ACTIONS","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN_ENV=("GITHUB_TOKEN","GH_TOKEN","HEALER_GH_TOKEN","COINBASE_API_KEY","COINBASE_API_SECRET","COINBASE_PRIVATE_KEY","OPENAI_API_KEY","ANTHROPIC_API_KEY")

def truthy(v: str|None)->bool:
    return str(v or "").strip().lower() not in ("","0","false","no")

def _blocked(reason:str,**extra:Any)->dict[str,Any]:
    return {
        "schema":"stegverse.kv.connection-revalidation-worker/v1",
        "state":"BLOCKED","transition_id":reason,"task_id":TASK_ID,
        "provider_network_access_performed":False,
        "provider_operation_authorized":False,
        "credential_material_present":False,
        "proof_generated_by_worker":False,
        "connection_verified":False,
        "authority_effect":"NONE",
        **extra,
    }

def _load_modules(cvk_root:Path)->dict[str,Any]:
    required=[
        "runtime/connection_revalidation.py",
        "runtime/connection_registry_store.py",
        "runtime/connection_assembly.py",
    ]
    missing=[rel for rel in required if not (cvk_root/rel).is_file()]
    if missing: raise ValueError("CVK_REVALIDATION_RUNTIME_INCOMPLETE:"+",".join(missing))
    root=str(cvk_root)
    if root not in sys.path: sys.path.insert(0,root)
    return {
        "revalidation":importlib.import_module("runtime.connection_revalidation"),
        "store":importlib.import_module("runtime.connection_registry_store"),
    }

def _read_json(path:Path,label:str)->dict[str,Any]:
    if not path.is_file(): raise ValueError(f"{label}_FILE_MISSING")
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError(f"{label}_OBJECT_REQUIRED")
    return value

def execute(env:dict[str,str]|None=None,*,modules:dict[str,Any]|None=None)->dict[str,Any]:
    values=dict(os.environ if env is None else env)
    hosted=[k for k in HOSTED_ENV if truthy(values.get(k))]
    if hosted: return _blocked("HOSTED_SURFACE_REJECTED",hosted=sorted(hosted))
    forbidden=[k for k in FORBIDDEN_ENV if values.get(k)]
    if forbidden: return _blocked("FORBIDDEN_CREDENTIAL_ENV",forbidden=sorted(forbidden))

    cvk_ref=values.get("STEGVERSE_CVK_ROOT","").strip()
    kv_ref=values.get("STEGVERSE_KV_ROOT","").strip()
    conformance_ref=values.get("STEGVERSE_KV_CONFORMANCE_PROOF","").strip()
    readback_ref=values.get("STEGVERSE_KV_READBACK_PROOF","").strip()
    required_after=values.get("STEGVERSE_KV_REVALIDATION_REQUIRED_AFTER","").strip() or None
    if not cvk_ref or not kv_ref or not conformance_ref or not readback_ref:
        return _blocked("REVALIDATION_BINDINGS_REQUIRED")

    cvk=Path(cvk_ref).expanduser().resolve()
    kv=Path(kv_ref).expanduser().resolve()
    if not cvk.is_dir(): return _blocked("CVK_LOCAL_SOURCE_MISSING")
    if not kv.is_dir(): return _blocked("PRIVATE_KV_ROOT_MISSING")

    try:
        mods=modules or _load_modules(cvk)
        conformance=_read_json(Path(conformance_ref).expanduser().resolve(),"CONFORMANCE_PROOF")
        readback=_read_json(Path(readback_ref).expanduser().resolve(),"READBACK_PROOF")
    except Exception as exc:
        return _blocked("REVALIDATION_PROOF_INPUT_INVALID",detail=str(exc))

    if conformance.get("schema")!="stegverse.kv.connection-conformance-proof/v1":
        return _blocked("CONFORMANCE_PROOF_SCHEMA_INVALID")
    if readback.get("schema")!="stegverse.kv.connection-readback-proof/v1":
        return _blocked("READBACK_PROOF_SCHEMA_INVALID")
    if conformance.get("assembly_id")!=readback.get("assembly_id"):
        return _blocked("REVALIDATION_PROOF_ASSEMBLY_MISMATCH")

    store=mods["store"]; revalidation=mods["revalidation"]
    try:
        registry=store.load_registry(kv)
    except Exception as exc:
        return _blocked("CONNECTION_REGISTRY_LOAD_FAILED",detail=str(exc))
    assembly_id=conformance.get("assembly_id")
    matches=[a for a in registry.get("assemblies",[]) if a.get("assembly_id")==assembly_id]
    if len(matches)!=1:
        return _blocked("EXACT_CONNECTION_ASSEMBLY_NOT_FOUND",assembly_id=assembly_id,match_count=len(matches))
    assembly=matches[0]
    if assembly.get("compatibility_state")=="VERIFIED":
        return _blocked("CONNECTION_ALREADY_VERIFIED",assembly_id=assembly_id)
    if assembly.get("compatibility_state")=="RETIRED":
        return _blocked("RETIRED_CONNECTION_REVALIDATION_PROHIBITED",assembly_id=assembly_id)

    if required_after is None and assembly.get("compatibility_state") in ("REVALIDATION_REQUIRED","BLOCKED_SOURCE_CHANGE"):
        required_after=(assembly.get("monitoring") or {}).get("last_checked_at")
        if not required_after:
            return _blocked("REVALIDATION_TIME_FLOOR_REQUIRED",assembly_id=assembly_id)
    if required_after is None and assembly.get("compatibility_state") in ("BLOCKED_SESSION","BLOCKED_RUNTIME","DEGRADED"):
        return _blocked("REVALIDATION_TIME_FLOOR_REQUIRED",assembly_id=assembly_id)

    try:
        updated,receipt=revalidation.admit_revalidation(
            assembly,conformance,readback,required_after=required_after
        )
        if updated.get("compatibility_state")!="VERIFIED":
            return _blocked("CANONICAL_REVALIDATION_DID_NOT_VERIFY",assembly_id=assembly_id)
        registry=store.upsert_assembly(kv,updated)
        health_path=store.persist_health_receipt(kv,receipt)
    except Exception as exc:
        return _blocked("CANONICAL_REVALIDATION_FAILED",assembly_id=assembly_id,detail=str(exc))

    persisted=[a for a in registry.get("assemblies",[]) if a.get("assembly_id")==assembly_id]
    if len(persisted)!=1 or persisted[0].get("compatibility_state")!="VERIFIED":
        return _blocked("VERIFIED_CONNECTION_PERSISTENCE_NOT_CONFIRMED",assembly_id=assembly_id)

    return {
        "schema":"stegverse.kv.connection-revalidation-worker/v1",
        "state":"COMPLETED","transition_id":"KV_CONNECTION_REVALIDATION_COMPLETED","task_id":TASK_ID,
        "assembly_id":assembly_id,
        "provider":updated.get("provider"),
        "compatibility_state":"VERIFIED",
        "required_after":required_after,
        "connection_proof_ref":conformance.get("connection_proof_ref"),
        "readback_proof_ref":readback.get("readback_proof_ref"),
        "health_receipt_path":str(health_path),
        "provider_network_access_performed":False,
        "provider_operation_authorized":False,
        "credential_material_present":False,
        "proof_generated_by_worker":False,
        "connection_verified":True,
        "authority_effect":"NONE"
    }

def main()->int:
    invocation=json.load(sys.stdin)
    task=invocation.get("task") or {}
    if invocation.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK_ID: return 2
    result=execute()
    response={
        "schema":"stegverse.worker-response/v0.1","state":result["state"],
        "transition_id":result["transition_id"],"transition_sequence":1,
        "expected_next_transition":None if result["state"]=="COMPLETED" else "RETRY_AFTER_RUNTIME_PREDICATE_CHANGE",
        "checkpoint_ref":"handoffs/KV-CONNECTION-REVALIDATION-001.json",
        "evidence_refs":["KV_CONNECTION_REVALIDATION_WORKER_MIRROR_HANDOFF.md"],
        "cost_observation":{"hb_transition_count":0,"compute_units":1,"external_cost_usd":0,"task_class":"kv_connection_revalidation"},
        "result":result
    }
    json.dump(response,sys.stdout,sort_keys=True); sys.stdout.write("\n"); return 0

if __name__=="__main__": raise SystemExit(main())
