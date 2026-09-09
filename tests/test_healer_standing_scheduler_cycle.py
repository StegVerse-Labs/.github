from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "workers" / "healer_sovereign_scheduler_worker.py"
SPEC = importlib.util.spec_from_file_location("healer_scheduler_worker", MODULE_PATH)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class HealerStandingSchedulerCycleTests(unittest.TestCase):
    def test_completed_scheduler_cycle_rearms_workercoordinator_task(self) -> None:
        response = MOD._response(
            "COMPLETED",
            "HEALER_SOVEREIGN_SCHEDULER_COMPLETED",
            "receipts/healer-sovereign-scheduler/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json",
            None,
            42,
        )
        self.assertEqual(response["state"], "HANDOFF_READY")
        self.assertEqual(response["transition_id"], "HEALER_SOVEREIGN_SCHEDULER_COMPLETED")
        self.assertEqual(response["expected_next_transition"], "HEALER_SOVEREIGN_SCHEDULER_RECHECK")
        self.assertEqual(response["expected_next_earliest_epoch"], 43)
        self.assertEqual(response["expected_next_latest_epoch"], 43)

    def test_nonterminal_states_are_not_rewritten(self) -> None:
        response = MOD._response(
            "BLOCKED",
            "HEALER_SOVEREIGN_SCHEDULER_BLOCKED",
            "receipts/healer-sovereign-scheduler/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json",
            {"dependency_class": "LOCAL_RESOURCE"},
            42,
        )
        self.assertEqual(response["state"], "BLOCKED")
        self.assertEqual(response["transition_id"], "HEALER_SOVEREIGN_SCHEDULER_BLOCKED")


if __name__ == "__main__":
    unittest.main()
