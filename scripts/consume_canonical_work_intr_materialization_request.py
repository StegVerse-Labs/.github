#!/usr/bin/env python3
"""Consume an admitted canonical-work Universal InTr materialization request.

This consumer binds the request to an authentic ingress receipt, validates the
optional HB32-derived carrier binding, reads the canonical task + existing
WorkerCoordinator state, and emits a non-authorizing coordination projection.
It never mints claim/fence state and never starts a second scheduler/runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from heartbeat_runtime.intr_carrier_profile import validate_carrier_binding

ROOT = Path(__file__).resolve().parents[1]
REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "CanonicalWork:Ingress"}
DOWNSTREAM_OWNER = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
BOUNDARY_PATH = ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"]
INGRESS_SCHEMA = "stegverse.canonical-work-intr-materialization-ingress/v1"
CONSUMPTION_SCHEMA = "stegverse.canonical-work-intr-materialization-consumption/v1"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def validate_request(request: dict[str, Any]) -> None:
    expected = {
        "schema": REQUEST_SCHEMA,
        "state": REQUEST_STATE,
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "destination": DESTINATION,
        "boundary_path": BOUNDARY_PATH,
        "downstream_owner_ref": DOWNSTREAM_OWNER,
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "exact_packet_transport_retry_allowed": True,
        "blind_consequence_retry_allowed": False,
        "interlock_required": True,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "transport_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_transfer": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    for key, value in expected.items():
        require(request.get(key) == value, f"materialization_{key}_mismatch")
    for field in ("materialization_id", "operation_id", "packet_id", "payload_ref", "transport_intent_hash", "payload_hash", "request_hash"):
        require(isinstance(request.get(field), str) and request[field], f"materialization_{field}_required")
    require(request["materialization_id"].startswith("INTR-MAT-") and len(request["materialization_id"]) == 33, "materialization_id_invalid")
    body = dict(request)
    claimed = body.pop("request_hash")
    require(claimed == sha_uri(body), "materialization_request_hash_mismatch")
    binding = request.get("carrier_binding")
    if binding is not None:
        validate_carrier_binding(binding, packet_id=request["packet_id"], payload_hash=request["payload_hash"])


def payload_path(runtime_root: Path, request: dict[str, Any]) -> Path:
    ref = request["payload_ref"]
    prefix = "runtime://intr-payloads/canonical-work/"
    require(ref.startswith(prefix), "payload_ref_namespace_invalid")
    name = ref[len(prefix):]
    require(name == request["materialization_id"] + ".json", "payload_ref_materialization_mismatch")
    return runtime_root / "intr-payloads" / "canonical-work" / name


def project_worker(worker_registry: dict[str, Any], task_id: str) -> dict[str, Any]:
    matches = [t for t in worker_registry.get("tasks", []) if t.get("task_id") == task_id or t.get("goal_id") == task_id]
    require(len(matches) <= 1, "worker_registry_task_ambiguous")
    if not matches:
        return {"matched": False, "claim_id": None, "fencing_token": None, "worker_id": None, "projection_only": True}
    task = matches[0]
    timing = task.get("heartbeat_timing") or {}
    timer = task.get("assignment_timer") or {}
    return {
        "matched": True,
        "claim_id": task.get("claim_id"),
        "fencing_token": timer.get("fencing_token", timing.get("fencing_token")),
        "worker_id": task.get("worker_id"),
        "worker_instance_id": task.get("worker_instance_id"),
        "state": task.get("state"),
        "executor_binding": task.get("executor_binding"),
        "last_checkpoint_ref": task.get("last_checkpoint_ref"),
        "projection_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--materialization-id", required=True)
    parser.add_argument("--registry", default=str(ROOT / "data" / "canonical-task-registry.json"))
    parser.add_argument("--worker-registry", default=str(ROOT / "control" / "worker-registry.json"))
    args = parser.parse_args()

    runtime = Path(args.runtime_root).resolve()
    request_path = runtime / "intr-materialization" / f"{args.materialization_id}.json"
    ingress_path = runtime / "receipts" / "sovereign-network" / "canonical-work-intr-ingress" / f"{args.materialization_id}.json"
    request = load(request_path)
    validate_request(request)
    ingress = load(ingress_path)
    require(ingress.get("schema") == INGRESS_SCHEMA and ingress.get("state") == "INGRESS_ADMITTED", "ingress_receipt_not_admitted")
    for key in ("materialization_id", "request_hash", "transport_intent_hash", "payload_hash", "operation_id", "packet_id"):
        require(ingress.get(key) == request.get(key), f"ingress_binding_mismatch:{key}")
    require(ingress.get("claim_or_fence_minted") is False, "ingress_minted_claim_or_fence")
    require(ingress.get("credential_authority") == "TV/TVC", "ingress_credential_authority_drift")

    payload = load(payload_path(runtime, request))
    require(sha_uri(payload) == request["payload_hash"], "payload_hash_mismatch")
    task_id = payload.get("task_id")
    correlation_id = payload.get("correlation_id")
    registry = load(Path(args.registry))
    tasks = [t for t in registry.get("tasks", []) if t.get("task_id") == task_id]
    require(len(tasks) == 1, "canonical_task_identity_not_unique")
    task = tasks[0]
    require(task.get("correlation_id") == correlation_id, "canonical_correlation_mismatch")
    worker = project_worker(load(Path(args.worker_registry)), str(task_id))

    receipt = {
        "schema": CONSUMPTION_SCHEMA,
        "state": "INGRESS_BOUND_COORDINATION_PROJECTED",
        "materialization_id": request["materialization_id"],
        "request_hash": request["request_hash"],
        "payload_hash": request["payload_hash"],
        "task_id": task_id,
        "correlation_id": correlation_id,
        "operation_id": request["operation_id"],
        "ingress_receipt_ref": str(ingress_path),
        "worker_claim_projection": worker,
        "master_records_reconciliation": "PENDING_DEFINED_FEED",
        "runtime_execution_attempted": False,
        "claim_or_fence_minted": False,
        "heartbeat_carrier_present": request.get("carrier_binding") is not None,
        "heartbeat_carrier_grants_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_COORDINATION_PROJECTION_ONLY"
    }
    out = runtime / "receipts" / "sovereign-host" / "canonical-work-intr-materialization" / f"{args.materialization_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if out.exists():
        existing = load(out)
        require(existing == receipt, "write_once_collision")
    else:
        out.write_text(raw, encoding="utf-8")
    latest = runtime / "receipts" / "sovereign-host" / "canonical-work-intr-materialization-consumption.latest.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
