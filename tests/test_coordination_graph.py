from __future__ import annotations

from datetime import datetime, timezone
import unittest

from heartbeat_runtime.coordination_graph import predicate_equivalence_key, review_coordination_preflight, scopes_collide


NOW = datetime(2026, 9, 4, 21, 50, tzinfo=timezone.utc)


class CoordinationGraphTests(unittest.TestCase):
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
            "tasks": [
                {
                    "task_id": "T",
                    "goal_id": "G",
                    "autonomous_augmentation": True,
                    "required_predicates": ["P"],
                    "mutation_scope": {"repositories": ["O/R"], "paths": ["src/a"]},
                    "expected_blast_radius": {"repositories": ["O/R"], "paths": ["src/a"]},
                },
                {
                    "task_id": "DOWNSTREAM",
                    "goal_id": "G",
                    "required_predicates": ["P"],
                    "mutation_scope": {"repositories": ["O/R"], "paths": ["src/b"]},
                    "expected_blast_radius": {"repositories": ["O/R"], "paths": ["src/b"]},
                },
            ],
            "predicates": [
                {
                    "predicate_id": "P",
                    "semantic_predicate_id": "resident_request_consumed",
                    "subject_binding": {"request_id": "REQ-1", "target": "worker-a"},
                    "state": "SATISFIED",
                    "authoritative_producer": "receiver",
                    "required_schema": "receipt/v1",
                    "required_scope": "node-1",
                    "required_execution_instance": "exec-1",
                    "required_fields": ["accepted", "transition.id"],
                    "max_age_seconds": 3600,
                    "expected_output_ref": "receipts/p.latest.json",
                }
            ],
            "evidence": [
                {
                    "evidence_id": "E",
                    "predicate_id": "P",
                    "subject_binding": {"target": "worker-a", "request_id": "REQ-1"},
                    "producer": "receiver",
                    "ref": "receipts/p.json",
                    "schema": "receipt/v1",
                    "scope": "node-1",
                    "execution_instance": "exec-1",
                    "observed_at": "2026-09-04T21:45:00+00:00",
                    "fields": {"accepted": True, "transition": {"id": "x"}},
                    "authority_effect": "EVIDENCE_ONLY",
                }
            ],
            "claims": [],
            "gaps": [],
        }

    def test_qualifying_authoritative_evidence_admits(self):
        result = review_coordination_preflight(ledger=self.ledger(), task={"task_id": "T"}, now=NOW)
        self.assertEqual(result["verdict"], "ADMIT_COORDINATION")
        self.assertTrue(result["resolved_predicates"][0]["satisfied"])
        self.assertEqual(result["resolved_predicates"][0]["qualifying_evidence_refs"], ["receipts/p.json"])
        self.assertEqual(result["resolved_predicates"][0]["semantic_predicate_id"], "resident_request_consumed")
        self.assertEqual(result["resolved_predicates"][0]["subject_binding"]["request_id"], "REQ-1")
        self.assertEqual(result["newly_unblocked_tasks"], ["DOWNSTREAM"])
        self.assertEqual(result["authority_effect"], "NONE")

    def test_wrong_producer_does_not_satisfy_predicate(self):
        ledger = self.ledger()
        ledger["evidence"][0]["producer"] = "deployment"
        result = review_coordination_preflight(ledger=ledger, task={"task_id": "T"}, now=NOW)
        self.assertEqual(result["verdict"], "BLOCK_COORDINATION")
        self.assertIn("AUTHORITATIVE_PRODUCER_MISMATCH", result["gaps"][0]["rejected_because"])

    def test_subject_binding_mismatch_does_not_cross_satisfy(self):
        ledger = self.ledger()
        ledger["evidence"][0]["subject_binding"]["request_id"] = "REQ-OTHER"
        result = review_coordination_preflight(ledger=ledger, task={"task_id": "T"}, now=NOW)
        self.assertEqual(result["verdict"], "BLOCK_COORDINATION")
        self.assertIn("SUBJECT_BINDING_MISMATCH", result["gaps"][0]["rejected_because"])

    def test_equivalence_requires_same_semantic_id_and_subject(self):
        a = {"predicate_id": "P1", "semantic_predicate_id": "resident_request_consumed", "subject_binding": {"request_id": "R1"}}
        b = {"predicate_id": "P2", "semantic_predicate_id": "resident_request_consumed", "subject_binding": {"request_id": "R1"}}
        c = {"predicate_id": "P3", "semantic_predicate_id": "resident_request_consumed", "subject_binding": {"request_id": "R2"}}
        self.assertEqual(predicate_equivalence_key(a), predicate_equivalence_key(b))
        self.assertNotEqual(predicate_equivalence_key(a), predicate_equivalence_key(c))

    def test_stale_evidence_is_rejected(self):
        ledger = self.ledger()
        ledger["evidence"][0]["observed_at"] = "2026-09-04T18:00:00+00:00"
        result = review_coordination_preflight(ledger=ledger, task={"task_id": "T"}, now=NOW)
        self.assertIn("FRESHNESS_REQUIREMENT_NOT_MET", result["gaps"][0]["rejected_because"])

    def test_active_overlapping_claim_blocks(self):
        ledger = self.ledger()
        ledger["claims"].append({
            "claim_id": "C2",
            "task_id": "OTHER",
            "state": "ACTIVE",
            "scope": {"repositories": ["O/R"], "paths": ["src/a/file.py"]},
        })
        result = review_coordination_preflight(ledger=ledger, task={"task_id": "T"}, now=NOW)
        self.assertEqual(result["verdict"], "BLOCK_COORDINATION")
        self.assertIn("ACTIVE_SCOPE_COLLISION", result["reasons"])
        self.assertEqual(result["collisions"][0]["claim_id"], "C2")

    def test_non_overlapping_claim_does_not_block(self):
        ledger = self.ledger()
        ledger["claims"].append({
            "claim_id": "C2",
            "task_id": "OTHER",
            "state": "ACTIVE",
            "scope": {"repositories": ["O/R"], "paths": ["docs/unrelated.md"]},
        })
        result = review_coordination_preflight(ledger=ledger, task={"task_id": "T"}, now=NOW)
        self.assertEqual(result["verdict"], "ADMIT_COORDINATION")

    def test_missing_blast_radius_blocks_autonomous_augmentation(self):
        ledger = self.ledger()
        del ledger["tasks"][0]["expected_blast_radius"]
        result = review_coordination_preflight(ledger=ledger, task={"task_id": "T"}, now=NOW)
        self.assertIn("EXPECTED_BLAST_RADIUS_NOT_DECLARED", result["reasons"])

    def test_in_progress_predicate_returns_collision_safe_action(self):
        ledger = self.ledger()
        ledger["predicates"][0]["state"] = "IN_PROGRESS"
        ledger["evidence"] = []
        result = review_coordination_preflight(ledger=ledger, task={"task_id": "T"}, now=NOW)
        self.assertIn("active producer task result", result["gaps"][0]["action_without_collision"])

    def test_scope_collision_helpers(self):
        self.assertTrue(scopes_collide(
            {"repositories": ["O/R"], "paths": ["src/a"]},
            {"repositories": ["O/R"], "paths": ["src/a/b.py"]},
        ))
        self.assertFalse(scopes_collide(
            {"repositories": ["O/R"], "paths": ["src/a"]},
            {"repositories": ["O/R"], "paths": ["src/z"]},
        ))
        self.assertFalse(scopes_collide(
            {"repositories": ["O/R"], "paths": ["src/a"]},
            {"repositories": ["X/Y"], "paths": ["src/a"]},
        ))


if __name__ == "__main__":
    unittest.main()
