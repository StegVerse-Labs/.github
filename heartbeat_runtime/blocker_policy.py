from __future__ import annotations

from typing import Any
import base64
import json


class BlockerPolicyError(RuntimeError):
    pass


RESOLUTION_EVIDENCE_PREFIX = "resolution-contract:v1:"


def _nonempty_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _append_resolution_contract(response: dict[str, Any], blocker: dict[str, Any]) -> None:
    """Carry the constraint into the heartbeat without adding a new response schema.

    ProcessWorkerAdapter already transports string evidence references into the
    canonical worker task. Encoding the resolution contract as a deterministic
    evidence reference lets the next heartbeat runtime derive a registered
    resolution/escalation task without granting the worker control-plane write
    authority.
    """
    contract = {
        "trigger_type": str(blocker.get("trigger_type") or "BLOCKED_CONDITION"),
        "dependency_class": str(blocker["dependency_class"]),
        "problem_statement": str(blocker["problem_statement"]).strip(),
        "solution_required": True,
        "workaround_candidates": _nonempty_strings(blocker.get("workaround_candidates")),
        "next_solution_action": str(blocker["next_solution_action"]).strip(),
        "resolvable_by_current_worker": bool(blocker.get("resolvable_by_current_worker", True)),
        "escalation_target": blocker.get("escalation_target"),
        "required_capabilities": _nonempty_strings(blocker.get("required_capabilities")),
        "completion_evidence": _nonempty_strings(blocker.get("completion_evidence")),
        "same_level_retry_authorized": bool(blocker.get("same_level_retry_authorized", False)),
        "workaround_candidate_changed": bool(blocker.get("workaround_candidate_changed", False)),
    }
    raw = json.dumps(contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    ref = RESOLUTION_EVIDENCE_PREFIX + encoded
    evidence = response.setdefault("evidence_refs", [])
    if not isinstance(evidence, list):
        raise BlockerPolicyError("worker response evidence_refs must be a list when present")
    if ref not in evidence:
        evidence.append(ref)


def validate_worker_response_blocker(response: dict[str, Any]) -> None:
    """Enforce active solution derivation for worker constraint responses.

    A fail-closed consequence remains refused, but the governing goal does not
    become passive. Any worker response represented as BLOCKED must carry enough
    information for the heartbeat runtime to derive a distinct resolution task.
    If the worker declares that it cannot resolve the constraint, an escalation
    target is required and the runtime advances the task to that level.
    """
    state = str(response.get("state", ""))
    blocker = response.get("blocker")

    if state != "BLOCKED":
        if isinstance(blocker, dict) and blocker.get("dependency_class") == "THIRD_PARTY":
            if blocker.get("solution_required") is not True:
                raise BlockerPolicyError("third-party condition must require a solution/workaround")
            if not _nonempty_strings(blocker.get("workaround_candidates")):
                raise BlockerPolicyError("third-party condition requires at least one workaround candidate")
        return

    if not isinstance(blocker, dict):
        raise BlockerPolicyError("BLOCKED worker response requires blocker resolution contract")

    dependency_class = blocker.get("dependency_class")
    if dependency_class == "THIRD_PARTY":
        raise BlockerPolicyError("third-party dependency may not be a BLOCKED worker state; pursue a workaround as ACTIVE")
    if not isinstance(dependency_class, str) or not dependency_class:
        raise BlockerPolicyError("BLOCKED worker response requires blocker.dependency_class")
    if not isinstance(blocker.get("problem_statement"), str) or not blocker["problem_statement"].strip():
        raise BlockerPolicyError("BLOCKED worker response requires blocker.problem_statement")
    if blocker.get("solution_required") is not True:
        raise BlockerPolicyError("BLOCKED worker response must state solution_required=true")
    if not _nonempty_strings(blocker.get("workaround_candidates")):
        raise BlockerPolicyError("BLOCKED worker response requires at least one workaround candidate")
    if not isinstance(blocker.get("next_solution_action"), str) or not blocker["next_solution_action"].strip():
        raise BlockerPolicyError("BLOCKED worker response requires blocker.next_solution_action")

    resolvable = blocker.get("resolvable_by_current_worker", True)
    if not isinstance(resolvable, bool):
        raise BlockerPolicyError("blocker.resolvable_by_current_worker must be boolean when present")
    if resolvable is False:
        target = blocker.get("escalation_target")
        if target is not None and (not isinstance(target, str) or not target.strip()):
            raise BlockerPolicyError("blocker.escalation_target must be a non-empty string when present")

    _append_resolution_contract(response, blocker)
