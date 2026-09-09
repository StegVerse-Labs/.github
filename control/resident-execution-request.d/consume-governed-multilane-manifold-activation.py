#!/usr/bin/env python3
"""Resident consumer for the complete governed multi-lane manifold lineage.

This control-directory copy is the runtime-dispatched compatibility surface. It
must preserve the same fail-closed prerequisite gating as the canonical scripts
consumer while remaining source-refresh compatible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
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


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize_static(source: Path, runtime: Path, rel: Path) -> dict[str, Any]:
    src = source / rel
    dst = runtime / rel
    require(src.is_file(), f"canonical static source missing:{rel}")
    src_hash = sha256(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.is_file() or sha256(dst) != src_hash:
        shutil.copy2(src, dst)
    require(dst.is_file() and sha256(dst) == src_hash, f"static materialization mismatch:{rel}")
    return {"ref": rel.as_posix(), "sha256": src_hash, "exact_copy": True}


def materialize_request_if_missing(source: Path, runtime: Path) -> dict[str, Any]:
    src = source / REQUEST_REL
    dst = runtime / REQUEST_REL
    if dst.is_file():
        return {
            "ref": REQUEST_REL.as_posix(),
            "materialized": False,
            "reason": "RUNTIME_REQUEST_ALREADY_PRESENT",
            "sha256": sha256(dst),
        }
    require(src.is_file(), f"canonical resident request missing:{REQUEST_REL}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    require(dst.is_file() and sha256(dst) == sha256(src), "resident request materialization mismatch")
    return {
        "ref": REQUEST_REL.as_posix(),
        "materialized": True,
        "reason": "MISSING_RUNTIME_REQUEST_RECOVERED_FROM_ALREADY_LOCAL_CANONICAL_SOURCE",
        "sha256": sha256(src),
    }


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


def normalized_state(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return value.strip().upper().replace("-", "_").replace(" ", "_")


def result_has_qualifying_evidence(result: dict[str, Any] | None) -> bool:
    if not isinstance(result, dict):
        return False
    for key in ("qualified", "qualifying", "receipt_observed", "activation_proven", "ready"):
        if result.get(key) is True:
            return True
    for key in ("state", "status", "completion_state", "validation_state", "integration_state"):
        state = normalized_state(result.get(key))
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
    return normalized_state(node.get("state")) in {
        "COMPLETE",
        "COMPLETE_RELEASED",
        "INITIAL_IMPLEMENTATION_COMPLETE",
    }


def consume(source_root: Path, runtime_root: Path, *, runner=subprocess.run) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    runtime = runtime_root.expanduser().resolve()

    request_transport = materialize_request_if_missing(source, runtime)
    materialized = [
        materialize_static(source, runtime, LINEAGE_REL),
        materialize_static(source, runtime, TASK_RECORD_REL),
    ]

    request = load_json(runtime / REQUEST_REL)
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
    require(record.get("task_id") == TASK_ID and record.get("cosv_task_vector") == COSV, "task record identity mismatch")

    nodes = lineage.get("nodes")
    declared = request.get("subordinate_task_ids")
    require(isinstance(nodes, list) and nodes, "lineage nodes missing")
    require(isinstance(declared, list) and declared, "request subordinate ids missing")
    node_ids = [row.get("task_id") for row in nodes if isinstance(row, dict)]
    require(set(node_ids) == set(declared), "request/lineage subordinate set mismatch")
    dependencies = dependency_map(lineage)

    entrypoint = runtime / RUNTIME_ENTRYPOINT_REL
    require(entrypoint.is_file(), "WorkerCoordinator runtime entrypoint missing")
    outcomes: list[dict[str, Any]] = []
    outcome_by_task: dict[str, dict[str, Any]] = {}
    external_pending = False
    execution_failures = False
    prerequisite_blocks = False

    for node in nodes:
        require(isinstance(node, dict), "invalid lineage node")
        child_id = node.get("task_id")
        disposition = node.get("disposition")
        require(isinstance(child_id, str) and child_id, "lineage child id missing")
        require(isinstance(disposition, str) and disposition, f"lineage disposition missing:{child_id}")

        if disposition in REUSE_DISPOSITIONS:
            outcome = {
                "task_id": child_id,
                "disposition": disposition,
                "state": "AGGREGATE_OR_COMPLETED_NODE_REUSED_CHILDREN_REMAIN_SEPARATE"
                if disposition == "EXECUTE_INCOMPLETE_CANONICAL_CHILDREN_THROUGH_EXISTING_OWNERS"
                else "REUSED_NO_EXECUTION",
                "execution_attempted": False,
                "children_must_execute_separately": disposition
                in {"REUSE_IMPLEMENTATION_EXECUTE_CHILDREN", "EXECUTE_INCOMPLETE_CANONICAL_CHILDREN_THROUGH_EXISTING_OWNERS"},
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

        require(disposition in EXECUTE_DISPOSITIONS, f"unsupported disposition:{child_id}:{disposition}")
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
            "state": "WORKERCOORDINATOR_VISIT_COMPLETE"
            if completed.returncode == 0
            else "WORKERCOORDINATOR_VISIT_FAILED_CLOSED",
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
        "request_transport": request_transport,
        "static_source_materialization": materialized,
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
        "network_source_fetch_performed": False,
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
