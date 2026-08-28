#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

TASK_ID="TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001"
TVC_REPO="StegVerse-Labs/TVC"
ROUTE_OBS=Path("/var/lib/stegverse/tvc/service-gateway/coinbase-public-route-observation.json")
ACTIVATION=Path("/var/lib/stegverse/skap/browser-recipient/receipts/latest.json")
LIVENESS=Path("/var/lib/stegverse/skap/browser-recipient/receipts/liveness-latest.json")
SITE_PROJECTION=Path("/var/lib/stegverse/skap/browser-recipient/public/coinbase-owner-ingress-site-config.json")
HOSTED_ENV=("GITHUB_ACTIONS","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN_CREDENTIAL_ENV=("GITHUB_TOKEN","GH_TOKEN","HEALER_GH_TOKEN","COINBASE_API_KEY","COINBASE_API_SECRET","COINBASE_PRIVATE_KEY")

def truthy(v: str|None)->bool:
    return str(v or "").strip().lower() not in ("","0","false","no")

def _json_tail(text: str)->dict[str,Any]|None:
    try:
        v=json.loads(text.strip().splitlines()[-1])
        return v if isinstance(v,dict) else None
    except Exception:
        return None

def _roots(env: dict[str,str])->dict[str,Path]:
    raw=env.get("STEGVERSE_REPO_ROOTS_JSON","").strip()
    out: dict[str,Path]={}
    if raw:
        value=json.loads(raw)
        if not isinstance(value,dict): raise ValueError("STEGVERSE_REPO_ROOTS_JSON_OBJECT_REQUIRED")
        for repo,path in value.items():
            if isinstance(repo,str) and isinstance(path,str):
                p=Path(path).expanduser().resolve()
                if p.is_dir(): out[repo]=p
    explicit=env.get("STEGVERSE_TVC_ROOT","").strip()
    if explicit:
        p=Path(explicit).expanduser().resolve()
        if p.is_dir(): out[TVC_REPO]=p
    return out

def _run(args:list[str],cwd:Path,*,timeout:int=300,env:dict[str,str]|None=None)->tuple[int,dict[str,Any]|None,str]:
    clean={"PATH":os.environ.get("PATH",""),"HOME":os.environ.get("HOME",str(Path.home())),"LANG":os.environ.get("LANG","C.UTF-8"),"LC_ALL":os.environ.get("LC_ALL","C.UTF-8")}
    if env: clean.update(env)
    p=subprocess.run(args,cwd=cwd,env=clean,text=True,capture_output=True,check=False,timeout=timeout)
    return p.returncode,_json_tail(p.stdout),p.stderr[-2000:]

def _blocked(reason:str,**extra:Any)->dict[str,Any]:
    return {"schema":"stegverse.tvc.intr_resident_activation_worker/v1","state":"BLOCKED","transition_id":reason,"task_id":TASK_ID,"credential_authority":"TV/TVC","provider_operation_authorized":False,"provider_operation_started":False,"site_repository_mutated":False,"new_credential_value_accepted":False,**extra}

def execute(env:dict[str,str]|None=None)->dict[str,Any]:
    values=dict(os.environ if env is None else env)
    hosted=[x for x in HOSTED_ENV if truthy(values.get(x))]
    if hosted: return _blocked("HOSTED_SURFACE_REJECTED",hosted=sorted(hosted))
    forbidden=[x for x in FORBIDDEN_CREDENTIAL_ENV if values.get(x)]
    if forbidden: return _blocked("FORBIDDEN_CREDENTIAL_ENV",forbidden=sorted(forbidden))
    if not hasattr(os,"geteuid") or os.geteuid()!=0: return _blocked("TVC_RESIDENT_ROOT_AUTHORITY_REQUIRED")
    roots=_roots(values); tvc=roots.get(TVC_REPO)
    if tvc is None: return _blocked("TVC_LOCAL_REPOSITORY_NOT_MATERIALIZED")
    required=[
        "scripts/activate_coinbase_intr_resident.py",
        "scripts/observe_coinbase_intr_resident_readiness.py",
        "scripts/observe_coinbase_service_gateway_route.py",
        "scripts/project_coinbase_owner_ingress_site_config.py",
    ]
    missing=[x for x in required if not (tvc/x).is_file()]
    if missing: return _blocked("TVC_INTR_ACTIVATION_SOURCE_INCOMPLETE",missing=missing)

    common={"PYTHONPATH":str(tvc)}
    rc,ready,_=_run([sys.executable,"scripts/observe_coinbase_intr_resident_readiness.py"],tvc,timeout=30,env=common)
    if rc==0 and ready and ready.get("ready_for_owner_ingress") is True:
        return _project(tvc,ready,common,activation_performed=False,route_observation_performed=False)

    reason=str((ready or {}).get("reason") or "")
    state=str((ready or {}).get("state") or "")
    key_stack_present=state=="BLOCKED_RESIDENT_BINDING_INVALID" and ("route observation" in reason)
    activation_performed=False
    if not key_stack_present:
        gateway=values.get("STEGVERSE_COINBASE_GATEWAY_STORAGE_ROOT","").strip()
        custody=values.get("STEGVERSE_KV_CUSTODY_ROOT","").strip()
        if not gateway or not custody:
            return _blocked("RESIDENT_STORAGE_BINDINGS_REQUIRED",readiness=ready)
        gp=Path(gateway).expanduser().resolve(); cp=Path(custody).expanduser().resolve()
        if not gp.is_dir() or not cp.is_dir():
            return _blocked("RESIDENT_STORAGE_BINDINGS_INVALID",gateway_storage_root=str(gp),tvc_custody_root=str(cp))
        rc,activated,stderr=_run([
            sys.executable,"scripts/activate_coinbase_intr_resident.py",
            "--gateway-storage-root",str(gp),"--tvc-custody-root",str(cp),"--repo-root",str(tvc)
        ],tvc,timeout=900,env=common)
        if rc!=0 or not activated:
            return _blocked("TVC_RESIDENT_ACTIVATION_FAILED",activation=activated,stderr_tail=stderr)
        if activated.get("provider_operation_started") is not False or activated.get("credential_values_provisioned") is not False:
            return _blocked("TVC_RESIDENT_ACTIVATION_AUTHORITY_BOUNDARY_INVALID",activation=activated)
        activation_performed=True

    node_url=values.get("STEGVERSE_COINBASE_PUBLIC_NODE_URL","").strip()
    route_performed=False
    if node_url:
        rc,route,stderr=_run([
            sys.executable,"scripts/observe_coinbase_service_gateway_route.py",
            "--node-url",node_url,"--output",str(ROUTE_OBS)
        ],tvc,timeout=30,env=common)
        if rc!=0 or not route or route.get("state")!="OBSERVED":
            return _blocked("PUBLIC_INTR_ROUTE_OBSERVATION_FAILED",route_observation=route,stderr_tail=stderr,activation_performed=activation_performed)
        route_performed=True

    rc,ready,stderr=_run([sys.executable,"scripts/observe_coinbase_intr_resident_readiness.py"],tvc,timeout=30,env=common)
    if rc!=0 or not ready or ready.get("ready_for_owner_ingress") is not True:
        return _blocked("READY_FOR_OWNER_INGRESS_NOT_OBSERVED",readiness=ready,stderr_tail=stderr,activation_performed=activation_performed,route_observation_performed=route_performed)
    return _project(tvc,ready,common,activation_performed=activation_performed,route_observation_performed=route_performed)

def _project(tvc:Path,ready:dict[str,Any],common:dict[str,str],*,activation_performed:bool,route_observation_performed:bool)->dict[str,Any]:
    rc,projection,stderr=_run([
        sys.executable,"scripts/project_coinbase_owner_ingress_site_config.py",
        "--activation",str(ACTIVATION),"--liveness",str(LIVENESS),
        "--route-observation",str(ROUTE_OBS),"--output",str(SITE_PROJECTION)
    ],tvc,timeout=30,env=common)
    if rc!=0 or not SITE_PROJECTION.is_file():
        return _blocked("SITE_OWNER_INGRESS_PROJECTION_FAILED",projection=projection,stderr_tail=stderr)
    value=json.loads(SITE_PROJECTION.read_text(encoding="utf-8"))
    if value.get("ready_for_owner_ingress") is not True or value.get("provider_operation_authorized") is not False or value.get("provider_operation_started") is not False:
        return _blocked("SITE_OWNER_INGRESS_PROJECTION_AUTHORITY_BOUNDARY_INVALID")
    return {
        "schema":"stegverse.tvc.intr_resident_activation_worker/v1",
        "state":"COMPLETED","transition_id":"TVC_INTR_READY_FOR_OWNER_INGRESS",
        "task_id":TASK_ID,"credential_authority":"TV/TVC",
        "ready_for_owner_ingress":True,
        "activation_performed":activation_performed,
        "route_observation_performed":route_observation_performed,
        "recipient_key_id":ready.get("recipient_key_id"),
        "runtime_instance_id":ready.get("runtime_instance_id"),
        "public_route_observation_digest":ready.get("public_intr_route_observation_digest"),
        "site_projection_path":str(SITE_PROJECTION),
        "provider_operation_authorized":False,"provider_operation_started":False,
        "site_repository_mutated":False,"new_credential_value_accepted":False,
        "authority_effect":"TVC_RESIDENT_INTR_ACTIVATION_ONLY",
    }

def main()->int:
    invocation=json.load(sys.stdin)
    task=invocation.get("task") or {}
    if invocation.get("schema")!="stegverse.worker-invocation/v0.1" or task.get("task_id")!=TASK_ID:
        return 2
    result=execute()
    response={
        "schema":"stegverse.worker-response/v0.1",
        "state":result["state"],
        "transition_id":result["transition_id"],
        "transition_sequence":1,
        "expected_next_transition":None if result["state"]=="COMPLETED" else "RETRY_AFTER_RUNTIME_PREDICATE_CHANGE",
        "checkpoint_ref":"StegVerse-Labs/TVC/tasks/TVC-COINBASE-RESIDENT-ACTIVATION-091.json",
        "evidence_refs":["StegVerse-Labs/TVC/docs/TVC_COINBASE_IPHONE_SKAP_ACTIVATION_MIRROR_HANDOFF.md"],
        "cost_observation":{"hb_transition_count":0,"compute_units":2,"external_cost_usd":0,"task_class":"tvc_intr_resident_activation"},
        "result":result,
    }
    json.dump(response,sys.stdout,sort_keys=True); sys.stdout.write("\n")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
