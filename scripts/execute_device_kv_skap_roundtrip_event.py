#!/usr/bin/env python3
"""Execute one bounded Device->KV->SKAP->KV->Device task on a sovereign event runtime.

This wrapper does not grant execution, transition, or credential authority. It refreshes
already-local canonical WorkerCoordinator source into the supplied event runtime,
validates the task/COSV pointer, forwards only the non-secret evidence bindings needed
by the registered worker, and invokes the normal WorkerCoordinator task runner so a
fresh claim/fence is still required by canonical task control.

Terminal success is derived from canonical WorkerCoordinator evidence: the targeted
cycle result, exact COMPLETED worker_response event, canonical fenced checkpoint,
COMPLETED task registry state, and exact worker-result readback. The worker response
is intentionally not expected to escape the WorkerCoordinator protocol directly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from refresh_sovereign_worker_runtime_source import refresh
from scripts.refresh_and_execute_resident_task import validate_cosv_task_pointer

TASK_ID = "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001"
COSV_VECTOR = "50000000102000"
TERMINAL_TRANSITION = "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED"
RUNNER_REL = Path("scripts/run_worker_runtime.py")
CARRIER_REL = Path("control/heartbeat-carrier-runtime-state.json")
REGISTRY_REL = Path("control/worker-registry.json")
RECEIPT_REL = Path("receipts/sovereign-host/device-kv-skap-roundtrip-event-execution.latest.json")
HOSTED_ENV = ("GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")


class RoundtripEventExecutionError(ValueError):
    pass


def _existing_file(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise RoundtripEventExecutionError(f"{label}_missing:{resolved}")
    return resolved


def _existing_dir(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_dir():
        raise RoundtripEventExecutionError(f"{label}_missing:{resolved}")
    return resolved


def _safe_env(base: Mapping[str, str] | None, *, runtime: Path, stegos: Path, sidecar: Path, tvc_receipt: Path, output: Path) -> dict[str, str]:
    values = dict(os.environ if base is None else base)
    if any(str(values.get(name, "")).strip().lower() not in {"", "0", "false", "no"} for name in HOSTED_ENV):
        raise RoundtripEventExecutionError("hosted_runtime_forbidden")
    keep = ("PATH", "HOME", "LANG", "LC_ALL", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "LOCALAPPDATA")
    env = {name: values[name] for name in keep if values.get(name)}
    env.update(
        {
            "STEGVERSE_DEVICE_KV_SKAP_RUNTIME_ROOT": str(runtime),
            "STEGVERSE_DEVICE_KV_SKAP_ROUNDTRIP_OUTPUT": str(output),
            "STEGVERSE_DEVICE_KV_SKAP_GATEWAY_SIDECAR": str(sidecar),
            "STEGVERSE_DEVICE_KV_SKAP_TVC_DRAIN_RECEIPT": str(tvc_receipt),
            "STEGVERSE_STEGOS_ROOT": str(stegos),
            "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC",
            "STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY": "NONE",
        }
    )
    return env


def _last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RoundtripEventExecutionError(f"{label}_invalid_json:{path}") from exc
    if not isinstance(value, dict):
        raise RoundtripEventExecutionError(f"{label}_object_required:{path}")
    return value


def _checkpoint_digest(checkpoint: Mapping[str, Any]) -> str:
    body = dict(checkpoint)
    body.pop("checkpoint_sha256", None)
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_targeted_terminal_evidence(*, runtime: Path, cycle: Mapping[str, Any], result_path: Path) -> dict[str, Any]:
    if cycle.get("schema") != "stegverse.worker-runtime-cycle-result/v1":
        raise RoundtripEventExecutionError("worker_cycle_schema_invalid")
    if cycle.get("target_task_id") != TASK_ID or cycle.get("targeted_independent_task_control") is not True:
        raise RoundtripEventExecutionError("worker_cycle_not_targeted_to_roundtrip_task")
    if cycle.get("unrelated_worker_execution_suppressed") is not True or cycle.get("carrier_packet_execution_suppressed") is not True:
        raise RoundtripEventExecutionError("targeted_worker_isolation_not_observed")
    if cycle.get("credential_authority") != "TV/TVC" or cycle.get("github_token_runtime_authority") != "NONE":
        raise RoundtripEventExecutionError("worker_cycle_authority_boundary_invalid")

    events = cycle.get("events")
    if not isinstance(events, list):
        raise RoundtripEventExecutionError("worker_cycle_events_required")
    responses = [
        event for event in events
        if isinstance(event, Mapping)
        and event.get("event_type") == "worker_response"
        and event.get("task_id") == TASK_ID
        and event.get("response_state") == "COMPLETED"
        and event.get("transition_id") == TERMINAL_TRANSITION
    ]
    if len(responses) != 1:
        raise RoundtripEventExecutionError("canonical_completed_worker_response_not_observed")

    checkpoints = [
        event for event in events
        if isinstance(event, Mapping)
        and event.get("event_type") == "canonical_worker_checkpoint_written"
        and event.get("task_id") == TASK_ID
    ]
    if len(checkpoints) != 1:
        raise RoundtripEventExecutionError("canonical_worker_checkpoint_event_not_observed")
    checkpoint_event = checkpoints[0]
    checkpoint_ref = checkpoint_event.get("checkpoint_ref")
    fence = checkpoint_event.get("fencing_token")
    if not isinstance(checkpoint_ref, str) or not checkpoint_ref.startswith("checkpoints/workers/"):
        raise RoundtripEventExecutionError("canonical_worker_checkpoint_ref_invalid")
    if not isinstance(fence, int) or fence < 1:
        raise RoundtripEventExecutionError("canonical_worker_checkpoint_fence_invalid")
    checkpoint_path = (runtime / checkpoint_ref).resolve()
    try:
        checkpoint_path.relative_to(runtime.resolve())
    except ValueError as exc:
        raise RoundtripEventExecutionError("canonical_worker_checkpoint_outside_runtime") from exc
    checkpoint = _load_object(_existing_file(checkpoint_path, "canonical_worker_checkpoint"), "canonical_worker_checkpoint")
    if checkpoint.get("schema") != "stegverse.worker-checkpoint/v0.1":
        raise RoundtripEventExecutionError("canonical_worker_checkpoint_schema_invalid")
    if checkpoint.get("task_id") != TASK_ID or checkpoint.get("current_state") != "COMPLETED":
        raise RoundtripEventExecutionError("canonical_worker_checkpoint_terminal_state_invalid")
    if checkpoint.get("fencing_token") != fence or checkpoint.get("execution_authority") is not False:
        raise RoundtripEventExecutionError("canonical_worker_checkpoint_authority_or_fence_invalid")
    if checkpoint.get("checkpoint_sha256") != _checkpoint_digest(checkpoint):
        raise RoundtripEventExecutionError("canonical_worker_checkpoint_digest_invalid")
    if checkpoint_event.get("checkpoint_sha256") != checkpoint.get("checkpoint_sha256"):
        raise RoundtripEventExecutionError("canonical_worker_checkpoint_event_digest_mismatch")
    transitions = checkpoint.get("completed_transitions")
    if not isinstance(transitions, list) or not transitions:
        raise RoundtripEventExecutionError("canonical_worker_checkpoint_transition_history_missing")
    terminal = transitions[-1]
    if not isinstance(terminal, Mapping) or terminal.get("transition_id") != TERMINAL_TRANSITION or terminal.get("response_state") != "COMPLETED":
        raise RoundtripEventExecutionError("canonical_worker_checkpoint_terminal_transition_invalid")

    registry = _load_object(_existing_file(runtime / REGISTRY_REL, "worker_registry"), "worker_registry")
    tasks = registry.get("tasks")
    task = next((item for item in tasks if isinstance(item, Mapping) and item.get("task_id") == TASK_ID), None) if isinstance(tasks, list) else None
    if not isinstance(task, Mapping) or task.get("state") != "COMPLETED":
        raise RoundtripEventExecutionError("worker_registry_task_not_completed")
    if task.get("last_checkpoint_ref") != checkpoint_ref:
        raise RoundtripEventExecutionError("worker_registry_checkpoint_binding_mismatch")
    timing = task.get("heartbeat_timing")
    if not isinstance(timing, Mapping) or timing.get("current_transition") != TERMINAL_TRANSITION or timing.get("fencing_token") != fence:
        raise RoundtripEventExecutionError("worker_registry_terminal_transition_or_fence_invalid")

    proof = _load_object(_existing_file(result_path, "roundtrip_worker_result"), "roundtrip_worker_result")
    if proof.get("state") != TERMINAL_TRANSITION:
        raise RoundtripEventExecutionError("roundtrip_worker_result_not_verified")

    return {
        "state": TERMINAL_TRANSITION,
        "worker_response_event": dict(responses[0]),
        "canonical_checkpoint_ref": checkpoint_ref,
        "canonical_checkpoint_sha256": checkpoint["checkpoint_sha256"],
        "fencing_token": fence,
        "worker_result_ref": str(result_path),
        "worker_result": proof,
    }


def execute(*, source_root: Path, runtime_root: Path, stegos_root: Path, gateway_sidecar: Path, tvc_drain_receipt: Path, output: Path | None = None, runner=subprocess.run, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = _existing_dir(source_root, "source_root")
    runtime = runtime_root.expanduser().resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    stegos = _existing_dir(stegos_root, "stegos_root")
    sidecar = _existing_file(gateway_sidecar, "gateway_sidecar")
    tvc_receipt = _existing_file(tvc_drain_receipt, "tvc_drain_receipt")
    result_path = (output or runtime / "receipts/sovereign-host/device-kv-skap-roundtrip/worker-result.json").expanduser().resolve()

    refresh_receipt = refresh(source, runtime)
    pointer = validate_cosv_task_pointer(runtime, TASK_ID, COSV_VECTOR)
    runner_path = runtime / RUNNER_REL
    if not runner_path.is_file():
        raise RoundtripEventExecutionError(f"workercoordinator_runner_missing:{runner_path}")
    if not (runtime / CARRIER_REL).is_file():
        raise RoundtripEventExecutionError("separated_carrier_reference_missing")

    child_env = _safe_env(env, runtime=runtime, stegos=stegos, sidecar=sidecar, tvc_receipt=tvc_receipt, output=result_path)
    command = [sys.executable, str(runner_path), "--root", str(runtime), "--task-id", TASK_ID]
    completed = runner(command, cwd=runtime, env=child_env, check=False, capture_output=True, text=True)
    cycle_result = _last_json(completed.stdout)
    terminal_evidence = None
    terminal_error = None
    if completed.returncode == 0 and isinstance(cycle_result, dict):
        try:
            terminal_evidence = _validate_targeted_terminal_evidence(runtime=runtime, cycle=cycle_result, result_path=result_path)
        except RoundtripEventExecutionError as exc:
            terminal_error = str(exc)
    else:
        terminal_error = "workercoordinator_cycle_failed_or_missing"

    terminal_verified = isinstance(terminal_evidence, dict) and terminal_evidence.get("state") == TERMINAL_TRANSITION
    receipt = {
        "schema": "stegverse.device-kv-skap.event-ephemeral-execution/v2",
        "state": TERMINAL_TRANSITION if terminal_verified else "DEVICE_KV_SKAP_ROUNDTRIP_EXECUTION_INCOMPLETE",
        "task_id": TASK_ID,
        "cosv_task_pointer": pointer,
        "refresh_receipt": refresh_receipt,
        "workercoordinator_command": command,
        "workercoordinator_returncode": completed.returncode,
        "workercoordinator_cycle_result": cycle_result,
        "terminal_evidence": terminal_evidence,
        "terminal_validation_error": terminal_error,
        "runtime_execution_attempted": True,
        "event_ephemeral_materialization": True,
        "persistent_transport_runtime_required": False,
        "always_on_receiver_required": False,
        "second_user_operated_device_used": False,
        "hosted_runtime_used": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "request_grants_execution_authority": False,
        "transport_grants_execution_authority": False,
        "authority_effect": "EXISTING_WORKERCOORDINATOR_AND_INTR_AUTHORITY_ONLY",
    }
    receipt_path = runtime / RECEIPT_REL
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if receipt_path.exists() and receipt_path.read_text(encoding="utf-8") != serialized:
        raise RoundtripEventExecutionError("event_execution_receipt_write_once_collision")
    receipt_path.write_text(serialized, encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute one governed Device-KV-SKAP roundtrip on a bounded sovereign event runtime.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--stegos-root", type=Path, required=True)
    parser.add_argument("--gateway-sidecar", type=Path, required=True)
    parser.add_argument("--tvc-drain-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        receipt = execute(source_root=args.source_root, runtime_root=args.runtime_root, stegos_root=args.stegos_root, gateway_sidecar=args.gateway_sidecar, tvc_drain_receipt=args.tvc_drain_receipt, output=args.output)
    except Exception as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc), "authority_effect": "NONE"}, sort_keys=True))
        return 1
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["state"] == TERMINAL_TRANSITION else 1


if __name__ == "__main__":
    raise SystemExit(main())
