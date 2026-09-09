#!/usr/bin/env python3
"""Consume the governed multi-lane manifold activation request.

This consumer grants no authority. It traverses the canonical manifold lineage,
reuses completed predecessor or aggregate nodes, delegates machine-owned
subordinate execution to the existing WorkerCoordinator targeted task path, and
records external TV/TVC-owned prerequisites without competing for their claims.

Conditional lineage nodes fail closed: they are not delegated until every
DEPENDS_ON predecessor has explicit qualifying evidence from the current visit.
A successful WorkerCoordinator process return code alone is not qualifying
activation evidence.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUEST_REL = Path("control/resident-execution-request.d/governed-multilane-manifold-activation-001.json")
LINEAGE_REL = Path("control/manifold-lineage.d/governed-multilane-manifold-activation-001.json")
TASK_RECORD_REL = Path("data/canonical-task-records/GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001.json")
RUNTIME_ENTRYPOINT_REL = Path("scripts/run_worker_runtime.py")
RECEIPT_REL = Path("receipts/sovereign-host/governed-multilane-manifold-activation-request-consumption.latest.json")
TASK_ID = "GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001"
COSV = "10100000100000"

EXECUTE_DISPOSITIONS = {
    "EXECUTE_IF_NOT_ALREADY_QUALIFYING",
    "EXECUTE_AFTER_PREREQUISITES_QUALIFY",
    "EXECUTE_WHEN_TVC_RUNTIME_PREREQUISITE_QUALIFIES",
}
CONDITIONAL_EXECUTE_DISPOSITIONS = {
    "EXECUTE_AFTER_PREREQUISITES_QUALIFY",
    "EXECUTE_WHEN_TVC_RUNTIME_PREREQUISITE_QUALIFIES",
}
REUSE_DISPOSITIONS = {
    "REUSE_IMPLEMENTATION_EXECUTE_CHILDREN",
    "REUSE_COMPLETE_DO_NOT_REEXECUTE",
    "EXECUTE_INCOMPLETE_CANONICAL_CHILDREN_THROUGH_EXISTING_OWNERS",
}
EXTERNAL_DISPOSITIONS = {"OBSERVE_EXISTING_OWNER_NO_COMPETE"}
QUALIFYING_STATES = {
    "ACTIVATED",
    "COMPLETE",
    "COMPLETE_RELEASED",
    "EXECUTED",
    "QUALIFIED",
    "QUALIFYING",
    "READY",
    "READY_PRIMARY_RUNTIME_PROVIDER_OPERATION_BOUND",
    "RECONCILED",
    "SUCCESS",
    "SUCCEEDED",
    "WALLET_HANDOFF_READY",
}
NONQUALIFYING_STATES = {
    "BLOCKED",
    "FAILED",
    "FAIL_CLOSED",
    "HANDOFF_READY",
    "PENDING",
    "PRIMARY_RUNTIME_NOT_YET_PROVEN",
    "REQUESTED",
    "UNCLAIMED",
    "WAITING",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def write_receipt(runtime: Path, receipt: dict[str, Any]) -> None:
    path = runtime / RECEIPT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def dependency_map(lineage: dict[str, Any]) -> dict[str, list[str]]:
    deps: dict[str, list[str]] = {}
    edges = lineage.get("edges")
    require(isinstance(edges, list), "manifold lineage edges missing")
    for edge in edges:
        require(isinstance(edge, dict), "invalid lineage edge")
        if edge.get("kind") != "DEPENDS_ON":
            continue
        child = edge.get("from")
        prerequisite = edge.get("to")
        require(isinstance(child, str) and child, "dependency edge child missing")
        require(isinstance(prerequisite, str) and prerequisite, "dependency edge prerequisite missing")
        deps.setdefault(child, []).append(prerequisite)
    return deps


def _normalized_state(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return value.strip().upper().replace("-", "_").replace(" ", "_")


def result_has_qualifying_evidence(result: dict[str, Any] | None) -> bool:
    """Require explicit positive evidence; return-code success is not enough."""
    if not isinstance(result, dict):
        return False

    for key in ("qualified", "qualifying", "receipt_observed", "activation_proven", "ready"):
        if result.get(key) is True:
            return True

    for key in ("state", "status", "completion_state", "validation_state", "integration_state"):
        state = _normalized_state(result.get(key))
        if state in NONQUALIFYING_STATES:
            return False
        if state in QUALIFYING_STATES:
            return True

    for key in ("result", "worker_result", "receipt", "evidence"):
        nested = result.get(key)
        if isinstance(nested, dict) and result_has_qualifying_evidence(nested):
            return True
    return False


def reuse_is_qualifying(node: dict[str, Any], disposition: str) -> bool:
    if disposition == "EXECUTE_INCOMPLETE_CANONICAL_CHILDREN_THROUGH_EXISTING_OWNERS":
        return False
    return _normalized_state(node.get("state")) in {
        "COMPLETE",
        "COMPLETE_RELEASED",
        "INITIAL_IMPLEMENTATION_COMPLETE",
    }


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run) -> dict[str, Any]:
    source_root.expanduser().resolve()  # retained for CLI/source-root compatibility
    runtime = runtime_root.expanduser().resolve()
    request_path = runtime / REQUEST_REL
    if not request_path.is_file():
        return {
            "schema": "stegverse.governed-manifold-request-consumption/v1",
            "state": "NO_REQUEST",
            "task_id": TASK_ID,
            "authority_effect": "NONE",
        }

    request = load_json(request_path)
    require(request.get("schema") == "stegverse.resident-execution-request/v1", "request schema mismatch")
    require(request.get("state") == "REQUESTED", "request state mismatch")
    require(request.get("task_id") == TASK_ID, "request task mismatch")
    require(request.get("cosv_task_vector") == COSV, "request COSV mismatch")
    require(request.get("mode") == "GOVERNED_MULTILANE_MANIFOLD_ACTIVATION", "request mode mismatch")
    require(request.get("execution_owner") == "CANONICAL_WORKERCOORDINATOR", "execution owner mismatch")
    require(request.get("credential_authority") == "TV/TVC", "credential authority mismatch")
    require(request.get("github_token_runtime_authority") == "NONE", "GitHub runtime authority mismatch")
    require(request.get("heartbeat_grants_execution_authority") is False, "heartbeat authority mismatch")
    require(request.get("request_granted_authority") is False, "request authority mismatch")
    require(request.get("manifold_lineage_ref") == str(LINEAGE_REL), "lineage ref mismatch")

    lineage = load_json(runtime / LINEAGE_REL)
    record = load_json(runtime / TASK_RECORD_REL)
    require(lineage.get("schema") == "stegverse.manifold-lineage/v1", "lineage schema mismatch")
    require(lineage.get("task_id") == TASK_ID and lineage.get("cosv_task_vector") == COSV, "lineage identity mismatch")
    require(record.get("task_id") == TASK_ID and record.get("cosv_task_vector") == COSV, "canonical task record identity mismatch")

    nodes = lineage.get("nodes")
    require(isinstance(nodes, list) and nodes, "manifold lineage nodes missing")
    declared = request.get("subordinate_task_ids")
    require(isinstance(declared, list) and declared, "request subordinate task ids missing")
    node_ids = [row.get("task_id") for row in nodes if isinstance(row, dict)]
    require(set(node_ids) == set(declared), "request/lineage subordinate set mismatch")
    dependencies = dependency_map(lineage)

    entrypoint = runtime / RUNTIME_ENTRYPOINT_REL
    require(entrypoint.is_file(), "canonical WorkerCoordinator runtime entrypoint missing")

    outcomes: list[dict[str, Any]] = []
    outcome_by_task: dict[str, dict[str, Any]] = {}
    external_pending = False
    execution_failures = False
    prerequisite_blocks = False

    for node in nodes:
        require(isinstance(node, dict), "invalid lineage node")
        child_id = node.get("task_id")
        disposition = node.get("disposition")
        require(isinstance(child_id, str) and child_id, "lineage node task id missing")
        require(isinstance(disposition, str) and disposition, f"lineage disposition missing:{child_id}")

        if disposition in REUSE_DISPOSITIONS:
            outcome = {
                "task_id": child_id,
                "disposition": disposition,
                "state": "AGGREGATE_OR_COMPLETED_NODE_REUSED_CHILDREN_REMAIN_SEPARATE" if disposition == "EXECUTE_INCOMPLETE_CANONICAL_CHILDREN_THROUGH_EXISTING_OWNERS" else "REUSED_NO_EXECUTION",
                "execution_attempted": False,
                "children_must_execute_separately": disposition in {"REUSE_IMPLEMENTATION_EXECUTE_CHILDREN", "EXECUTE_INCOMPLETE_CANONICAL_CHILDREN_THROUGH_EXISTING_OWNERS"},
                "qualifying_for_dependents": reuse_is_qualifying(node, disposition),
                "authority_effect": "NONE",
            }
            outcomes.append(outcome)
            outcome_by_task[child_id] = outcome
            continue

        if disposition in EXTERNAL_DISPOSITIONS:
            external_pending = True
            outcome = {
                "task_id": child_id,
                "disposition": disposition,
                "state": "EXTERNAL_OWNER_OBSERVATION_REQUIRED",
                "execution_attempted": False,
                "qualifying_for_dependents": False,
                "competing_claim_created": False,
                "authority_effect": "NONE_EXTERNAL_OWNER_RETAINED",
            }
            outcomes.append(outcome)
            outcome_by_task[child_id] = outcome
            continue

        require(disposition in EXECUTE_DISPOSITIONS, f"unsupported lineage disposition:{child_id}:{disposition}")
        required = dependencies.get(child_id, [])
        if disposition in CONDITIONAL_EXECUTE_DISPOSITIONS:
            unqualified = [
                prerequisite
                for prerequisite in required
                if not outcome_by_task.get(prerequisite, {}).get("qualifying_for_dependents")
            ]
            if unqualified:
                prerequisite_blocks = True
                outcome = {
                    "task_id": child_id,
                    "disposition": disposition,
                    "state": "PREREQUISITES_NOT_QUALIFIED_FAIL_CLOSED",
                    "execution_attempted": False,
                    "required_prerequisites": required,
                    "unqualified_prerequisites": unqualified,
                    "qualifying_for_dependents": False,
                    "authority_effect": "NONE_FAIL_CLOSED",
                }
                outcomes.append(outcome)
                outcome_by_task[child_id] = outcome
                continue

        command = [sys.executable, str(entrypoint), "--root", str(runtime), "--task-id", child_id]
        completed = runner(command, cwd=runtime, capture_output=True, text=True, check=False, timeout=1200)
        result = parse_last_json(completed.stdout)
        qualifying = completed.returncode == 0 and result_has_qualifying_evidence(result)
        if completed.returncode != 0:
            execution_failures = True
        outcome = {
            "task_id": child_id,
            "disposition": disposition,
            "state": "WORKERCOORDINATOR_VISIT_COMPLETE" if completed.returncode == 0 else "WORKERCOORDINATOR_VISIT_FAILED_CLOSED",
            "execution_attempted": True,
            "returncode": completed.returncode,
            "result": result,
            "qualifying_for_dependents": qualifying,
            "claim_and_fence_authority": "CANONICAL_WORKERCOORDINATOR",
            "authority_effect": "NONE_DELEGATED_TO_EXISTING_AUTHORITY",
        }
        outcomes.append(outcome)
        outcome_by_task[child_id] = outcome

    receipt = {
        "schema": "stegverse.governed-manifold-request-consumption/v1",
        "state": "MANIFOLD_VISIT_RECORDED",
        "task_id": TASK_ID,
        "cosv_task_vector": COSV,
        "manifold_lineage_ref": str(LINEAGE_REL),
        "declared_subordinate_count": len(declared),
        "visited_subordinate_count": len(outcomes),
        "full_declared_set_visited": len(outcomes) == len(declared),
        "external_authority_evidence_pending": external_pending,
        "workercoordinator_visit_failures_observed": execution_failures,
        "conditional_prerequisite_blocks_observed": prerequisite_blocks,
        "outcomes": outcomes,
        "activation_declared": False,
        "activation_requires_separate_qualifying_machine_evidence": True,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "request_grants_execution_authority": False,
        "wallet_signing_broadcast": "USER_ONLY",
        "authority_effect": "NONE_CONSUMPTION_AND_DELEGATION_ONLY",
    }
    write_receipt(runtime, receipt)
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
            "schema": "stegverse.governed-manifold-request-consumption/v1",
            "state": "MANIFOLD_REQUEST_REJECTED_FAIL_CLOSED",
            "task_id": TASK_ID,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "activation_declared": False,
            "authority_effect": "NONE_FAIL_CLOSED",
        }
        write_receipt(args.runtime_root.expanduser().resolve(), receipt)
        print(json.dumps(receipt, sort_keys=True))
        return 1
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
