#!/usr/bin/env python3
"""Build a Universal InTr materialization request for canonical-work coordination.

The request is source material only until authentic Interlock/InTr ingress admits it.
HB32 independent-oscillator data is optional non-authorizing carrier/reference metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from heartbeat_runtime.intr_carrier_profile import build_carrier_binding

REQUEST_SCHEMA = "stegverse.universal-intr-materialization-request/v1"
REQUEST_STATE = "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION"
DESTINATION = {"boundary": "STEGOS_ECOSYSTEM", "subsystem": "CanonicalWork:Ingress"}
DOWNSTREAM_OWNER = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
BOUNDARY_PATH = ["DEVICE_SYSTEM", "STEGOS_ECOSYSTEM"]


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha_uri(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--correlation-id")
    parser.add_argument("--operation", choices=["TASK_INGRESS", "TASK_TRANSFER", "TASK_EGRESS", "DEPENDENCY_REEVALUATION"], default="TASK_INGRESS")
    parser.add_argument("--registry", default="data/canonical-task-registry.json")
    parser.add_argument("--payload-output", default="intr-payloads/canonical-work")
    parser.add_argument("--output")
    parser.add_argument("--without-carrier-binding", action="store_true")
    args = parser.parse_args()

    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    matches = [task for task in registry.get("tasks", []) if task.get("task_id") == args.task_id]
    if len(matches) != 1:
        raise SystemExit("FAIL_CLOSED: canonical task identity must resolve exactly once")
    task = matches[0]
    correlation_id = args.correlation_id or task.get("correlation_id")
    if correlation_id != task.get("correlation_id"):
        raise SystemExit("FAIL_CLOSED: correlation identity drift")

    payload = {
        "schema": "stegverse.canonical-work-transition-payload/v1",
        "task_id": args.task_id,
        "correlation_id": correlation_id,
        "operation": args.operation,
        "coordination_state": task.get("coordination_state"),
        "dependencies": task.get("dependencies", []),
        "blockers": task.get("blockers", []),
        "worker_claim_ref": task.get("worker_claim", {}),
        "authority": {
            "task_registry_mints_execution_authority": False,
            "claim_fence_authority": "WORKERCOORDINATOR",
            "observed_reality_authority": "MASTER_RECORDS",
            "ingress_egress_authority": "INTERLOCK_INTR"
        }
    }
    payload_hash = sha_uri(payload)
    packet_id = "CW-" + hashlib.sha256((args.task_id + ":" + args.operation + ":" + payload_hash).encode("utf-8")).hexdigest()[:24]
    materialization_id = "INTR-MAT-" + hashlib.sha256((packet_id + ":" + payload_hash).encode("utf-8")).hexdigest()[:24]
    payload_dir = Path(args.payload_output)
    payload_path = payload_dir / f"{materialization_id}.json"
    payload_ref = f"runtime://intr-payloads/canonical-work/{materialization_id}.json"
    transport_intent = {
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "boundary_path": BOUNDARY_PATH,
        "destination": DESTINATION,
        "downstream_owner_ref": DOWNSTREAM_OWNER,
        "operation_id": args.operation,
        "packet_id": packet_id,
        "payload_hash": payload_hash
    }
    transport_intent_hash = sha_uri(transport_intent)

    body = {
        "schema": REQUEST_SCHEMA,
        "state": REQUEST_STATE,
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "materialization_id": materialization_id,
        "operation_id": args.operation,
        "packet_id": packet_id,
        "transport_intent_hash": transport_intent_hash,
        "payload_hash": payload_hash,
        "payload_ref": payload_ref,
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
        "authority_effect": "NONE_REQUEST_ONLY"
    }
    if not args.without_carrier_binding:
        body["carrier_binding"] = build_carrier_binding(packet_id=packet_id, payload_hash=payload_hash, sampled_unix_ms=time.time_ns() // 1_000_000)
    body["request_hash"] = sha_uri(body)

    payload_dir.mkdir(parents=True, exist_ok=True)
    payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raw = json.dumps(body, indent=2, sort_keys=True) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
