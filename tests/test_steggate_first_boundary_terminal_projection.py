from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "STEGGATE-FIRST-BOUNDARY-001"


class StegGateFirstBoundaryTerminalProjectionTests(unittest.TestCase):
    def test_global_registry_matches_terminal_handoff(self) -> None:
        registry = json.loads((ROOT / "control" / "worker-registry.json").read_text(encoding="utf-8"))
        handoff = json.loads((ROOT / "handoffs" / "STEGGATE-FIRST-BOUNDARY-001.json").read_text(encoding="utf-8"))
        task = next(row for row in registry["tasks"] if row.get("task_id") == TASK_ID)

        self.assertEqual(handoff["state"], "COMPLETED")
        self.assertEqual(handoff["task"]["operational_state"], "COMPLETE")
        self.assertEqual(handoff["task"]["claim_state"], "COMPLETE_RELEASED")
        self.assertEqual(task["state"], "COMPLETED")
        self.assertTrue(task["archive_eligible"])
        self.assertIsNone(task["claim_id"])
        self.assertIsNone(task["worker_id"])
        self.assertIsNone(task["block_ref"])
        self.assertIn("management/first-boundary-activation.json:COMPLETE", " ".join(task["evidence_refs"]))

    def test_terminal_task_is_not_in_active_cosv_gap(self) -> None:
        coverage = json.loads((ROOT / "control" / "cosv-global-registry-coverage.json").read_text(encoding="utf-8"))
        self.assertNotIn(TASK_ID, coverage["active_worker_task_ids_missing_canonical_cosv"])
        matches = [x for x in coverage.get("reconciled_terminal_tasks", []) if x.get("task_id") == TASK_ID]
        self.assertEqual(len(matches), 1)
        self.assertFalse(matches[0]["vector_required_for_active_coverage"])


if __name__ == "__main__":
    unittest.main()
