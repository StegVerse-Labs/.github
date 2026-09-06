#!/usr/bin/env python3
"""Repair missing resident WorkerCoordinator presence without granting task authority.

This module is process supervision only. A live HeartBeat carrier may be used as
node-presence evidence, but neither the carrier nor this repair function grants
claim, fence, admission, credential, route, transition, publication, or task
execution authority. The spawned WorkerCoordinator must independently admit and
execute work under its existing contracts.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from heartbeat_runtime.runtime_presence_projection import project

PROCESS_RECEIPT = Path("receipts/sovereign-host/ephemeral-process.latest.json")
PRESENCE_RECEIPT = Path("receipts/sovereign-host/runtime-presence.latest.json")
WORKER_STATE = Path("control/worker-runtime-state.json")
WORKER_RUNNER = Path("scripts/run_worker_runtime.py")
HOSTED_ENV = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
FORBIDDEN_NAME_PARTS = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "API_KEY", "PRIVATE_KEY", "CREDENTIAL")
SAFE_ENV = {
    "HOME", "USER", "LOGNAME", "SHELL", "PATH", "PYTHONPATH", "LANG", "LC_ALL", "TMPDIR",
    "XDG_CONFIG_HOME", "XDG_STATE_HOME", "LOCALAPPDATA", "UID",
    "STEGVERSE_SOVEREIGN_NODE", "STEGVERSE_HEARTBEAT_ROOT", "STEGVERSE_HEARTBEAT_SOURCE_ROOT",
    "STEGVERSE_HEALER_ROOT", "STEGVERSE_REPO_ROOTS_JSON", "STEGVERSE_STEGINDEX_SOURCE_ROOT",
    "STEGVERSE_LLM_ADAPTER_ROOT", "STEGVERSE_TVC_ROOT", "STEGVERSE_TV_ROOT",
    "STEGVERSE_MICRO_NODE_RUNTIME_ROOT", "STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT",
    "STEGVERSE_MASTER_RECORDS_ROOT", "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
    "STEGVERSE_STEGCORE_SOURCE_ROOT", "STEGVERSE_STEGOS_ROOT", "STEGVERSE_KV_SOURCE_ROOT",
    "STEGVERSE_KV_ROOT", "STEGVERSE_KV_PROVIDER_BINDING_PATH", "STEGVERSE_KV_PROVIDER_MATERIALIZED_ROOT",
    "STEGVERSE_TVC_PROVIDER_SESSION_FILE", "STEGVERSE_SITE_ROOT", "STEGVERSE_TT_ROOT",
    "STEGVERSE_RTG_ROOT", "STEGVERSE_GTG_ROOT", "STEGVERSE_AE_ROOT",
    "STEGVERSE_RESIDENT_SOURCE_MANIFEST", "STEGVERSE_SV001_AUTONOMY_LEASE",
    "STEGVERSE_SV011_ORG_ROOT", "STEGVERSE_SV002_MICRO_NODE_ROOT",
}


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _alive(pid: Any) -> bool:
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _clean_env(runtime_root: Path) -> dict[str, str]:
    source = os.environ
    env = {name: source[name] for name in SAFE_ENV if source.get(name)}
    env["STEGVERSE_SOVEREIGN_NODE"] = "1"
    env["STEGVERSE_HEARTBEAT_ROOT"] = str(runtime_root)
    for name in list(env):
        upper = name.upper()
        if any(part in upper for part in FORBIDDEN_NAME_PARTS):
            env.pop(name, None)
    return env


def _runtime_tick(runtime_root: Path) -> int:
    value = _load(runtime_root / WORKER_STATE)
    tick = value.get("runtime_tick")
    return tick if isinstance(tick, int) and not isinstance(tick, bool) else -1


def _wait_for_tick(runtime_root: Path, baseline: int, pid: int, timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _alive(pid):
            return {"observed": False, "reason": "WORKER_EXITED_BEFORE_TASK_CAPABLE_TICK", "baseline_tick": baseline, "observed_tick": _runtime_tick(runtime_root)}
        current = _runtime_tick(runtime_root)
        if current > baseline:
            return {"observed": True, "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_OBSERVED", "baseline_tick": baseline, "observed_tick": current}
        time.sleep(0.02)
    return {"observed": False, "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_TIMEOUT", "baseline_tick": baseline, "observed_tick": _runtime_tick(runtime_root)}


def _supervision_receipt(
    prior: dict[str, Any],
    runtime_root: Path,
    *,
    carrier_pid: int,
    worker_pid: int,
    worker_tick_observed: bool,
    tick_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    receipt = dict(prior)
    receipt.update({
        "schema": receipt.get("schema") or "stegverse.ephemeral-sovereign-process/v3",
        "runtime_root": str(runtime_root),
        "carrier_pid": carrier_pid,
        "worker_pid": worker_pid,
        "carrier_active": True,
        "worker_active": True,
        "worker_task_capable_cycle_observed": bool(worker_tick_observed),
        "active": True,
        "separate_carrier_and_worker_processes": True,
        "canonical_carrier_runtime": "heartbeat_runtime.engine_v13.HeartbeatRuntime",
        "worker_runtime": "heartbeat_runtime.worker_runtime.WorkerCoordinator",
        "supervision_kind": "STEGVERSE_CARRIER_OBSERVED_SELF_HEAL",
        "third_party_process_host_required": False,
        "third_party_scheduler_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "worker_coordinator_retains_admission_authority": True,
        "authority_effect": "NONE_SUPERVISION_ONLY",
    })
    if tick_evidence is not None:
        receipt["worker_tick_evidence"] = tick_evidence
    return receipt


def _persist_presence_projection(runtime_root: Path) -> dict[str, Any]:
    projection = project(runtime_root)
    path = runtime_root / PRESENCE_RECEIPT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(projection, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return projection


def ensure_worker_presence(runtime_root: Path, *, carrier_pid: int, interval_ms: float = 10.0, timeout: float = 3.0) -> dict[str, Any]:
    runtime_root = runtime_root.expanduser().resolve()
    if any(os.environ.get(name) for name in HOSTED_ENV):
        return {"state": "HOSTED_ENVIRONMENT_REJECTED", "worker_repair_attempted": False, "authority_effect": "NONE"}
    if not _alive(carrier_pid):
        return {"state": "CARRIER_PROCESS_NOT_ALIVE", "worker_repair_attempted": False, "authority_effect": "NONE"}
    runner = runtime_root / WORKER_RUNNER
    if not runner.is_file():
        return {"state": "WORKER_RUNNER_NOT_MATERIALIZED", "worker_repair_attempted": False, "authority_effect": "NONE"}

    receipt_path = runtime_root / PROCESS_RECEIPT
    receipt = _load(receipt_path)
    existing_worker_pid = receipt.get("worker_pid")
    if _alive(existing_worker_pid):
        worker_state = _load(runtime_root / WORKER_STATE)
        structural_task_capable = (
            worker_state.get("schema") == "stegverse.worker-runtime-state/v1"
            and worker_state.get("observation_mode") != "CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION"
            and isinstance(worker_state.get("runtime_tick"), int)
        )
        receipt = _supervision_receipt(
            receipt,
            runtime_root,
            carrier_pid=carrier_pid,
            worker_pid=existing_worker_pid,
            worker_tick_observed=structural_task_capable,
        )
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        presence = _persist_presence_projection(runtime_root)
        return {
            "state": "WORKER_ALREADY_PRESENT",
            "worker_repair_attempted": False,
            "carrier_pid": carrier_pid,
            "worker_pid": existing_worker_pid,
            "present_worker_runtime_observed": presence.get("resident", {}).get("present_worker_runtime_observed") is True,
            "presence_receipt_ref": str(PRESENCE_RECEIPT),
            "heartbeat_grants_execution_authority": False,
            "worker_coordinator_retains_admission_authority": True,
            "authority_effect": "NONE_SUPERVISION_ONLY",
        }

    baseline = _runtime_tick(runtime_root)
    receipt_root = runtime_root / "receipts" / "sovereign-host"
    receipt_root.mkdir(parents=True, exist_ok=True)
    out_handle = (receipt_root / "self-healed-worker.stdout.log").open("ab", buffering=0)
    err_handle = (receipt_root / "self-healed-worker.stderr.log").open("ab", buffering=0)
    worker = subprocess.Popen(
        [sys.executable, str(runner), "--root", str(runtime_root), "--continuous", "--interval-ms", str(interval_ms)],
        cwd=str(runtime_root), env=_clean_env(runtime_root), stdin=subprocess.DEVNULL,
        stdout=out_handle, stderr=err_handle, start_new_session=True, close_fds=True,
    )
    tick = _wait_for_tick(runtime_root, baseline, worker.pid, timeout)
    if not tick.get("observed"):
        try:
            os.kill(worker.pid, signal.SIGTERM)
        except OSError:
            pass
        return {
            "state": "WORKER_REPAIR_FAILED",
            "worker_repair_attempted": True,
            "carrier_pid": carrier_pid,
            "worker_pid": worker.pid,
            "worker_tick_evidence": tick,
            "heartbeat_grants_execution_authority": False,
            "worker_coordinator_retains_admission_authority": True,
            "authority_effect": "NONE_SUPERVISION_ONLY",
        }

    receipt = _supervision_receipt(
        receipt,
        runtime_root,
        carrier_pid=carrier_pid,
        worker_pid=worker.pid,
        worker_tick_observed=True,
        tick_evidence=tick,
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    presence = _persist_presence_projection(runtime_root)
    return {
        "state": "WORKER_REPAIRED",
        "worker_repair_attempted": True,
        "carrier_pid": carrier_pid,
        "worker_pid": worker.pid,
        "worker_tick_evidence": tick,
        "present_worker_runtime_observed": presence.get("resident", {}).get("present_worker_runtime_observed") is True,
        "presence_receipt_ref": str(PRESENCE_RECEIPT),
        "request_drain_expected_on_worker_start": True,
        "heartbeat_grants_execution_authority": False,
        "worker_coordinator_retains_admission_authority": True,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_SUPERVISION_ONLY",
    }


if __name__ == "__main__":
    raise SystemExit("import ensure_worker_presence from the canonical carrier runtime")
