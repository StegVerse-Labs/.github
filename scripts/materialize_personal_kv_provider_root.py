#!/usr/bin/env python3
"""Resolve/materialize a Personal KnowledgeVault runtime root from a private provider binding.

Credential-bearing provider processing occurs only inside TV/TVC. This resolver accepts
only a secret-free TVC resident materialization result and never accepts a bearer/session file.
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
RESULT_FILE_ENV="STEGVERSE_TVC_PROVIDER_MATERIALIZATION_RESULT_FILE"
RETIRED_SESSION_FILE_ENV="STEGVERSE_TVC_PROVIDER_SESSION_FILE"
TVC_RESULT_SCHEMA="stegverse.tvc.personal-kv-google-drive-materialization-result/v1"
RECEIPT_REL=Path("control/kv-provider-materialization/latest.json")

class KVProviderMaterializationError(ValueError): pass

def _load_module(source_root:Path):
    path=(source_root/"runtime/personal_provider_binding.py").resolve()
    if not path.is_file(): raise KVProviderMaterializationError("personal_provider_binding_source_missing")
    spec=importlib.util.spec_from_file_location("stegverse_personal_provider_binding",path)
    if spec is None or spec.loader is None: raise KVProviderMaterializationError("personal_provider_binding_loader_unavailable")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for name in ("validate_binding","materialize_broker_result"):
        if not hasattr(module,name): raise KVProviderMaterializationError("personal_provider_binding_entrypoint_missing:"+name)
    return module

def _read_object(path:Path,label:str)->dict[str,Any]:
    p=path.expanduser().resolve()
    if not p.is_file(): raise KVProviderMaterializationError(label+"_missing")
    try:value=json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc: raise KVProviderMaterializationError(label+"_invalid_json") from exc
    if not isinstance(value,dict): raise KVProviderMaterializationError(label+"_object_required")
    return value

def _validate_tvc_result(value:dict[str,Any],binding_id:str)->dict[str,Any]:
    if value.get("schema")!=TVC_RESULT_SCHEMA: raise KVProviderMaterializationError("tvc_materialization_result_schema_invalid")
    if value.get("provider")!="GOOGLE_DRIVE": raise KVProviderMaterializationError("tvc_materialization_result_provider_invalid")
    if value.get("binding_id")!=binding_id: raise KVProviderMaterializationError("tvc_materialization_result_binding_mismatch")
    if value.get("credential_authority")!="TV/TVC": raise KVProviderMaterializationError("tvc_materialization_result_credential_authority_invalid")
    if value.get("credential_material_exported") is not False: raise KVProviderMaterializationError("tvc_materialization_result_credential_export_prohibited")
    if value.get("provider_operation_authority_transferred") is not False: raise KVProviderMaterializationError("tvc_materialization_result_authority_transfer_prohibited")
    if value.get("runtime_activation_claimed") is not False: raise KVProviderMaterializationError("tvc_materialization_result_runtime_claim_invalid")
    broker=value.get("broker_response")
    if not isinstance(broker,dict): raise KVProviderMaterializationError("tvc_materialization_broker_response_missing")
    return broker

def resolve_kv_root(env:dict[str,str],runtime_root:Path)->tuple[Path,dict[str,Any]]:
    explicit=(env.get(KV_ROOT_ENV) or "").strip()
    if explicit:
        root=Path(explicit).expanduser().resolve()
        if root.is_dir():
            return root,{"schema":"stegverse.kv.runtime-root-resolution/v1","state":"EXISTING_LOCAL_ROOT","kv_root":str(root),"provider_materialization_performed":False,"credential_material_persisted":False,"authority_effect":"NONE"}

    if (env.get(RETIRED_SESSION_FILE_ENV) or "").strip():
        raise KVProviderMaterializationError("retired_tvc_provider_session_file_input_prohibited")

    source=(env.get(KV_SOURCE_ROOT_ENV) or "").strip()
    binding_path=(env.get(BINDING_PATH_ENV) or "").strip()
    materialized=(env.get(MATERIALIZED_ROOT_ENV) or "").strip()
    result_file=(env.get(RESULT_FILE_ENV) or "").strip()
    if not source: raise KVProviderMaterializationError("portable_kv_source_root_missing")
    if not binding_path: raise KVProviderMaterializationError("kv_provider_binding_path_missing")
    if not materialized: raise KVProviderMaterializationError("kv_provider_materialized_root_missing")
    if not result_file: raise KVProviderMaterializationError("tvc_provider_materialization_result_file_missing")

    module=_load_module(Path(source).expanduser().resolve())
    binding=module.validate_binding(_read_object(Path(binding_path),"private_provider_binding"))
    if binding.get("compatibility_state") not in {"ASSEMBLED_UNVERIFIED","VERIFIED","REVALIDATION_REQUIRED","BLOCKED_RUNTIME"}:
        raise KVProviderMaterializationError("kv_provider_binding_not_materializable:"+str(binding.get("compatibility_state")))

    tvc_result=_read_object(Path(result_file),"tvc_provider_materialization_result")
    broker_response=_validate_tvc_result(tvc_result,binding["binding_id"])
    destination=Path(materialized).expanduser().resolve()
    receipt=module.materialize_broker_result(binding=binding,broker_response=broker_response,destination_root=destination)
    receipt["resolved_at"]=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    receipt["runtime_root_resolution"]="PROVIDER_MATERIALIZED_ROOT"
    receipt["provider_binding_path"]=str(Path(binding_path).expanduser().resolve())
    receipt["provider_materialization_reference_class"]="TVC_NONSECRET_PROVIDER_MATERIALIZATION_RESULT"
    receipt["tvc_result_request_id"]=tvc_result.get("request_id")
    receipt["tvc_result_request_sha256"]=tvc_result.get("request_sha256")
    receipt["credential_material_persisted"]=False
    receipt["consumer_received_provider_credential"]=False
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
    p.add_argument("--materialization-result",type=Path)
    a=p.parse_args()
    env=dict(os.environ)
    if a.source_root:env[KV_SOURCE_ROOT_ENV]=str(a.source_root)
    if a.binding:env[BINDING_PATH_ENV]=str(a.binding)
    if a.materialized_root:env[MATERIALIZED_ROOT_ENV]=str(a.materialized_root)
    if a.materialization_result:env[RESULT_FILE_ENV]=str(a.materialization_result)
    root,receipt=resolve_kv_root(env,a.runtime_root.expanduser().resolve())
    print(json.dumps({"state":"KV_ROOT_RESOLVED","kv_root":str(root),"receipt":receipt},sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
