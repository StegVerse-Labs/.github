from __future__ import annotations

from datetime import datetime, timezone
import unittest

from heartbeat_runtime.coordination_graph import review_coordination_preflight


NOW = datetime(2026, 9, 6, 6, 30, tzinfo=timezone.utc)


class RequiredFieldValueTests(unittest.TestCase):
    def ledger(self):
        return {
            "schema": "stegverse.cross-task-coordination-ledger/v1",
            "authority": {
                "coordination_authority": "StegVerse-Labs/.github",
                "runtime_truth_authority_effect": "NONE",
                "credential_authority": "TV/TVC",
                "github_token_runtime_authority": "NONE",
            },
            "goals": [{"goal_id": "G"}],
            "tasks": [{
                "task_id": "T",
                "goal_id": "G",
                "required_predicates": ["P"],
                "mutation_scope": {"repositories": ["StegVerse-Labs/.github"], "paths": ["control/x"]},
            }],
            "predicates": [{
                "predicate_id": "P",
                "state": "SATISFIED",
                "authoritative_producer": "consumer",
                "required_fields": ["terminal", "claim.id", "claim.fence"],
                "required_field_values": {
                    "terminal": True,
                    "claim.id": "CLAIM-G18",
                    "claim.fence": 18,
                },
            }],
            "evidence": [{
                "evidence_id": "E",
                "predicate_id": "P",
                "producer": "consumer",
                "ref": "receipts/example.json",
                "fields": {
                    "terminal": True,
                    "claim": {"id": "CLAIM-G18", "fence": 18},
                },
                "authority_effect": "EVIDENCE_ONLY",
            }],
            "claims": [],
            "gaps": [],
        }

    def review(self, ledger):
        return review_coordination_preflight(ledger=ledger, task={"task_id": "T"}, now=NOW)

    def test_exact_values_qualify(self):
        result = self.review(self.ledger())
        self.assertEqual(result["verdict"], "ADMIT_COORDINATION")
        self.assertTrue(result["resolved_predicates"][0]["satisfied"])

    def test_false_does_not_satisfy_required_true(self):
        ledger = self.ledger()
        ledger["evidence"][0]["fields"]["terminal"] = False
        result = self.review(ledger)
        self.assertEqual(result["verdict"], "BLOCK_COORDINATION")
        self.assertIn("REQUIRED_FIELD_VALUE_MISMATCH:terminal", result["gaps"][0]["rejected_because"])

    def test_nested_wrong_value_fails_closed(self):
        ledger = self.ledger()
        ledger["evidence"][0]["fields"]["claim"]["fence"] = 19
        result = self.review(ledger)
        self.assertIn("REQUIRED_FIELD_VALUE_MISMATCH:claim.fence", result["gaps"][0]["rejected_because"])
        self.assertEqual(result["gaps"][0]["required_field_values"]["claim.fence"], 18)

    def test_missing_required_value_path_fails_closed(self):
        ledger = self.ledger()
        del ledger["evidence"][0]["fields"]["claim"]["id"]
        result = self.review(ledger)
        self.assertIn("REQUIRED_FIELD_VALUE_MISMATCH:claim.id", result["gaps"][0]["rejected_because"])


if __name__ == "__main__":
    unittest.main()
