#!/usr/bin/env python3
"""Consume the bounded SDK evaluator-governance posture runtime proof request."""
from __future__ import annotations
import argparse, hashlib, json, os, sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/sdk-evaluator-governance-posture-runtime-proof-001.json")
RECEIPT_REL = Path("receipts/sovereign-host/sdk-evaluator-governance-posture-runtime-proof.latest.json")
TARGET_TASK = "SDK-EVALUATOR-GOVERNANCE-POSTURE-RUNTIME-PROOF-001"
TARGET_MODE = "SDK_EVALUATOR_GOVERNANCE_POSTURE_RUNTIME_PROOF"
TARGET_ENTRYPOINT = "stegverse.evaluator_governance_runtime.run_evaluator_governance_manifest"

def load_json(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value

def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate_request(req: dict[str, Any]) -> None:
    expected={
      "schema":"stegverse.resident-execution-request/v1","state":"REQUESTED",
      "task_id":TARGET_TASK,"mode":TARGET_MODE,"entrypoint":TARGET_ENTRYPOINT,
      "credential_authority":"TV/TVC","transition_authority":"Interlock/InTr",
      "sdk_authority_effect":"NONE_TRANSPORT_AND_EVIDENCE_ONLY",
      "github_token_required":False,"github_token_runtime_authority":"NONE",
      "heartbeat_grants_execution_authority":False,"second_machine_required":False,
      "network_source_fetch_allowed":False,"request_granted_authority":False,
      "authority_effect":"NONE_REQUEST_ONLY"
    }
    for key,value in expected.items():
        if req.get(key)!=value:
            raise RuntimeError(f"sdk evaluator posture request {key} mismatch")
    if not isinstance(req.get("manifest_ref"),str) or not req["manifest_ref"].strip():
        raise RuntimeError("manifest_ref missing")

def consume(source_root: Path, runtime_root: Path, *, env: dict[str,str] | None=None) -> dict[str, Any]:
    source=source_root.expanduser().resolve()
    runtime=runtime_root.expanduser().resolve()
    request_path=runtime/REQUEST_REL
    if not request_path.is_file():
        return {"schema":"stegverse.sdk-evaluator-governance-posture-runtime-proof/v1","state":"NO_REQUEST","runtime_execution_attempted":False,"authority_effect":"NONE"}
    request=load_json(request_path)
    validate_request(request)
    manifest_path=runtime/Path(request["manifest_ref"])
    if not manifest_path.is_file():
        return {"schema":"stegverse.sdk-evaluator-governance-posture-runtime-proof/v1","state":"INPUT_NOT_MATERIALIZED","missing":"manifest","manifest_ref":request["manifest_ref"],"runtime_execution_attempted":False,"authority_effect":"NONE"}
    values=dict(os.environ if env is None else env)
    sdk_root=Path(values.get("STEGVERSE_SDK_SOURCE_ROOT","")).expanduser() if values.get("STEGVERSE_SDK_SOURCE_ROOT") else None
    stegos_root=Path(values.get("STEGVERSE_STEGOS_ROOT","")).expanduser() if values.get("STEGVERSE_STEGOS_ROOT") else None
    if sdk_root is None or not sdk_root.is_dir():
        return {"schema":"stegverse.sdk-evaluator-governance-posture-runtime-proof/v1","state":"INPUT_NOT_MATERIALIZED","missing":"sdk_source_root","runtime_execution_attempted":False,"authority_effect":"NONE"}
    for root in (stegos_root,sdk_root):
        if root is not None and root.is_dir():
            value=str(root.resolve())
            if value not in sys.path:
                sys.path.insert(0,value)
    from stegverse.evaluator_governance_runtime import run_evaluator_governance_manifest
    manifest=load_json(manifest_path)
    custody_rel=Path(str(request.get("custody_db_ref") or "runtime-state/sdk-evaluator-governance-posture/custody.sqlite3"))
    custody_path=runtime/custody_rel
    custody_path.parent.mkdir(parents=True,exist_ok=True)
    result=run_evaluator_governance_manifest(manifest,custody_db=str(custody_path),host_identity=str(request.get("host_identity") or "stegverse-sovereign-local"))
    binding=result.get("intr_security_posture_binding") if isinstance(result,dict) else None
    resolution=(binding or {}).get("resolution") if isinstance(binding,dict) else None
    projection=(binding or {}).get("projection") if isinstance(binding,dict) else None
    instance=(projection or {}).get("posture_instance") if isinstance(projection,dict) else None
    if not isinstance(instance,dict) and isinstance(resolution,dict):
        instance=resolution.get("posture_instance")
    extensions=manifest.get("extensions") if isinstance(manifest,dict) else {}
    graph=(extensions or {}).get("governance_reference_graph") if isinstance(extensions,dict) else None
    terminal=bool(
      isinstance(result,dict) and result.get("posture_bound_execution") is True
      and result.get("sdk_resolved_posture") is False and isinstance(binding,dict)
      and binding.get("resolution_authority")=="INTERLOCK_INTR"
      and isinstance(binding.get("transition_request_sha256"),str)
    )
    receipt={
      "schema":"stegverse.sdk-evaluator-governance-posture-runtime-proof/v1",
      "state":"COMPLETED" if terminal else "ATTEMPT_RECORDED",
      "task_id":TARGET_TASK,"request_id":request.get("request_id"),
      "manifest_ref":request["manifest_ref"],"manifest_file_sha256":file_sha256(manifest_path),
      "manifest_sha256":manifest.get("manifest_sha256") if isinstance(manifest,dict) else None,
      "graph_sha256":graph.get("graph_sha256") if isinstance(graph,dict) else None,
      "transition_request_sha256":binding.get("transition_request_sha256") if isinstance(binding,dict) else None,
      "payload_sha256":binding.get("payload_sha256") if isinstance(binding,dict) else None,
      "posture_instance_id":instance.get("instance_id") if isinstance(instance,dict) else None,
      "posture_instance_sha256":instance.get("instance_sha256") if isinstance(instance,dict) else None,
      "resolution_authority":binding.get("resolution_authority") if isinstance(binding,dict) else None,
      "posture_bound_execution":result.get("posture_bound_execution") if isinstance(result,dict) else False,
      "sdk_resolved_posture":result.get("sdk_resolved_posture") if isinstance(result,dict) else None,
      "custody_db_ref":custody_rel.as_posix(),"runtime_execution_attempted":True,
      "credential_authority":"TV/TVC","transition_authority":"Interlock/InTr",
      "github_token_required":False,"github_token_runtime_authority":"NONE",
      "heartbeat_grants_execution_authority":False,"second_machine_required":False,
      "authority_effect":"NONE_EVIDENCE_ONLY"
    }
    path=runtime/RECEIPT_REL
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    # Every resulting state transition is authoritative only after the existing
    # canonical Master Records custody/reconstruction seam validates the exact
    # receipt and the retained runtime receipt as required evidence.
    workers_root=source/"workers"
    if str(workers_root) not in sys.path:
        sys.path.insert(0,str(workers_root))
    from canonical_state_transition_custody import build_state_receipt, submit_state_receipt, sha256_uri
    transition_id=f"{TARGET_TASK}:{receipt['state']}"
    # The existing organization receipt contract requires exact canonical inline
    # evidence bytes. A legacy evidence_ref/hex-only manifest is rejected before
    # Master Records gets the transition, masking its actual disposition.
    required_evidence=[{
      "evidence_id":"sdk-evaluator-governance-posture-runtime-receipt",
      "evidence_type":"SDK_EVALUATOR_GOVERNANCE_POSTURE_RUNTIME_RECEIPT",
      "origin_transition_id":transition_id,
      "encoding":"canonical-json",
      "sha256":sha256_uri(receipt).split(":",1)[1],
      "content":receipt,
      "evidence_ref":RECEIPT_REL.as_posix(),
      "evidence_sha256":file_sha256(path),
      "media_type":"application/json",
    }]
    state_receipt=build_state_receipt(
      transition_id=transition_id,
      transition_sequence=1,
      subject_or_correlation_id=TARGET_TASK,
      transition_outcome="COMPLETED" if terminal else "PARTIAL",
      prior_state_ref_or_hash=None,
      resulting_state_ref_or_hash=sha256_uri(receipt),
      governance_decision_ref_where_applicable=receipt.get("transition_request_sha256"),
      transition_evidence={
        "request_id":request.get("request_id"),
        "manifest_ref":request["manifest_ref"],
        "manifest_file_sha256":receipt.get("manifest_file_sha256"),
        "manifest_sha256":receipt.get("manifest_sha256"),
        "graph_sha256":receipt.get("graph_sha256"),
        "transition_request_sha256":receipt.get("transition_request_sha256"),
        "posture_instance_id":receipt.get("posture_instance_id"),
        "posture_instance_sha256":receipt.get("posture_instance_sha256"),
        "resolution_authority":receipt.get("resolution_authority"),
        "posture_bound_execution":receipt.get("posture_bound_execution"),
        "sdk_resolved_posture":receipt.get("sdk_resolved_posture"),
        "custody_db_ref":receipt.get("custody_db_ref"),
        "runtime_receipt_ref":RECEIPT_REL.as_posix(),
      },
      required_evidence_manifest=required_evidence,
      proof_scope="SDK_EVALUATOR_GOVERNANCE_POSTURE_RUNTIME_TRANSITION_ONLY",
      proof_ceiling="MASTER_RECORDS_VALIDATED_RUNTIME_TRANSITION_EVIDENCE_ONLY",
    )
    mr=submit_state_receipt(state_receipt)
    receipt["master_records_state"]=mr.get("state")
    receipt["master_records_reconstruction_status"]=mr.get("reconstruction_status")
    receipt["master_records_required_evidence_validation_status"]=mr.get("required_evidence_validation_status")
    receipt["master_records_required_evidence_count"]=mr.get("required_evidence_count")
    receipt["master_records_receipt_sha256"]=mr.get("receipt_sha256")
    receipt["master_records_reconstructed_receipt_sha256"]=mr.get("reconstructed_receipt_sha256")
    receipt["master_records_reason"]=mr.get("reason")
    receipt["state"]="COMPLETED" if terminal and mr.get("state")=="RECORDED" and mr.get("reconstruction_status")=="PASS" and mr.get("required_evidence_validation_status")=="PASS" and mr.get("receipt_sha256")==mr.get("reconstructed_receipt_sha256") else "MASTER_RECORDS_VALIDATION_PENDING_OR_FAILED"
    path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-root",type=Path,default=ROOT)
    ap.add_argument("--runtime-root",type=Path,required=True)
    args=ap.parse_args()
    result=consume(args.source_root,args.runtime_root)
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
