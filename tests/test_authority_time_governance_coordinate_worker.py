import unittest

from workers.authority_time_governance_coordinate_worker import evaluate_declaration


class AuthorityTimeGovernanceCoordinateTests(unittest.TestCase):
    def test_non_authorizing_observations_pass_when_separate_authority_exists(self):
        result = evaluate_declaration(
            {
                "wall_clock": "2026-09-07T12:13:00-05:00",
                "heartbeat": "HB32+derived",
                "observer_freshness": "CURRENT",
                "workflow_success": True,
                "carrier_correctness": True,
                "protected_boundary": True,
                "requests_transition": True,
                "authority_source": "StegCore/StegGate",
                "disposition": "ALLOW",
            }
        )
        self.assertEqual("PASS", result["state"])
        self.assertEqual([], result["violations"])

    def test_heartbeat_cannot_be_promoted_to_authority(self):
        result = evaluate_declaration({"heartbeat_grants_authority": True})
        self.assertEqual("FAIL_CLOSED", result["state"])
        self.assertEqual(
            "NON_AUTHORIZING_SIGNAL_PROMOTED_TO_AUTHORITY",
            result["violations"][0]["code"],
        )

    def test_wall_clock_cannot_be_promoted_to_authority(self):
        result = evaluate_declaration({"wall_clock_grants_authority": True})
        self.assertEqual("FAIL_CLOSED", result["state"])

    def test_workflow_success_cannot_be_promoted_to_authority(self):
        result = evaluate_declaration({"workflow_success_grants_authority": True})
        self.assertEqual("FAIL_CLOSED", result["state"])

    def test_carrier_correctness_cannot_be_promoted_to_authority(self):
        result = evaluate_declaration({"carrier_correctness_grants_authority": True})
        self.assertEqual("FAIL_CLOSED", result["state"])

    def test_observer_freshness_cannot_be_promoted_to_authority(self):
        result = evaluate_declaration({"observer_freshness_grants_authority": True})
        self.assertEqual("FAIL_CLOSED", result["state"])

    def test_protected_boundary_requires_named_authority(self):
        result = evaluate_declaration(
            {
                "protected_boundary": True,
                "requests_transition": True,
                "disposition": "ALLOW",
            }
        )
        self.assertEqual("FAIL_CLOSED", result["state"])
        codes = {item["code"] for item in result["violations"]}
        self.assertIn("PROTECTED_BOUNDARY_AUTHORITY_MISSING_OR_UNKNOWN", codes)
        self.assertIn("ALLOW_WITHOUT_SEPARATE_AUTHORITY", codes)

    def test_human_review_timeout_must_not_silently_allow(self):
        result = evaluate_declaration({"human_review_timeout_result": "ALLOW"})
        self.assertEqual("FAIL_CLOSED", result["state"])
        self.assertEqual(
            "HUMAN_TIMEOUT_MUST_NOT_SILENTLY_ALLOW",
            result["violations"][0]["code"],
        )

    def test_review_is_preserved_without_temporal_promotion(self):
        result = evaluate_declaration(
            {
                "protected_boundary": True,
                "requests_transition": True,
                "authority_source": "InTr/Interlock",
                "disposition": "REVIEW",
                "wall_clock": "later",
                "heartbeat": "advanced",
            }
        )
        self.assertEqual("PASS", result["state"])

    def test_receipt_is_deterministic_for_equivalent_input(self):
        left = evaluate_declaration({"heartbeat": "HB42", "workflow_success": True})
        right = evaluate_declaration({"workflow_success": True, "heartbeat": "HB42"})
        self.assertEqual(left["input_sha256"], right["input_sha256"])
        self.assertEqual(left["receipt_sha256"], right["receipt_sha256"])


if __name__ == "__main__":
    unittest.main()
