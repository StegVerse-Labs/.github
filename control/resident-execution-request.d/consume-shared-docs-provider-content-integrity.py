#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, sys
from pathlib import Path
from typing import Any, Mapping

TASK_ID="SHARED-DOCS-PROVIDER-FREEZE-INTEGRATION-001"
SELECTOR="shared_docs_provider_content_integrity"
REQUEST_REL=Path("control/resident-execution-request.d/shared-docs-provider-content-integrity-001.json")
RECEIPT_REL=Path("receipts/sovereign-host/shared-docs-provider-content-integrity.latest.json")
TVC_RUNTIME="tvc_external_collab_google_drive_content_integrity_runtime.py"
CONTENT_PROFILE="google-drive.downloaded-bytes.v1"
HOSTED=("GITHUB_ACTIONS","CI","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")
TVC_CANDIDATES=(Path.home()/".stegverse/repos/StegVerse-Labs/TVC",Path("/srv/stegverse/repos/StegVerse-Labs/TVC"),Path("/opt/stegverse/repos/StegVerse-Labs/TVC"),Path("/var/lib/stegverse/source/StegVerse-Labs/TVC"))

def _load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text());
    if not isinstance(v,dict): raise RuntimeError("json object required")
    return v

def _hash(v:Any)->str:
    return "sha256:"+hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def _write(p:Path,v:Mapping[str,Any])->None:
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_name("."+p.name+".tmp"); t.write_text(json.dumps(dict(v),sort_keys=True,separators=(",",":"))+"\n"); os.replace(t,p)

def _base(state:str)->dict[str,Any]:
    return {"schema":"stegverse.resident-execution-request-consumption/v1","state":state,"task_id":TASK_ID,"selector":SELECTOR,"credential_authority":"TV/TVC","provider_operation_authority_transferred":False,"provider_mutation_performed":False,"github_token_runtime_authority":"NONE","heartbeat_grants_execution_authority":False,"second_machine_required":False,"authority_effect":"NONE_CONTENT_INTEGRITY_OBSERVATION_ONLY"}

def _validate(v:Mapping[str,Any])->dict[str,Any]:
    expected={"schema":"stegverse.resident-execution-request/v1","state":"REQUESTED","task_id":TASK_ID,"mode":"TARGETED_INDEPENDENT_TASK_CONTROL","selector":SELECTOR,"credential_authority":"TV/TVC","github_token_required":False,"github_token_runtime_authority":"NONE","heartbeat_grants_execution_authority":False,"second_machine_required":False,"credential_material_allowed":False,"provider_mutation_allowed":False,"request_granted_authority":False,"authority_effect":"NONE_REQUEST_ONLY"}
    for k,w in expected.items():
        if v.get(k)!=w: raise RuntimeError(f"outer {k} mismatch")
    p=v.get("provider_request")
    if not isinstance(p,Mapping): raise RuntimeError("provider_request missing")
    req={"schema":"stegverse.tvc.external-collaboration-google-drive-content-integrity-request/v1","content_profile":CONTENT_PROFILE,"read_only":True,"provider_mutation_allowed":False}
    for k,w in req.items():
        if p.get(k)!=w: raise RuntimeError(f"provider {k} mismatch")
    if not isinstance(p.get("request_id"),str) or len(p["request_id"])<16: raise RuntimeError("request_id invalid")
    if not isinstance(p.get("binding_id"),str) or not p["binding_id"].startswith("wsprobe_"): raise RuntimeError("binding_id invalid")
    if not isinstance(p.get("provider_file_id"),str) or not 3<=len(p["provider_file_id"])<=256: raise RuntimeError("provider_file_id invalid")
    if not isinstance(p.get("probe_reason"),str) or not p["probe_reason"].strip(): raise RuntimeError("probe_reason invalid")
    raw=json.dumps(v).lower()
    if any(x in raw for x in ("access_token","refresh_token","client_secret","authorization","bearer ","password")): raise RuntimeError("credential material prohibited")
    return dict(p)

