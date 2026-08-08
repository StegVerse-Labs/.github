#!/usr/bin/env python3
"""Project one-heartbeat continuity state across workers and custody.

This module is observational and deterministic. It does not create execution
authority. It interprets the single organization heartbeat epoch as the common
relative timing frame for worker transitions, detects reconciliation conditions,
and emits registry-task candidates for failures such as known worker expiry with
missing required Master Records finalization.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HB_STATE = ROOT / "control" / "heartbeat-state.json"
WORKERS = ROOT / "control" / "worker-registry.json"
OUT = ROOT / "control" / "heartbeat-continuity.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def has_master_records_final(task: dict[str, Any]) -> bool:
    refs = [str(x).lower() for x in task.get("evidence_refs", [])]
    final_markers = ("final-worker-report", "task_completed", "claim_released", "finalization")
    return any("master-records:" in ref and any(marker in ref for marker in final_markers) for ref in refs)


def recovery_candidate(task: dict[str, Any], epoch: int, reason: str) -> dict[str, Any]:
    task_id = task["task_id"]
    fence = int((task.get("lease") or {}).get("fencing_token", 0))
    return {
        "schema": "stegverse.registry-task-candidate/v0.1",
        "candidate_id": f"RECOVER-{task_id}-HB{epoch}",
        "parent_task_id": task_id,
        "goal_id": task.get("goal_id"),
        "reason": reason,
        "created_from_heartbeat_epoch": epoch,
        "last_known_worker_id": task.get("worker_id"),
        "last_known_worker_instance_id": task.get("worker_instance_id"),
        "last_known_claim_id": task.get("claim_id"),
        "last_known_fencing_token": fence or None,
        "last_checkpoint_ref": task.get("last_checkpoint_ref"),
        "required_action": "reconcile lifecycle evidence, investigate failure, sandbox-test candidate remediation when needed, and admit only a validated remediation task",
        "execution_authority": False,
        "requires_registry_admission": True,
    }


def project() -> dict[str, Any]:
    hb = load(HB_STATE)
    registry = load(WORKERS)
    epoch = int(hb.get("epoch", 0))
    observations: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    for task in registry.get("tasks", []):
        timing = task.get("heartbeat_timing") or {}
        last_response = timing.get("last_response_epoch")
        last_transition = timing.get("last_transition_epoch")
        expiry_epoch = timing.get("expiry_epoch")
        delta_since_transition = None if last_transition is None else max(0, epoch - int(last_transition))
        delta_since_response = None if last_response is None else max(0, epoch - int(last_response))

        reason_codes: list[str] = []
        status = "OBSERVATION_ONLY"
        if not timing:
            reason_codes.append("HB_RELATIVE_TIMING_NOT_YET_RECORDED")
        else:
            if delta_since_response is not None and delta_since_response > int(timing.get("max_missing_response_beats", 0)):
                reason_codes.append("WORKER_RESPONSE_BEYOND_EXPECTED_HB_WINDOW")
                status = "INVESTIGATION_REQUIRED"
            if expiry_epoch is not None and epoch >= int(expiry_epoch):
                reason_codes.append("KNOWN_WORKER_EXPIRY_REACHED")
                if not has_master_records_final(task):
                    reason_codes.append("MASTER_RECORDS_FINAL_WORKER_REPORT_MISSING")
                    status = "RECONCILIATION_REQUIRED"
                    candidates.append(recovery_candidate(task, epoch, "KNOWN_EXPIRY_WITHOUT_MASTER_RECORDS_FINAL_WORKER_REPORT"))

        observations.append({
            "task_id": task.get("task_id"),
            "goal_id": task.get("goal_id"),
            "state": task.get("state"),
            "heartbeat_epoch": epoch,
            "current_transition": timing.get("current_transition"),
            "transition_sequence": timing.get("transition_sequence"),
            "last_response_epoch": last_response,
            "last_transition_epoch": last_transition,
            "delta_hb_since_response": delta_since_response,
            "delta_hb_since_transition": delta_since_transition,
            "expected_next_transition": timing.get("expected_next_transition"),
            "expiry_epoch": expiry_epoch,
            "cost_basis_ref": task.get("cost_basis_ref"),
            "continuity_status": status,
            "continuity_lost": False,
            "reason_codes": reason_codes,
        })

    return {
        "schema": "stegverse.heartbeat-continuity-projection/v0.1",
        "heartbeat_epoch": epoch,
        "heartbeat_is_single_common_timing_frame": True,
        "absence_or_delay_is_not_by_itself_continuity_loss": True,
        "observations": observations,
        "registry_task_candidates": candidates,
        "candidate_count": len(candidates),
        "authority_effect": "none",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = project()
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if args.write:
        OUT.write_text(rendered, encoding="utf-8")
    if args.check and OUT.exists() and load(OUT) != value:
        print("ERROR: committed heartbeat continuity projection differs from current state")
        return 1
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
