#!/usr/bin/env python3
"""Consume the bounded HIL resident-session manifold request.

This composes existing resident-request consumers and existing WorkerCoordinator
registered-task execution. It grants no new authority and never merges child
claims, fences, predicates, or completion states.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REQUEST_REL = Path("control/resident-execution-request.d/hil-resident-session-manifold-activation-001.json")
LINEAGE_REL = Path("control/manifold-lineage.d/hil-resident-session-manifold-activation-001.json")
DISPATCHER_REL = Path("scripts/dispatch_resident_execution_requests.py")
WORKER_REL = Path("scripts/run_worker_runtime.py")
RECEIPT_REL = Path("receipts/sovereign-host/hil-resident-session-manifold-activation-request-consumption.latest.json")
TASK_ID = "HIL-RESIDENT-SESSION-MANIFOLD-ACTIVATION-001"
REQUEST_ID = "RESIDENT-EXEC-HIL-SESSION-MANIFOLD-001"


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


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def write_receipt(runtime: Path, receipt: dict[str, Any]) -> None:
    path = runtime / RECEIPT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {
            "schema": "stegverse.hil-resident-session-manifold-consumption/v1",
            "state": "NO_REQUEST",
            "task_id": TASK_ID,
            "authority_effect": "NONE",
        }

    request = load_json(request_path)
    lineage = load_json(runtime / LINEAGE_REL)
    require(request.get("schema") == "stegverse.resident-execution-request/v1", "request schema mismatch")
    require(request.get("request_id") == REQUEST_ID, "request id mismatch")
    require(request.get("state") == "REQUESTED", "request state mismatch")
    require(request.get("task_id") == TASK_ID, "request task mismatch")
    require(request.get("mode") == "GOVERNED_HIL_RESIDENT_SESSION_MANIFOLD", "request mode mismatch")
    require(request.get("credential_authority") == "TV/TVC", "credential authority mismatch")
    require(request.get("github_token_runtime_authority") == "NONE", "GitHub runtime authority mismatch")
    require(request.get("heartbeat_grants_execution_authority") is False, "heartbeat authority mismatch")
    require(request.get("request_granted_authority") is False, "request authority mismatch")
    require(request.get("second_machine_required") is False, "second-machine invariant mismatch")
    require(request.get("manifold_lineage_ref") == str(LINEAGE_REL), "lineage ref mismatch")

    require(lineage.get("schema") == "stegverse.manifold-lineage/v1", "lineage schema mismatch")
    require(lineage.get("task_id") == TASK_ID, "lineage task mismatch")
    nodes = lineage.get("nodes")
    declared = request.get("subordinate_task_ids")
    require(isinstance(nodes, list) and nodes, "lineage nodes missing")
    require(isinstance(declared, list) and declared, "declared child tasks missing")
    node_ids = [row.get("task_id") for row in nodes if isinstance(row, dict)]
    require(node_ids == declared, "lineage/request child ordering mismatch")

    dispatcher = runtime / DISPATCHER_REL
    worker = runtime / WORKER_REL
    require(dispatcher.is_file(), "resident dispatcher not materialized")
    require(worker.is_file(), "WorkerCoordinator runner not materialized")

    outcomes: list[dict[str, Any]] = []
    failures = False
    for node in nodes:
        require(isinstance(node, dict), "invalid lineage node")
        child_id = node.get("task_id")
        mode = node.get("execution_mode")
        require(isinstance(child_id, str) and child_id, "child task id missing")
        require(mode in {"RESIDENT_REQUEST_CONSUMER", "WORKERCOORDINATOR_TASK"}, f"unsupported execution mode:{child_id}")

        if mode == "RESIDENT_REQUEST_CONSUMER":
            selector = node.get("selector")
            require(isinstance(selector, str) and selector, f"selector missing:{child_id}")
            command = [
                sys.executable,
                str(dispatcher),
                "--source-root",
                str(source),
                "--runtime-root",
                str(runtime),
                "--only-consumer",
                selector,
            ]
        else:
            command = [
                sys.executable,
                str(worker),
                "--root",
                str(runtime),
                "--task-id",
                child_id,
            ]

        try:
            completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, timeout=1200)
            result = parse_last_json(completed.stdout)
            if completed.returncode != 0:
                failures = True
            outcomes.append({
                "task_id": child_id,
                "execution_mode": mode,
                "selector": node.get("selector"),
                "attempted": True,
                "returncode": completed.returncode,
                "result": result,
                "child_completion_inferred": False,
                "authority_effect": "NONE_EXISTING_CHILD_AUTHORITY_ONLY",
            })
        except Exception as exc:
            failures = True
            outcomes.append({
                "task_id": child_id,
                "execution_mode": mode,
                "selector": node.get("selector"),
                "attempted": True,
                "returncode": None,
                "error_type": type(exc).__name__,
                "child_completion_inferred": False,
                "authority_effect": "NONE_FAIL_CLOSED",
            })

    receipt = {
        "schema": "stegverse.hil-resident-session-manifold-consumption/v1",
        "state": "MANIFOLD_VISIT_RECORDED",
        "request_id": REQUEST_ID,
        "task_id": TASK_ID,
        "manifold_lineage_ref": str(LINEAGE_REL),
        "declared_child_count": len(declared),
        "visited_child_count": len(outcomes),
        "full_declared_set_visited": len(outcomes) == len(declared),
        "child_visit_failures_observed": failures,
        "outcomes": outcomes,
        "hil_subject_predicate": "PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002",
        "g18_completion_required_for_hil": False,
        "ecosystem_chat_completion_required_for_hil": False,
        "aggregate_visit_satisfies_child_completion": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_grants_execution_authority": False,
        "second_machine_required": False,
        "authority_effect": "NONE_COMPOSITION_ONLY",
    }
    write_receipt(runtime, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume HIL resident-session manifold request")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = consume(args.source_root, args.runtime_root)
    except Exception as exc:
        receipt = {
            "schema": "stegverse.hil-resident-session-manifold-consumption/v1",
            "state": "MANIFOLD_REQUEST_REJECTED_FAIL_CLOSED",
            "task_id": TASK_ID,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "authority_effect": "NONE_FAIL_CLOSED",
        }
        write_receipt(args.runtime_root.expanduser().resolve(), receipt)
        print(json.dumps(receipt, sort_keys=True))
        return 1
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
