#!/usr/bin/env python3
"""Generic SDK manifest state-transition profile for the existing Universal InTr listener.

This module is a non-authorizing ingress/return adapter. It does not create a
listener, scheduler, dispatcher, WorkerCoordinator, credential authority,
transition authority, execution authority, or custody authority. It validates
and retains one SDK manifest-state-transition request, invokes the existing
targeted WorkerCoordinator path in-process, and returns only evidence already
produced by the canonical runtime chain.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from heartbeat_runtime.worker_runtime import WorkerCoordinator
from scripts.run_worker_runtime import load_adapters

REQUEST_SCHEMA = "stegverse.sdk.manifest-state-transition-request/v1"
RESULT_SCHEMA = "stegverse.sdk.manifest-state-transition-result/v1"
PROFILE = "SDK:ManifestStateTransition"
REQUEST_DIR = Path("runtime-state/sdk-manifest-state-transition")
LATEST_SUFFIX = ".latest.json"
IMMUTABLE_DIR = "requests"

REQUIRED_AUTHORITIES = {
    "credential_authority": "TV/TVC",
    "claim_fence_authority": "WORKERCOORDINATOR",
    "transition_authority": "INTERLOCK_INTR",
    "custody_replay_reconstruction_authority": "MASTER_RECORDS",
    "request_grants_authority": False,
    "sdk_executes_lifecycle": False,
    "authority_effect": "NONE_MANIFEST_RUNTIME_REQUEST_ONLY",
}

def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")

def sha256(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return hashlib.sha256(raw).hexdigest()

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)

def is_manifest_state_transition(payload: Any) -> bool:
    return isinstance(payload, dict) and payload.get("schema") == REQUEST_SCHEMA

def _validate_manifest_hash(manifest: Mapping[str, Any], claimed: str) -> None:
    body = dict(manifest)
    embedded = body.pop("canonical_manifest_sha256", None)
    require(isinstance(embedded, str) and embedded == claimed, "canonical_manifest_sha256_binding_mismatch")
    require(sha256(body) == claimed, "canonical_manifest_sha256_recompute_mismatch")

def validate_request(request: Mapping[str, Any]) -> dict[str, Any]:
    require(request.get("schema") == REQUEST_SCHEMA, "manifest_state_transition_request_schema_mismatch")
    body = dict(request)
    claimed_request_hash = body.pop("request_sha256", None)
    require(isinstance(claimed_request_hash, str) and len(claimed_request_hash) == 64, "request_sha256_required")
    require(sha256(body) == claimed_request_hash, "request_sha256_mismatch")
    for key, expected in REQUIRED_AUTHORITIES.items():
        require(request.get(key) == expected, f"{key}_mismatch")
    manifest = request.get("canonical_manifest")
    require(isinstance(manifest, Mapping), "canonical_manifest_required")
    manifest_hash = request.get("canonical_manifest_sha256")
    require(isinstance(manifest_hash, str) and len(manifest_hash) == 64, "canonical_manifest_sha256_required")
    _validate_manifest_hash(manifest, manifest_hash)
    graph = request.get("state_graph")
    require(isinstance(graph, Mapping), "state_graph_required")
    require(graph.get("schema") == "stegverse.sdk.installed-state-transition-graph/v1", "state_graph_schema_mismatch")
    for key in ("graph_id", "processing_capability", "route_id"):
        require(isinstance(request.get(key), str) and request.get(key), f"{key}_required")
    require(graph.get("graph_id") == request.get("graph_id"), "graph_id_binding_mismatch")
    require(graph.get("processing_capability") == request.get("processing_capability"), "processing_capability_binding_mismatch")
    require(graph.get("route_id") == request.get("route_id"), "route_id_binding_mismatch")
    task_id = request.get("canonical_task_id")
    if request.get("requires_workercoordinator_claim_fence") is True:
        require(isinstance(task_id, str) and task_id, "canonical_task_id_required_for_worker_graph")
    elif task_id is not None:
        require(isinstance(task_id, str) and task_id, "canonical_task_id_invalid")
    require(request.get("predecessor_closure_required") is True, "predecessor_closure_required")
    return dict(request)

def _request_path(runtime_root: Path, task_id: str) -> Path:
    return runtime_root / REQUEST_DIR / (task_id + LATEST_SUFFIX)

def persist_request(runtime_root: Path, request: Mapping[str, Any]) -> Path:
    """Retain immutable request bytes and advance only the non-authorizing latest pointer.

    Re-running the same canonical task with a newly manifested input must not collide
    with prior history. Every request remains content-addressed by request_sha256;
    the existing worker reads only the latest pointer for the current invocation.
    """
    task_id = str(request.get("canonical_task_id") or request["graph_id"])
    request_hash = str(request["request_sha256"])
    root = runtime_root / REQUEST_DIR
    immutable = root / IMMUTABLE_DIR / task_id / f"{request_hash}.json"
    latest = _request_path(runtime_root, task_id)
    raw = json.dumps(dict(request), indent=2, sort_keys=True) + "\n"
    immutable.parent.mkdir(parents=True, exist_ok=True)
    if immutable.exists():
        existing = json.loads(immutable.read_text(encoding="utf-8"))
        require(existing == dict(request), "manifest_state_transition_immutable_request_collision")
    else:
        immutable.write_text(raw, encoding="utf-8")
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(raw, encoding="utf-8")
    return latest

def _closed(row: Any, transition_id: str | None = None) -> dict[str, Any]:
    require(isinstance(row, Mapping), "master_records_transition_missing")
    value = dict(row)
    if transition_id is not None:
        require(value.get("transition_id") == transition_id, f"transition_id_mismatch:{transition_id}")
    require(value.get("state") == "RECORDED", f"master_records_state_not_recorded:{value.get('transition_id')}")
    require(value.get("reconstruction_status") == "PASS", f"reconstruction_not_pass:{value.get('transition_id')}")
    require(value.get("required_evidence_validation_status") == "PASS", f"required_evidence_not_pass:{value.get('transition_id')}")
    receipt = value.get("receipt_sha256")
    require(isinstance(receipt, str) and receipt == value.get("reconstructed_receipt_sha256"), f"receipt_reconstruction_digest_mismatch:{value.get('transition_id')}")
    return value

def _assemble_purpose_result(request: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    result = receipt.get("result")
    require(isinstance(result, Mapping), "purpose_runtime_result_missing")
    assignment = _closed(receipt.get("claim_fence_master_records_transition"), "WORKERCOORDINATOR_CLAIM_FENCE_BOUND")
    closures = [
        assignment,
        _closed(result.get("warrant_policy_master_records_transition"), "TV_TVC_WARRANT_POLICY_VERIFIED"),
        _closed(result.get("intr_admission_master_records_transition"), "STEGCORE_INTR_MATERIALIZATION_ADMITTED"),
    ]
    lifecycle = result.get("purpose_bound_worker_result")
    require(isinstance(lifecycle, Mapping), "purpose_bound_worker_result_missing")
    lifecycle_closures = lifecycle.get("canonical_master_records_transitions")
    require(isinstance(lifecycle_closures, list), "purpose_lifecycle_closures_missing")
    for row in lifecycle_closures:
        closures.append(_closed(row))
    previous = None
    for index, row in enumerate(closures):
        if index and row.get("predecessor_receipt_sha256") != previous:
            raise ValueError(f"immediate_predecessor_closure_mismatch:{row.get('transition_id')}")
        previous = row.get("receipt_sha256")
    governance = result.get("governance")
    require(isinstance(governance, Mapping), "governance_result_missing")
    manifest_receipt_id = governance.get("manifest_receipt_id")
    require(isinstance(manifest_receipt_id, str) and manifest_receipt_id, "manifest_receipt_id_missing")
    replay = result.get("master_records_replay")
    require(isinstance(replay, Mapping) and replay.get("status") == "PASS", "MASTER_RECORDS_REPLAY_NOT_OBSERVED")
    reconstruction = result.get("master_records_reconstruction")
    require(isinstance(reconstruction, Mapping), "MASTER_RECORDS_RECONSTRUCTION_NOT_OBSERVED")
    return {
        "schema": RESULT_SCHEMA,
        "state": "COMPLETE",
        "canonical_manifest_sha256": request["canonical_manifest_sha256"],
        "graph_id": request["graph_id"],
        "canonical_task_id": request.get("canonical_task_id"),
        "processing_capability": request["processing_capability"],
        "route_id": request["route_id"],
        "transition_closures": closures,
        "replay_status": "PASS",
        "reconstruction_status": "PASS",
        "terminal_state": {
            "records_only": result.get("records_only"),
            "continued_authority": result.get("continued_authority_after_retirement"),
            "worker_live_after_close": result.get("worker_live_after_close"),
        },
        "manifest_receipt_id": manifest_receipt_id,
        "authority_effect": "NONE_RETURN_ASSEMBLY_ONLY",
    }

def execute(runtime_root: Path, request: Mapping[str, Any]) -> dict[str, Any]:
    validated = validate_request(request)
    task_id = validated.get("canonical_task_id")
    require(isinstance(task_id, str) and task_id, "canonical_task_id_required")
    persist_request(runtime_root, validated)
    runtime = WorkerCoordinator(runtime_root, adapters=load_adapters(runtime_root))
    cycle = runtime.cycle(write=True, target_task_id=task_id)
    require(isinstance(cycle, Mapping), "workercoordinator_cycle_result_missing")
    latest = runtime_root / "receipts/sovereign-host/sdk-tt-purpose-bound-worker-runtime-proof.latest.json"
    require(latest.is_file(), "AUTHENTIC_PURPOSE_RUNTIME_RECEIPT_NOT_OBSERVED")
    receipt = json.loads(latest.read_text(encoding="utf-8"))
    require(receipt.get("task_id") == task_id, "purpose_runtime_receipt_task_mismatch")
    return _assemble_purpose_result(validated, receipt)

def admit(*, runtime_root: Path, body: bytes, headers: Mapping[str, str], transport_validator) -> dict[str, Any]:
    transport = transport_validator(headers, body)
    require(transport.get("origin") in {"STEGOS_NODE_OUTBOX", "TVC_RELAY_EGRESS"}, "manifest_state_transition_transport_origin_invalid")
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ValueError("manifest_state_transition_request_json_invalid") from exc
    require(isinstance(payload, dict), "manifest_state_transition_request_object_required")
    return execute(runtime_root, payload)

__all__ = ["PROFILE", "REQUEST_SCHEMA", "RESULT_SCHEMA", "admit", "execute", "is_manifest_state_transition", "validate_request"]
