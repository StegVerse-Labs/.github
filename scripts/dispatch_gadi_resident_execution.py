#!/usr/bin/env python3
"""Dispatch GADI-RESIDENT-EXECUTION-001 through local source resolution, materialization, and mandatory preflight gating.

The `dispatch()` function is the post-claim path used by the process-worker bridge. It
accepts the already-created current WorkerCoordinator task row, resolves only non-claim
sources first, then stages the exact live claim before materialization/preflight.

The claimless CLI is a resident/convergence entry surface. It may not bypass
WorkerCoordinator. Therefore `main()` delegates to the readiness-gated targeted runtime
wrapper, which verifies current non-claim evidence and invokes the canonical targeted
WorkerCoordinator only when those inputs and the separated carrier reference are ready.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "GADI-RESIDENT-EXECUTION-001"
RESOLVER = Path("scripts/resolve_gadi_resident_runtime_sources.py")
MATERIALIZER = Path("scripts/materialize_gadi_resident_runtime_bundle.py")
PREFLIGHT = Path("scripts/preflight_gadi_resident_execution.py")
CONSUMER = Path("control/resident-execution-request.d/consume-gadi-resident-execution.py")
CURRENT_CLAIM_REL = Path("state/gadi-resident-execution/source/worker-claim.json")
RECEIPT_REL = Path("receipts/sovereign-host/gadi-resident-dispatch.latest.json")


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_receipt(runtime: Path, payload: dict[str, Any]) -> None:
    write_json(runtime / RECEIPT_REL, payload)


def resolve(runtime: Path, source: Path, rel: Path) -> Path | None:
    local = runtime / rel
    if local.is_file():
        return local
    source_path = source / rel
    return source_path if source_path.is_file() else None


def validate_current_worker_claim(task: dict[str, Any]) -> None:
    if task.get("task_id") != TASK_ID:
        raise ValueError("current WorkerCoordinator task id mismatch")
    if task.get("state") != "ACTIVE":
        raise ValueError("current WorkerCoordinator task is not ACTIVE")
    claim_id = task.get("claim_id")
    worker_id = task.get("worker_id")
    worker_instance_id = task.get("worker_instance_id")
    timing = task.get("heartbeat_timing") if isinstance(task.get("heartbeat_timing"), dict) else {}
    fence = timing.get("fencing_token")
    if not isinstance(claim_id, str) or not claim_id:
        raise ValueError("current WorkerCoordinator claim id missing")
    if not isinstance(worker_id, str) or not worker_id:
        raise ValueError("current WorkerCoordinator worker id missing")
    if not isinstance(worker_instance_id, str) or not worker_instance_id:
        raise ValueError("current WorkerCoordinator worker instance id missing")
    if not isinstance(fence, int) or fence < 1:
        raise ValueError("current WorkerCoordinator fence missing")
    if not claim_id.endswith(f"-G{fence}"):
        raise ValueError("current WorkerCoordinator claim/fence mismatch")


def stage_current_worker_claim(runtime: Path, task: dict[str, Any]) -> None:
    validate_current_worker_claim(task)
    write_json(runtime / CURRENT_CLAIM_REL, task)


def dispatch(
    source_root: Path,
    runtime_root: Path,
    *,
    current_worker_claim: dict[str, Any] | None = None,
    runner=subprocess.run,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    resolver_path = resolve(runtime, source, RESOLVER)
    materializer_path = resolve(runtime, source, MATERIALIZER)
    preflight_path = resolve(runtime, source, PREFLIGHT)
    consumer_path = resolve(runtime, source, CONSUMER)

    for label, path in (("RESOLVER", resolver_path), ("MATERIALIZER", materializer_path), ("PREFLIGHT", preflight_path), ("CONSUMER", consumer_path)):
        if path is None:
            result = {"schema":"stegverse.gadi-resident-dispatch/v1","state":"BLOCKED_FAIL_CLOSED","blocker":f"{label}_NOT_MATERIALIZED","consumer_attempted":False,"execution_claimed":False,"activation_claimed":False}
            write_receipt(runtime, result)
            return result

    resolver_command = [sys.executable, str(resolver_path), "--runtime-root", str(runtime)]
    if current_worker_claim is not None:
        resolver_command.append("--defer-worker-claim")
    resolved = runner(resolver_command, cwd=runtime, capture_output=True, text=True, check=False, timeout=120)
    resolved_result = parse_last_json(resolved.stdout)
    if resolved.returncode != 0 or not isinstance(resolved_result, dict) or resolved_result.get("state") != "SOURCE_RESOLUTION_COMPLETE":
        result = {
            "schema":"stegverse.gadi-resident-dispatch/v1","state":"SOURCE_RESOLUTION_BLOCKED_FAIL_CLOSED",
            "source_resolution_returncode":resolved.returncode,"source_resolution":resolved_result,
            "materializer_attempted":False,"preflight_attempted":False,"consumer_attempted":False,
            "execution_claimed":False,"activation_claimed":False,
        }
        write_receipt(runtime, result)
        return result

    if current_worker_claim is not None:
        try:
            stage_current_worker_claim(runtime, current_worker_claim)
        except Exception as exc:
            result = {
                "schema":"stegverse.gadi-resident-dispatch/v1","state":"WORKER_CLAIM_PROJECTION_BLOCKED_FAIL_CLOSED",
                "error_type":type(exc).__name__,"error":str(exc),"source_resolution":resolved_result,
                "materializer_attempted":False,"preflight_attempted":False,"consumer_attempted":False,
                "execution_claimed":False,"activation_claimed":False,
            }
            write_receipt(runtime, result)
            return result

    materialized = runner([sys.executable, str(materializer_path), "--runtime-root", str(runtime)], cwd=runtime, capture_output=True, text=True, check=False, timeout=120)
    materialized_result = parse_last_json(materialized.stdout)
    if materialized.returncode != 0 or not isinstance(materialized_result, dict) or materialized_result.get("state") != "MATERIALIZED_READY_FOR_PREFLIGHT" or materialized_result.get("ready") is not True or materialized_result.get("blockers") not in ([], None):
        result = {
            "schema":"stegverse.gadi-resident-dispatch/v1","state":"MATERIALIZATION_BLOCKED_FAIL_CLOSED",
            "source_resolution":resolved_result,"materializer_returncode":materialized.returncode,"materialization":materialized_result,
            "preflight_attempted":False,"consumer_attempted":False,"execution_claimed":False,"activation_claimed":False,
        }
        write_receipt(runtime, result)
        return result

    pre = runner([sys.executable, str(preflight_path), "--source-root", str(source), "--runtime-root", str(runtime)], cwd=runtime, capture_output=True, text=True, check=False, timeout=120)
    pre_result = parse_last_json(pre.stdout)
    if pre.returncode != 0 or not isinstance(pre_result, dict) or pre_result.get("state") != "READY_FOR_RESIDENT_CONSUMPTION" or pre_result.get("ready") is not True or pre_result.get("blocker_count") != 0:
        result = {
            "schema":"stegverse.gadi-resident-dispatch/v1","state":"PREFLIGHT_BLOCKED_FAIL_CLOSED",
            "source_resolution":resolved_result,"materialization":materialized_result,"preflight_returncode":pre.returncode,"preflight":pre_result,
            "preflight_attempted":True,"consumer_attempted":False,"execution_claimed":False,"activation_claimed":False,
        }
        write_receipt(runtime, result)
        return result

    consumed = runner([sys.executable, str(consumer_path), "--source-root", str(source), "--runtime-root", str(runtime)], cwd=runtime, capture_output=True, text=True, check=False, timeout=1200)
    consume_result = parse_last_json(consumed.stdout)
    state = consume_result.get("state") if isinstance(consume_result, dict) else "NO_MACHINE_RESULT"
    result = {
        "schema":"stegverse.gadi-resident-dispatch/v1","state":state,"source_resolution":resolved_result,
        "materialization":materialized_result,"preflight":pre_result,"preflight_returncode":pre.returncode,
        "preflight_attempted":True,"consumer_attempted":True,"consumer_returncode":consumed.returncode,"consumer":consume_result,
        "execution_claimed":state == "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED","activation_claimed":False,
    }
    write_receipt(runtime, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    # The CLI is intentionally pre-claim. Global convergence and human/operator
    # visits may not call the post-claim dispatcher directly. The readiness wrapper
    # invokes the existing targeted WorkerCoordinator only when current non-claim
    # evidence is coherent; ProcessWorkerAdapter then calls dispatch() with the
    # authentic current task row.
    from run_gadi_targeted_runtime_if_ready import execute as execute_if_ready
    result = execute_if_ready(args.source_root, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
