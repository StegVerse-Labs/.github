#!/usr/bin/env python3
"""Evaluate the first unresolved HIL stage after browser ESRL intake.

This is a read-only readiness classifier. It never converts source, CI, merge, or
missing evidence into runtime success and does not mutate WorkerCoordinator,
receiver, custody, TVC, or COSV state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

TASK_ID = "SHWP-HIL-SOVEREIGN-RECEIVER-001"
ESRL_SCHEMA = "stegverse.hil-browser-esrl-evidence-intake/v1"
WORKER_SCHEMA = "stegverse.hil.sovereign-receiver-worker-receipt/v0.1"
RESTART_SCHEMA = "stegverse.hil.post-restart-reconstruction/v1"
TVC_SCHEMA = "stegverse.hil.tvc-lifecycle-outbox-consumption/v1"

WORKER_REL = Path("receipts/hil-sovereign-receiver/SHWP-HIL-SOVEREIGN-RECEIVER-001.json")
RESTART_REL = Path("receipts/hil-sovereign-receiver/post-restart-reconstruction.latest.json")
TVC_REL = Path("receipts/hil-sovereign-receiver/tvc-lifecycle-outbox-consumption.latest.json")

PARENT_BLOCKERS = (
    "AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED",
    "POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED",
    "TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN",
)


def _load(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
    return value


def _result(stage: str, reason: str, remaining: list[str], refs: Mapping[str, str | None]) -> dict[str, Any]:
    return {
        "schema": "stegverse.hil.post-esrl-readiness/v1",
        "state": "READY_FOR_NEXT_STAGE" if stage != "PARENT_RUNTIME_EVIDENCE_COMPLETE" else "PARENT_RUNTIME_EVIDENCE_COMPLETE",
        "task_id": TASK_ID,
        "first_unresolved_stage": stage,
        "reason": reason,
        "remaining_parent_blockers": remaining,
        "evidence_refs": dict(refs),
        "source_or_ci_can_satisfy_runtime_predicate": False,
        "second_user_device_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_READ_ONLY_CLASSIFICATION",
    }


def evaluate(*, repo_root: Path, esrl_intake: Path | None = None) -> dict[str, Any]:
    root = repo_root.resolve()
    esrl = _load(esrl_intake.resolve()) if esrl_intake is not None else None
    worker_path = root / WORKER_REL
    restart_path = root / RESTART_REL
    tvc_path = root / TVC_REL
    refs: dict[str, str | None] = {
        "esrl_intake": str(esrl_intake.resolve()) if esrl_intake is not None else None,
        "worker_receipt": str(WORKER_REL),
        "post_restart_receipt": str(RESTART_REL),
        "tvc_lifecycle_receipt": str(TVC_REL),
    }

    if not esrl or esrl.get("schema") != ESRL_SCHEMA or esrl.get("state") != "ACCEPTED" or esrl.get("esrl_lease_open_observed") is not True:
        return _result("ESRL_LEASE_OPEN", "accepted physical ESRL intake receipt not present", list(PARENT_BLOCKERS), refs)
    if esrl.get("task_id") != TASK_ID or esrl.get("lease_state") != "LEASE_OPEN":
        return _result("ESRL_LEASE_OPEN", "ESRL intake subject/state binding invalid", list(PARENT_BLOCKERS), refs)

    worker = _load(worker_path)
    remaining = [PARENT_BLOCKERS[1], PARENT_BLOCKERS[2]]
    if not worker or worker.get("schema") != WORKER_SCHEMA or worker.get("task_id") != TASK_ID or worker.get("receiver_ready") is not True:
        return _result("HIL_RECEIVER_READY_AND_CUSTODY", "authentic receiver READY receipt not present", remaining, refs)

    restart = _load(restart_path)
    if not restart or restart.get("schema") != RESTART_SCHEMA or restart.get("state") != "PASS" or restart.get("receiver_restart_reconstruction_observed") is not True or restart.get("reconstruction_state") != "EXACT_BYTES_HASH_VERIFIED":
        return _result("POST_RESTART_EXACT_BYTE_PROOF", "qualifying controlled restart/reconstruction receipt not present", remaining, refs)

    remaining = [PARENT_BLOCKERS[2]]
    tvc = _load(tvc_path)
    if not tvc or tvc.get("schema") != TVC_SCHEMA or tvc.get("state") != "ADMITTED_TO_TVC_HIL_LIFECYCLE" or not tvc.get("results") or not all(isinstance(row, dict) and row.get("admitted") is True for row in tvc.get("results", [])):
        return _result("TVC_HIL_LIFECYCLE_HANDOFF", "qualifying TVC lifecycle admission receipt not present", remaining, refs)

    return _result("PARENT_RUNTIME_EVIDENCE_COMPLETE", "all three parent runtime evidence obligations are directly observed", [], refs)


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify HIL post-ESRL continuation without promoting evidence.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--esrl-intake", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(repo_root=args.repo_root, esrl_intake=args.esrl_intake)
    except Exception as exc:
        result = {
            "schema": "stegverse.hil.post-esrl-readiness/v1",
            "state": "FAIL_CLOSED",
            "reason": f"{type(exc).__name__}:{exc}",
            "task_id": TASK_ID,
            "authority_effect": "NONE",
        }
        print(json.dumps(result, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
