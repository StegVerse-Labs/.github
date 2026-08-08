#!/usr/bin/env python3
"""Validate executable HANDOFF state and project heartbeat-worker status.

This is deliberately a control-plane projector, not an executor. Heartbeat may
surface activation candidates; only a separately bound/authorized executor may
perform task mutations.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "control" / "worker-registry.json"
STATUS = ROOT / "control" / "worker-status.json"
HANDOFFS = ROOT / "handoffs"

ACTIVE_STATES = {"CLAIMED", "ACTIVE", "BLOCKED", "EXPIRING", "HANDOFF_WRITING"}
UNFINISHED_STATES = {
    "HANDOFF_READY", "ACTIVATION_PENDING", "CLAIMED", "ACTIVE", "BLOCKED",
    "HUMAN_AUTHORITY_REQUIRED", "EXPIRING", "HANDOFF_WRITING",
    "FAILED_RETRYABLE", "QUARANTINED"
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def capabilities_match(required: set[str], workers: list[dict]) -> list[str]:
    matches = []
    for worker in workers:
        if worker.get("status") != "AVAILABLE":
            continue
        if required.issubset(set(worker.get("capabilities", []))):
            matches.append(worker["worker_id"])
    return sorted(matches)


def evaluate(task_state: dict, handoff: dict, workers: list[dict], now: datetime) -> tuple[dict, list[str]]:
    errors: list[str] = []
    task_id = task_state["task_id"]
    if handoff.get("schema") != "stegverse.executable-handoff/v0.1":
        errors.append(f"{task_id}: unsupported handoff schema")
    if handoff.get("task", {}).get("task_id") != task_id:
        errors.append(f"{task_id}: handoff task_id mismatch")
    if handoff.get("goal", {}).get("goal_id") != task_state.get("goal_id"):
        errors.append(f"{task_id}: goal_id mismatch")
    if handoff.get("authority", {}).get("heartbeat_grants_execution_authority") is not False:
        errors.append(f"{task_id}: heartbeat must not grant execution authority")
    if handoff.get("activation", {}).get("carrier") != "heartbeat":
        errors.append(f"{task_id}: activation carrier must be heartbeat")
    if handoff.get("activation", {}).get("checkout_policy") != "fenced_atomic_checkout":
        errors.append(f"{task_id}: checkout policy must be fenced_atomic_checkout")

    state = task_state.get("state")
    binding = task_state.get("executor_binding")
    lease = task_state.get("lease")
    valid_lease = False
    stale_lease = False
    if lease:
        expires = parse_time(lease.get("expires_at"))
        heartbeat_due = parse_time(lease.get("heartbeat_due_at"))
        valid_lease = bool(expires and expires > now)
        stale_lease = bool(expires and expires <= now)
        if not heartbeat_due:
            errors.append(f"{task_id}: lease missing heartbeat_due_at")
        if int(lease.get("fencing_token", 0)) < 1:
            errors.append(f"{task_id}: invalid fencing token")

    if state in ACTIVE_STATES:
        for field in ("worker_id", "worker_instance_id", "claim_id"):
            if not task_state.get(field):
                errors.append(f"{task_id}: {state} requires {field}")
        if not lease:
            errors.append(f"{task_id}: {state} requires lease")

    required = set(handoff.get("execution", {}).get("required_capabilities", []))
    eligible_workers = capabilities_match(required, workers)
    activation_required = state == "HANDOFF_READY" and not valid_lease
    executor_resolved = binding in {"AUTHORIZED", "BOUND"} and bool(eligible_workers or task_state.get("worker_id"))

    reasons: list[str] = []
    if state == "COMPLETED":
        archive_eligible = True
    elif state in UNFINISHED_STATES:
        archive_eligible = bool(
            binding == "BOUND"
            and executor_resolved
            and not stale_lease
            and handoff.get("continuity", {}).get("status_projection")
            and handoff.get("activation", {}).get("carrier") == "heartbeat"
        )
        if binding != "BOUND":
            reasons.append("EXECUTOR_NOT_BOUND")
        if not executor_resolved:
            reasons.append("EXECUTOR_NOT_RESOLVED")
        if stale_lease:
            reasons.append("LEASE_EXPIRED")
        if handoff.get("continuity", {}).get("master_records_required"):
            reasons.append("MASTER_RECORDS_CUSTODY_REQUIRED")
        if activation_required:
            reasons.append("HEARTBEAT_ACTIVATION_REQUIRED")
    else:
        archive_eligible = False
        reasons.append("UNSUPPORTED_LIFECYCLE_STATE")

    # Custody is a separate gate. Until a durable return is represented in evidence,
    # worker-managed unfinished work remains non-archivable.
    if state != "COMPLETED" and handoff.get("continuity", {}).get("master_records_required"):
        custody_proven = any("master-records:" in ref.lower() for ref in task_state.get("evidence_refs", []))
        if not custody_proven:
            archive_eligible = False
            if "MASTER_RECORDS_CUSTODY_NOT_PROVEN" not in reasons:
                reasons.append("MASTER_RECORDS_CUSTODY_NOT_PROVEN")

    projection = {
        "task_id": task_id,
        "goal_id": task_state.get("goal_id"),
        "state": state,
        "executor_binding": binding,
        "activation_carrier": "heartbeat",
        "activation_required": activation_required,
        "executor_resolved": executor_resolved,
        "eligible_workers": eligible_workers,
        "worker_id": task_state.get("worker_id"),
        "worker_instance_id": task_state.get("worker_instance_id"),
        "claim_id": task_state.get("claim_id"),
        "valid_lease": valid_lease,
        "stale_lease": stale_lease,
        "last_checkpoint_ref": task_state.get("last_checkpoint_ref"),
        "next_authorized_action": handoff.get("completion", {}).get("next_authorized_action"),
        "archive_eligible": archive_eligible,
        "archive_reason_codes": sorted(set(reasons)),
        "handoff_ref": task_state.get("handoff_ref"),
        "evidence_refs": task_state.get("evidence_refs", []),
    }
    return projection, errors


def project(now: datetime) -> tuple[dict, list[str]]:
    registry = load(REGISTRY)
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
            continue
        handoff = load(handoff_path)
        projection, task_errors = evaluate(task_state, handoff, workers, now)
        results.append(projection)
        errors.extend(task_errors)

    status = {
        "schema": "stegverse.heartbeat-worker-status/v0.1",
        "generated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_registry_generation": registry.get("generation", 0),
        "activation_driver": ".github/workflows/heartbeat-worker-project.yml",
        "execution_authority_from_heartbeat": False,
        "task_count": len(results),
        "activation_required_count": sum(1 for r in results if r["activation_required"]),
        "archive_eligible_count": sum(1 for r in results if r["archive_eligible"]),
        "tasks": sorted(results, key=lambda r: (r["goal_id"], r["task_id"])),
        "validation": {"ok": not errors, "errors": errors},
    }
    return status, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if committed projection differs semantically")
    parser.add_argument("--write", action="store_true", help="write control/worker-status.json")
    parser.add_argument("--now", help="override current UTC time for deterministic testing")
    args = parser.parse_args()
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    assert now is not None
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
