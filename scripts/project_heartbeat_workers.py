#!/usr/bin/env python3
"""Validate executable handoff state and project canonical worker status.

This surface is observational only. Engine v11 owns fail-closed resolution task
creation. Projection normalizes legacy registry state so stale BLOCKED labels do
not contradict authoritative completed handoffs or actively bound workers.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "control" / "worker-registry.json"
STATUS = ROOT / "control" / "worker-status.json"
HB_STATE = ROOT / "control" / "heartbeat-state.json"

SUPPORTED_HANDOFF_SCHEMAS = {
    "stegverse.executable-handoff/v0.1",
    "stegverse.executable-handoff/v0.2",
}
WORKER_OWNED_STATES = {"CLAIMED", "ACTIVE", "EXPIRING", "HANDOFF_WRITING"}
UNFINISHED_STATES = {
    "HANDOFF_READY", "ACTIVATION_PENDING", "CLAIMED", "ACTIVE",
    "HUMAN_AUTHORITY_REQUIRED", "EXPIRING", "HANDOFF_WRITING",
    "FAILED_RETRYABLE", "QUARANTINED"
}
TERMINAL_HANDOFF_STATES = {"COMPLETE", "COMPLETED", "COMPLETE_RELEASED"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def capabilities_match(required: set[str], workers: list[dict]) -> list[str]:
    matches = []
    for worker in workers:
        if worker.get("status") != "AVAILABLE" or not worker.get("adapter_ref"):
            continue
        if required.issubset(set(worker.get("capabilities", []))):
            matches.append(worker["worker_id"])
    return sorted(matches)


def normalize_state(task_state: dict, handoff: dict) -> tuple[str, str | None]:
    """Return effective operational state plus reconciliation reason.

    Registry rows are historical runtime projections. A newer authoritative
    handoff can prove a task complete, and a legacy BLOCKED row with an active
    bound worker represents active solution execution rather than idle work.
    """
    raw = str(task_state.get("state", ""))
    handoff_state = str(handoff.get("state", ""))
    handoff_task_state = str(handoff.get("task", {}).get("operational_state", ""))

    if handoff_state in TERMINAL_HANDOFF_STATES or handoff_task_state in {"COMPLETE", "COMPLETED"}:
        return "COMPLETED", "AUTHORITATIVE_HANDOFF_COMPLETE"
    if raw == "BLOCKED" and task_state.get("executor_binding") == "BOUND" and task_state.get("claim_id"):
        return "ACTIVE", "LEGACY_BOUND_CONSTRAINT_NORMALIZED_TO_ACTIVE_WORKER"
    if raw == "BLOCKED":
        return "ACTIVATION_PENDING", "LEGACY_UNOWNED_CONSTRAINT_REQUIRES_RESOLUTION_OR_RECONCILIATION"
    return raw, None


def evaluate(task_state: dict, handoff: dict, workers: list[dict], hb_epoch: int) -> tuple[dict, list[str]]:
    errors: list[str] = []
    task_id = task_state["task_id"]
    if handoff.get("schema") not in SUPPORTED_HANDOFF_SCHEMAS:
        errors.append(f"{task_id}: unsupported handoff schema")
    if handoff.get("task", {}).get("task_id") != task_id:
        errors.append(f"{task_id}: handoff task_id mismatch")
    if handoff.get("goal", {}).get("goal_id") != task_state.get("goal_id"):
        errors.append(f"{task_id}: goal_id mismatch")
    if handoff.get("authority", {}).get("heartbeat_grants_execution_authority") is not False:
        errors.append(f"{task_id}: heartbeat must not expand execution authority")
    if handoff.get("activation", {}).get("carrier") != "heartbeat":
        errors.append(f"{task_id}: activation carrier must be heartbeat")
    if handoff.get("activation", {}).get("checkout_policy") != "fenced_atomic_checkout":
        errors.append(f"{task_id}: checkout policy must be fenced_atomic_checkout")

    raw_state = str(task_state.get("state", ""))
    state, reconciliation = normalize_state(task_state, handoff)
    binding = task_state.get("executor_binding")
    timing = task_state.get("heartbeat_timing") or None
    hb_timing_valid = False
    hb_expired = False
    delta_hb_since_response = None
    delta_hb_since_transition = None
    fence = 0
    if timing:
        last_response = int(timing["last_response_epoch"])
        last_transition = int(timing["last_transition_epoch"])
        delta_hb_since_response = max(0, hb_epoch - last_response)
        delta_hb_since_transition = max(0, hb_epoch - last_transition)
        expiry_epoch = timing.get("expiry_epoch")
        hb_expired = expiry_epoch is not None and hb_epoch >= int(expiry_epoch)
        hb_timing_valid = not hb_expired
        fence = int(timing.get("fencing_token", 0))
        if last_response > hb_epoch or last_transition > hb_epoch:
            errors.append(f"{task_id}: heartbeat timing references future epoch")
    elif task_state.get("lease"):
        fence = int(task_state["lease"].get("fencing_token", 0))

    worker_owned = state in WORKER_OWNED_STATES
    if worker_owned:
        for field in ("worker_id", "worker_instance_id", "claim_id"):
            if not task_state.get(field):
                errors.append(f"{task_id}: worker-owned {state} requires {field}")
        if fence < 1:
            errors.append(f"{task_id}: worker-owned state requires fencing token")
        if not timing:
            errors.append(f"{task_id}: worker-owned state requires heartbeat_timing")

    execution = handoff.get("execution", {})
    activation = handoff.get("activation", {})
    continuity = handoff.get("continuity", {})
    required = set(execution.get("required_capabilities", []))
    eligible_workers = capabilities_match(required, workers)
    activation_required = state in {"HANDOFF_READY", "ACTIVATION_PENDING"}
    unique_executor = len(eligible_workers) == 1
    executor_resolved = binding == "BOUND" or (binding in {"AUTHORIZED", "RELEASED"} and unique_executor)
    authority_resolved = (
        handoff.get("authority", {}).get("heartbeat_grants_execution_authority") is False
        and (binding == "BOUND" or activation.get("executor_binding") in {"AUTHORIZED", "RELEASED"})
    )

    reasons: list[str] = list(task_state.get("archive_reason_codes", []))
    if state == "COMPLETED":
        archive_eligible = True
        reasons = []
    elif state in UNFINISHED_STATES:
        archive_eligible = bool(
            worker_owned and binding == "BOUND" and executor_resolved and authority_resolved
            and hb_timing_valid and continuity.get("status_projection")
            and activation.get("carrier") == "heartbeat"
        )
        if binding != "BOUND": reasons.append("EXECUTOR_NOT_BOUND")
        if not eligible_workers and binding != "BOUND": reasons.append("EXECUTOR_NOT_RESOLVED")
        if len(eligible_workers) > 1 and binding != "BOUND": reasons.append("EXECUTOR_AMBIGUOUS")
        if not authority_resolved: reasons.append("EXECUTION_AUTHORITY_UNRESOLVED")
        if worker_owned and not timing: reasons.append("HB_RELATIVE_TIMING_NOT_ESTABLISHED")
        if worker_owned and not task_state.get("last_checkpoint_ref"):
            archive_eligible = False
            reasons.append("CHECKPOINT_MISSING")
        if hb_expired: reasons.append("HB_RELATIVE_EXPIRY_REACHED")
        if activation_required: reasons.append("HEARTBEAT_ACTIVATION_REQUIRED")
        if reconciliation == "LEGACY_UNOWNED_CONSTRAINT_REQUIRES_RESOLUTION_OR_RECONCILIATION":
            archive_eligible = False
            reasons.append("RESOLUTION_OR_COMPLETION_RECONCILIATION_REQUIRED")
    else:
        archive_eligible = False
        reasons.append("UNSUPPORTED_LIFECYCLE_STATE")

    parent_task_id = handoff.get("task", {}).get("parent_task_id")
    reconstruction_ref = continuity.get("reconstruction_ref")
    if parent_task_id and state not in {"COMPLETED", "HUMAN_AUTHORITY_REQUIRED"} and not reconstruction_ref:
        archive_eligible = False
        reasons.append("SUCCESSOR_RECONSTRUCTION_REQUIRED")

    if state != "COMPLETED" and continuity.get("master_records_required"):
        custody_proven = any("master-records:" in str(ref).lower() for ref in task_state.get("evidence_refs", []))
        if not custody_proven:
            archive_eligible = False
            reasons.append("MASTER_RECORDS_CUSTODY_NOT_PROVEN")

    if errors:
        archive_eligible = False
        reasons.append("VALIDATION_ERROR_FAIL_CLOSED")

    projection = {
        "task_id": task_id,
        "goal_id": task_state.get("goal_id"),
        "state": state,
        "raw_registry_state": raw_state,
        "state_reconciliation": reconciliation,
        "constraint_present": bool(handoff.get("constraint") or handoff.get("block_ref") or task_state.get("block_ref")),
        "executor_binding": binding,
        "activation_carrier": "heartbeat",
        "activation_required": activation_required,
        "executor_resolved": executor_resolved,
        "authority_resolved": authority_resolved,
        "eligible_workers": eligible_workers,
        "worker_id": task_state.get("worker_id"),
        "worker_instance_id": task_state.get("worker_instance_id"),
        "claim_id": task_state.get("claim_id"),
        "fencing_token": fence or None,
        "heartbeat_epoch": hb_epoch,
        "heartbeat_timing_established": timing is not None,
        "delta_hb_since_response": delta_hb_since_response,
        "delta_hb_since_transition": delta_hb_since_transition,
        "current_transition": timing.get("current_transition") if timing else None,
        "expected_next_transition": timing.get("expected_next_transition") if timing else None,
        "expiry_epoch": timing.get("expiry_epoch") if timing else None,
        "cost_basis_ref": task_state.get("cost_basis_ref"),
        "legacy_wall_clock_lease_is_timing_authority": False,
        "last_checkpoint_ref": task_state.get("last_checkpoint_ref"),
        "next_authorized_action": handoff.get("completion", {}).get("next_authorized_action"),
        "archive_eligible": archive_eligible,
        "archive_reason_codes": sorted(set(reasons)),
        "handoff_ref": task_state.get("handoff_ref"),
        "evidence_refs": task_state.get("evidence_refs", []),
        "validation_errors": list(errors),
    }
    return projection, errors


def project(now: datetime) -> tuple[dict, list[str]]:
    registry = load(REGISTRY)
    hb = load(HB_STATE)
    hb_epoch = int(hb.get("epoch", 0))
    errors: list[str] = []
    if registry.get("schema") != "stegverse.heartbeat-worker-registry/v0.1":
        errors.append("unsupported worker registry schema")

    workers = registry.get("workers", [])
    results = []
    seen: set[str] = set()
    for task_state in registry.get("tasks", []):
        task_id = task_state.get("task_id")
        if not task_id or task_id in seen:
            errors.append(f"duplicate or missing task_id: {task_id}")
            continue
        seen.add(task_id)
        handoff_path = ROOT / task_state["handoff_ref"]
        if not handoff_path.exists():
            errors.append(f"{task_id}: missing handoff {task_state['handoff_ref']}")
            results.append({
                "task_id": task_id, "goal_id": task_state.get("goal_id"), "state": "ACTIVATION_PENDING",
                "raw_registry_state": task_state.get("state"), "archive_eligible": False,
                "archive_reason_codes": ["HANDOFF_MISSING", "VALIDATION_ERROR_FAIL_CLOSED"],
                "last_checkpoint_ref": task_state.get("last_checkpoint_ref"),
                "evidence_refs": task_state.get("evidence_refs", []),
                "validation_errors": [f"missing handoff {task_state['handoff_ref']}"]
            })
            continue
        projection, task_errors = evaluate(task_state, load(handoff_path), workers, hb_epoch)
        results.append(projection)
        errors.extend(task_errors)

    status = {
        "schema": "stegverse.heartbeat-worker-status/v0.4",
        "generated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_registry_generation": registry.get("generation", 0),
        "heartbeat_epoch": hb_epoch,
        "activation_driver": "internal_heartbeat_registry_evaluation",
        "single_heartbeat_timing_frame": True,
        "execution_authority_from_heartbeat": False,
        "query_is_observational": True,
        "passive_blocked_projection_allowed": False,
        "task_count": len(results),
        "activation_required_count": sum(1 for r in results if r.get("activation_required")),
        "archive_eligible_count": sum(1 for r in results if r.get("archive_eligible")),
        "tasks": sorted(results, key=lambda r: (str(r.get("goal_id")), str(r.get("task_id")))),
        "validation": {"ok": not errors, "errors": errors},
    }
    return status, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--now", help="override current UTC time for deterministic projection metadata")
    args = parser.parse_args()
    now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else datetime.now(timezone.utc)
    status, errors = project(now)
    if args.write:
        STATUS.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.check and STATUS.exists():
        committed = load(STATUS)
        for value in (committed, status):
            value.pop("generated_at", None)
        if committed != status:
            errors.append("committed worker-status projection differs from current state")
    print(json.dumps(status, indent=2, sort_keys=True))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
