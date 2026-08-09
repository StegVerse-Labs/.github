from heartbeat_runtime.blocker_policy import BlockerPolicyError, validate_worker_response_blocker


def test_third_party_dependency_cannot_be_blocked():
    response = {
        "state": "BLOCKED",
        "blocker": {
            "dependency_class": "THIRD_PARTY",
            "problem_statement": "provider credential missing",
            "solution_required": True,
            "workaround_candidates": ["use sovereign carrier"],
            "next_solution_action": "activate sovereign carrier",
        },
    }
    try:
        validate_worker_response_blocker(response)
    except BlockerPolicyError as exc:
        assert "third-party dependency may not be a BLOCKED" in str(exc)
    else:
        raise AssertionError("third-party dependency was incorrectly accepted as BLOCKED")


def test_blocked_requires_solution_contract():
    try:
        validate_worker_response_blocker({"state": "BLOCKED"})
    except BlockerPolicyError as exc:
        assert "requires blocker resolution contract" in str(exc)
    else:
        raise AssertionError("passive BLOCKED response was incorrectly accepted")


def test_internal_blocker_requires_workaround_and_next_action():
    response = {
        "state": "BLOCKED",
        "blocker": {
            "dependency_class": "INTERNAL_CAPABILITY",
            "problem_statement": "missing native capability",
            "solution_required": True,
            "workaround_candidates": ["build alternate native capability"],
            "next_solution_action": "implement alternate native capability",
        },
    }
    validate_worker_response_blocker(response)


def test_third_party_active_workaround_is_allowed():
    response = {
        "state": "ACTIVE",
        "transition_id": "THIRD_PARTY_WORKAROUND_REQUIRED",
        "blocker": {
            "dependency_class": "THIRD_PARTY",
            "problem_statement": "provider path unavailable",
            "solution_required": True,
            "workaround_candidates": ["use StegVerse-owned path"],
            "next_solution_action": "activate StegVerse-owned path",
        },
    }
    validate_worker_response_blocker(response)
