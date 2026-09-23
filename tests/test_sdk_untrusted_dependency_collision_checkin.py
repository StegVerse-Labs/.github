"""Exact canonical evaluator exercise for the distinct SDK-only inert fixture scope.

GitHub CI is source/coordination evidence only. The event ledger is temporary;
this is not an authentic resident claim/fence or an authority-bearing check-in.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TASK = "SDK-UNTRUSTED-DEPENDENCY-EXECUTION-BOUNDARY-001"
COMPONENT = "sdk:untrusted-dependency-contract-and-inert-tests"


class SDKUntrustedDependencyCollisionCheckinTests(unittest.TestCase):
    def test_exact_scoped_canonical_evaluator_with_ephemeral_event_history(self):
        registry = json.loads((ROOT / "data/canonical-task-registry.json").read_text())
        record = next(row for row in registry["tasks"] if row["task_id"] == TASK)
        self.assertEqual(record["coordination_state"], "ACTIVE")
        self.assertEqual(record["checkout_state"], "HANDOFF_READY")
        self.assertEqual(record["cosv_task_vector"], "71000000111111")
        request = {
            "task_id": TASK,
            "observed_registry_generation": registry["generation"],
            "caller_surface": "INTERNAL_CANONICAL_WORK_BOOTSTRAP",
            "checkin_context": {
                "repository": "StegVerse-org/StegVerse-SDK",
                "repositories_under_mutation": ["StegVerse-org/StegVerse-SDK"],
                "components_under_mutation": [COMPONENT],
                "first_unresolved_predicate": "INERT_SOURCE_FIXTURE_COMPATIBILITY_ONLY",
                "session_id": "source-validation-ephemeral-not-resident",
            },
        }
        with tempfile.TemporaryDirectory() as temp:
            ledger = Path(temp) / "checkin-events.jsonl"
            env = dict(os.environ, STEGVERSE_TASK_REGISTRY_EVENT_LEDGER=str(ledger))
            completed = subprocess.run(
                [sys.executable, "scripts/evaluate_task_registry_collision_checkin.py"],
                input=json.dumps(request), text=True, capture_output=True,
                cwd=ROOT, env=env, check=True,
            )
            result = json.loads(completed.stdout.strip().splitlines()[-1])
            assert ledger.is_file(), "canonical evaluator must retain its ephemeral event"
            events = [json.loads(row) for row in ledger.read_text().splitlines()]
            self.assertTrue(events)
            self.assertEqual(events[0]["task_id"], TASK)
        self.assertEqual(result["current_registry_generation"], registry["generation"])
        self.assertTrue(result["coordination_generation_current"])
        self.assertEqual(result["disposition"], "COORDINATE_CONVERGENCE")
        self.assertEqual(result["session_action"], "COORDINATE_BEFORE_MUTATION")
        self.assertEqual(result["hard_collision_task_ids"], [])
        adjacent = {row["task_id"] for row in result["collision_candidates"]}
        self.assertIn("SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001", adjacent)
        self.assertIn("SDK-MICRO-NODE-COMMIT-TIME-ADMISSIBILITY-001", adjacent)
        self.assertIn("CANONICAL-MASTER-RECORDS-STATE-TRANSITION-CUSTODY-001", adjacent)
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertFalse(result["caller_surface_attestation_proven"])
        print("SDK_INERT_SCOPE_CANONICAL_EVALUATOR_COORDINATE_CONVERGENCE_NO_HARD_COLLISION")


if __name__ == "__main__":
    unittest.main()
