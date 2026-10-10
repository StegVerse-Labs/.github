"""Regression tests for proposal-only canonical dependency reevaluation (H7)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "reevaluate_canonical_task_dependencies.py"


class DependencyProposalTests(unittest.TestCase):
    def run_proposal(self, state):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = {
                "generation": 305,
                "status": "AUTHORITATIVE_STATUS_UNCHANGED",
                "tasks": [{
                    "task_id": "STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001",
                    "coordination_state": "PROPOSED",
                    "cosv_task_vector": "10500000114000",
                    "dependencies": [{"dependency_id": "BLK1", "resolved": False}],
                    "blockers": [{"dependency_id": "BLK1", "blocker_id": "BLOCK-BLK1"}],
                    "allowed_next_transitions": ["ACTIVE"]
                }]
            }
            original = root / "registry.json"
            output = root / "proposal.json"
            original.write_text(json.dumps(registry))
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "BLK1", "--state", state,
                 "--registry", str(original), "--output", str(output)],
                capture_output=True, text=True, check=False
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(original.read_text()), registry,
                             "proposal producer must not mutate authoritative input")
            return json.loads(output.read_text())

    def test_resolved_bool_and_cosv_blocker_count(self):
        result = self.run_proposal("RESOLVED")
        proposal = result["proposed_registry"]
        row = proposal["tasks"][0]
        self.assertEqual(proposal["status"], "AUTHORITATIVE_STATUS_UNCHANGED")
        self.assertEqual(row["dependencies"][0], {"dependency_id": "BLK1", "resolved": True})
        self.assertEqual(row["blockers"], [])
        self.assertEqual(row["cosv_task_vector"], "10500000110000")
        self.assertEqual(result["authority_effect"], "NONE_PROPOSAL_ONLY")
        self.assertEqual(row["coordination_state"], "PROPOSED")

    def test_unresolved_bool_does_not_create_state_field(self):
        result = self.run_proposal("UNRESOLVED")
        row = result["proposed_registry"]["tasks"][0]
        self.assertEqual(row["dependencies"][0], {"dependency_id": "BLK1", "resolved": False})
        self.assertEqual(row["cosv_task_vector"], "10500000111000")
        self.assertEqual(result["affected"][0]["remaining_unresolved_dependencies"], ["BLK1"])
        self.assertEqual(result["affected"][0]["next_transition_candidates"], [])


if __name__ == "__main__":
    unittest.main()
