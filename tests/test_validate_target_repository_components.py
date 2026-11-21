"""Exact repository -> component pairings in canonical task records (R-P8)."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_target_repository_components as pairs  # noqa: E402

RECORDS = ROOT / "data" / "canonical-task-records"


def load(task_id):
    return json.loads((RECORDS / f"{task_id}.json").read_text(encoding="utf-8"))


class RepositoryComponentsTests(unittest.TestCase):
    def test_ownership_records_declare_exactly_their_intended_pairs(self):
        for task_id, expected in (("HEALER-ORCHESTRATOR-TARGET-OWNERSHIP-001", 12),
                                  ("AWAIT-SURFACE-TRANSITION-OWNERSHIP-001", 6)):
            with self.subTest(task_id=task_id):
                record = load(task_id)
                self.assertEqual(pairs.defects(record), [])
                targets = record["targets"]
                in_scope = [(r, c) for r in targets["repositories"] for c in targets["components"]
                            if pairs.pair_in_scope(record, r, c)]
                self.assertEqual(len(in_scope), expected)
                self.assertGreater(len(targets["repositories"]) * len(targets["components"]), expected)

    def test_a_pair_outside_the_mapping_is_rejected(self):
        record = load("HEALER-ORCHESTRATOR-TARGET-OWNERSHIP-001")
        self.assertTrue(pairs.pair_in_scope(record, "StegVerse-Labs/SCW", "uptime"))
        # Both names are in the flat lists, but this pair is not declared.
        self.assertFalse(pairs.pair_in_scope(record, "StegVerse-Labs/TV", "uptime"))
        self.assertFalse(pairs.pair_in_scope(record, "StegVerse-Labs/Site", "quiet_enforcer"))
        self.assertFalse(pairs.pair_in_scope(record, "StegVerse-Labs/Unlisted", "uptime"))

    def test_malformed_mappings_fail_closed(self):
        base = load("HEALER-ORCHESTRATOR-TARGET-OWNERSHIP-001")
        cases = {
            "extra repository key": lambda t: t["repository_components"].update({"StegVerse-Labs/Other": ["x"]}),
            "missing repository key": lambda t: t["repository_components"].pop("StegVerse-Labs/TV"),
            "component under two repositories": lambda t: t["repository_components"]["StegVerse-Labs/TV"].append("uptime"),
            "component not in components": lambda t: t["repository_components"]["StegVerse-Labs/TV"].append("ghost"),
            "component left unmapped": lambda t: t["repository_components"]["StegVerse-Labs/SCW"].remove("uptime"),
            "empty list": lambda t: t["repository_components"].update({"StegVerse-Labs/TV": []}),
            "not an object": lambda t: t.update({"repository_components": ["StegVerse-Labs/TV"]}),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                record = copy.deepcopy(base)
                mutate(record["targets"])
                self.assertNotEqual(pairs.defects(record), [])

    def test_records_without_the_field_are_not_judged(self):
        record = {"targets": {"repositories": ["a/b"], "components": ["c"]}}
        self.assertEqual(pairs.defects(record), [])
        self.assertTrue(pairs.pair_in_scope(record, "a/b", "c"))

    def test_every_committed_mapping_passes(self):
        self.assertEqual(pairs.main(), 0)


if __name__ == "__main__":
    unittest.main()
