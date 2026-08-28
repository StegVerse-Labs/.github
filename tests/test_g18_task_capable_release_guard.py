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
    def complete_proof(self) -> dict:
        proof = {name: True for name in guard.base.REQUIRED_PREDICATES}
        proof["schema"] = "stegverse.sovereign-runtime-activation-proof/v1"
        proof["all_predicates_pass"] = True
        return proof

    def test_observation_only_or_missing_task_capable_predicate_cannot_terminalize_g18(self) -> None:
        proof = self.complete_proof()
        proof["worker_task_capable_cycle_observed"] = False
        self.assertFalse(guard.base.all_activation_predicates_pass(proof))

    def test_all_runtime_predicates_and_task_capable_cycle_are_required(self) -> None:
        proof = self.complete_proof()
        self.assertTrue(guard.base.all_activation_predicates_pass(proof))
        for predicate in guard.base.REQUIRED_PREDICATES:
            broken = dict(proof)
            broken[predicate] = False
            self.assertFalse(
                guard.base.all_activation_predicates_pass(broken),
                predicate,
            )

    def test_entrypoint_delegates_to_single_canonical_g18_worker(self) -> None:
        with mock.patch.object(guard.base, "main", return_value=0) as main:
            self.assertEqual(guard.main(), 0)
        main.assert_called_once_with()

    def test_entrypoint_contains_no_historical_transition_release_guard(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("refresh_heartbeat_transition_receipt", source)
        self.assertNotIn("guarded_state_transition_status", source)
        self.assertNotIn("_base_state_transition_status", source)
        self.assertIn("sovereign_runtime_activation_worker.py", source)


if __name__ == "__main__":
    unittest.main()