def _tvc_root(env:Mapping[str,str])->Path|None:
    cs=[]; explicit=str(env.get("STEGVERSE_TVC_ROOT") or "").strip()
    if explicit: cs.append(Path(explicit).expanduser())
    cs.extend(TVC_CANDIDATES)
    for c in cs:
        r=c.resolve()
        if (r/TVC_RUNTIME).is_file(): return r
    return None

def consume(source_root:Path,runtime_root:Path,environ:Mapping[str,str]|None=None)->dict[str,Any]:
    del source_root; rt=runtime_root.resolve(); reqp=rt/REQUEST_REL; out=rt/RECEIPT_REL
    if not reqp.is_file():
        r=_base("INPUT_NOT_MATERIALIZED"); r["reason"]="RESIDENT_CONTENT_INTEGRITY_REQUEST_ABSENT"; _write(out,r); return r
    env=dict(os.environ if environ is None else environ)
    if any(str(env.get(k) or "").strip().lower() not in {"","0","false","no"} for k in HOSTED):
        r=_base("BLOCKED"); r["reason"]="HOSTED_ENVIRONMENT_PROHIBITED"; _write(out,r); return r
    outer=_load(reqp)
    try: p=_validate(outer)
    except Exception as e:
        r=_base("BLOCKED"); r.update(reason="REQUEST_INVALID:"+str(e),request_sha256=_hash(outer)); _write(out,r); return r
    tvc=_tvc_root(env)
    if tvc is None:
        r=_base("INPUT_NOT_MATERIALIZED"); r.update(reason="TVC_CONTENT_INTEGRITY_RUNTIME_NOT_MATERIALIZED",request_sha256=_hash(outer)); _write(out,r); return r
    try:
        if str(tvc) not in sys.path: sys.path.insert(0,str(tvc))
        spec=importlib.util.spec_from_file_location("shared_docs_tvc_content_integrity",tvc/TVC_RUNTIME)
        if spec is None or spec.loader is None: raise RuntimeError("runtime import unavailable")
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        result=mod.execute(p,broker_socket=str(env.get("STEGTV_PROVIDER_OPERATION_VAULT_BROKER_SOCKET") or "/run/stegverse/vault-broker.sock"))
    except Exception as e:
        r=_base("BLOCKED"); r.update(reason="PROVIDER_CONTENT_INTEGRITY_EXECUTION_FAILED:"+type(e).__name__,request_sha256=_hash(outer),tvc_root=str(tvc)); _write(out,r); return r
    digest=result.get("provider_content_sha256"); version=result.get("provider_version_id")
    ok=(result.get("schema")=="stegverse.tvc.external-collaboration-google-drive-content-integrity-result/v1" and result.get("provider_file_id")==p["provider_file_id"] and result.get("content_profile")==CONTENT_PROFILE and result.get("credential_authority")=="TV/TVC" and result.get("credential_material_exported") is False and result.get("provider_operation_authority_transferred") is False and result.get("provider_mutation_performed") is False and isinstance(digest,str) and digest.startswith("sha256:") and len(digest)==71 and isinstance(version,str) and bool(version))
    if not ok:
        r=_base("BLOCKED"); r.update(reason="TVC_RESULT_CONTRACT_MISMATCH",request_sha256=_hash(outer)); _write(out,r); return r
    r=_base("COMPLETED"); r.update(request_sha256=_hash(outer),provider_file_id=p["provider_file_id"],provider_version_id=version,provider_content_sha256=digest,content_profile=CONTENT_PROFILE,provider_result_sha256=_hash(result),lease_receipt_sha256=result.get("lease_receipt_sha256"),tvc_root=str(tvc),authentic_provider_observation_claimed=True); _write(out,r); return r

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--source-root",type=Path,required=True); ap.add_argument("--runtime-root",type=Path,required=True); a=ap.parse_args(); r=consume(a.source_root,a.runtime_root); print(json.dumps(r,sort_keys=True)); return 0 if r.get("state") in {"COMPLETED","INPUT_NOT_MATERIALIZED","BLOCKED"} else 1
if __name__=="__main__": raise SystemExit(main())
