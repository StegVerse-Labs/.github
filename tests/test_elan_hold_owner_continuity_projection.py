"""Regression: existing ELAN HOLD stays in the Registry without inventing a human checkout."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TASK = "ELAN-PAPER-COAUTHOR-PUBLICATION-001"


class ELANHoldProjectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shard = json.loads((ROOT / "data/canonical-task-records" / (TASK + ".json")).read_text())
        cls.registry = json.loads((ROOT / "data/canonical-task-registry.json").read_text())
        cls.vector = json.loads((ROOT / "control/task-vectors" / (TASK + ".json")).read_text())

    def test_one_existing_task_in_aggregate_with_exact_shard_parity(self):
        matched = [t for t in self.registry["tasks"] if t["task_id"] == TASK]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0], self.shard)
        self.assertGreaterEqual(self.registry["generation"], 264)

    def test_machine_continuation_does_not_assert_human_or_session_checkout(self):
        self.assertEqual(self.shard["coordination_state"], "ACTIVE")
        self.assertEqual(self.shard["cosv"]["vector"], "71000000100100")
        self.assertEqual(self.shard["cosv"]["vector"], self.vector["vector"])
        self.assertIn("NO_VERIFIED_SESSION_CHECKOUT", self.shard["checkout_state"])
        self.assertFalse(self.shard["completion"]["claimed"])
        self.assertIn("EXECUTE_AUTHENTIC_HOLD_MANIFEST_AND_PRESERVE_DISPOSITION",
                      self.shard["allowed_next_transitions"])

    def test_no_authoritative_ownership_inferred_from_source_only_projection(self):
        task = next(t for t in self.registry["tasks"] if t["task_id"] == TASK)
        self.assertEqual(task["cosv"]["authority_effect"], "NONE")
        self.assertFalse(task["completion"]["validated"])


if __name__ == "__main__":
    unittest.main()
