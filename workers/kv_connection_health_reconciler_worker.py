#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

TASK_ID="KV-CONNECTION-HEALTH-RECONCILER-001"
HOSTED_ENV=("GITHUB_ACTIONS","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN_ENV=("GITHUB_TOKEN","GH_TOKEN","HEALER_GH_TOKEN","COINBASE_API_KEY","COINBASE_API_SECRET","COINBASE_PRIVATE_KEY","OPENAI_API_KEY","ANTHROPIC_API_KEY")

def truthy(v: str|None)->bool:
    return str(v or "").strip().lower() not in ("","0","false","no")

def _blocked(reason:str,**extra:Any)->dict[str,Any]:
    return {
        "schema":"stegverse.kv.connection-health-reconciler-worker/v1",
        "state":"BLOCKED","transition_id":reason,"task_id":TASK_ID,
        "provider_operation_authorized":False,
        "credential_material_present":False,
        "provider_network_access_performed":False,
        "connection_verified":False,
        "authority_effect":"NONE",
        **extra,
    }

def _load_modules(cvk_root:Path)->dict[str,Any]:
    required=[
        "runtime/connection_assembly.py",
        "runtime/source_change_monitor.py",
        "runtime/connection_registry_store.py",
    ]
    missing=[rel for rel in required if not (cvk_root/rel).is_file()]
    if missing: raise ValueError("CVK_CONNECTION_RUNTIME_INCOMPLETE:"+",".join(missing))
    root=str(cvk_root)
    if root not in sys.path: sys.path.insert(0,root)
    return {
        "monitor":importlib.import_module("runtime.source_change_monitor"),
        "store":importlib.import_module("runtime.connection_registry_store"),
    }

def _observation_files(path:Path)->list[Path]:
    if path.is_file(): return [path]
    if path.is_dir(): return sorted(p for p in path.glob("*.json") if p.is_file())
    raise ValueError("SOURCE_CHANGE_INPUT_MISSING")

def execute(env:dict[str,str]|None=None,*,modules:dict[str,Any]|None=None)->dict[str,Any]:
    values=dict(os.environ if env is None else env)
    hosted=[k for k in HOSTED_ENV if truthy(values.get(k))]
    if hosted: return _blocked("HOSTED_SURFACE_REJECTED",hosted=sorted(hosted))
    forbidden=[k for k in FORBIDDEN_ENV if values.get(k)]
    if forbidden: return _blocked("FORBIDDEN_CREDENTIAL_ENV",forbidden=sorted(forbidden))

    cvk_ref=values.get("STEGVERSE_CVK_ROOT","").strip()
    kv_ref=values.get("STEGVERSE_KV_ROOT","").strip()
    input_ref=values.get("STEGVERSE_KV_SOURCE_CHANGE_INPUT","").strip()
    if not cvk_ref or not kv_ref or not input_ref: return _blocked("RECONCILER_BINDINGS_REQUIRED")

    cvk=Path(cvk_ref).expanduser().resolve()
    kv=Path(kv_ref).expanduser().resolve()
    inp=Path(input_ref).expanduser().resolve()
    if not cvk.is_dir(): return _blocked("CVK_LOCAL_SOURCE_MISSING")
    if not kv.is_dir(): return _blocked("PRIVATE_KV_ROOT_MISSING")
    try:
        mods=modules or _load_modules(cvk)
        files=_observation_files(inp)
    except Exception as exc:
        return _blocked("RECONCILER_SOURCE_INVALID",detail=str(exc))
    if not files: return _blocked("SOURCE_CHANGE_INPUT_EMPTY")

    monitor=mods["monitor"]; store=mods["store"]
    try:
        registry=store.load_registry(kv)
    except Exception as exc:
        return _blocked("CONNECTION_REGISTRY_LOAD_FAILED",detail=str(exc))

    results=[]; applied=0; skipped=0
    for path in files:
        try:
            obs=json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return _blocked("SOURCE_CHANGE_OBSERVATION_UNREADABLE",path=str(path),detail=str(exc))
        if not isinstance(obs,dict) or obs.get("schema")!="stegverse.kv.source-change-observation/v1":
            return _blocked("SOURCE_CHANGE_OBSERVATION_SCHEMA_INVALID",path=str(path))
        provider=str(obs.get("provider") or "").lower()
        matches=[a for a in registry.get("assemblies",[]) if str(a.get("provider") or "").lower()==provider]
        if not matches:
            return _blocked("PROVIDER_ASSEMBLY_NOT_FOUND",provider=provider,path=str(path))
        try:
            persisted_change=store.persist_source_change(kv,obs)
        except Exception as exc:
            return _blocked("SOURCE_CHANGE_PERSISTENCE_FAILED",detail=str(exc),path=str(path))
        for assembly in matches:
            last=(assembly.get("monitoring") or {}).get("last_change_ref")
            if last==obs.get("observation_id"):
                skipped+=1
                results.append({"assembly_id":assembly.get("assembly_id"),"observation_id":obs.get("observation_id"),"state":"ALREADY_APPLIED"})
                continue
            try:
                updated,receipt=monitor.evaluate_source_change(assembly,obs)
                registry=store.upsert_assembly(kv,updated)
                health_path=store.persist_health_receipt(kv,receipt)
            except Exception as exc:
                return _blocked("CONNECTION_HEALTH_RECONCILIATION_FAILED",assembly_id=assembly.get("assembly_id"),detail=str(exc))
            if updated.get("compatibility_state")=="VERIFIED":
                return _blocked("RECONCILER_MAY_NOT_RESTORE_VERIFIED",assembly_id=assembly.get("assembly_id"))
            applied+=1
            results.append({
                "assembly_id":updated.get("assembly_id"),
                "observation_id":obs.get("observation_id"),
                "state":updated.get("compatibility_state"),
                "health_receipt_path":str(health_path),
                "source_change_path":str(persisted_change)
            })

    return {
        "schema":"stegverse.kv.connection-health-reconciler-worker/v1",
        "state":"COMPLETED","transition_id":"KV_CONNECTION_HEALTH_RECONCILIATION_COMPLETED","task_id":TASK_ID,
        "observations_processed":len(files),"assemblies_applied":applied,"assemblies_skipped":skipped,
        "results":results,
        "provider_operation_authorized":False,
        "credential_material_present":False,
        "provider_network_access_performed":False,
        "connection_verified":False,
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
        "checkpoint_ref":"handoffs/KV-CONNECTION-HEALTH-RECONCILER-001.json",
        "evidence_refs":["KV_CONNECTION_HEALTH_RECONCILER_MIRROR_HANDOFF.md"],
        "cost_observation":{"hb_transition_count":0,"compute_units":1,"external_cost_usd":0,"task_class":"kv_connection_health_reconciliation"},
        "result":result
    }
    json.dump(response,sys.stdout,sort_keys=True); sys.stdout.write("\n"); return 0

if __name__=="__main__": raise SystemExit(main())
