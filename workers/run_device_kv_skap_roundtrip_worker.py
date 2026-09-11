#!/usr/bin/env python3
"""WorkerCoordinator entrypoint for authentic Device <-> KV <-> SKAP continuation.

For authentic Gateway/TVC continuation, this worker must consume the exact
retained Node projection, Universal InTr materialization request, and already-
open canonical StegOS EVENT_EPHEMERAL lease prepared by the outer runtime
wrapper. The fresh WorkerCoordinator claim/fence supplied on stdin is bound to
those artifacts through WorkerCoordinatorCanonicalRuntimeBridge before the
four-leg continuation may execute.

Manifest-only mode remains reconstruction/verification of already-materialized
evidence and does not claim a new authentic runtime execution.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

from workers.device_kv_skap_roundtrip_verifier import HOSTED_ENV, _load_json, verify_manifest

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001"
COSV = "50000000102000"
INVOCATION_SCHEMA = "stegverse.worker-invocation/v0.1"
RESPONSE_SCHEMA = "stegverse.worker-response/v0.1"
TERMINAL_STATE = "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED"


def required_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{name.lower()}_required")
    path = Path(value)
    if not path.exists():
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{name.lower()}_missing")
    return path


def optional_path(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value) if value else None


def _load_continuation():
    path = ROOT / "scripts" / "continue_device_kv_skap_from_tvc_custody.py"
    spec = importlib.util.spec_from_file_location("device_kv_skap_tvc_continuation", path)
    if spec is None or spec.loader is None:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:continuation_loader_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_once(output: Path, value: Mapping[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(dict(value), sort_keys=True, indent=2) + "\n"
    if output.exists() and output.read_text(encoding="utf-8") != raw:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:write_once_collision")
    output.write_text(raw, encoding="utf-8")
    if output.read_text(encoding="utf-8") != raw:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:write_readback_mismatch")


def _read_invocation() -> dict[str, Any]:
    try:
        value = json.loads(sys.stdin.read())
    except Exception as exc:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_invocation_invalid_json") from exc
    if not isinstance(value, dict) or value.get("schema") != INVOCATION_SCHEMA:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_invocation_schema_invalid")
    return value


def _validate_invocation(invocation: Mapping[str, Any]) -> tuple[int, str, int]:
    task = invocation.get("task")
    handoff = invocation.get("handoff")
    scope = invocation.get("scope")
    epoch = invocation.get("heartbeat_epoch")
    if not isinstance(task, Mapping) or task.get("task_id") != TASK_ID:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_task_identity_invalid")
    if not isinstance(handoff, Mapping):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_handoff_required")
    goal = handoff.get("goal")
    handoff_task = handoff.get("task")
    authority = handoff.get("authority")
    if not isinstance(goal, Mapping) or goal.get("goal_id") != TASK_ID:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_handoff_goal_invalid")
    if not isinstance(handoff_task, Mapping) or handoff_task.get("task_id") != TASK_ID:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_handoff_task_invalid")
    if not isinstance(authority, Mapping):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_handoff_authority_required")
    if authority.get("credential_authority") != "TV/TVC":
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:credential_authority_invalid")
    if authority.get("github_token_runtime_authority") != "NONE":
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:github_runtime_authority_invalid")
    if authority.get("transition_authority") != "Interlock/InTr":
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:transition_authority_invalid")

    if not isinstance(scope, Mapping):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_scope_required")
    claim_id = scope.get("claim_id")
    fence = scope.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_claim_required")
    if not isinstance(fence, int) or fence < 1 or not claim_id.endswith(f"-G{fence}"):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_claim_fence_invalid")
    if task.get("claim_id") != claim_id:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_claim_binding_mismatch")
    timing = task.get("heartbeat_timing") or {}
    if timing.get("fencing_token") != fence:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_fence_binding_mismatch")
    if not isinstance(epoch, int) or epoch < 0:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:worker_epoch_invalid")
    return epoch, claim_id, fence


def _evidence_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _response(*, output: Path, bridge_receipt: Path | None, epoch: int, claim_id: str, fence: int) -> dict[str, Any]:
    checkpoint = _evidence_ref(output)
    evidence_refs = [checkpoint]
    if bridge_receipt is not None:
        evidence_refs.append(_evidence_ref(bridge_receipt))
    return {
        "schema": RESPONSE_SCHEMA,
        "state": "COMPLETED",
        "transition_id": TERMINAL_STATE,
        "transition_sequence": 1,
        "expected_next_transition": None,
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": checkpoint,
        "evidence_refs": evidence_refs,
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 1,
            "external_cost_usd": 0,
            "task_class": "device_kv_skap_roundtrip",
        },
        "worker_binding": {
            "task_id": TASK_ID,
            "heartbeat_epoch": epoch,
            "claim_id": claim_id,
            "fencing_token": fence,
            "canonical_runtime_bridge_observed": bridge_receipt is not None,
            "claim_or_fence_minted_by_worker": False,
            "transition_authority": "Interlock/InTr",
            "credential_authority": "TV/TVC",
            "github_runtime_authority": "NONE",
            "authority_effect": "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY",
        },
    }


def _execute_roundtrip() -> tuple[Path, dict[str, Any]]:
    if any(str(os.environ.get(name, "")).strip().lower() not in {"", "0", "false", "no"} for name in HOSTED_ENV):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:hosted_runtime_forbidden")

    runtime_root = required_path("STEGVERSE_DEVICE_KV_SKAP_RUNTIME_ROOT")
    output_value = os.environ.get("STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_OUTPUT")
    if not output_value:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:stegverse_device_kv_skap_roundtrip_output_required")
    output = Path(output_value)
    manifest_path = optional_path("STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_MANIFEST")
    gateway_sidecar = optional_path("STEGVERSE_DEVICE_KV_SKAP_GATEWAY_SIDECAR")
    tvc_drain_receipt = optional_path("STEGVERSE_DEVICE_KV_SKAP_TVC_DRAIN_RECEIPT")
    stegos_root = optional_path("STEGVERSE_STEGOS_ROOT")

    continuation_inputs = [gateway_sidecar, tvc_drain_receipt, stegos_root]
    if any(continuation_inputs) and not all(continuation_inputs):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:incomplete_tvc_continuation_inputs")

    if all(continuation_inputs):
        for path, label in ((gateway_sidecar, "gateway_sidecar"), (tvc_drain_receipt, "tvc_drain_receipt"), (stegos_root, "stegos_root")):
            if path is None or not path.exists():
                raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{label}_missing")
        continuation = _load_continuation()
        result = continuation.continue_roundtrip(
            runtime_root=runtime_root,
            stegos_root=stegos_root,
            gateway_sidecar_path=gateway_sidecar,
            tvc_drain_receipt_path=tvc_drain_receipt,
        )
        if result.get("state") != TERMINAL_STATE:
            raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:continuation_not_verified")
        _write_once(output, result)
        return output, result

    if manifest_path is None:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:manifest_or_tvc_continuation_required")
    if not manifest_path.is_file():
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:manifest_missing")
    manifest = _load_json(manifest_path, "manifest")
    proof = verify_manifest(manifest, runtime_root=runtime_root)
    if proof.get("state") != TERMINAL_STATE:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:manifest_not_verified")
    _write_once(output, proof)
    return output, proof


def _execute_authentic_continuation_through_bridge(*, claim_id: str, fence: int) -> tuple[Path, Path]:
    stegos_root = required_path("STEGVERSE_STEGOS_ROOT").resolve()
    if str(stegos_root) not in sys.path:
        sys.path.insert(0, str(stegos_root))
    from stegos.node_event_execution_broker import (
        CapabilityAdapter,
        WorkerCoordinatorCanonicalRuntimeBridge,
        build_runtime_admission_from_lease_snapshot,
    )
    from stegos.universal_intr_transport import sha256_uri

    retained_node = _load_json(required_path("STEGVERSE_DEVICE_KV_SKAP_RETAINED_NODE"), "retained_node")
    materialization = _load_json(required_path("STEGVERSE_DEVICE_KV_SKAP_INTR_MATERIALIZATION"), "intr_materialization")
    lease_snapshot = _load_json(required_path("STEGVERSE_DEVICE_KV_SKAP_RUNTIME_LEASE_SNAPSHOT"), "runtime_lease_snapshot")
    bridge_path = required_path("STEGVERSE_DEVICE_KV_SKAP_BRIDGE_RECEIPT") if Path(os.environ.get("STEGVERSE_DEVICE_KV_SKAP_BRIDGE_RECEIPT", "")).exists() else Path(os.environ.get("STEGVERSE_DEVICE_KV_SKAP_BRIDGE_RECEIPT", ""))
    if not str(bridge_path):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:stegverse_device_kv_skap_bridge_receipt_required")

    runtime_admission = build_runtime_admission_from_lease_snapshot(lease_snapshot)
    bridge = WorkerCoordinatorCanonicalRuntimeBridge()
    executed: dict[str, Any] = {}

    def execute_domain(_binding: Mapping[str, Any]) -> Mapping[str, Any]:
        output, proof = _execute_roundtrip()
        executed["output"] = output
        executed["proof"] = proof
        return {
            "status": proof["state"],
            "worker_result_ref": str(output.resolve()),
            "worker_result_hash": sha256_uri(proof),
            "transition_authority": "Interlock/InTr",
            "credential_authority": "TV/TVC",
            "authority_effect": "NONE_DOMAIN_RESULT_ONLY",
        }

    bridge.register_adapter(CapabilityAdapter("device-kv-skap-roundtrip", execute_domain))
    request = bridge.build_request(
        task_id=TASK_ID,
        cosv=COSV,
        materialization=materialization,
        retained_node=retained_node,
        worker_claim={
            "state": "CLAIM_GRANT_OBSERVED",
            "claim_id": claim_id,
            "fence": fence,
            "authority_effect": "WORKERCOORDINATOR_CLAIM_ONLY",
        },
        runtime_admission=runtime_admission,
        capability_adapter="device-kv-skap-roundtrip",
        invocation={
            "runtime_root_ref": str(required_path("STEGVERSE_DEVICE_KV_SKAP_RUNTIME_ROOT").resolve()),
            "gateway_sidecar_ref": str(required_path("STEGVERSE_DEVICE_KV_SKAP_GATEWAY_SIDECAR").resolve()),
            "tvc_drain_receipt_ref": str(required_path("STEGVERSE_DEVICE_KV_SKAP_TVC_DRAIN_RECEIPT").resolve()),
            "credential_material_present": False,
        },
    )
    receipt = bridge.execute(request)
    if receipt.get("state") != "CANONICAL_RUNTIME_CAPABILITY_EXECUTION_OBSERVED":
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:canonical_runtime_bridge_execution_not_observed")
    if receipt.get("result", {}).get("status") != TERMINAL_STATE:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:canonical_runtime_bridge_terminal_status_invalid")
    if "output" not in executed:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:canonical_runtime_domain_executor_not_invoked")
    _write_once(bridge_path, receipt)
    return executed["output"], bridge_path


def main() -> int:
    invocation = _read_invocation()
    epoch, claim_id, fence = _validate_invocation(invocation)
    authentic_continuation = bool(os.environ.get("STEGVERSE_DEVICE_KV_SKAP_GATEWAY_SIDECAR") or os.environ.get("STEGVERSE_DEVICE_KV_SKAP_TVC_DRAIN_RECEIPT"))
    if authentic_continuation:
        required_domain = (
            "STEGVERSE_DEVICE_KV_SKAP_RETAINED_NODE",
            "STEGVERSE_DEVICE_KV_SKAP_INTR_MATERIALIZATION",
            "STEGVERSE_DEVICE_KV_SKAP_RUNTIME_LEASE_SNAPSHOT",
            "STEGVERSE_DEVICE_KV_SKAP_BRIDGE_RECEIPT",
        )
        missing = [name for name in required_domain if not os.environ.get(name)]
        if missing:
            raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:canonical_runtime_domain_binding_required:" + ",".join(missing))
        output, bridge_receipt = _execute_authentic_continuation_through_bridge(claim_id=claim_id, fence=fence)
    else:
        output, _proof = _execute_roundtrip()
        bridge_receipt = None
    print(json.dumps(_response(output=output, bridge_receipt=bridge_receipt, epoch=epoch, claim_id=claim_id, fence=fence), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
