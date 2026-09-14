#!/usr/bin/env python3
"""Fenced WorkerCoordinator bridge for Personal-KV AI memory materialization.

The worker receives only the canonical process-worker invocation plus a sandboxed
bound-state mirror. Private KV packet/prompt material stays in bound state. The
worker delegates exact ProviderRequest construction to the already-local
LLM-adapter materializer and emits no provider, InTr, TV/TVC, or KV-write claim.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

TASK_ID = "SV-KV-AI-PERSISTENCE-001"
BOUND_STATE_ENV = "STEGVERSE_BOUND_STATE_ROOT"
LLM_ROOT_ENV = "STEGVERSE_LLM_ADAPTER_ROOT"
PACKET_REL = Path("inputs/context-packet.json")
ADMISSION_REL = Path("inputs/memory-packet-admission.json")
REQUEST_INPUT_REL = Path("inputs/provider-request-input.json")
OUTPUT_REL = Path("materialized/provider-request.json")
RECEIPT_REL = Path("receipts/provider-request-materialization.json")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def validate_invocation(invocation: dict[str, Any]) -> dict[str, Any]:
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        raise ValueError("worker invocation schema mismatch")
    task = invocation.get("task")
    scope = invocation.get("scope")
    if not isinstance(task, dict) or not isinstance(scope, dict):
        raise ValueError("worker invocation task/scope missing")
    if task.get("task_id") != TASK_ID:
        raise ValueError("worker invocation task mismatch")
    if task.get("state") != "ACTIVE":
        raise ValueError("worker invocation task is not ACTIVE")
    claim_id = task.get("claim_id")
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), dict) else {}
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id or not isinstance(fence, int) or fence < 1:
        raise ValueError("current WorkerCoordinator claim/fence required")
    if claim_id != scope.get("claim_id") or fence != scope.get("fencing_token"):
        raise ValueError("worker invocation scope claim/fence mismatch")
    if not claim_id.endswith(f"-G{fence}"):
        raise ValueError("worker invocation claim generation mismatch")
    if scope.get("bound_state_enabled") is not True:
        raise ValueError("KV AI memory worker requires fenced bound state")
    return task


def require_bound_state() -> Path:
    raw = str(os.environ.get(BOUND_STATE_ENV) or "").strip()
    if not raw:
        raise RuntimeError("fenced KV AI memory bound-state root unavailable")
    root = Path(raw).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def require_llm_root() -> Path:
    raw = str(os.environ.get(LLM_ROOT_ENV) or "").strip()
    if not raw:
        raise RuntimeError("already-local LLM-adapter root unavailable")
    root = Path(raw).expanduser().resolve()
    script = root / "scripts/materialize_kv_memory_provider_request.py"
    if not script.is_file():
        raise RuntimeError("KV memory ProviderRequest materializer unavailable in LLM-adapter root")
    return root


def response(state: str, transition: str, *, checkpoint: str | None, evidence: list[str], recovery_units: int = 0, error: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": "KV_AI_MEMORY_LIVE_PROVIDER_INGRESS" if state != "COMPLETED" else None,
        "expected_next_earliest_epoch": None,
        "expected_next_latest_epoch": None,
        "checkpoint_ref": checkpoint,
        "evidence_refs": evidence,
        "cost_observation": {
            "compute_units": 1,
            "token_units": 0,
            "storage_bytes": 0,
            "network_bytes": 0,
            "operator_seconds": 0,
            "external_cost_usd": 0,
            "latency_ms": None,
            "failure_recovery_units": recovery_units,
            "services_used": [],
        },
        "authority_effect": "NONE_BOUND_STATE_MATERIALIZATION_ONLY",
    }
    if error is not None:
        value["error"] = error
    return value


def run(invocation: dict[str, Any], *, runner: Callable[..., Any] = subprocess.run) -> dict[str, Any]:
    validate_invocation(invocation)
    state_root = require_bound_state()
    llm_root = require_llm_root()
    packet = state_root / PACKET_REL
    admission = state_root / ADMISSION_REL
    request_input = state_root / REQUEST_INPUT_REL
    missing = [str(path.relative_to(state_root)) for path in (packet, admission, request_input) if not path.is_file()]
    if missing:
        return response(
            "HANDOFF_READY",
            "KV_AI_MEMORY_RESIDENT_INPUT_NOT_READY",
            checkpoint=None,
            evidence=[],
            recovery_units=1,
            error="missing resident-local bound-state input: " + ",".join(missing),
        )

    output = state_root / OUTPUT_REL
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(llm_root / "scripts/materialize_kv_memory_provider_request.py"),
        "--packet", str(packet),
        "--admission", str(admission),
        "--request-input", str(request_input),
        "--output", str(output),
    ]
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(llm_root),
        "HOME": os.environ.get("HOME", ""),
    }
    completed = runner(command, cwd=llm_root, capture_output=True, text=True, check=False, env=env, timeout=120)
    if completed.returncode != 0 or not output.is_file():
        return response(
            "HANDOFF_READY",
            "KV_AI_MEMORY_PROVIDER_REQUEST_MATERIALIZATION_FAIL_CLOSED",
            checkpoint=None,
            evidence=[],
            recovery_units=1,
            error=(completed.stderr or "materializer produced no output")[-1200:],
        )

    materialized = load_object(output)
    checks = {
        "state": materialized.get("state") == "PROVIDER_REQUEST_MATERIALIZED",
        "credential_material_present": materialized.get("credential_material_present") is False,
        "request_granted_authority": materialized.get("request_granted_authority") is False,
        "provider_ingress_admission_observed": materialized.get("provider_ingress_admission_observed") is False,
        "provider_execution_observed": materialized.get("provider_execution_observed") is False,
        "provider_egress_admission_observed": materialized.get("provider_egress_admission_observed") is False,
        "kv_writeback_observed": materialized.get("kv_writeback_observed") is False,
        "authority_effect": materialized.get("authority_effect") == "NONE_MATERIALIZATION_ONLY",
    }
    failed = sorted(key for key, ok in checks.items() if not ok)
    if failed:
        raise RuntimeError("materialized ProviderRequest authority invariant mismatch: " + ",".join(failed))

    receipt = {
        "schema": "stegverse.kv-ai-memory.resident-provider-request-materialization/v1",
        "state": "PROVIDER_REQUEST_MATERIALIZED",
        "task_id": TASK_ID,
        "provider_request_hash": materialized.get("provider_request_hash"),
        "memory_packet_id": materialized.get("memory_packet_id"),
        "memory_packet_sha256": materialized.get("memory_packet_sha256"),
        "memory_packet_intr_receipt_hash": materialized.get("memory_packet_intr_receipt_hash"),
        "materialized_object_sha256": canonical_hash(materialized),
        "provider_request_ref": OUTPUT_REL.as_posix(),
        "provider_ingress_admission_observed": False,
        "provider_execution_observed": False,
        "provider_egress_admission_observed": False,
        "kv_writeback_observed": False,
        "credential_material_present": False,
        "worker_claim_or_fence_minted": False,
        "authority_effect": "NONE_BOUND_STATE_MATERIALIZATION_ONLY",
    }
    receipt_path = state_root / RECEIPT_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return response(
        "HANDOFF_READY",
        "KV_AI_MEMORY_PROVIDER_REQUEST_MATERIALIZED",
        checkpoint="bound-state:" + RECEIPT_REL.as_posix(),
        evidence=["bound-state:" + OUTPUT_REL.as_posix(), "bound-state:" + RECEIPT_REL.as_posix()],
    )


def main() -> int:
    try:
        invocation = json.load(sys.stdin)
        if not isinstance(invocation, dict):
            raise ValueError("worker invocation must be object")
        result = run(invocation)
    except Exception as exc:
        result = response(
            "HANDOFF_READY",
            "KV_AI_MEMORY_WORKER_FAIL_CLOSED",
            checkpoint=None,
            evidence=[],
            recovery_units=1,
            error=f"{type(exc).__name__}: {exc}",
        )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
