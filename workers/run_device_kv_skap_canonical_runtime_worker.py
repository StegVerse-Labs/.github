#!/usr/bin/env python3
"""WorkerCoordinator entrypoint for the canonical Device <-> KV <-> SKAP lane.

This wrapper is intentionally thin. It consumes the exact fenced
``stegverse.worker-invocation/v0.1`` supplied by WorkerCoordinator, loads the
merged StegOS Device/KV/SKAP canonical-runtime domain binding, derives runtime
admission from an authentic already-open canonical lease snapshot, and delegates
one bounded execution to StegOS.

It does not reimplement the bridge, mint a claim/fence, open a runtime lease,
grant Interlock/InTr transition admission, or carry credential authority.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

from workers import run_device_kv_skap_roundtrip_worker as domain_worker

TASK_ID = domain_worker.TASK_ID
ROOT = Path(__file__).resolve().parents[1]


def _required_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{name.lower()}_required")
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{name.lower()}_missing")
    return path


def _output_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{name.lower()}_required")
    path = Path(value).expanduser().resolve()
    parent = path.parent
    if not parent.exists() or not parent.is_dir():
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{name.lower()}_parent_missing")
    return path


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{label}_invalid_json") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{label}_object_required")
    return value


def _load_stegos_domain_binding(stegos_root: Path):
    root = stegos_root.resolve()
    required = root / "stegos" / "device_kv_skap_canonical_runtime.py"
    if not required.is_file():
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:stegos_domain_binding_missing")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from stegos.device_kv_skap_canonical_runtime import (  # type: ignore
        DeviceKVSKAPCanonicalRuntimeCapability,
        execute_bound_device_kv_skap_roundtrip,
        worker_claim_from_invocation,
    )
    from stegos.node_event_execution_broker import build_runtime_admission_from_lease_snapshot  # type: ignore
    from stegos.universal_intr_transport import sha256_uri  # type: ignore
    return (
        DeviceKVSKAPCanonicalRuntimeCapability,
        execute_bound_device_kv_skap_roundtrip,
        worker_claim_from_invocation,
        build_runtime_admission_from_lease_snapshot,
        sha256_uri,
    )


def main() -> int:
    try:
        invocation = json.loads(sys.stdin.read())
    except Exception as exc:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_invocation_invalid_json") from exc
    if not isinstance(invocation, dict):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_invocation_object_required")

    # Preserve the existing worker's exact fenced invocation contract before
    # asking StegOS to bind it into the canonical runtime lane.
    epoch, claim_id, fence = domain_worker._validate_invocation(invocation)

    stegos_root = _required_path("STEGVERSE_STEGOS_ROOT")
    runtime_root = _required_path("STEGVERSE_DEVICE_KV_SKAP_RUNTIME_ROOT")
    gateway_sidecar = _required_path("STEGVERSE_DEVICE_KV_SKAP_GATEWAY_SIDECAR")
    tvc_drain_receipt = _required_path("STEGVERSE_DEVICE_KV_SKAP_TVC_DRAIN_RECEIPT")
    roundtrip_output = _output_path("STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_OUTPUT")
    bridge_receipt_path = _output_path("STEGVERSE_DEVICE_KV_SKAP_BRIDGE_RECEIPT")

    materialization = _load_object(
        _required_path("STEGVERSE_DEVICE_KV_SKAP_INTR_MATERIALIZATION"),
        "intr_materialization",
    )
    retained_node = _load_object(
        _required_path("STEGVERSE_DEVICE_KV_SKAP_RETAINED_NODE"),
        "retained_node",
    )
    lease_snapshot = _load_object(
        _required_path("STEGVERSE_DEVICE_KV_SKAP_CANONICAL_LEASE_SNAPSHOT"),
        "canonical_lease_snapshot",
    )

    (
        Capability,
        execute_bound,
        claim_from_invocation,
        build_runtime_admission,
        sha256_uri,
    ) = _load_stegos_domain_binding(stegos_root)

    # Fail closed if StegOS derives a different claim/fence from the exact same
    # invocation than the existing domain worker contract does.
    derived_claim = claim_from_invocation(invocation)
    if derived_claim.get("claim_id") != claim_id or derived_claim.get("fence") != fence:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:stegos_worker_claim_binding_mismatch")

    runtime_admission = build_runtime_admission(lease_snapshot)
    lease_id = runtime_admission.get("lease_id")
    if not isinstance(lease_id, str) or not lease_id:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:canonical_runtime_lease_id_missing")

    capability = Capability(
        worker_source_root=ROOT,
        runtime_root=runtime_root,
        runtime_lease_id=lease_id,
        stegos_root=stegos_root,
        gateway_sidecar=gateway_sidecar,
        tvc_drain_receipt=tvc_drain_receipt,
        output=roundtrip_output,
    )
    receipt = execute_bound(
        materialization=materialization,
        retained_node=retained_node,
        runtime_admission=runtime_admission,
        worker_invocation=invocation,
        capability=capability,
    )

    result = receipt.get("result")
    if not isinstance(result, Mapping) or result.get("status") != "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED":
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:canonical_domain_binding_not_verified")
    if result.get("runtime_lease_id") != lease_id or receipt.get("runtime_lease_id") != lease_id:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:canonical_runtime_lease_binding_mismatch")

    # Reconstruct the canonical outer WorkerCoordinator response from the exact
    # invocation/output and verify it matches the response StegOS observed before
    # adding the bridge receipt as additional evidence for the outer adapter.
    worker_response = domain_worker._response(
        output=roundtrip_output,
        epoch=epoch,
        claim_id=claim_id,
        fence=fence,
    )
    if sha256_uri(worker_response) != result.get("worker_response_hash"):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:canonical_worker_response_hash_mismatch")

    domain_worker._write_once(bridge_receipt_path, dict(receipt))
    bridge_ref = domain_worker._evidence_ref(bridge_receipt_path)
    if bridge_ref not in worker_response["evidence_refs"]:
        worker_response["evidence_refs"].append(bridge_ref)

    print(json.dumps(worker_response, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
