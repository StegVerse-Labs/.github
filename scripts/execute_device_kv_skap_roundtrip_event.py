#!/usr/bin/env python3
"""Execute one bounded Device->KV->SKAP->KV->Device task on a sovereign event runtime.

This wrapper does not grant execution, transition, or credential authority. It refreshes
already-local canonical WorkerCoordinator source into the supplied event runtime,
validates the task/COSV pointer, forwards only the non-secret evidence bindings needed
by the registered worker, and invokes the normal WorkerCoordinator task runner so a
fresh claim/fence is still required by canonical task control.
"""
from __future__ import annotations

import argparse
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
RUNNER_REL = Path("scripts/run_worker_runtime.py")
CARRIER_REL = Path("control/heartbeat-carrier-runtime-state.json")
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
    execution_result = _last_json(completed.stdout)
    terminal_verified = isinstance(execution_result, dict) and execution_result.get("state") == "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED"
    receipt = {
        "schema": "stegverse.device-kv-skap.event-ephemeral-execution/v1",
        "state": "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED" if completed.returncode == 0 and terminal_verified else "DEVICE_KV_SKAP_ROUNDTRIP_EXECUTION_INCOMPLETE",
        "task_id": TASK_ID,
        "cosv_task_pointer": pointer,
        "refresh_receipt": refresh_receipt,
        "workercoordinator_command": command,
        "workercoordinator_returncode": completed.returncode,
        "execution_result": execution_result,
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
    return 0 if receipt["state"] == "DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
