#!/usr/bin/env python3
"""Resolve/materialize a Personal KnowledgeVault runtime root from a private provider binding.

Credential authority remains TV/TVC. This wrapper never accepts a bearer token value
in arguments or environment; only a path to a TV/TVC-owned ephemeral session file.
"""
from __future__ import annotations
import argparse, importlib.util, json, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

KV_SOURCE_ROOT_ENV="STEGVERSE_KV_SOURCE_ROOT"
KV_ROOT_ENV="STEGVERSE_KV_ROOT"
BINDING_PATH_ENV="STEGVERSE_KV_PROVIDER_BINDING_PATH"
MATERIALIZED_ROOT_ENV="STEGVERSE_KV_PROVIDER_MATERIALIZED_ROOT"
SESSION_FILE_ENV="STEGVERSE_TVC_PROVIDER_SESSION_FILE"
RECEIPT_REL=Path("control/kv-provider-materialization/latest.json")

class KVProviderMaterializationError(ValueError): pass

def _load_module(source_root:Path):
    path=(source_root/"runtime/personal_provider_binding.py").resolve()
    if not path.is_file(): raise KVProviderMaterializationError("personal_provider_binding_source_missing")
    spec=importlib.util.spec_from_file_location("stegverse_personal_provider_binding",path)
    if spec is None or spec.loader is None: raise KVProviderMaterializationError("personal_provider_binding_loader_unavailable")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for name in ("validate_binding","materialize_google_drive_scope"):
        if not hasattr(module,name): raise KVProviderMaterializationError("personal_provider_binding_entrypoint_missing:"+name)
    return module

def _read_binding(path:Path)->dict[str,Any]:
    p=path.expanduser().resolve()
    if not p.is_file(): raise KVProviderMaterializationError("private_provider_binding_missing")
    try:value=json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc: raise KVProviderMaterializationError("private_provider_binding_invalid_json") from exc
    if not isinstance(value,dict): raise KVProviderMaterializationError("private_provider_binding_object_required")
    return value

def resolve_kv_root(env:dict[str,str],runtime_root:Path)->tuple[Path,dict[str,Any]]:
    explicit=(env.get(KV_ROOT_ENV) or "").strip()
    if explicit:
        root=Path(explicit).expanduser().resolve()
        if root.is_dir():
            return root,{"schema":"stegverse.kv.runtime-root-resolution/v1","state":"EXISTING_LOCAL_ROOT","kv_root":str(root),"provider_materialization_performed":False,"credential_material_persisted":False,"authority_effect":"NONE"}
    source=(env.get(KV_SOURCE_ROOT_ENV) or "").strip()
    binding=(env.get(BINDING_PATH_ENV) or "").strip()
    materialized=(env.get(MATERIALIZED_ROOT_ENV) or "").strip()
    session_file=(env.get(SESSION_FILE_ENV) or "").strip()
    if not source: raise KVProviderMaterializationError("portable_kv_source_root_missing")
    if not binding: raise KVProviderMaterializationError("kv_provider_binding_path_missing")
    if not materialized: raise KVProviderMaterializationError("kv_provider_materialized_root_missing")
    if not session_file: raise KVProviderMaterializationError("tvc_provider_session_file_missing")
    module=_load_module(Path(source).expanduser().resolve())
    value=module.validate_binding(_read_binding(Path(binding)))
    if value.get("compatibility_state") not in {"ASSEMBLED_UNVERIFIED","VERIFIED","REVALIDATION_REQUIRED","BLOCKED_RUNTIME"}:
        raise KVProviderMaterializationError("kv_provider_binding_not_materializable:"+str(value.get("compatibility_state")))
    destination=Path(materialized).expanduser().resolve()
    receipt=module.materialize_google_drive_scope(binding=value,token_file=Path(session_file),destination_root=destination)
    receipt["resolved_at"]=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    receipt["runtime_root_resolution"]="PROVIDER_MATERIALIZED_ROOT"
    receipt["provider_binding_path"]=str(Path(binding).expanduser().resolve())
    receipt["provider_session_reference_class"]="TVC_EPHEMERAL_PROVIDER_SESSION"
    receipt["credential_material_persisted"]=False
    receipt["authority_effect"]="NONE"
    target=runtime_root/RECEIPT_REL;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return destination,receipt

def env_with_resolved_kv_root(env:dict[str,str],runtime_root:Path)->tuple[dict[str,str],dict[str,Any]]:
    root,receipt=resolve_kv_root(env,runtime_root)
    updated=dict(env);updated[KV_ROOT_ENV]=str(root)
    return updated,receipt

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--runtime-root",type=Path,required=True)
    p.add_argument("--source-root",type=Path)
    p.add_argument("--binding",type=Path)
    p.add_argument("--materialized-root",type=Path)
    p.add_argument("--session-file",type=Path)
    a=p.parse_args()
    env=dict(os.environ)
    if a.source_root:env[KV_SOURCE_ROOT_ENV]=str(a.source_root)
    if a.binding:env[BINDING_PATH_ENV]=str(a.binding)
    if a.materialized_root:env[MATERIALIZED_ROOT_ENV]=str(a.materialized_root)
    if a.session_file:env[SESSION_FILE_ENV]=str(a.session_file)
    root,receipt=resolve_kv_root(env,a.runtime_root.expanduser().resolve())
    print(json.dumps({"state":"KV_ROOT_RESOLVED","kv_root":str(root),"receipt":receipt},sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
