from __future__ import annotations

from typing import Any


class BlockerPolicyError(RuntimeError):
    pass


def validate_worker_response_blocker(response: dict[str, Any]) -> None:
    """Enforce workaround-first semantics for worker responses.

    BLOCKED is legal only for a non-third-party constraint and only when the
    worker provides a concrete resolution contract. Third-party conditions are
    solution-selection events and must remain ACTIVE while an alternate path is
    pursued.
    """
    state = str(response.get("state", ""))
    blocker = response.get("blocker")

    if state != "BLOCKED":
        if isinstance(blocker, dict) and blocker.get("dependency_class") == "THIRD_PARTY":
            if blocker.get("solution_required") is not True:
                raise BlockerPolicyError("third-party condition must require a solution/workaround")
            candidates = blocker.get("workaround_candidates")
            if not isinstance(candidates, list) or not any(isinstance(x, str) and x.strip() for x in candidates):
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
    candidates = blocker.get("workaround_candidates")
    if not isinstance(candidates, list) or not any(isinstance(x, str) and x.strip() for x in candidates):
        raise BlockerPolicyError("BLOCKED worker response requires at least one workaround candidate")
    if not isinstance(blocker.get("next_solution_action"), str) or not blocker["next_solution_action"].strip():
        raise BlockerPolicyError("BLOCKED worker response requires blocker.next_solution_action")
