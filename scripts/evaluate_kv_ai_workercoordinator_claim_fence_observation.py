#!/usr/bin/env python3
"""Evaluate the first same-execution KV AI WorkerCoordinator claim/fence predicate.

This observer is deliberately non-authorizing. It does not mint a claim, fence,
lease, assignment timer, InTr receipt, ProviderRequest receipt, KV writeback, or
Master Records reconstruction. It only accepts already-observed owner-custodied
resident runtime evidence when the same execution binds:

- the exact SV-KV-AI-PERSISTENCE-001 task id;
- the exact 20111110110000 COSV task.v1 pointer;
- the targeted independent WorkerCoordinator cycle receipt;
- a WorkerCoordinator assignment event carrying claim_id + fencing_token;
- resident registry state carrying the matching worker_instance_id and timer;
- a Master Records worker-assignment record carrying the same claim/fence tuple.

Hosted CI can validate this evaluator's logic, but a passing source test is not
runtime evidence for SV-KV-AI-PERSISTENCE-001.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_TASK_ID = "SV-KV-AI-PERSISTENCE-001"
DEFAULT_COSV_VECTOR = "20111110110000"
DEFAULT_WORKER_ID = "kv-ai-memory-resident-worker"
DEFAULT_RECEIPT_REL = Path("receipts/sovereign-host/resident-targeted-execution.latest.json")
REGISTRY_REL = Path("control/worker-registry.json")
ASSIGNMENT_RECORD_REL = Path("events/master-records-worker-assignment.jsonl")
OBSERVATION_REL = Path("data/runtime-observations/SV-KV-AI-PERSISTENCE-001-workercoordinator-claim-fence-observation.latest.json")


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _find_task(registry: dict[str, Any] | None, task_id: str) -> dict[str, Any] | None:
    tasks = registry.get("tasks") if isinstance(registry, dict) else None
    if not isinstance(tasks, list):
        return None
    matches = [row for row in tasks if isinstance(row, dict) and row.get("task_id") == task_id]
    return matches[0] if len(matches) == 1 else None


def _event_tuple(receipt: dict[str, Any] | None, task_id: str) -> dict[str, Any] | None:
    result = receipt.get("execution_result") if isinstance(receipt, dict) else None
    events = result.get("events") if isinstance(result, dict) else None
    if not isinstance(events, list):
        return None
    matches = [
        event for event in events
        if isinstance(event, dict)
        and event.get("event_type") == "worker_assignment_bound_from_independent_task_control"
        and event.get("task_id") == task_id
    ]
    return matches[0] if len(matches) == 1 else None


def _assignment_record(records: list[dict[str, Any]], *, task_id: str, claim_id: str, fencing_token: int) -> dict[str, Any] | None:
    matches = [
        row for row in records
        if row.get("task_id") == task_id
        and row.get("claim_id") == claim_id
        and row.get("fencing_token") == fencing_token
    ]
    return matches[0] if len(matches) == 1 else None


def evaluate(runtime_root: Path, *, task_id: str = DEFAULT_TASK_ID, cosv_task_vector: str = DEFAULT_COSV_VECTOR) -> dict[str, Any]:
    root = runtime_root.expanduser().resolve()
    receipt_path = root / DEFAULT_RECEIPT_REL
    registry_path = root / REGISTRY_REL
    assignments_path = root / ASSIGNMENT_RECORD_REL

    receipt = _load_json(receipt_path)
    registry = _load_json(registry_path)
    task = _find_task(registry, task_id)
    event = _event_tuple(receipt, task_id)
    assignments = _load_jsonl(assignments_path)

    missing: list[str] = []
    if receipt is None:
        missing.append("resident_targeted_execution_receipt")
    if registry is None:
        missing.append("worker_registry")
    if task is None:
        missing.append("registry_task")
    if event is None:
        missing.append("same_execution_assignment_event")

    pointer = receipt.get("cosv_task_pointer") if isinstance(receipt, dict) else None
    if not isinstance(pointer, dict) or pointer.get("task_id") != task_id or pointer.get("vector") != cosv_task_vector or pointer.get("binding_verified") is not True:
        missing.append("exact_cosv_task_pointer_binding")

    if isinstance(receipt, dict) and receipt.get("task_id") != task_id:
        missing.append("receipt_task_id")
    if isinstance(receipt, dict) and receipt.get("mode") != "TARGETED_INDEPENDENT_TASK_CONTROL":
        missing.append("targeted_independent_task_control_mode")
    if isinstance(receipt, dict) and receipt.get("runtime_execution_attempted") is not True:
        missing.append("runtime_execution_attempted")

    claim_id = event.get("claim_id") if isinstance(event, dict) else None
    worker_id = event.get("worker_id") if isinstance(event, dict) else None
    fencing_token = event.get("fencing_token") if isinstance(event, dict) else None
    master_ref = event.get("master_records_binding_ref") if isinstance(event, dict) else None

    if not isinstance(claim_id, str) or not claim_id:
        missing.append("event_claim_id")
    if worker_id != DEFAULT_WORKER_ID:
        missing.append("event_worker_id")
    if not isinstance(fencing_token, int):
        missing.append("event_fencing_token")
    if not isinstance(master_ref, str) or not master_ref:
        missing.append("event_master_records_binding_ref")

    registry_tuple: dict[str, Any] | None = None
    if isinstance(task, dict) and isinstance(claim_id, str) and isinstance(fencing_token, int):
        timer = task.get("assignment_timer") if isinstance(task.get("assignment_timer"), dict) else {}
        registry_tuple = {
            "state": task.get("state"),
            "claim_id": task.get("claim_id"),
            "worker_id": task.get("worker_id"),
            "worker_instance_id": task.get("worker_instance_id"),
            "timer_claim_id": timer.get("claim_id"),
            "timer_fencing_token": timer.get("fencing_token"),
            "timer_worker_instance_id": timer.get("worker_instance_id"),
        }
        if task.get("state") != "ACTIVE":
            missing.append("registry_active_state")
        if task.get("claim_id") != claim_id:
            missing.append("registry_claim_id_match")
        if task.get("worker_id") != DEFAULT_WORKER_ID:
            missing.append("registry_worker_id_match")
        if not isinstance(task.get("worker_instance_id"), str) or not task.get("worker_instance_id"):
            missing.append("registry_worker_instance_id")
        if timer.get("claim_id") != claim_id:
            missing.append("assignment_timer_claim_id_match")
        if timer.get("fencing_token") != fencing_token:
            missing.append("assignment_timer_fencing_token_match")
        if timer.get("worker_instance_id") != task.get("worker_instance_id"):
            missing.append("assignment_timer_worker_instance_id_match")
    elif isinstance(task, dict):
        missing.append("registry_claim_fence_tuple_uncheckable")

    assignment_record = None
    if isinstance(claim_id, str) and isinstance(fencing_token, int):
        assignment_record = _assignment_record(assignments, task_id=task_id, claim_id=claim_id, fencing_token=fencing_token)
        if assignment_record is None:
            missing.append("master_records_worker_assignment_record")
        elif isinstance(task, dict) and assignment_record.get("worker_instance_id") != task.get("worker_instance_id"):
            missing.append("assignment_record_worker_instance_id_match")

    observed = not missing
    return {
        "schema": "stegverse.kv-ai-workercoordinator-claim-fence-observation/v1",
        "task_id": task_id,
        "cosv_task_vector": cosv_task_vector,
        "runtime_root": str(root),
        "receipt_ref": str(DEFAULT_RECEIPT_REL),
        "registry_ref": str(REGISTRY_REL),
        "assignment_record_ref": str(ASSIGNMENT_RECORD_REL),
        "observed": observed,
        "status": "AUTHENTIC_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED" if observed else "AUTHENTIC_WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED",
        "missing_predicates": sorted(set(missing)),
        "claim_id": claim_id if observed else None,
        "worker_id": worker_id if observed else None,
        "worker_instance_id": task.get("worker_instance_id") if observed and isinstance(task, dict) else None,
        "fencing_token": fencing_token if observed else None,
        "same_execution_event": event if observed else None,
        "registry_tuple": registry_tuple,
        "assignment_record": assignment_record if observed else None,
        "nonclaims": [
            "OBSERVER_DOES_NOT_MINT_CLAIM_OR_FENCE",
            "OBSERVER_DOES_NOT_PROVE_PERSONAL_KV_INPUTS",
            "OBSERVER_DOES_NOT_PROVE_INTR_ADMISSION",
            "OBSERVER_DOES_NOT_PROVE_PROVIDER_EXECUTION",
            "OBSERVER_DOES_NOT_PROVE_KV_WRITEBACK_READBACK",
            "OBSERVER_DOES_NOT_COMPLETE_SV_KV_AI_PERSISTENCE_001"
        ],
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--cosv-task-vector", default=DEFAULT_COSV_VECTOR)
    parser.add_argument("--write-observation", action="store_true")
    args = parser.parse_args()
    result = evaluate(args.runtime_root, task_id=args.task_id, cosv_task_vector=args.cosv_task_vector)
    if args.write_observation:
        path = args.runtime_root / OBSERVATION_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["observed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
