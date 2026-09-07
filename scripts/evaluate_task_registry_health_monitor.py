#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MONOLITHIC_REGISTRY = ROOT / "data" / "canonical-task-registry.json"
SHARDED_RECORDS = ROOT / "data" / "canonical-task-records"
CONTRACT = ROOT / "data" / "task-registry-health-monitor-contract.json"

OPEN_LIFECYCLES = {"ACTIVE", "COMPLETED"}
RELATION_FIELDS = (
    "parent_task_id",
    "dependency_refs",
    "dependencies",
    "adjacent_task_refs",
    "adjacent_tasks",
    "integration_candidates",
    "successor_task_id",
    "superseded_by_task_id",
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _all_records() -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    if MONOLITHIC_REGISTRY.exists():
        data = _load(MONOLITHIC_REGISTRY)
        rows = data.get("tasks") if isinstance(data, dict) else None
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and row.get("task_id"):
                    by_id[str(row["task_id"])] = row
    if SHARDED_RECORDS.exists():
        for path in sorted(SHARDED_RECORDS.glob("*.json")):
            try:
                row = _load(path)
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(row, dict) and row.get("task_id"):
                by_id[str(row["task_id"])] = row
    return [by_id[key] for key in sorted(by_id)]


def _lifecycle(record: dict[str, Any]) -> str:
    return str(record.get("coordination_state") or record.get("state") or "ACTIVE").strip().upper()


def _checked_out(record: dict[str, Any]) -> bool:
    checkout = str(record.get("checkout_state") or "").strip().upper()
    if checkout == "CHECKED_OUT":
        return True
    claim = record.get("worker_claim")
    return isinstance(claim, dict) and bool(claim.get("claim_ref")) and claim.get("active") is not False


def _posture(record: dict[str, Any]) -> str:
    lifecycle = _lifecycle(record)
    if lifecycle == "RETIRED":
        return "RETIRED"
    if lifecycle == "COMPLETED":
        return "COMPLETED"
    if lifecycle == "SUPERSEDED":
        return "SUPERSEDED"
    if lifecycle == "INVALID":
        return "INVALID"
    return "ACTIVE" if _checked_out(record) else "INACTIVE"


def _path_return_present(ref: Any) -> bool:
    if not isinstance(ref, str) or not ref.strip():
        return False
    ref = ref.split("#", 1)[0]
    return (ROOT / ref).exists()


def _task_ref(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        for key in ("task_id", "ref", "id"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return None


def _relation_ids(record: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for field in RELATION_FIELDS:
        value = record.get(field)
        if isinstance(value, list):
            for item in value:
                ref = _task_ref(item)
                if ref:
                    refs.add(ref)
        else:
            ref = _task_ref(value)
            if ref:
                refs.add(ref)
    refs.discard(str(record.get("task_id") or ""))
    return refs


def _one_hop_open_related(record: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> list[str]:
    task_id = str(record.get("task_id") or "")
    related = set(_relation_ids(record))
    # Treat relationships as observable graph edges in either direction.
    for other_id, other in by_id.items():
        if other_id == task_id:
            continue
        if task_id in _relation_ids(other):
            related.add(other_id)
    return sorted(
        ref for ref in related
        if ref in by_id and _lifecycle(by_id[ref]) in OPEN_LIFECYCLES
    )


def _worker_return_observation(record: dict[str, Any], now: datetime) -> dict[str, Any]:
    obligation = record.get("worker_return_obligation")
    if not isinstance(obligation, dict):
        return {
            "task_id": record.get("task_id"),
            "posture": "UNKNOWN",
            "reason": "checked-out task has no bound worker_return_obligation; silence is not failure proof",
            "recovery_required": False,
        }

    return_ref = (
        obligation.get("master_records_return_ref")
        or obligation.get("matching_master_records_return_ref")
        or record.get("master_records_return_ref")
    )
    if obligation.get("fulfilled") is True or _path_return_present(return_ref):
        return {
            "task_id": record.get("task_id"),
            "posture": "HEALTHY",
            "reason": "matching Master Records return is present",
            "recovery_required": False,
            "master_records_return_ref": return_ref,
        }

    retry_count = int(obligation.get("retry_count") or record.get("retry_count") or 0)
    retry_limit_raw = obligation.get("retry_limit") or record.get("retry_limit")
    retry_limit = int(retry_limit_raw) if retry_limit_raw is not None else None
    if retry_limit is not None and retry_count < retry_limit:
        return {
            "task_id": record.get("task_id"),
            "posture": "RETRYING",
            "reason": f"worker is within bounded retry resilience ({retry_count}/{retry_limit})",
            "recovery_required": False,
            "retry_count": retry_count,
            "retry_limit": retry_limit,
        }

    due = _parse_time(obligation.get("expected_return_by") or obligation.get("expiry_or_return_expectation"))
    if due is None:
        return {
            "task_id": record.get("task_id"),
            "posture": "RECONCILIATION_REQUIRED",
            "reason": "worker-return obligation exists but governed return expectation cannot be resolved",
            "recovery_required": False,
        }
    if now < due:
        return {
            "task_id": record.get("task_id"),
            "posture": "RETURN_PENDING",
            "reason": "governed worker-return expectation has not elapsed",
            "recovery_required": False,
            "expected_return_by": due.isoformat().replace("+00:00", "Z"),
        }

    confirmed_nonreport = bool(obligation.get("nonreport_confirmed"))
    return {
        "task_id": record.get("task_id"),
        "posture": "WORKER_NONREPORT" if confirmed_nonreport else "RETURN_OVERDUE",
        "reason": "bound expected worker return is overdue and no matching Master Records return is present",
        "recovery_required": True,
        "expected_return_by": due.isoformat().replace("+00:00", "Z"),
        "worker_return_obligation_ref": obligation.get("ref"),
        "claim_or_execution_ref": obligation.get("claim_or_execution_ref") or record.get("claim_or_execution_ref"),
        "master_records_subject_binding": obligation.get("master_records_subject_binding"),
    }


def _recovery_task_id(source_task_id: str) -> str:
    safe = source_task_id.upper().replace("_", "-")
    return f"STEGHEALTH-RECOVER-{safe}-001"


def _recovery_cosv() -> str:
    return "20010000100000"


def _task_creation_event(source: dict[str, Any], recovery_task_id: str, symptom: str, now: datetime) -> dict[str, Any]:
    event_id = f"STEGHEALTH-TASK-CREATION:{recovery_task_id}"
    return {
        "schema": "stegverse.recordable-action-event/v1",
        "event_id": event_id,
        "actor": "StegHealth",
        "action": "CREATE_RECOVERY_TASK",
        "source_task_id": source.get("task_id"),
        "created_task_id": recovery_task_id,
        "created_task_cosv": _recovery_cosv(),
        "symptom": symptom,
        "observed_at": now.isoformat().replace("+00:00", "Z"),
        "task_registry_registration_required": True,
        "master_records_recording_required": True,
        "authority_effect": "NONE_OBSERVATION_AND_TASK_CREATION_EVENT",
    }


def evaluate(now: datetime | None = None) -> dict[str, Any]:
    _ = _load(CONTRACT)
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    records = _all_records()
    by_id = {str(row.get("task_id")): row for row in records if row.get("task_id")}
    counts = {key: 0 for key in ["ACTIVE", "INACTIVE", "COMPLETED", "RETIRED", "SUPERSEDED", "INVALID"]}
    checked_out: list[dict[str, Any]] = []
    retirement_blocks: list[dict[str, Any]] = []
    recovery_specs: list[dict[str, Any]] = []
    action_events: list[dict[str, Any]] = []

    for record in records:
        posture = _posture(record)
        counts[posture] = counts.get(posture, 0) + 1

        if _lifecycle(record) == "COMPLETED":
            open_related = _one_hop_open_related(record, by_id)
            if open_related:
                retirement_blocks.append({
                    "task_id": record.get("task_id"),
                    "retirement_ready": False,
                    "open_one_hop_related_task_ids": open_related,
                })

        if not _checked_out(record):
            continue
        obs = _worker_return_observation(record, now)
        checked_out.append(obs)
        if not obs.get("recovery_required"):
            continue

        source_task_id = str(record.get("task_id"))
        candidate = _recovery_task_id(source_task_id)
        if candidate in by_id:
            recovery_specs.append({
                "source_task_id": source_task_id,
                "recovery_task_id": candidate,
                "recovery_task_cosv": by_id[candidate].get("cosv_task_vector"),
                "action": "REUSE_REGISTERED_RECOVERY_TASK",
                "task_registry_registered": True,
                "symptom": obs.get("posture"),
            })
            continue

        spec = {
            "schema": "stegverse.steghealth-recovery-task-spec/v1",
            "task_id": candidate,
            "cosv_task_vector": _recovery_cosv(),
            "owner": "StegVerse-Labs/StegHealth",
            "coordination_state": "ACTIVE",
            "checkout_state": "NOT_CHECKED_OUT",
            "source_task_id": source_task_id,
            "source_cosv_task_vector": record.get("cosv_task_vector"),
            "root_correlation_id": record.get("root_correlation_id") or record.get("correlation_id") or source_task_id,
            "symptom": obs.get("posture"),
            "worker_return_obligation_ref": obs.get("worker_return_obligation_ref"),
            "claim_or_execution_ref": obs.get("claim_or_execution_ref"),
            "master_records_subject_binding": obs.get("master_records_subject_binding"),
            "action": "CREATE_AND_REGISTER_THROUGH_CANONICAL_TASK_INGRESS",
            "task_registry_registration_required": True,
            "master_records_recording_required": True,
            "execution_authority_effect": "NONE",
        }
        recovery_specs.append(spec)
        action_events.append(_task_creation_event(record, candidate, str(obs.get("posture")), now))

    symptom_counts: dict[str, int] = {}
    for obs in checked_out:
        symptom = str(obs.get("posture") or "UNKNOWN")
        symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1

    counts["CHECKED_OUT"] = len(checked_out)
    counts["CHECKED_OUT_WITH_RETURN_OVERDUE"] = symptom_counts.get("RETURN_OVERDUE", 0)
    counts["CHECKED_OUT_WITH_WORKER_NONREPORT"] = symptom_counts.get("WORKER_NONREPORT", 0)
    counts["COMPLETED_BLOCKED_FROM_RETIREMENT_BY_OPEN_ONE_HOP_RELATED_TASKS"] = len(retirement_blocks)
    counts["RECOVERY_TASKS_DERIVED"] = sum(1 for row in recovery_specs if row.get("action") == "CREATE_AND_REGISTER_THROUGH_CANONICAL_TASK_INGRESS")
    counts["RECOVERY_TASKS_ALREADY_REGISTERED"] = sum(1 for row in recovery_specs if row.get("task_registry_registered") is True)

    return {
        "schema": "stegverse.task-registry-health-monitor-report/v1",
        "task_id": "STEGVERSE-TASK-REGISTRY-HEALTH-MONITOR-001",
        "cosv_task_vector": "20010000100000",
        "status": "ACTIVE",
        "observed_at": now.isoformat().replace("+00:00", "Z"),
        "counts": counts,
        "checked_out_findings": checked_out,
        "completed_retirement_blocks": retirement_blocks,
        "steghealth_recovery_tasks": recovery_specs,
        "recordable_action_events": action_events,
        "inactive_is_reporting_posture_not_lifecycle": True,
        "retired_is_terminal_for_execution": True,
        "retired_history_review_only_revive": True,
        "all_created_tasks_require_registry_registration": True,
        "all_actions_are_recordable_events": True,
        "percent_complete_inferred": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate canonical task registry and checked-out worker-return health.")
    parser.add_argument("--now", help="Optional ISO-8601 reference time")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    now = _parse_time(args.now) if args.now else None
    report = evaluate(now=now)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
