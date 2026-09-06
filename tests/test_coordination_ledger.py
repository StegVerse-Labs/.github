from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from heartbeat_runtime.coordination_ledger import (
    CoordinationLedgerError,
    compose_coordination_ledger,
    load_composed_coordination_ledger,
)


class CoordinationLedgerCompositionTests(unittest.TestCase):
    def base(self):
        return {
            "schema": "stegverse.cross-task-coordination-ledger/v1",
            "authority": {"runtime_truth_authority_effect": "NONE"},
            "goals": [{"goal_id": "G"}],
            "tasks": [],
            "predicates": [{"predicate_id": "P0", "state": "UNKNOWN", "authoritative_producer": "base"}],
            "evidence": [],
            "claims": [],
            "gaps": [],
        }

    def fragment(self, fragment_id="F1", predicate_id="P1"):
        return {
            "schema": "stegverse.cross-task-coordination-fragment/v1",
            "fragment_id": fragment_id,
            "authority_effect": "NONE_COORDINATION_ONLY",
            "predicates": [
                {
                    "predicate_id": predicate_id,
                    "state": "UNKNOWN",
                    "authoritative_producer": "fragment",
                    "semantic_predicate_id": "resident_request_consumed",
                    "subject_binding": {"request_id": fragment_id},
                }
            ],
            "gaps": [
                {
                    "predicate_id": predicate_id,
                    "subject_binding": {"request_id": fragment_id},
                    "rejected_because": ["NO_QUALIFYING_EVIDENCE_OBSERVED"],
                    "required_producer": "fragment",
                    "action_without_collision": "consume existing producer",
                }
            ],
        }

    def test_composes_fragment_without_mutating_base(self):
        base = self.base()
        result = compose_coordination_ledger(base, [self.fragment()])
        self.assertEqual([p["predicate_id"] for p in base["predicates"]], ["P0"])
        self.assertEqual([p["predicate_id"] for p in result["predicates"]], ["P0", "P1"])
        self.assertEqual(result["composition"]["fragment_ids"], ["F1"])
        self.assertEqual(result["composition"]["authority_effect"], "NONE")

    def test_duplicate_predicate_fails_closed(self):
        with self.assertRaises(CoordinationLedgerError):
            compose_coordination_ledger(self.base(), [self.fragment(predicate_id="P0")])

    def test_duplicate_fragment_id_fails_closed(self):
        with self.assertRaises(CoordinationLedgerError):
            compose_coordination_ledger(self.base(), [self.fragment(), self.fragment()])

    def test_invalid_authority_effect_fails_closed(self):
        fragment = self.fragment()
        fragment["authority_effect"] = "EXECUTION"
        with self.assertRaises(CoordinationLedgerError):
            compose_coordination_ledger(self.base(), [fragment])

    def test_loader_uses_sorted_fragment_filenames(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            control = root / "control"
            fragments = control / "cross-task-coordination.d"
            fragments.mkdir(parents=True)
            (control / "cross-task-coordination.json").write_text(json.dumps(self.base()), encoding="utf-8")
            (fragments / "b.json").write_text(json.dumps(self.fragment("F-B", "P-B")), encoding="utf-8")
            (fragments / "a.json").write_text(json.dumps(self.fragment("F-A", "P-A")), encoding="utf-8")
            result = load_composed_coordination_ledger(control / "cross-task-coordination.json")
            self.assertEqual(result["composition"]["fragment_ids"], ["F-A", "F-B"])
            self.assertEqual([p["predicate_id"] for p in result["predicates"]], ["P0", "P-A", "P-B"])


if __name__ == "__main__":
    unittest.main()
