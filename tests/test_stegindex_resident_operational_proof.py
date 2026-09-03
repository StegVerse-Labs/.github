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

def test_operational_verifier_is_materialized_by_all_resident_paths():
    refresh=(ROOT/"scripts/refresh_sovereign_worker_runtime_source.py").read_text()
    refresh_base=(ROOT/"scripts/refresh_sovereign_worker_runtime_source_base.py").read_text()
    install=(ROOT/"scripts/install_sovereign_heartbeat_service.py").read_text()
    install_base=(ROOT/"scripts/install_sovereign_heartbeat_service_base.py").read_text()
    bootstrap=(ROOT/"scripts/bootstrap_sovereign_runtime.py").read_text()
    bootstrap_base=(ROOT/"scripts/bootstrap_sovereign_runtime_base.py").read_text()
    needle="verify_stegindex_resident_operational_proof.py"
    for source in (refresh,refresh_base,install,install_base,bootstrap,bootstrap_base):
        assert needle in source

def test_authentic_evidence_producers_refresh_operational_proof():
    engine=(ROOT/"heartbeat_runtime/engine_v10.py").read_text()
    consumer=(ROOT/"scripts/consume_one_shot_resident_stack_activation_request.py").read_text()
    assert "self._refresh_stegindex_operational_proof()" in engine
    assert "verify_stegindex_resident_operational_proof.py" in engine
    assert "refresh_stegindex_operational_proof(runtime)" in consumer
    assert "verify_stegindex_resident_operational_proof.py" in consumer

