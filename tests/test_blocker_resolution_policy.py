import unittest

from heartbeat_runtime.blocker_policy import BlockerPolicyError, validate_worker_response_blocker


class BlockerResolutionPolicyTests(unittest.TestCase):
    def test_third_party_dependency_cannot_be_blocked(self):
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
        with self.assertRaisesRegex(BlockerPolicyError, "third-party dependency may not be a BLOCKED"):
            validate_worker_response_blocker(response)

    def test_blocked_requires_solution_contract(self):
        with self.assertRaisesRegex(BlockerPolicyError, "requires blocker resolution contract"):
            validate_worker_response_blocker({"state": "BLOCKED"})

    def test_internal_blocker_requires_workaround_and_next_action(self):
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

    def test_third_party_active_workaround_is_allowed(self):
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


if __name__ == "__main__":
    unittest.main()
