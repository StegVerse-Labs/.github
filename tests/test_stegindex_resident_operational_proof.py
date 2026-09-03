from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
S=importlib.util.spec_from_file_location("verifier",ROOT/"scripts/verify_stegindex_resident_operational_proof.py")
M=importlib.util.module_from_spec(S); assert S.loader; S.loader.exec_module(M)

def write_json(path:Path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding="utf-8")

def one_shot():
    return {
      "schema":"stegverse.resident-execution-request-consumption/v1",
      "state":"ALREADY_CONSUMED",
      "source_root_resolution_observed":True,
      "resolved_source_roots":["ae","healer","llm","master_records","micro_node","stegindex","stegos","tt","tv","tvc"],
      "missing_source_roots":[],
      "stegindex_source_root_resolved":True,
      "network_source_fetch_performed":False,
      "github_token_runtime_authority":"NONE",
      "credential_authority":"TV/TVC",
      "authority_effect":"NONE_REQUEST_ONLY",
    }

def preflight():
    return {
      "schema":"stegverse.stegindex-resolution-admission-preflight/v1",
      "parent_task_id":"PARENT-1",
      "heartbeat_epoch":42,
      "preflight":{
        "state":"RESOLVED",
        "canonical_resolver_invoked":True,
        "authority_effect":"NONE_READ_RESOLVE_ONLY",
      },
      "network_fetch_performed":False,
      "github_token_required":False,
      "credential_authority":"TV/TVC",
      "authority_effect":"NONE_READ_RESOLVE_ONLY",
    }

def test_complete_requires_both_resident_predicates():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        write_json(root/M.ONE_SHOT_REL,one_shot())
        write_json(root/M.PREFLIGHT_DIR/"p.json",preflight())
        out=M.verify(root)
        assert out["state"]=="COMPLETE"
        assert all(out["predicates"].values())
        assert out["preflight_parent_task_id"]=="PARENT-1"
        assert out["runtime_activation_claimed"] is False

def test_root_only_is_incomplete():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        write_json(root/M.ONE_SHOT_REL,one_shot())
        out=M.verify(root)
        assert out["state"]=="INCOMPLETE"
        assert out["predicates"]["stegindex_resident_source_root_resolved"] is True
        assert out["predicates"]["stegindex_resolution_admission_preflight_receipt_observed"] is False

def test_preflight_unavailable_does_not_satisfy():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        write_json(root/M.ONE_SHOT_REL,one_shot())
        row=preflight(); row["preflight"]["state"]="PREFLIGHT_UNAVAILABLE"; row["preflight"]["canonical_resolver_invoked"]=False
        write_json(root/M.PREFLIGHT_DIR/"p.json",row)
        out=M.verify(root)
        assert out["state"]=="INCOMPLETE"
        assert out["predicates"]["stegindex_resolution_admission_preflight_receipt_observed"] is False

def test_non_tvtvc_or_network_receipt_does_not_satisfy():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        write_json(root/M.ONE_SHOT_REL,one_shot())
        row=preflight(); row["network_fetch_performed"]=True
        write_json(root/M.PREFLIGHT_DIR/"p.json",row)
        out=M.verify(root)
        assert out["state"]=="INCOMPLETE"
