from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import hashlib
import json

SNAPSHOT_SCHEMA = "stegverse.heartbeat-reference-snapshot/v1"
POLICY_SCHEMA = "stegverse.heartbeat-reference-snapshot-policy/v1"
REACQUISITION_RULE = "GATE_PASSBAND_DERIVED"


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _json_path(value: Any, path: list[str]) -> Any:
    current = value
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _compare(observed: Any, operator: str, expected: Any) -> bool:
    if operator == "eq":
        return observed == expected
    if operator == "ne":
        return observed != expected
    if operator == "gte":
        return isinstance(observed, (int, float)) and isinstance(expected, (int, float)) and observed >= expected
    if operator == "is_none":
        return observed is None
    if operator == "not_none":
        return observed is not None
    raise ValueError(f"unsupported snapshot check operator: {operator}")


def _registry_task(registry: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    for task in registry.get("tasks", []):
        if isinstance(task, dict) and task.get("task_id") == task_id:
            return task
    return None


def evaluate_required_states(root: Path, policy: dict[str, Any]) -> list[dict[str, Any]]:
    if policy.get("schema") != POLICY_SCHEMA:
        raise ValueError("unsupported reference snapshot policy schema")
    if policy.get("reacquisition_rule") != REACQUISITION_RULE:
        raise ValueError("reference snapshot policy must use GATE_PASSBAND_DERIVED")

    cache: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    for requirement in policy.get("required_states", []):
        if not isinstance(requirement, dict):
            raise ValueError("required state entry must be an object")
        state_id = requirement.get("state_id")
        checks = requirement.get("checks") or []
        if not isinstance(state_id, str) or not state_id or not isinstance(checks, list) or not checks:
            raise ValueError("required state needs state_id and checks")
        observations: list[dict[str, Any]] = []
        complete = True
        evidence_refs: list[str] = []

        for check in checks:
            if not isinstance(check, dict):
                raise ValueError(f"invalid check for {state_id}")
            source_ref = check.get("source_ref")
            check_type = check.get("type")
            if not isinstance(source_ref, str) or not source_ref:
                raise ValueError(f"missing source_ref for {state_id}")
            path = root / source_ref
            if source_ref not in cache:
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    loaded = {}
                cache[source_ref] = loaded if isinstance(loaded, dict) else {}
            source = cache[source_ref]

            if check_type == "json_path":
                key_path = check.get("path") or []
                if not isinstance(key_path, list) or not all(isinstance(item, str) for item in key_path):
                    raise ValueError(f"invalid json path for {state_id}")
                observed = _json_path(source, key_path)
            elif check_type == "registry_task_field":
                task_id = check.get("task_id")
                field = check.get("field")
                if not isinstance(task_id, str) or not isinstance(field, str):
                    raise ValueError(f"invalid registry task check for {state_id}")
                task = _registry_task(source, task_id)
                observed = task.get(field) if isinstance(task, dict) else None
            else:
                raise ValueError(f"unsupported check type for {state_id}: {check_type}")

            operator = str(check.get("operator") or "eq")
            expected = check.get("expected")
            passed = _compare(observed, operator, expected)
            complete = complete and passed
            evidence_refs.append(source_ref)
            observations.append({
                "type": check_type,
                "source_ref": source_ref,
                "path": deepcopy(check.get("path")),
                "task_id": check.get("task_id"),
                "field": check.get("field"),
                "operator": operator,
                "expected": expected,
                "observed": observed,
                "passed": passed,
            })

        results.append({
            "state_id": state_id,
            "description": requirement.get("description"),
            "complete": complete,
            "observations": observations,
            "evidence_refs": sorted(set(evidence_refs)),
        })
    return results


def _snapshot_payload(
    *,
    policy: dict[str, Any],
    carrier: dict[str, Any],
    required_states: list[dict[str, Any]],
    previous: dict[str, Any] | None,
    acquired_at: str,
    reason: str,
) -> dict[str, Any]:
    epoch = carrier.get("epoch")
    generation = carrier.get("generation")
    if not isinstance(epoch, int) or not isinstance(generation, int):
        raise ValueError("carrier snapshot requires integer epoch and generation")
    previous_epoch = None
    previous_sha = None
    previous_id = None
    if isinstance(previous, dict):
        previous_epoch = ((previous.get("reference") or {}).get("carrier_epoch"))
        previous_sha = previous.get("snapshot_sha256")
        previous_id = previous.get("snapshot_id")
    reference_delta = epoch - previous_epoch if isinstance(previous_epoch, int) else 0
    passband = int(policy.get("passband_width_references", 1))
    if passband < 1:
        raise ValueError("passband_width_references must be >= 1")

    complete_count = sum(1 for item in required_states if item.get("complete") is True)
    required_count = len(required_states)
    pending_count = required_count - complete_count
    gate_state = "CLOSED" if required_count > 0 and pending_count == 0 else "OPEN"
    state_fingerprint = canonical_sha256(required_states)

    return {
        "schema": SNAPSHOT_SCHEMA,
        "monitor_id": policy["monitor_id"],
        "goal_id": policy["goal_id"],
        "policy_revision": int(policy.get("revision", 1)),
        "acquired_at": acquired_at,
        "snapshot_id": f"{policy['monitor_id']}:{epoch}:{state_fingerprint[:16]}",
        "previous_snapshot_id": previous_id,
        "previous_snapshot_sha256": previous_sha,
        "reference": {
            "carrier_epoch": epoch,
            "carrier_generation": generation,
            "reference_frame": carrier.get("reference_frame"),
            "carrier_frequency_rule_observed": carrier.get("frequency_rule"),
            "snapshot_is_observation_only": True,
        },
        "reacquisition": {
            "rule": REACQUISITION_RULE,
            "passband_width_references": passband,
            "reference_delta_from_previous": reference_delta,
            "reason": reason,
            "carrier_progression_effect": "NONE",
        },
        "gate": {
            "state": gate_state,
            "required_count": required_count,
            "complete_count": complete_count,
            "pending_count": pending_count,
            "completion_claim_requires_evidence": True,
        },
        "required_state_fingerprint": state_fingerprint,
        "required_states": required_states,
        "authority": {
            "authority_effect": "NONE",
            "heartbeat_grants_execution_authority": False,
            "snapshot_grants_execution_authority": False,
            "snapshot_grants_claim_or_fence_authority": False,
            "snapshot_controls_carrier_progression": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": False,
        },
    }


def decide_reacquisition(
    *,
    policy: dict[str, Any],
    carrier: dict[str, Any],
    required_states: list[dict[str, Any]],
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    current_epoch = carrier.get("epoch")
    if not isinstance(current_epoch, int):
        raise ValueError("carrier epoch is required")
    current_fingerprint = canonical_sha256(required_states)
    pending = any(item.get("complete") is not True for item in required_states)

    if not isinstance(previous, dict):
        return {"reacquire": True, "reason": "INITIAL", "state_changed": True, "passband_crossed": False}

    if (previous.get("gate") or {}).get("state") == "CLOSED" and not pending:
        return {"reacquire": False, "reason": "NONE_TERMINAL", "state_changed": False, "passband_crossed": False}

    previous_epoch = (previous.get("reference") or {}).get("carrier_epoch")
    if not isinstance(previous_epoch, int):
        return {"reacquire": True, "reason": "REFERENCE_REPAIR", "state_changed": True, "passband_crossed": False}
    delta = current_epoch - previous_epoch
    if delta < 0:
        raise ValueError("carrier reference regressed relative to prior snapshot")

    previous_fingerprint = previous.get("required_state_fingerprint")
    state_changed = previous_fingerprint != current_fingerprint
    passband = int(policy.get("passband_width_references", 1))
    passband_crossed = pending and delta >= passband

    if not pending and ((previous.get("gate") or {}).get("state") != "CLOSED" or state_changed):
        return {"reacquire": True, "reason": "TERMINAL_GATE_CLOSED", "state_changed": state_changed, "passband_crossed": passband_crossed}
    if state_changed:
        return {"reacquire": True, "reason": "REQUIRED_STATE_CHANGED", "state_changed": True, "passband_crossed": passband_crossed}
    if passband_crossed:
        return {"reacquire": True, "reason": "PASSBAND_CROSSED", "state_changed": False, "passband_crossed": True}
    return {"reacquire": False, "reason": "WITHIN_PASSBAND_NO_STATE_CHANGE", "state_changed": False, "passband_crossed": False}


def reacquire_reference_snapshot(
    *,
    policy: dict[str, Any],
    carrier: dict[str, Any],
    required_states: list[dict[str, Any]],
    previous: dict[str, Any] | None,
    acquired_at: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    decision = decide_reacquisition(policy=policy, carrier=carrier, required_states=required_states, previous=previous)
    if not decision["reacquire"]:
        return None, decision
    snapshot = _snapshot_payload(
        policy=policy,
        carrier=carrier,
        required_states=required_states,
        previous=previous,
        acquired_at=acquired_at,
        reason=decision["reason"],
    )
    payload = dict(snapshot)
    snapshot["snapshot_sha256"] = canonical_sha256(payload)
    return snapshot, decision


__all__ = [
    "SNAPSHOT_SCHEMA",
    "POLICY_SCHEMA",
    "REACQUISITION_RULE",
    "canonical_sha256",
    "evaluate_required_states",
    "decide_reacquisition",
    "reacquire_reference_snapshot",
]
