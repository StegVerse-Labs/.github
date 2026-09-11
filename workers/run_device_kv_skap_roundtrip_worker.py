#!/usr/bin/env python3
"""WorkerCoordinator entrypoint for authentic Device <-> KV <-> SKAP continuation.

The process adapter supplies one already-claimed/fenced worker invocation on
stdin. This worker binds that exact task/handoff/scope before touching runtime
evidence, then emits one canonical worker-response object. It does not mint a
claim/fence, admit an Interlock/InTr transition, resolve credentials, or create
substitute runtime evidence.
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
INVOCATION_SCHEMA = "stegverse.worker-invocation/v0.1"
RESPONSE_SCHEMA = "stegverse.worker-response/v0.1"


def required_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"DEVICE_KV_SKAP_ROUNDTRIP_FAIL:{name.lower()}_required")
    return Path(value)


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


def _write_once(output: Path, value: dict) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, sort_keys=True, indent=2) + "\n"
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


def _response(*, output: Path, epoch: int, claim_id: str, fence: int) -> dict[str, Any]:
    checkpoint = _evidence_ref(output)
    return {
        "schema": RESPONSE_SCHEMA,
        "state": "COMPLETED",
        "transition_id": "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED",
        "transition_sequence": 1,
        "expected_next_transition": None,
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": checkpoint,
        "evidence_refs": [checkpoint],
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
    output = required_path("STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_OUTPUT")
    manifest_path = optional_path("STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_MANIFEST")
    gateway_sidecar = optional_path("STEGVERSE_DEVICE_KV_SKAP_GATEWAY_SIDECAR")
    tvc_drain_receipt = optional_path("STEGVERSE_DEVICE_KV_SKAP_TVC_DRAIN_RECEIPT")
    stegos_root = optional_path("STEGVERSE_STEGOS_ROOT")

    continuation_inputs = [gateway_sidecar, tvc_drain_receipt, stegos_root]
    if any(continuation_inputs) and not all(continuation_inputs):
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:incomplete_tvc_continuation_inputs")

    if all(continuation_inputs):
        continuation = _load_continuation()
        result = continuation.continue_roundtrip(
            runtime_root=runtime_root,
            stegos_root=stegos_root,
            gateway_sidecar_path=gateway_sidecar,
            tvc_drain_receipt_path=tvc_drain_receipt,
        )
        if result.get("state") != "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED":
            raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:continuation_not_verified")
        _write_once(output, result)
        return output, result

    if manifest_path is None:
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:manifest_or_tvc_continuation_required")

    manifest = _load_json(manifest_path, "manifest")
    proof = verify_manifest(manifest, runtime_root=runtime_root)
    if proof.get("state") != "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED":
        raise SystemExit("DEVICE_KV_SKAP_ROUNDTRIP_FAIL:manifest_not_verified")
    _write_once(output, proof)
    return output, proof


def main() -> int:
    invocation = _read_invocation()
    epoch, claim_id, fence = _validate_invocation(invocation)
    output, _proof = _execute_roundtrip()
    print(json.dumps(_response(output=output, epoch=epoch, claim_id=claim_id, fence=fence), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
