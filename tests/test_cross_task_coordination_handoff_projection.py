from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("render_cross_task_coordination_handoff", ROOT / "scripts" / "render_cross_task_coordination_handoff.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class CrossTaskCoordinationHandoffProjectionTests(unittest.TestCase):
    def test_projection_exposes_claims_predicates_and_gaps_without_authority(self):
        ledger = {
            "schema": "stegverse.cross-task-coordination-ledger/v1",
            "tasks": [{"task_id": "B", "state": "HANDOFF_READY", "required_predicates": ["P1"]}],
            "predicates": [{"predicate_id": "P1", "state": "IN_PROGRESS", "authoritative_producer": "worker-a"}],
            "claims": [{"claim_id": "C1", "task_id": "A", "state": "ACTIVE", "scope": {}}],
            "gaps": [{"predicate_id": "P1", "missing_observation": "receiver acceptance", "required_producer": "worker-a", "action_without_collision": "consume worker-a output"}],
        }
        text = MOD.render(ledger)
        self.assertIn("P1=IN_PROGRESS", text)
        self.assertIn("`C1`", text)
        self.assertIn("consume worker-a output", text)
        self.assertIn("grants no execution", text)
        self.assertIn("Before declaring a blocker", text)

    def test_empty_claims_and_gaps_are_explicit(self):
        ledger = {"schema": "stegverse.cross-task-coordination-ledger/v1", "tasks": [], "predicates": [], "claims": [], "gaps": []}
        text = MOD.render(ledger)
        self.assertGreaterEqual(text.count("- none"), 2)


if __name__ == "__main__":
    unittest.main()
