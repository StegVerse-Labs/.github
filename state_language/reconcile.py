from __future__ import annotations

from copy import deepcopy
from typing import Any

from .vector import canonical_hash, normalize_vector

ALIGNMENT_SCHEMA = "stegverse.master-records-alignment-transition/v1"
TERMINAL_RECONCILIATION_STATES = {
    "SUPERSEDED",
    "SATISFIED_BY_EXISTING_STATE",
    "CANCELLED_BY_AUTHORITY",
}


def _authority_signature(task: dict[str, Any]) -> tuple[Any, Any]:
    authority = task.get("authority") or task.get("admission") or {}
    return authority.get("domain") or authority.get("authority_domain"), authority.get("ceiling_ref") or authority.get("authority_source")


def _task_semantics(task: dict[str, Any]) -> dict[str, Any]:
    """Fields that define what work is required; runtime claim/fence fields are excluded."""
    keys = (
        "task_id",
        "goal",
        "instructions",
        "success_predicates",
        "dependencies",
        "authority",
        "admission",
        "endpoint",
        "source_state_hash",
        "source_state_vector_ref",
        "source_handoff_ref",
    )
    return {key: deepcopy(task.get(key)) for key in keys if key in task}


def reconcile_tasks(
    registry: dict[str, Any],
    desired_tasks: list[dict[str, Any]],
    *,
    source_state_hash: str,
    source_handoff_ref: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Reconcile a task registry to the desired task projection.

    Historical tasks are retained. Reconciliation cannot mutate an ACTIVE task into a
    semantically different job under the same claim; such a task is marked for
    revalidation/escalation instead. Reapplying an already-reconciled projection does
    not advance reconciliation_generation.
    """
    result = deepcopy(registry)
    tasks = result.setdefault("tasks", [])
    existing = {task.get("task_id"): task for task in tasks if task.get("task_id")}
    desired = {task["task_id"]: deepcopy(task) for task in desired_tasks}
    effects: list[dict[str, Any]] = []

    for task_id in sorted(desired):
        target = desired[task_id]
        target["source_state_hash"] = source_state_hash
        target["source_handoff_ref"] = source_handoff_ref
        current = existing.get(task_id)
        if current is None:
            target.setdefault("state", "HANDOFF_READY")
            tasks.append(target)
            existing[task_id] = target
            effects.append({"task_id": task_id, "disposition": "CREATED"})
            continue

        if _authority_signature(current) != _authority_signature(target) and _authority_signature(current) != (None, None):
            effects.append({"task_id": task_id, "disposition": "ESCALATION_REQUIRED", "reason": "AUTHORITY_ENVELOPE_CHANGED"})
            current["reconciliation_disposition"] = "ESCALATION_REQUIRED"
            current["reconciliation_reason"] = "AUTHORITY_ENVELOPE_CHANGED"
            continue

        if canonical_hash(_task_semantics(current)) == canonical_hash(_task_semantics(target)):
            current["source_state_hash"] = source_state_hash
            current["source_handoff_ref"] = source_handoff_ref
            current["reconciliation_disposition"] = "UNCHANGED"
            effects.append({"task_id": task_id, "disposition": "UNCHANGED"})
            continue

        if current.get("state") == "ACTIVE" or current.get("claim_id") or current.get("worker_id"):
            current["reconciliation_disposition"] = "ESCALATION_REQUIRED"
            current["reconciliation_reason"] = "ACTIVE_CLAIM_REQUIRES_PRECLAIM_OR_SUCCESSOR_RECONCILIATION"
            effects.append({"task_id": task_id, "disposition": "ESCALATION_REQUIRED", "reason": current["reconciliation_reason"]})
            continue

        prior_snapshot = _task_semantics(current)
        history = deepcopy(current.get("history", []))
        if not history or canonical_hash(history[-1].get("task_semantics", {})) != canonical_hash(prior_snapshot):
            history.append(
                {
                    "disposition": "AMENDED",
                    "superseded_by_state_hash": source_state_hash,
                    "task_semantics": prior_snapshot,
                }
            )
        preserved = {
            key: deepcopy(current[key])
            for key in ("created_at", "evidence_refs")
            if key in current
        }
        current.clear()
        current.update(target)
        current.update(preserved)
        current["history"] = history
        current.setdefault("state", "HANDOFF_READY")
        current["reconciliation_disposition"] = "AMENDED"
        effects.append({"task_id": task_id, "disposition": "AMENDED"})

    for task_id, current in sorted(existing.items()):
        if task_id in desired:
            continue
        if current.get("state") in TERMINAL_RECONCILIATION_STATES:
            continue
        if current.get("state") == "ACTIVE" or current.get("claim_id") or current.get("worker_id"):
            current["reconciliation_disposition"] = "ESCALATION_REQUIRED"
            current["reconciliation_reason"] = "TASK_NO_LONGER_DESIRED_BUT_ACTIVE_CLAIM_EXISTS"
            effects.append({"task_id": task_id, "disposition": "ESCALATION_REQUIRED", "reason": current["reconciliation_reason"]})
            continue
        current["state"] = "SUPERSEDED"
        current["reconciliation_disposition"] = "SUPERSEDED"
        current["superseded_by_state_hash"] = source_state_hash
        current["source_handoff_ref"] = source_handoff_ref
        effects.append({"task_id": task_id, "disposition": "SUPERSEDED"})

    result["source_state_hash"] = source_state_hash
    result["source_handoff_ref"] = source_handoff_ref
    materially_changed = any(effect["disposition"] != "UNCHANGED" for effect in effects)
    if materially_changed:
        result["reconciliation_generation"] = int(result.get("reconciliation_generation", 0)) + 1
    else:
        result.setdefault("reconciliation_generation", int(registry.get("reconciliation_generation", 0)))
    return result, effects


def preclaim_revalidate(task: dict[str, Any], canonical_state: dict[str, Any]) -> tuple[bool, str]:
    """Fail closed when a task premise was derived from an older canonical state."""
    state = normalize_vector(canonical_state)
    current_hash = canonical_hash(state)
    task_hash = task.get("source_state_hash")
    if not isinstance(task_hash, str):
        return False, "TASK_SOURCE_STATE_HASH_MISSING"
    if task_hash != current_hash:
        return False, "TASK_SOURCE_STATE_STALE"
    if task.get("reconciliation_disposition") in {"SUPERSEDED", "SATISFIED_BY_EXISTING_STATE", "CANCELLED_BY_AUTHORITY", "ESCALATION_REQUIRED"}:
        return False, f"TASK_NOT_EXECUTABLE_{task['reconciliation_disposition']}"
    return True, "CURRENT_CANONICAL_STATE_CONFIRMED"


def build_alignment_packet(
    *,
    transition_id: str,
    source_handoff_ref: str,
    before_state: dict[str, Any],
    after_state: dict[str, Any],
    semantic_delta: dict[str, Any],
    module_id: str,
    endpoint_id: str,
    projection_before: Any,
    projection_after: Any,
    task_effects: list[dict[str, Any]],
    alignment_disposition: str,
    reconstruction_state: str = "PASS",
    parent_transition_id: str | None = None,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    allowed = {"ALIGNED", "PROPAGATING", "ALIGNED_WITH_DRIFT", "STALE", "DIVERGENT", "OSCILLATING", "FAIL_CLOSED"}
    if alignment_disposition not in allowed:
        raise ValueError("unsupported alignment disposition")
    before = normalize_vector(before_state)
    after = normalize_vector(after_state)
    return {
        "schema": ALIGNMENT_SCHEMA,
        "transition_id": transition_id,
        "parent_transition_id": parent_transition_id,
        "source_handoff_ref": source_handoff_ref,
        "source_state_hash": canonical_hash(before),
        "target_state_hash": canonical_hash(after),
        "semantic_delta_hash": canonical_hash(semantic_delta),
        "module_id": module_id,
        "endpoint_id": endpoint_id,
        "projection_before_hash": canonical_hash(projection_before),
        "projection_after_hash": canonical_hash(projection_after),
        "task_effects": deepcopy(task_effects),
        "alignment_disposition": alignment_disposition,
        "reconstruction_state": reconstruction_state,
        "evidence_refs": sorted(set(evidence_refs or [])),
        "authority_effect": after["authority"].get("effect", "NONE"),
        "custody_destination": "master-records/orchestration",
    }
