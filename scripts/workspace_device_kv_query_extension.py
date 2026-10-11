#!/usr/bin/env python3
"""Bounded Personal Workspace projection extension for the DEVICE_KV endpoint handler."""
from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Any

RECORD_CLASS="WORKSPACE_PERSONAL_PROJECTION"
TASKS_RECORD_CLASS="WORKSPACE_TASKS_PROJECTION"
FAMILY_RECORD_CLASS="WORKSPACE_FAMILY_PROJECTIONS"
CHECKPOINT_RECORD_CLASS="WORKSPACE_CONTINUITY_CHECKPOINT"
REQUESTER={"module":"Site","component":"Workspace"}
SCOPES=["workspace_identity","principals","relationships","organizations","memberships","feed","assistant"]
TASKS_SCOPES=["tasks","commitments","timeline"]
FAMILY_SCOPES=["projections"]
CHECKPOINT_SCOPES=["checkpoint","decision"]
SELECTOR={"workspace_type":"PERSONAL"}
WORKSPACE_PROJECTION_REL=Path("runtime/workspace_projection.py")
# Each admitted record class binds exactly one continuity-vault-kit producer, its entrypoint, scope list and output schema.
# Both producers read only the owner's Personal KV (_System/Workspace); neither writes, contacts a provider or grants authority.
RECORD_CLASSES={
 RECORD_CLASS:{"scopes":SCOPES,"source":WORKSPACE_PROJECTION_REL,"entrypoint":"get_personal_workspace_projection","schema":"stegverse.kv.personal-workspace-projection/v1"},
 TASKS_RECORD_CLASS:{"scopes":TASKS_SCOPES,"source":Path("runtime/workspace_tasks_projection.py"),"entrypoint":"get_personal_tasks_projection","schema":"stegverse.kv.workspace-tasks-projection/v1"},
 FAMILY_RECORD_CLASS:{"scopes":FAMILY_SCOPES,"source":Path("runtime/workspace_family_projections.py"),"entrypoint":"get_personal_family_projections","schema":"stegverse.kv.workspace-family-projections/v1"},
 CHECKPOINT_RECORD_CLASS:{"scopes":CHECKPOINT_SCOPES,"source":Path("runtime/workspace_continuity_checkpoint_projection.py"),"entrypoint":"get_personal_continuity_checkpoint","schema":"stegverse.kv.workspace-continuity-checkpoint-delivery/v1"},
}

class WorkspaceDeviceKVQueryError(ValueError): pass

def validate_workspace_query(query:dict[str,Any],*,node_id:str)->dict[str,Any]:
    if query.get("schema_version")!="kv.interlock.request.v1" or query.get("operation")!="REQUEST": raise WorkspaceDeviceKVQueryError("workspace_query_schema_invalid")
    binding=RECORD_CLASSES.get(query.get("record_class")) if isinstance(query.get("record_class"),str) else None
    if binding is None: raise WorkspaceDeviceKVQueryError("workspace_query_record_class_invalid")
    if query.get("requester")!=REQUESTER: raise WorkspaceDeviceKVQueryError("workspace_query_requester_invalid")
    if query.get("requested_scope")!=binding["scopes"]: raise WorkspaceDeviceKVQueryError("workspace_query_scope_invalid")
    if query.get("selector")!=SELECTOR: raise WorkspaceDeviceKVQueryError("workspace_query_selector_invalid")
    if query.get("disclosure_mode")!="BOUNDED_CONTEXT": raise WorkspaceDeviceKVQueryError("workspace_query_disclosure_invalid")
    if query.get("authority_ref")!="stegos-node://"+node_id: raise WorkspaceDeviceKVQueryError("workspace_query_node_binding_invalid")
    if not isinstance(query.get("request_id"),str) or not query["request_id"]: raise WorkspaceDeviceKVQueryError("workspace_query_request_id_required")
    if not isinstance(query.get("purpose"),str) or not query["purpose"]: raise WorkspaceDeviceKVQueryError("workspace_query_purpose_required")
    if not isinstance(query.get("minimum_necessary_justification"),str) or not query["minimum_necessary_justification"]: raise WorkspaceDeviceKVQueryError("workspace_query_minimum_necessary_required")
    return query

def _load(source_root:Path,binding:dict[str,Any]|None=None):
    binding=binding or RECORD_CLASSES[RECORD_CLASS]
    path=(source_root/binding["source"]).resolve()
    if not path.is_file(): raise WorkspaceDeviceKVQueryError("workspace_projection_source_missing")
    spec=importlib.util.spec_from_file_location("stegverse_cvk_"+path.stem,path)
    if spec is None or spec.loader is None: raise WorkspaceDeviceKVQueryError("workspace_projection_loader_unavailable")
    # The tasks producer imports runtime.workspace_projection relatively; expose the CVK source root for that import only.
    import sys
    added=False
    if str(source_root) not in sys.path: sys.path.insert(0,str(source_root)); added=True
    try:
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    finally:
        if added: sys.path.remove(str(source_root))
    if not hasattr(module,binding["entrypoint"]): raise WorkspaceDeviceKVQueryError("workspace_projection_entrypoint_missing")
    return module

def execute_workspace_query(*,query:dict[str,Any],node_id:str,kv_source_root:Path,kv_data_root:Path)->dict[str,Any]:
    validate_workspace_query(query,node_id=node_id)
    binding=RECORD_CLASSES[query["record_class"]]
    try: projection=getattr(_load(kv_source_root,binding),binding["entrypoint"])(kv_data_root=kv_data_root)
    except Exception as exc: raise WorkspaceDeviceKVQueryError("workspace_projection_failed:"+type(exc).__name__+":"+str(exc)) from exc
    if not isinstance(projection,dict) or projection.get("schema")!=binding["schema"]: raise WorkspaceDeviceKVQueryError("workspace_projection_invalid")
    if query["record_class"]!=RECORD_CLASS and projection.get("action_authority")!="NONE": raise WorkspaceDeviceKVQueryError("workspace_projection_authority_invalid")
    # A checkpoint delivery can never carry a verified decision from the KV reader (no anchor verifier there).
    if query["record_class"]==CHECKPOINT_RECORD_CLASS:
        decision=projection.get("decision")
        if projection.get("anchor_verified") is not False or (decision is not None and (not isinstance(decision,dict) or decision.get("disposition")=="ALLOW")): raise WorkspaceDeviceKVQueryError("workspace_projection_authority_invalid")
    if projection.get("workspace_type")!="PERSONAL" or projection.get("credential_material_present") is not False or projection.get("provider_operation_authorized") is not False or projection.get("workspace_grants_authority") is not False or projection.get("authority_effect")!="NONE": raise WorkspaceDeviceKVQueryError("workspace_projection_authority_invalid")
    return projection
