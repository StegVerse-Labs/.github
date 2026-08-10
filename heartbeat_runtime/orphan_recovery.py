from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

RECOVERY_REQUIRED_CODES = [
    "ORPHAN_RECOVERY_REQUIRED",
    "SUCCESSOR_RECONSTRUCTION_REQUIRED",
    "EXECUTOR_NOT_BOUND",
    "MASTER_RECORDS_CUSTODY_NOT_PROVEN",
]


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _scope_narrow_or_equal(parent_handoff: dict[str, Any], recovery_handoff: dict[str, Any]) -> bool:
    parent_goal = parent_handoff.get("goal") or {}
    recovery_goal = recovery_handoff.get("goal") or {}
    parent_task = parent_handoff.get("task") or {}
    recovery_task = recovery_handoff.get("task") or {}
    parent_exec = parent_handoff.get("execution") or {}
    recovery_exec = recovery_handoff.get("execution") or {}
    if recovery_task.get("repository") != parent_task.get("repository"):
        return False
    if recovery_task.get("canonical_owner_ref") != parent_task.get("canonical_owner_ref"):
        return False
    if not set(recovery_goal.get("authority_ceiling") or []).issubset(set(parent_goal.get("authority_ceiling") or [])):
        return False
    if not set(recovery_exec.get("required_capabilities") or []).issubset(set(parent_exec.get("required_capabilities") or [])):
        return False
    if not set(recovery_exec.get("allowed_paths") or []).issubset(set(parent_exec.get("allowed_paths") or [])):
        return False
    if not set(recovery_exec.get("allowed_services") or []).issubset(set(parent_exec.get("allowed_services") or [])):
        return False
    for key in ("max_actions", "max_retries", "external_cost_ceiling_usd", "runtime_window_beats"):
        p = parent_exec.get(key)
        c = recovery_exec.get(key)
        if not isinstance(p, (int, float)) or not isinstance(c, (int, float)) or c > p:
            return False
    return True


