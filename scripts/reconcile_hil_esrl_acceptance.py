#!/usr/bin/env python3
"""Build the canonical HIL state transition implied by an ACCEPTED ESRL intake receipt.

This module is intentionally non-mutating. It validates exact parent/task/COSV state and
returns the only lawful post-ESRL task-vector/blocker transition. Repository mutation is
a separate reviewed step after authentic physical evidence exists.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

TASK_ID = "SHWP-HIL-SOVEREIGN-RECEIVER-001"
CURRENT_VECTOR = "50000000103000"
NEXT_VECTOR = "50000000102000"
ESRL_BLOCKER = "AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED"
REMAINING_BLOCKERS = [
    "POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED",
    "TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN",
]
INTAKE_SCHEMA = "stegverse.hil-browser-esrl-evidence-intake/v1"
PROPOSAL_SCHEMA = "stegverse.hil-esrl-acceptance-reconciliation-proposal/v1"

class ReconciliationError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ReconciliationError(reason)


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"json_object_required:{path}")
    return value


def build_proposal(*, intake: Mapping[str, Any], task_vector: Mapping[str, Any], worker_registry: Mapping[str, Any]) -> dict[str, Any]:
    require(intake.get("schema") == INTAKE_SCHEMA, "intake_schema_invalid")
    require(intake.get("state") == "ACCEPTED", "intake_not_accepted")
    require(intake.get("task_id") == TASK_ID, "intake_task_mismatch")
    require(intake.get("esrl_lease_open_observed") is True, "lease_open_not_observed")
    require(intake.get("lease_state") == "LEASE_OPEN", "lease_state_invalid")
    require(intake.get("post_restart_exact_byte_proof_observed") is False, "unexpected_post_restart_promotion")
    require(intake.get("tvc_lifecycle_receipt_observed") is False, "unexpected_tvc_lifecycle_promotion")
    require(intake.get("broader_hil_lifecycle_complete") is False, "unexpected_broader_lifecycle_promotion")

    require(task_vector.get("identity") == f"StegVerse-Labs/.github:task:{TASK_ID}", "task_vector_identity_invalid")
    require(task_vector.get("profile") == "task.v1", "task_vector_profile_invalid")
    require(task_vector.get("vector") == CURRENT_VECTOR, "task_vector_not_expected_pre_esrl_state")
    metrics = task_vector.get("exact_metrics")
    require(isinstance(metrics, Mapping), "task_vector_metrics_required")
    require(metrics.get("blocker_count") == 3, "task_vector_blocker_count_not_three")
    require(metrics.get("evidence_complete") is False and metrics.get("activated") is False and metrics.get("propagated") is False, "task_vector_terminal_state_unexpected")

    tasks = worker_registry.get("tasks")
    require(isinstance(tasks, list) and len(tasks) == 1 and isinstance(tasks[0], Mapping), "worker_registry_task_shape_invalid")
    task = tasks[0]
    require(task.get("task_id") == TASK_ID, "worker_registry_task_mismatch")
    require(task.get("state") == "HANDOFF_READY", "worker_registry_state_invalid")
    require(task.get("archive_eligible") is False, "worker_registry_archive_state_invalid")
    blockers = task.get("archive_reason_codes")
    require(isinstance(blockers, list), "worker_registry_blockers_required")
    require(blockers == [ESRL_BLOCKER, *REMAINING_BLOCKERS], "worker_registry_blocker_set_invalid")

    return {
        "schema": PROPOSAL_SCHEMA,
        "state": "READY_FOR_CANONICAL_RECONCILIATION",
        "task_id": TASK_ID,
        "source_intake_schema": INTAKE_SCHEMA,
        "source_lease_id": intake.get("lease_id"),
        "source_artifact_sha256": intake.get("source_artifact_sha256"),
        "previous_vector": CURRENT_VECTOR,
        "proposed_vector": NEXT_VECTOR,
        "removed_blocker": ESRL_BLOCKER,
        "remaining_blockers": list(REMAINING_BLOCKERS),
        "proposed_blocker_count": 2,
        "proposed_worker_state": "HANDOFF_READY",
        "proposed_archive_eligible": False,
        "next_runtime_stage": "HIL_RECEIVER_READY_AND_CUSTODY",
        "post_restart_exact_byte_proof_observed": False,
        "tvc_lifecycle_receipt_observed": False,
        "broader_hil_lifecycle_complete": False,
        "activated": False,
        "propagated": False,
        "mutation_performed": False,
        "authority_effect": "NONE_PROPOSAL_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake", type=Path, required=True)
    parser.add_argument("--task-vector", type=Path, required=True)
    parser.add_argument("--worker-registry", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build_proposal(
            intake=load_object(args.intake),
            task_vector=load_object(args.task_vector),
            worker_registry=load_object(args.worker_registry),
        )
    except Exception as exc:
        print(json.dumps({"schema": PROPOSAL_SCHEMA, "state": "FAIL_CLOSED", "reason": f"{type(exc).__name__}:{exc}", "mutation_performed": False, "authority_effect": "NONE"}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
