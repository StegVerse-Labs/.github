#!/usr/bin/env python3
"""Build a canonical-work InTr materialization request with optional HB-derived carrier binding.

The request is source material only until an authentic Interlock/InTr ingress admits it.
The HB32 independent oscillator supplies deterministic reference/carrier metadata only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from heartbeat_runtime.intr_carrier_profile import build_carrier_binding

SCHEMA = "stegverse.canonical-work-intr-materialization-request/v1"
DESTINATION = "STEGVERSE_CANONICAL_WORK_COORDINATION"
DOWNSTREAM_OWNER = "WORKERCOORDINATOR_CANONICAL_COORDINATION_ADAPTER"


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
    now_ms = time.time_ns() // 1_000_000

    body = {
        "schema": SCHEMA,
        "destination": DESTINATION,
        "downstream_owner_ref": DOWNSTREAM_OWNER,
        "task_id": args.task_id,
        "correlation_id": correlation_id,
        "operation_id": args.operation,
        "packet_id": packet_id,
        "payload": payload,
        "payload_hash": payload_hash,
        "request_grants_execution_authority": False,
        "request_mints_claim_or_fence": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_REQUEST_ONLY"
    }
    if not args.without_carrier_binding:
        body["carrier_binding"] = build_carrier_binding(packet_id=packet_id, payload_hash=payload_hash, sampled_unix_ms=now_ms)
    body["request_hash"] = sha_uri(body)

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
