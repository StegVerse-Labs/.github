#!/usr/bin/env python3
"""Consume the bounded pre-claim GADI runtime-observation request.

This consumer creates no claim, fence, admission, credential, runtime, listener, or
execution authority. It validates one static observation request and invokes the
already-merged claimless GADI dispatcher entry point. That dispatcher may visit the
existing WorkerCoordinator only after current retained discovery, current-iPhone
receipt readback, runtime binding, and all remaining non-claim evidence are coherent.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/gadi-runtime-observation-001.json")
DISPATCHER_REL = Path("scripts/dispatch_gadi_resident_execution.py")
RECEIPT_REL = Path("receipts/sovereign-host/gadi-runtime-observation-request-consumption.latest.json")
TASK_ID = "GADI-RESIDENT-EXECUTION-001"
PARENT_TASK_ID = "GADI-001"
REQUEST_ID = "RESIDENT-OBSERVE-GADI-RUNTIME-001"
EXPECTED_STEPS = [
    "CURRENT_RETAINED_STEGBROWSER_STEGOS_NODE_DISCOVERY",
    "CURRENT_RETAINED_STEGBROWSER_STEGOS_CURRENT_IPHONE_RECEIPT_READBACK",
    "CURRENT_GADI_RUNTIME_BINDING",
]


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def validate_request(value: dict[str, Any]) -> None:
    expected = {
        "schema": "stegverse.resident-execution-request/v1",
        "request_id": REQUEST_ID,
        "state": "REQUESTED",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "mode": "GADI_RUNTIME_OBSERVATION",
        "entrypoint": "scripts/dispatch_gadi_resident_execution.py",
        "observation_steps": EXPECTED_STEPS,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_granted_authority": False,
        "network_source_fetch_allowed": False,
        "second_machine_required": False,
        "workercoordinator_may_be_visited_only_after_nonclaim_readiness": True,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    if value != expected:
        raise RuntimeError("GADI runtime-observation request contract mismatch")


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        request_path = source / REQUEST_REL
    if not request_path.is_file():
        raise RuntimeError("GADI runtime-observation request not materialized")
    request = load_json(request_path)
    validate_request(request)

    dispatcher = runtime / DISPATCHER_REL
    if not dispatcher.is_file():
        dispatcher = source / DISPATCHER_REL
    if not dispatcher.is_file():
        raise RuntimeError("claimless GADI dispatcher not materialized")

    completed = runner(
        [sys.executable, str(dispatcher), "--source-root", str(source), "--runtime-root", str(runtime)],
        cwd=runtime,
        capture_output=True,
        text=True,
        check=False,
        timeout=1800,
    )
    result = parse_last_json(completed.stdout)
    if not isinstance(result, dict):
        result = {"state": "NO_MACHINE_RESULT"}

    receipt = {
        "schema": "stegverse.gadi-runtime-observation-request-consumption/v1",
        "task_id": TASK_ID,
        "parent_task_id": PARENT_TASK_ID,
        "request_id": REQUEST_ID,
        "state": "OBSERVATION_ATTEMPT_RECORDED",
        "dispatcher_returncode": completed.returncode,
        "dispatcher_state": result.get("state"),
        "dispatcher_result": result,
        "workercoordinator_visit_permitted_only_after_nonclaim_readiness": True,
        "request_granted_authority": False,
        "claim_or_fence_created_by_consumer": False,
        "intr_admission_created_by_consumer": False,
        "credential_created_by_consumer": False,
        "runtime_created_by_consumer": False,
        "listener_created_by_consumer": False,
        "second_machine_required": False,
        "authority_effect": "NONE_OBSERVATION_REQUEST_ONLY",
    }
    write_json(runtime / RECEIPT_REL, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = consume(args.source_root, args.runtime_root)
    except Exception as exc:
        receipt = {
            "schema": "stegverse.gadi-runtime-observation-request-consumption/v1",
            "task_id": TASK_ID,
            "parent_task_id": PARENT_TASK_ID,
            "request_id": REQUEST_ID,
            "state": "OBSERVATION_REQUEST_BLOCKED_FAIL_CLOSED",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "request_granted_authority": False,
            "claim_or_fence_created_by_consumer": False,
            "authority_effect": "NONE_FAIL_CLOSED",
        }
        write_json(args.runtime_root.expanduser().resolve() / RECEIPT_REL, receipt)
        print(json.dumps(receipt, sort_keys=True))
        return 1
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
