#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

TASK_ID="KV-PROVIDER-CHANGE-OBSERVER-001"
HOSTED_ENV=("GITHUB_ACTIONS","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
FORBIDDEN_ENV=("GITHUB_TOKEN","GH_TOKEN","HEALER_GH_TOKEN","COINBASE_API_KEY","COINBASE_API_SECRET","COINBASE_PRIVATE_KEY","OPENAI_API_KEY","ANTHROPIC_API_KEY")
ALLOWED_SOURCE_TYPES={"provider_documentation","provider_changelog","provider_status"}
ALLOWED_CHANGE_CLASSES={"api_version","authentication","mfa_session","endpoint","deprecation","changelog","sdk_dependency","rate_limit","permission_scope","product_model","data_schema","export_format","browser_platform","service_health"}
MAX_BYTES=2_000_000

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def truthy(v: str|None)->bool:
    return str(v or "").strip().lower() not in ("","0","false","no")

def _now()->str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def _blocked(reason:str,**extra:Any)->dict[str,Any]:
    return {
        "schema":"stegverse.kv.provider-change-observer-worker/v1",
        "state":"BLOCKED","transition_id":reason,"task_id":TASK_ID,
        "provider_operation_authorized":False,
        "credential_material_present":False,
        "authenticated_provider_request":False,
        "authority_effect":"NONE",
        **extra,
    }

def _safe_target(target:dict[str,Any])->tuple[bool,str]:
    required=("target_id","provider","url","allowed_host","source_type","change_class","severity","affected_assumptions")
    missing=[k for k in required if not target.get(k) and target.get(k) != []]
    if missing: return False,"TARGET_FIELDS_MISSING:"+",".join(missing)
    parsed=urllib.parse.urlparse(str(target["url"]))
    if parsed.scheme!="https": return False,"TARGET_HTTPS_REQUIRED"
    if parsed.username or parsed.password: return False,"TARGET_EMBEDDED_CREDENTIAL_PROHIBITED"
    if parsed.hostname != target["allowed_host"]: return False,"TARGET_HOST_BINDING_MISMATCH"
    if target["source_type"] not in ALLOWED_SOURCE_TYPES: return False,"TARGET_SOURCE_TYPE_NOT_ADMITTED"
    if target["change_class"] not in ALLOWED_CHANGE_CLASSES: return False,"TARGET_CHANGE_CLASS_NOT_ADMITTED"
    return True,"OK"

def _fetch(url:str,allowed_host:str)->bytes:
    request=urllib.request.Request(url,headers={"User-Agent":"StegVerse-KV-Provider-Change-Observer/1","Accept":"text/plain,text/html,application/json,application/xml;q=0.9,*/*;q=0.1"})
    opener=urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(request,timeout=20) as response:
            final=urllib.parse.urlparse(response.geturl())
            if final.scheme!="https" or final.hostname!=allowed_host:
                raise ValueError("SOURCE_REDIRECT_OR_HOST_DRIFT")
            length=response.headers.get("Content-Length")
            if length and int(length)>MAX_BYTES:
                raise ValueError("SOURCE_TOO_LARGE")
            body=response.read(MAX_BYTES+1)
            if len(body)>MAX_BYTES: raise ValueError("SOURCE_TOO_LARGE")
            return body
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            raise ValueError("SOURCE_REDIRECT_PROHIBITED") from exc
        raise

def _fingerprint(body:bytes)->str:
    return "sha256:"+hashlib.sha256(body).hexdigest()

def _observation_id(provider:str,source_ref:str,observed_at:str,change_class:str)->str:
    material="|".join((provider,source_ref,observed_at,change_class)).lower()
    return "kvchg_"+hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]

def _load_targets(path:Path)->list[dict[str,Any]]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict) or value.get("schema")!="stegverse.kv.provider-monitor-targets/v1":
        raise ValueError("MONITOR_TARGET_SCHEMA_INVALID")
    targets=value.get("targets")
    if not isinstance(targets,list) or not targets:
        raise ValueError("MONITOR_TARGETS_EMPTY")
    return targets

