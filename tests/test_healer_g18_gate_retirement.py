from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HealerG18GateRetirementTests(unittest.TestCase):
    def test_healer_scheduler_has_no_g18_dependency_gate(self):
        handoff = json.loads((ROOT / "handoffs" / "SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json").read_text())
        registry = json.loads((ROOT / "control" / "worker-registry.d" / "healer-sovereign-scheduler-001.json").read_text())
        vector = json.loads((ROOT / "control" / "task-vectors" / "SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json").read_text())

        self.assertEqual(handoff["task"]["dependencies"], [])
        self.assertEqual(registry["tasks"][0]["dependencies"], [])
        self.assertEqual(handoff["completion"]["dependency_state"]["state"], "RELEASE_COMPLETE_NOT_A_DOWNSTREAM_GATE")
        self.assertIsNone(handoff["completion"]["dependency_state"]["blocker"])
        self.assertFalse(handoff["completion"]["dependency_state"]["g18_terminalization_required"])
        self.assertEqual(vector["exact_metrics"]["blocker_count"], 0)
        self.assertEqual(vector["vector"], "50000000100000")
        self.assertEqual(handoff["machine_readable_state"]["cosv"]["vector"], "50000000100000")

    def test_next_action_targets_native_resident_request_consumption(self):
        handoff = json.loads((ROOT / "handoffs" / "SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json").read_text())
        next_action = handoff["completion"]["next_authorized_action"]
        self.assertIn("RESIDENT-EXEC-HEALER-SOVEREIGN-SCHEDULER-001", next_action)
        self.assertIn("Do not wait on G18 terminalization", next_action)
        self.assertIn("WorkerCoordinator", next_action)


if __name__ == "__main__":
    unittest.main()