def orphan_recovery_contract_valid(
    root: Path,
    *,
    registry_task: dict[str, Any],
    registry: dict[str, Any],
) -> tuple[bool, str]:
    task_id = str(registry_task.get("task_id") or "")
    handoff_ref = str(registry_task.get("handoff_ref") or "")
    if not task_id.startswith("RECOVER-") or "-ORPHAN-HB" not in task_id:
        return False, "NOT_ORPHAN_RECOVERY_TASK"
    if not handoff_ref.startswith("handoffs/generated/RECOVER-"):
        return False, "RECOVERY_HANDOFF_NOT_GENERATED"
    handoff = _load_json(root / handoff_ref)
    if not isinstance(handoff, dict):
        return False, "RECOVERY_HANDOFF_UNREADABLE"
    if handoff.get("schema") != "stegverse.executable-handoff/v0.1" or handoff.get("state") != "BLOCKED":
        return False, "RECOVERY_HANDOFF_NOT_FAIL_CLOSED"
    task_spec = handoff.get("task") or {}
    parent_id = task_spec.get("parent_task_id")
    if not isinstance(parent_id, str) or not parent_id:
        return False, "RECOVERY_PARENT_MISSING"
    expected_prefix = f"RECOVER-{parent_id}-ORPHAN-HB"
    if not task_id.startswith(expected_prefix):
        return False, "RECOVERY_TASK_PARENT_ID_MISMATCH"
    parent = next((item for item in registry.get("tasks", []) if item.get("task_id") == parent_id), None)
    if not isinstance(parent, dict):
        return False, "RECOVERY_PARENT_REGISTRY_MISSING"
    parent_ref = str(parent.get("handoff_ref") or "")
    parent_handoff = _load_json(root / parent_ref)
    if not isinstance(parent_handoff, dict):
        return False, "RECOVERY_PARENT_HANDOFF_UNREADABLE"
    if parent.get("state") != "BLOCKED" or parent.get("claim_id") is not None or parent.get("worker_id") is not None:
        return False, "RECOVERY_PARENT_OLD_AUTHORITY_NOT_ENDED"
    parent_codes = set(parent.get("archive_reason_codes") or [])
    if not {"WORKER_ORPHANED", "OLD_AUTHORITY_RELEASED", "RECOVERY_RECONSTRUCTION_REQUIRED"}.issubset(parent_codes):
        return False, "RECOVERY_PARENT_ORPHAN_EVIDENCE_MISSING"
    checkpoint = str(parent.get("last_checkpoint_ref") or "")
    continuity = handoff.get("continuity") or {}
    source_refs = set(task_spec.get("source_refs") or [])
    if not checkpoint or continuity.get("checkpoint_ref") != checkpoint or checkpoint not in source_refs or parent_ref not in source_refs:
        return False, "RECOVERY_CHECKPOINT_BINDING_MISMATCH"
    parent_authority = parent_handoff.get("authority") or {}
    recovery_authority = handoff.get("authority") or {}
    if (
        recovery_authority.get("authority_source") != parent_authority.get("authority_source")
        or recovery_authority.get("policy_version") != parent_authority.get("policy_version")
        or recovery_authority.get("heartbeat_grants_execution_authority") is not False
    ):
        return False, "RECOVERY_AUTHORITY_BINDING_MISMATCH"
    if not _scope_narrow_or_equal(parent_handoff, handoff):
        return False, "RECOVERY_SCOPE_EXPANSION_DETECTED"
    activation = handoff.get("activation") or {}
    block = handoff.get("block") or {}
    if activation.get("executor_binding") != "UNBOUND":
        return False, "RECOVERY_EXECUTOR_MUST_REMAIN_UNBOUND"
    if block.get("block_reason") != "ORPHAN_RECOVERY_RECONSTRUCTION_REQUIRED":
        return False, "RECOVERY_BLOCK_CONTRACT_MISSING"
    if continuity.get("master_records_required") is not True:
        return False, "RECOVERY_MASTER_RECORDS_REQUIRED"
    if (handoff.get("goal") or {}).get("successor_policy") != "NONE":
        return False, "RECOVERY_MAY_NOT_CREATE_NESTED_SUCCESSORS"
    return True, "NARROW_ORPHAN_RECOVERY_CONTRACT_VALID"


def reconcile_quarantined_orphan_recoveries(
    root: Path,
    registry: dict[str, Any],
    *,
    epoch: int,
    event: Callable[..., None] | None = None,
) -> list[str]:
    reconciled: list[str] = []
    for task in registry.get("tasks", []):
        if task.get("state") != "QUARANTINED":
            continue
        valid, reason = orphan_recovery_contract_valid(root, registry_task=task, registry=registry)
        if not valid:
            if event is not None and str(task.get("task_id") or "").startswith("RECOVER-"):
                event(
                    epoch,
                    "orphan_recovery_quarantine_retained",
                    task_id=task.get("task_id"),
                    reason=reason,
                    authority_effect=False,
                )
            continue
        task["state"] = "BLOCKED"
        task["block_ref"] = f"{task['handoff_ref']}#block"
        task["archive_eligible"] = False
        task["archive_reason_codes"] = list(RECOVERY_REQUIRED_CODES)
        task["claim_id"] = None
        task["worker_id"] = None
        task["worker_instance_id"] = None
        task["lease"] = None
        task["heartbeat_timing"] = None
        reconciled.append(str(task["task_id"]))
        if event is not None:
            event(
                epoch,
                "orphan_recovery_quarantine_reconciled",
                task_id=task.get("task_id"),
                reason=reason,
                state="BLOCKED",
                old_authority_reused=False,
                successor_authority_granted=False,
                authority_effect=False,
            )
    return reconciled


__all__ = [
    "RECOVERY_REQUIRED_CODES",
    "orphan_recovery_contract_valid",
    "reconcile_quarantined_orphan_recoveries",
]
