#!/usr/bin/env python3
"""Bounded Personal Workspace projection extension for the DEVICE_KV endpoint handler."""
from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Any

RECORD_CLASS="WORKSPACE_PERSONAL_PROJECTION"
REQUESTER={"module":"Site","component":"Workspace"}
SCOPES=["workspace_identity","principals","relationships","organizations","memberships","feed","assistant"]
SELECTOR={"workspace_type":"PERSONAL"}
WORKSPACE_PROJECTION_REL=Path("runtime/workspace_projection.py")

class WorkspaceDeviceKVQueryError(ValueError): pass

def validate_workspace_query(query:dict[str,Any],*,node_id:str)->dict[str,Any]:
    if query.get("schema_version")!="kv.interlock.request.v1" or query.get("operation")!="REQUEST": raise WorkspaceDeviceKVQueryError("workspace_query_schema_invalid")
    if query.get("record_class")!=RECORD_CLASS: raise WorkspaceDeviceKVQueryError("workspace_query_record_class_invalid")
    if query.get("requester")!=REQUESTER: raise WorkspaceDeviceKVQueryError("workspace_query_requester_invalid")
    if query.get("requested_scope")!=SCOPES: raise WorkspaceDeviceKVQueryError("workspace_query_scope_invalid")
    if query.get("selector")!=SELECTOR: raise WorkspaceDeviceKVQueryError("workspace_query_selector_invalid")
    if query.get("disclosure_mode")!="BOUNDED_CONTEXT": raise WorkspaceDeviceKVQueryError("workspace_query_disclosure_invalid")
    if query.get("authority_ref")!="stegos-node://"+node_id: raise WorkspaceDeviceKVQueryError("workspace_query_node_binding_invalid")
    if not isinstance(query.get("request_id"),str) or not query["request_id"]: raise WorkspaceDeviceKVQueryError("workspace_query_request_id_required")
    if not isinstance(query.get("purpose"),str) or not query["purpose"]: raise WorkspaceDeviceKVQueryError("workspace_query_purpose_required")
    if not isinstance(query.get("minimum_necessary_justification"),str) or not query["minimum_necessary_justification"]: raise WorkspaceDeviceKVQueryError("workspace_query_minimum_necessary_required")
    return query

def _load(source_root:Path):
    path=(source_root/WORKSPACE_PROJECTION_REL).resolve()
    if not path.is_file(): raise WorkspaceDeviceKVQueryError("workspace_projection_source_missing")
    spec=importlib.util.spec_from_file_location("stegverse_cvk_workspace_projection",path)
    if spec is None or spec.loader is None: raise WorkspaceDeviceKVQueryError("workspace_projection_loader_unavailable")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    if not hasattr(module,"get_personal_workspace_projection"): raise WorkspaceDeviceKVQueryError("workspace_projection_entrypoint_missing")
    return module

def execute_workspace_query(*,query:dict[str,Any],node_id:str,kv_source_root:Path,kv_data_root:Path)->dict[str,Any]:
    validate_workspace_query(query,node_id=node_id)
    try: projection=_load(kv_source_root).get_personal_workspace_projection(kv_data_root=kv_data_root)
    except Exception as exc: raise WorkspaceDeviceKVQueryError("workspace_projection_failed:"+type(exc).__name__+":"+str(exc)) from exc
    if not isinstance(projection,dict) or projection.get("schema")!="stegverse.kv.personal-workspace-projection/v1": raise WorkspaceDeviceKVQueryError("workspace_projection_invalid")
    if projection.get("workspace_type")!="PERSONAL" or projection.get("credential_material_present") is not False or projection.get("provider_operation_authorized") is not False or projection.get("workspace_grants_authority") is not False or projection.get("authority_effect")!="NONE": raise WorkspaceDeviceKVQueryError("workspace_projection_authority_invalid")
    return projection
