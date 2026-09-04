"""Non-authorizing cross-task coordination and evidence-resolution preflight."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

LEDGER_SCHEMA = "stegverse.cross-task-coordination-ledger/v1"
PREFLIGHT_SCHEMA = "stegverse.cross-task-coordination-preflight/v1"
PREDICATE_STATES = {"SATISFIED", "UNSATISFIED", "IN_PROGRESS", "UNKNOWN", "CONFLICTED"}
ACTIVE_CLAIM_STATES = {"ACTIVE"}


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _now(value: datetime | None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current


def _field_present(fields: dict[str, Any], dotted: str) -> bool:
    cursor: Any = fields
    for part in dotted.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            return False
        cursor = cursor[part]
    return cursor is not None


def _evidence_rejection_reasons(predicate: dict[str, Any], evidence: dict[str, Any], now: datetime) -> list[str]:
    reasons: list[str] = []
    if evidence.get("predicate_id") != predicate.get("predicate_id"):
        reasons.append("PREDICATE_ID_MISMATCH")
    if evidence.get("producer") != predicate.get("authoritative_producer"):
        reasons.append("AUTHORITATIVE_PRODUCER_MISMATCH")
    required_schema = predicate.get("required_schema")
    if required_schema and evidence.get("schema") != required_schema:
        reasons.append("SCHEMA_MISMATCH")
    required_scope = predicate.get("required_scope")
    if required_scope and evidence.get("scope") != required_scope:
        reasons.append("SCOPE_MISMATCH")
    required_execution = predicate.get("required_execution_instance")
    if required_execution and evidence.get("execution_instance") != required_execution:
        reasons.append("EXECUTION_INSTANCE_MISMATCH")
    authority_effect = evidence.get("authority_effect")
    if authority_effect not in {"NONE", "EVIDENCE_ONLY"}:
        reasons.append("EVIDENCE_AUTHORITY_EFFECT_INVALID")
    fields = evidence.get("fields") if isinstance(evidence.get("fields"), dict) else {}
    for field in predicate.get("required_fields") or []:
        if not _field_present(fields, str(field)):
            reasons.append(f"REQUIRED_FIELD_MISSING:{field}")
    max_age = predicate.get("max_age_seconds")
    if max_age is not None:
        observed = _parse_time(evidence.get("observed_at"))
        if observed is None:
            reasons.append("FRESHNESS_UNPROVABLE")
        else:
            age = (now - observed.astimezone(now.tzinfo)).total_seconds()
            if age < 0 or age > int(max_age):
                reasons.append("FRESHNESS_REQUIREMENT_NOT_MET")
    return sorted(set(reasons))


def _normalize_scope(scope: dict[str, Any] | None) -> dict[str, set[str]]:
    source = scope if isinstance(scope, dict) else {}
    return {
        key: {str(value).rstrip("/") for value in source.get(key, []) if value not in (None, "")}
        for key in ("repositories", "paths", "modules", "runtime_surfaces", "evidence_responsibilities")
    }


def _path_overlap(left: str, right: str) -> bool:
    left = left.rstrip("/")
    right = right.rstrip("/")
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def scopes_collide(left: dict[str, Any] | None, right: dict[str, Any] | None) -> bool:
    """Return true only for overlapping mutation/evidence responsibility scopes."""
    a = _normalize_scope(left)
    b = _normalize_scope(right)
    repository_overlap = not a["repositories"] or not b["repositories"] or bool(a["repositories"] & b["repositories"])
    if not repository_overlap:
        return False
    if a["modules"] & b["modules"]:
        return True
    if a["runtime_surfaces"] & b["runtime_surfaces"]:
        return True
    if a["evidence_responsibilities"] & b["evidence_responsibilities"]:
        return True
    return any(_path_overlap(x, y) for x in a["paths"] for y in b["paths"])


def _gap_for(
    predicate: dict[str, Any],
    candidate_evidence: list[dict[str, Any]],
    rejection_map: dict[str, list[str]],
    collisions: list[dict[str, Any]],
) -> dict[str, Any]:
    collision_refs = [str(item.get("claim_id")) for item in collisions if item.get("claim_id")]
    reasons = sorted({reason for values in rejection_map.values() for reason in values})
    state = predicate.get("state")
    if not candidate_evidence and state != "SATISFIED":
        reasons.append("NO_QUALIFYING_EVIDENCE_OBSERVED")
    action = "Consume qualifying authoritative evidence; do not repeat the check."
    if state == "IN_PROGRESS":
        action = "Consume the active producer task result when emitted; do not duplicate its production scope."
    elif collisions:
        action = "Do not mutate the colliding scope; consume the active claim output or select non-overlapping adjacent work."
    elif not candidate_evidence:
        action = "Request only the declared missing observation from the authoritative producer; do not infer it from adjacent artifacts."
    return {
        "predicate_id": predicate.get("predicate_id"),
        "existing_evidence_refs": [str(item.get("ref")) for item in candidate_evidence if item.get("ref")],
        "rejected_because": sorted(set(reasons)),
        "missing_observation": predicate.get("description") or predicate.get("predicate_id"),
        "required_producer": predicate.get("authoritative_producer"),
        "required_output_ref": predicate.get("expected_output_ref"),
        "required_schema": predicate.get("required_schema"),
        "required_fields": list(predicate.get("required_fields") or []),
        "required_freshness": predicate.get("max_age_seconds"),
        "collision_refs": collision_refs,
        "action_without_collision": action,
    }


def review_coordination_preflight(
    *,
    ledger: dict[str, Any],
    task: dict[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    """Resolve reusable evidence, adjacency and mutation collisions without granting authority."""
    current = _now(now)
    reasons: list[str] = []
    if ledger.get("schema") != LEDGER_SCHEMA:
        return {
            "schema": PREFLIGHT_SCHEMA,
            "task_id": task.get("task_id"),
            "verdict": "BLOCK_COORDINATION",
            "reasons": ["LEDGER_SCHEMA_INVALID"],
            "authority_effect": "NONE",
            "resolved_predicates": [],
            "gaps": [],
            "collisions": [],
            "newly_unblocked_tasks": [],
        }

    task_id = str(task.get("task_id") or "")
    ledger_tasks = {str(item.get("task_id")): item for item in ledger.get("tasks", []) if item.get("task_id")}
    task_record = ledger_tasks.get(task_id)
    if task_record is None:
        reasons.append("TASK_NOT_REGISTERED_IN_COORDINATION_LEDGER")
        task_record = task

    required_ids = list(task_record.get("required_predicates") or task.get("required_predicates") or [])
    predicates = {str(item.get("predicate_id")): item for item in ledger.get("predicates", []) if item.get("predicate_id")}
    evidence_rows = list(ledger.get("evidence", []))
    claims = list(ledger.get("claims", []))

    mutation_scope = task_record.get("mutation_scope") or task.get("mutation_scope") or {}
    expected_blast = task_record.get("expected_blast_radius") or task.get("expected_blast_radius")
    autonomous = bool(task_record.get("autonomous_augmentation", task.get("autonomous_augmentation", False)))
    if autonomous and not expected_blast:
        reasons.append("EXPECTED_BLAST_RADIUS_NOT_DECLARED")

    collisions = [
        claim for claim in claims
        if claim.get("state") in ACTIVE_CLAIM_STATES
        and str(claim.get("task_id") or "") != task_id
        and scopes_collide(mutation_scope, claim.get("scope"))
    ]
    if collisions:
        reasons.append("ACTIVE_SCOPE_COLLISION")

    resolved: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    for predicate_id in required_ids:
        predicate = predicates.get(str(predicate_id))
        if predicate is None:
            reasons.append(f"PREDICATE_NOT_REGISTERED:{predicate_id}")
            gaps.append({
                "predicate_id": predicate_id,
                "existing_evidence_refs": [],
                "rejected_because": ["PREDICATE_NOT_REGISTERED"],
                "missing_observation": predicate_id,
                "required_producer": "UNKNOWN",
                "required_output_ref": None,
                "required_schema": None,
                "required_fields": [],
                "required_freshness": None,
                "collision_refs": [str(item.get("claim_id")) for item in collisions if item.get("claim_id")],
                "action_without_collision": "Register the predicate and authoritative producer before performing a new check.",
            })
            continue
        if predicate.get("state") not in PREDICATE_STATES:
            reasons.append(f"PREDICATE_STATE_INVALID:{predicate_id}")
        candidates = [row for row in evidence_rows if row.get("predicate_id") == predicate_id]
        rejection_map: dict[str, list[str]] = {}
        qualifying: list[dict[str, Any]] = []
        for row in candidates:
            rejection = _evidence_rejection_reasons(predicate, row, current)
            if rejection:
                rejection_map[str(row.get("evidence_id") or row.get("ref") or "UNKNOWN")] = rejection
            else:
                qualifying.append(row)
        satisfied = predicate.get("state") == "SATISFIED" and bool(qualifying)
        resolved.append({
            "predicate_id": predicate_id,
            "declared_state": predicate.get("state"),
            "satisfied": satisfied,
            "qualifying_evidence_refs": [row.get("ref") for row in qualifying],
            "rejected_evidence": rejection_map,
            "authoritative_producer": predicate.get("authoritative_producer"),
        })
        if not satisfied:
            reasons.append(f"PREDICATE_NOT_SATISFIED:{predicate_id}")
            gaps.append(_gap_for(predicate, candidates, rejection_map, collisions))

    newly_unblocked: list[str] = []
    satisfied_ids = {item["predicate_id"] for item in resolved if item["satisfied"]}
    for other_id, other in ledger_tasks.items():
        if other_id == task_id:
            continue
        required = set(other.get("required_predicates") or [])
        if required and required.issubset(satisfied_ids):
            newly_unblocked.append(other_id)

    verdict = "ADMIT_COORDINATION" if not reasons else "BLOCK_COORDINATION"
    if reasons and all(reason.startswith("TASK_NOT_REGISTERED") for reason in reasons):
        verdict = "UPDATE_COORDINATION"
    return {
        "schema": PREFLIGHT_SCHEMA,
        "task_id": task_id,
        "goal_id": task_record.get("goal_id") or task.get("goal_id"),
        "verdict": verdict,
        "reasons": sorted(set(reasons)) or ["COORDINATION_PREFLIGHT_PASS"],
        "authority_effect": "NONE",
        "resolved_predicates": resolved,
        "gaps": gaps,
        "collisions": [
            {"claim_id": item.get("claim_id"), "task_id": item.get("task_id"), "scope": item.get("scope")}
            for item in collisions
        ],
        "newly_unblocked_tasks": sorted(set(newly_unblocked)),
    }


__all__ = [
    "LEDGER_SCHEMA",
    "PREFLIGHT_SCHEMA",
    "PREDICATE_STATES",
    "review_coordination_preflight",
    "scopes_collide",
]
