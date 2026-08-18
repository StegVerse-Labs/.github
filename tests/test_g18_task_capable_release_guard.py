from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workers" / "sovereign_runtime_activation_entrypoint.py"
spec = importlib.util.spec_from_file_location("g18_guard", SCRIPT)
guard = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(guard)


class G18TaskCapableReleaseGuardTests(unittest.TestCase):
    def _base_status(self) -> dict:
        return {
            "predicates": {
                "carrier_transition_receipt_complete": True,
                "worker_runtime_checkpoint_observed_at_or_after_carrier_epoch": True,
                "state_reconstruction_pass": True,
            },
            "complete": True,
        }

    def test_observation_only_state_cannot_terminalize_g18(self) -> None:
        def fake_load(path: Path):
            if path == guard.base.TRANSITION_RECEIPT:
                return {"carrier_epoch_after": 31}
            if path == ROOT / "control" / "worker-runtime-state.json":
                return {
                    "runtime_tick": 2,
                    "observation_mode": "CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION",
                }
            return {}

        with mock.patch.object(guard, "_base_state_transition_status", return_value=self._base_status()), \
             mock.patch.object(guard.base, "load_json", side_effect=fake_load), \
             mock.patch.object(guard.release, "task_capable_worker_cycle_observed", return_value=False):
            status = guard.guarded_state_transition_status()

        self.assertFalse(status["complete"])
        self.assertFalse(status["predicates"]["worker_task_capable_cycle_observed"])
        self.assertEqual(status["worker_runtime_tick"], 2)
        self.assertEqual(status["worker_observation_mode"], "CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION")

    def test_task_capable_cycle_preserves_otherwise_complete_g18_state(self) -> None:
        def fake_load(path: Path):
            if path == guard.base.TRANSITION_RECEIPT:
                return {"carrier_epoch_after": 31}
            if path == ROOT / "control" / "worker-runtime-state.json":
                return {
                    "runtime_tick": 3,
                    "observation_mode": "TASK_CAPABLE_WORKER_COORDINATOR",
                }
            return {}

        with mock.patch.object(guard, "_base_state_transition_status", return_value=self._base_status()), \
             mock.patch.object(guard.base, "load_json", side_effect=fake_load), \
             mock.patch.object(guard.release, "task_capable_worker_cycle_observed", return_value=True):
            status = guard.guarded_state_transition_status()

        self.assertTrue(status["complete"])
        self.assertTrue(status["predicates"]["worker_task_capable_cycle_observed"])
        self.assertEqual(status["worker_runtime_tick"], 3)


if __name__ == "__main__":
    unittest.main()