def execute(env:dict[str,str]|None=None,*,fetcher:Callable[[str,str],bytes]=_fetch,now:Callable[[],str]=_now)->dict[str,Any]:
    values=dict(os.environ if env is None else env)
    hosted=[k for k in HOSTED_ENV if truthy(values.get(k))]
    if hosted: return _blocked("HOSTED_SURFACE_REJECTED",hosted=sorted(hosted))
    forbidden=[k for k in FORBIDDEN_ENV if values.get(k)]
    if forbidden: return _blocked("FORBIDDEN_CREDENTIAL_ENV",forbidden=sorted(forbidden))
    target_ref=values.get("STEGVERSE_KV_PROVIDER_MONITOR_TARGETS","").strip()
    state_ref=values.get("STEGVERSE_KV_PROVIDER_MONITOR_STATE_ROOT","").strip()
    if not target_ref or not state_ref: return _blocked("MONITOR_BINDINGS_REQUIRED")
    target_path=Path(target_ref).expanduser().resolve()
    state_root=Path(state_ref).expanduser().resolve()
    if not target_path.is_file(): return _blocked("MONITOR_TARGET_FILE_MISSING")
    if not state_root.is_dir(): return _blocked("MONITOR_STATE_ROOT_MISSING")
    try: targets=_load_targets(target_path)
    except Exception as exc: return _blocked("MONITOR_TARGETS_INVALID",detail=str(exc))

    fingerprints=state_root/"fingerprints"; observations=state_root/"observations"
    fingerprints.mkdir(mode=0o750,parents=True,exist_ok=True)
    observations.mkdir(mode=0o750,parents=True,exist_ok=True)
    results=[]; emitted=[]
    for target in targets:
        ok,reason=_safe_target(target)
        if not ok: return _blocked(reason,target_id=target.get("target_id"))
        target_id=str(target["target_id"])
        try: body=fetcher(str(target["url"]),str(target["allowed_host"]))
        except Exception as exc: return _blocked("SOURCE_OBSERVATION_FAILED",target_id=target_id,detail=str(exc))
        observed_at=now(); fp=_fingerprint(body)
        fp_path=fingerprints/f"{target_id}.json"
        prior=None
        if fp_path.is_file():
            try: prior=json.loads(fp_path.read_text(encoding="utf-8")).get("fingerprint")
            except Exception: return _blocked("PRIOR_FINGERPRINT_INVALID",target_id=target_id)
        baseline=prior is None
        changed=prior is not None and prior!=fp
        fp_receipt={
            "schema":"stegverse.kv.provider-source-fingerprint/v1","target_id":target_id,
            "provider":target["provider"],"source_ref":target["url"],"observed_at":observed_at,
            "fingerprint":fp,"prior_fingerprint":prior,"changed":changed,"authority_effect":"NONE"
        }
        fp_path.write_text(json.dumps(fp_receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        if changed:
            obs={
                "schema":"stegverse.kv.source-change-observation/v1",
                "observation_id":_observation_id(str(target["provider"]),str(target["url"]),observed_at,str(target["change_class"])),
                "provider":target["provider"],"observed_at":observed_at,"source_ref":target["url"],
                "source_type":target["source_type"],"change_class":target["change_class"],
                "severity":target["severity"],"breaking":bool(target.get("breaking_on_change",False)),
                "affected_assumptions":list(target.get("affected_assumptions") or []),
                "summary":str(target.get("summary_on_change") or "Authoritative provider source content changed."),
                "effective_at":None,"authority_effect":"NONE"
            }
            obs_path=observations/f"{obs['observation_id']}.json"
            obs_path.write_text(json.dumps(obs,sort_keys=True,indent=2)+"\n",encoding="utf-8")
            emitted.append({"observation_id":obs["observation_id"],"path":str(obs_path)})
        results.append({"target_id":target_id,"baseline_recorded":baseline,"changed":changed,"fingerprint":fp})

    return {
        "schema":"stegverse.kv.provider-change-observer-worker/v1","state":"COMPLETED",
        "transition_id":"KV_PROVIDER_CHANGE_OBSERVATION_CYCLE_COMPLETED","task_id":TASK_ID,
        "target_count":len(results),"emitted_change_count":len(emitted),
        "results":results,"emitted_observations":emitted,
        "provider_operation_authorized":False,"credential_material_present":False,
        "authenticated_provider_request":False,"authority_effect":"NONE"
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
        "checkpoint_ref":"handoffs/KV-PROVIDER-CHANGE-OBSERVER-001.json",
        "evidence_refs":["KV_PROVIDER_CHANGE_OBSERVER_MIRROR_HANDOFF.md"],
        "cost_observation":{"hb_transition_count":0,"compute_units":1,"external_cost_usd":0,"task_class":"kv_provider_change_observation"},
        "result":result
    }
    json.dump(response,sys.stdout,sort_keys=True); sys.stdout.write("\n"); return 0

if __name__=="__main__": raise SystemExit(main())
