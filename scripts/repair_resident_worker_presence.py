#!/usr/bin/env python3
"""Repair missing or stalled resident WorkerCoordinator presence without granting task authority.

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
PRESENCE_MR_INTAKE_RECEIPT = Path("receipts/sovereign-host/runtime-presence-master-records-intake.latest.json")
WORKER_STATE = Path("control/worker-runtime-state.json")
WORKER_RUNNER = Path("scripts/run_worker_runtime.py")
MR_IMPORTER = Path("scripts/intake_resident_runtime_presence.py")
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


def _intake_env() -> dict[str, str]:
    allowed = ("HOME", "PATH", "PYTHONPATH", "LANG", "LC_ALL", "TMPDIR", "XDG_CONFIG_HOME", "XDG_STATE_HOME")
    env = {name: os.environ[name] for name in allowed if os.environ.get(name)}
    for name in list(env):
        if any(part in name.upper() for part in FORBIDDEN_NAME_PARTS):
            env.pop(name, None)
    return env


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _runtime_tick(runtime_root: Path) -> int:
    value = _load(runtime_root / WORKER_STATE)
    tick = value.get("runtime_tick")
    return tick if isinstance(tick, int) and not isinstance(tick, bool) else -1


def _task_capable_state(runtime_root: Path) -> bool:
    value = _load(runtime_root / WORKER_STATE)
    return (
        value.get("schema") == "stegverse.worker-runtime-state/v1"
        and value.get("observation_mode") != "CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION"
        and isinstance(value.get("runtime_tick"), int)
        and not isinstance(value.get("runtime_tick"), bool)
    )


def _wait_for_tick(runtime_root: Path, baseline: int, pid: int, timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _alive(pid):
            return {"observed": False, "reason": "WORKER_EXITED_BEFORE_TASK_CAPABLE_TICK", "baseline_tick": baseline, "observed_tick": _runtime_tick(runtime_root)}
        current = _runtime_tick(runtime_root)
        if current > baseline and _task_capable_state(runtime_root):
            return {"observed": True, "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_OBSERVED", "baseline_tick": baseline, "observed_tick": current}
        time.sleep(0.02)
    return {"observed": False, "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_TIMEOUT", "baseline_tick": baseline, "observed_tick": _runtime_tick(runtime_root)}


def _stop_stale_worker(pid: int, timeout: float = 1.0) -> dict[str, Any]:
    """Stop one stale canonical worker before restarting the same worker implementation."""
    if not _alive(pid):
        return {"stopped": True, "signal": None, "reason": "WORKER_ALREADY_EXITED"}
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return {"stopped": not _alive(pid), "signal": "SIGTERM", "reason": "SIGTERM_RACE"}
    deadline = time.monotonic() + max(timeout, 0.0)
    while time.monotonic() < deadline:
        if not _alive(pid):
            return {"stopped": True, "signal": "SIGTERM", "reason": "STALE_WORKER_TERMINATED"}
        time.sleep(0.02)
    if hasattr(signal, "SIGKILL"):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        kill_deadline = time.monotonic() + min(max(timeout, 0.0), 0.5)
        while time.monotonic() < kill_deadline:
            if not _alive(pid):
                return {"stopped": True, "signal": "SIGKILL", "reason": "STALE_WORKER_KILLED_AFTER_TIMEOUT"}
            time.sleep(0.02)
    return {"stopped": not _alive(pid), "signal": "SIGKILL" if hasattr(signal, "SIGKILL") else "SIGTERM", "reason": "STALE_WORKER_STOP_TIMEOUT"}


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
    _write_json(path, projection)
    return projection


def _persist_presence_master_records_intake(runtime_root: Path) -> dict[str, Any]:
    """Attempt local Master Records custody without making custody a presence prerequisite."""
    presence_path = runtime_root / PRESENCE_RECEIPT
    output_path = runtime_root / PRESENCE_MR_INTAKE_RECEIPT
    mr_root_raw = os.environ.get("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", "").strip()
    base = {
        "schema": "stegverse.runtime-presence-master-records-intake/v1",
        "presence_receipt_ref": str(PRESENCE_RECEIPT),
        "master_records_root": mr_root_raw or None,
        "network_fetch_performed": False,
        "repository_writeback_performed": False,
        "cross_task_reuse_authorized": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "authority_effect": "NONE_CUSTODY_HANDOFF_ONLY",
    }
    if not presence_path.is_file():
        result = {**base, "state": "PRESENCE_RECEIPT_NOT_MATERIALIZED"}
        _write_json(output_path, result)
        return result
    if not mr_root_raw:
        result = {**base, "state": "MASTER_RECORDS_ROOT_NOT_DECLARED"}
        _write_json(output_path, result)
        return result
    mr_root = Path(mr_root_raw).expanduser().resolve()
    importer = mr_root / MR_IMPORTER
    if not importer.is_file():
        result = {**base, "state": "MASTER_RECORDS_IMPORTER_NOT_MATERIALIZED", "master_records_root": str(mr_root)}
        _write_json(output_path, result)
        return result
    try:
        completed = subprocess.run(
            [sys.executable, str(importer), "--repo-root", str(mr_root), "--source", str(presence_path)],
            cwd=str(mr_root),
            env=_intake_env(),
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        parsed = json.loads(completed.stdout.strip()) if completed.stdout.strip() else {}
        valid = (
            completed.returncode == 0
            and isinstance(parsed, dict)
            and parsed.get("state") == "COMPLETED"
            and parsed.get("cross_task_reuse_authorized") is False
            and parsed.get("credential_authority") == "TV/TVC"
            and parsed.get("github_token_runtime_authority") == "NONE"
            and parsed.get("authority_effect") == "NONE_INTAKE_RECEIPT_ONLY"
        )
        result = {
            **base,
            "state": "COMPLETED" if valid else "FAIL_CLOSED_INVALID_MASTER_RECORDS_INTAKE",
            "master_records_root": str(mr_root),
            "importer_ref": str(MR_IMPORTER),
            "returncode": completed.returncode,
            "custody_id": parsed.get("custody_id") if valid else None,
            "custody_ref": parsed.get("custody_ref") if valid else None,
            "runtime_root": parsed.get("runtime_root") if valid else None,
            "resident_node_id": parsed.get("resident_node_id") if valid else None,
            "present_worker_runtime_observed": parsed.get("present_worker_runtime_observed") if valid else None,
            "stderr_tail": completed.stderr[-1000:],
        }
    except Exception as exc:
        result = {**base, "state": "FAIL_CLOSED_MASTER_RECORDS_INTAKE_EXCEPTION", "master_records_root": str(mr_root), "error": type(exc).__name__}
    _write_json(output_path, result)
    return result


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
    stale_worker_evidence: dict[str, Any] | None = None
    if _alive(existing_worker_pid):
        baseline = _runtime_tick(runtime_root)
        tick = _wait_for_tick(runtime_root, baseline, existing_worker_pid, timeout)
        if tick.get("observed"):
            receipt = _supervision_receipt(
                receipt,
                runtime_root,
                carrier_pid=carrier_pid,
                worker_pid=existing_worker_pid,
                worker_tick_observed=True,
                tick_evidence=tick,
            )
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            presence = _persist_presence_projection(runtime_root)
            intake = _persist_presence_master_records_intake(runtime_root)
            return {
                "state": "WORKER_ALREADY_PRESENT",
                "worker_repair_attempted": False,
                "carrier_pid": carrier_pid,
                "worker_pid": existing_worker_pid,
                "worker_tick_evidence": tick,
                "present_worker_runtime_observed": presence.get("resident", {}).get("present_worker_runtime_observed") is True,
                "presence_receipt_ref": str(PRESENCE_RECEIPT),
                "master_records_intake_state": intake.get("state"),
                "master_records_intake_receipt_ref": str(PRESENCE_MR_INTAKE_RECEIPT),
                "heartbeat_grants_execution_authority": False,
                "worker_coordinator_retains_admission_authority": True,
                "authority_effect": "NONE_SUPERVISION_ONLY",
            }
        stop = _stop_stale_worker(existing_worker_pid, timeout=min(timeout, 1.0))
        stale_worker_evidence = {"worker_pid": existing_worker_pid, "tick_evidence": tick, "stop_evidence": stop}
        if not stop.get("stopped"):
            return {
                "state": "STALE_WORKER_REPAIR_BLOCKED",
                "worker_repair_attempted": True,
                "carrier_pid": carrier_pid,
                "worker_pid": existing_worker_pid,
                "stale_worker_evidence": stale_worker_evidence,
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
            "stale_worker_evidence": stale_worker_evidence,
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
    if stale_worker_evidence is not None:
        receipt["stale_worker_replaced"] = stale_worker_evidence
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    presence = _persist_presence_projection(runtime_root)
    intake = _persist_presence_master_records_intake(runtime_root)
    return {
        "state": "WORKER_REPAIRED_STALE_PROCESS" if stale_worker_evidence is not None else "WORKER_REPAIRED",
        "worker_repair_attempted": True,
        "carrier_pid": carrier_pid,
        "worker_pid": worker.pid,
        "worker_tick_evidence": tick,
        "stale_worker_evidence": stale_worker_evidence,
        "present_worker_runtime_observed": presence.get("resident", {}).get("present_worker_runtime_observed") is True,
        "presence_receipt_ref": str(PRESENCE_RECEIPT),
        "master_records_intake_state": intake.get("state"),
        "master_records_intake_receipt_ref": str(PRESENCE_MR_INTAKE_RECEIPT),
        "request_drain_expected_on_worker_start": True,
        "heartbeat_grants_execution_authority": False,
        "worker_coordinator_retains_admission_authority": True,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_effect": "NONE_SUPERVISION_ONLY",
    }


if __name__ == "__main__":
    raise SystemExit("import ensure_worker_presence from the canonical carrier runtime")