#!/usr/bin/env python3
"""Canonical runtime-lane wrapper for the Device <-> KV <-> SKAP worker.

Consumes the exact WorkerCoordinator invocation on stdin plus authentic retained
Node, Universal InTr materialization, and already-open canonical EVENT_EPHEMERAL
lease evidence. The wrapper binds those inputs through StegOS
WorkerCoordinatorCanonicalRuntimeBridge and then invokes the existing roundtrip
worker logic. It mints no claim/fence, opens no lease, grants no transition
admission, and carries no credential authority.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

from workers import run_device_kv_skap_roundtrip_worker as domain_worker

TASK_ID = domain_worker.TASK_ID
COSV = "50000000102000"
CAPABILITY = "device-kv-skap-roundtrip"


def _required_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{name.lower()}_required")
    path = Path(value)
    if not path.exists():
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{name.lower()}_missing")
    return path


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{label}_invalid_json") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{label}_object_required")
    return value


def _load_stegos_bridge(stegos_root: Path):
    root = stegos_root.resolve()
    if not (root / "stegos" / "node_event_execution_broker.py").is_file():
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:stegos_bridge_missing")
    sys.path.insert(0, str(root))
    from stegos.node_event_execution_broker import (  # type: ignore
        CapabilityAdapter,
        WorkerCoordinatorCanonicalRuntimeBridge,
        build_runtime_admission_from_lease_snapshot,
    )
    return CapabilityAdapter, WorkerCoordinatorCanonicalRuntimeBridge, build_runtime_admission_from_lease_snapshot


def _worker_claim(invocation: Mapping[str, Any], claim_id: str, fence: int) -> dict[str, Any]:
    return {
        "state": "CLAIM_GRANT_OBSERVED",
        "task_id": TASK_ID,
        "claim_id": claim_id,
        "fence": fence,
        "authority_effect": "WORKERCOORDINATOR_CLAIM_ONLY",
        "source_schema": invocation.get("schema"),
    }


def main() -> int:
    try:
        invocation = json.loads(sys.stdin.read())
    except Exception as exc:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_invocation_invalid_json") from exc
    if not isinstance(invocation, dict):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_invocation_object_required")

    epoch, claim_id, fence = domain_worker._validate_invocation(invocation)
    stegos_root = _required_path("STEGVERSE_STEGOS_ROOT")
    materialization = _load_object(_required_path("STEGVERSE_DEVICE_KV_SKAP_INTR_MATERIALIZATION"), "intr_materialization")
    retained_node = _load_object(_required_path("STEGVERSE_DEVICE_KV_SKAP_RETAINED_NODE"), "retained_node")
    lease_snapshot = _load_object(_required_path("STEGVERSE_DEVICE_KV_SKAP_CANONICAL_LEASE_SNAPSHOT"), "canonical_lease_snapshot")
    bridge_receipt_path = _required_path("STEGVERSE_DEVICE_KV_SKAP_BRIDGE_RECEIPT")

    CapabilityAdapter, Bridge, build_runtime_admission = _load_stegos_bridge(stegos_root)
    runtime_admission = build_runtime_admission(lease_snapshot)
    bridge = Bridge()

    def execute_domain(exact_invocation: Mapping[str, Any]) -> Mapping[str, Any]:
        inner_epoch, inner_claim_id, inner_fence = domain_worker._validate_invocation(exact_invocation)
        if (inner_epoch, inner_claim_id, inner_fence) != (epoch, claim_id, fence):
            raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:bridge_invocation_binding_mismatch")
        output, proof = domain_worker._execute_roundtrip()
        response = domain_worker._response(output=output, epoch=epoch, claim_id=claim_id, fence=fence)
        bridge_ref = domain_worker._evidence_ref(bridge_receipt_path)
        if bridge_ref not in response["evidence_refs"]:
            response["evidence_refs"].append(bridge_ref)
        return {
            "status": "COMPLETED",
            "transition_id": "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED",
            "proof_state": proof.get("state"),
            "worker_response": response,
        }

    bridge.register_adapter(CapabilityAdapter(CAPABILITY, execute_domain))
    request = bridge.build_request(
        task_id=TASK_ID,
        cosv=COSV,
        materialization=materialization,
        retained_node=retained_node,
        worker_claim=_worker_claim(invocation, claim_id, fence),
        runtime_admission=runtime_admission,
        capability_adapter=CAPABILITY,
        invocation=invocation,
    )
    receipt = bridge.execute(request)
    result = receipt.get("result")
    if not isinstance(result, Mapping) or result.get("status") != "COMPLETED":
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:canonical_bridge_not_completed")
    worker_response = result.get("worker_response")
    if not isinstance(worker_response, dict) or worker_response.get("transition_id") != "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED":
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:canonical_bridge_worker_response_invalid")

    domain_worker._write_once(bridge_receipt_path, dict(receipt))
    print(json.dumps(worker_response, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
