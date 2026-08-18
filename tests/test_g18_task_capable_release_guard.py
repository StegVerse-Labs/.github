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

    def _fake_load(self, tick: int, mode: str):
        def fake_load(path: Path):
            if path == guard.base.TRANSITION_RECEIPT:
                return {"carrier_epoch_after": 31}
            if path == ROOT / "control" / "worker-runtime-state.json":
                return {"runtime_tick": tick, "observation_mode": mode}
            return {}
        return fake_load

    def test_observation_only_state_cannot_terminalize_g18(self) -> None:
        with mock.patch.object(guard, "_base_state_transition_status", return_value=self._base_status()), \
             mock.patch.object(guard.base, "load_json", side_effect=self._fake_load(2, "CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION")), \
             mock.patch.object(guard.release, "refresh", return_value={"all_carrier_transition_predicates_pass": True, "release_state": "RELEASE_COMPLETE", "runtime_goal_release_state": "WORKER_TASK_CAPABLE_CYCLE_PENDING"}), \
             mock.patch.object(guard.release, "task_capable_worker_cycle_observed", return_value=False):
            status = guard.guarded_state_transition_status()

        self.assertFalse(status["complete"])
        self.assertTrue(status["predicates"]["oscillator_carrier_release_complete"])
        self.assertFalse(status["predicates"]["worker_task_capable_cycle_observed"])
        self.assertEqual(status["worker_runtime_tick"], 2)

    def test_pre_correction_carrier_cannot_terminalize_g18_even_with_worker(self) -> None:
        with mock.patch.object(guard, "_base_state_transition_status", return_value=self._base_status()), \
             mock.patch.object(guard.base, "load_json", side_effect=self._fake_load(3, "TASK_CAPABLE_WORKER_COORDINATOR")), \
             mock.patch.object(guard.release, "refresh", return_value={"all_carrier_transition_predicates_pass": False, "release_state": "FAIL_CLOSED_CARRIER_INTEGRITY", "runtime_goal_release_state": "CARRIER_INTEGRITY_PENDING"}), \
             mock.patch.object(guard.release, "task_capable_worker_cycle_observed", return_value=True):
            status = guard.guarded_state_transition_status()

        self.assertFalse(status["complete"])
        self.assertFalse(status["predicates"]["oscillator_carrier_release_complete"])
        self.assertTrue(status["predicates"]["worker_task_capable_cycle_observed"])
        self.assertEqual(status["carrier_release_state"], "FAIL_CLOSED_CARRIER_INTEGRITY")

    def test_both_oscillator_release_and_task_capable_cycle_are_required(self) -> None:
        with mock.patch.object(guard, "_base_state_transition_status", return_value=self._base_status()), \
             mock.patch.object(guard.base, "load_json", side_effect=self._fake_load(3, "TASK_CAPABLE_WORKER_COORDINATOR")), \
             mock.patch.object(guard.release, "refresh", return_value={"all_carrier_transition_predicates_pass": True, "release_state": "RELEASE_COMPLETE", "runtime_goal_release_state": "RELEASE_COMPLETE"}), \
             mock.patch.object(guard.release, "task_capable_worker_cycle_observed", return_value=True):
            status = guard.guarded_state_transition_status()

        self.assertTrue(status["complete"])
        self.assertTrue(status["predicates"]["oscillator_carrier_release_complete"])
        self.assertTrue(status["predicates"]["worker_task_capable_cycle_observed"])
        self.assertEqual(status["carrier_release_state"], "RELEASE_COMPLETE")
        self.assertEqual(status["worker_runtime_tick"], 3)


if __name__ == "__main__":
    unittest.main()
