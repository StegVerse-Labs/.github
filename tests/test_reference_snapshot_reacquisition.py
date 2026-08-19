from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from heartbeat_runtime.reference_snapshot import (
    evaluate_required_states,
    reacquire_reference_snapshot,
)


def carrier(epoch: int, *, corrected: bool = True) -> dict:
    value = {
        "epoch": epoch,
        "generation": epoch,
        "reference_frame": f"heartbeat_epoch:{epoch}",
        "frequency_rule": "INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL" if corrected else "GATE_PASSBAND_DERIVED",
    }
    if corrected:
        value["oscillator"] = {
            "progression_dependency": "OSCILLATOR_ONLY",
            "snapshot_is_observation_only": True,
        }
    return value


def policy(passband: int = 2) -> dict:
    return {
        "schema": "stegverse.heartbeat-reference-snapshot-policy/v1",
        "monitor_id": "TEST-MONITOR",
        "goal_id": "TEST-GOAL",
        "revision": 1,
        "reacquisition_rule": "GATE_PASSBAND_DERIVED",
        "passband_width_references": passband,
        "required_states": [],
    }


def states(*completed: bool) -> list[dict]:
    return [
        {
            "state_id": f"S{index}",
            "description": None,
            "complete": complete,
            "observations": [{"observed": "COMPLETE" if complete else "PENDING", "passed": complete}],
            "evidence_refs": [f"evidence:{index}"],
        }
        for index, complete in enumerate(completed, start=1)
    ]


class ReferenceSnapshotReacquisitionTests(unittest.TestCase):
    def acquire(self, *, epoch: int, required: list[dict], previous=None, passband: int = 2, at: str = "2026-08-18T19:21:00Z"):
        return reacquire_reference_snapshot(
            policy=policy(passband),
            carrier=carrier(epoch),
            required_states=required,
            previous=previous,
            acquired_at=at,
        )

    def test_initial_snapshot_opens_gate_while_required_state_pending(self) -> None:
        snapshot, decision = self.acquire(epoch=31, required=states(False, False))
        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(decision["reason"], "INITIAL")
        self.assertEqual(snapshot["gate"]["state"], "OPEN")
        self.assertEqual(snapshot["gate"]["pending_count"], 2)
        self.assertEqual(snapshot["reacquisition"]["rule"], "GATE_PASSBAND_DERIVED")
        self.assertTrue(snapshot["reference"]["snapshot_is_observation_only"])
        self.assertFalse(snapshot["authority"]["snapshot_controls_carrier_progression"])
        self.assertFalse(snapshot["authority"]["snapshot_grants_execution_authority"])

    def test_no_reacquisition_inside_passband_without_state_change(self) -> None:
        previous, _ = self.acquire(epoch=31, required=states(False, False), passband=2)
        snapshot, decision = self.acquire(epoch=32, required=states(False, False), previous=previous, passband=2)
        self.assertIsNone(snapshot)
        self.assertEqual(decision["reason"], "WITHIN_PASSBAND_NO_STATE_CHANGE")

    def test_state_progress_reacquires_even_inside_passband(self) -> None:
        previous, _ = self.acquire(epoch=31, required=states(False, False), passband=5)
        snapshot, decision = self.acquire(epoch=32, required=states(True, False), previous=previous, passband=5)
        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(decision["reason"], "REQUIRED_STATE_CHANGED")
        self.assertEqual(snapshot["gate"]["complete_count"], 1)
        self.assertEqual(snapshot["previous_snapshot_sha256"], previous["snapshot_sha256"])

    def test_passband_crossing_reacquires_unresolved_state(self) -> None:
        previous, _ = self.acquire(epoch=31, required=states(False), passband=2)
        snapshot, decision = self.acquire(epoch=33, required=states(False), previous=previous, passband=2)
        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(decision["reason"], "PASSBAND_CROSSED")
        self.assertEqual(snapshot["reacquisition"]["reference_delta_from_previous"], 2)

    def test_terminal_progress_reacquires_and_closes_gate(self) -> None:
        previous, _ = self.acquire(epoch=31, required=states(False, True), passband=5)
        snapshot, decision = self.acquire(epoch=32, required=states(True, True), previous=previous, passband=5)
        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(decision["reason"], "TERMINAL_GATE_CLOSED")
        self.assertEqual(snapshot["gate"]["state"], "CLOSED")
        self.assertEqual(snapshot["gate"]["pending_count"], 0)

    def test_closed_chain_does_not_periodically_reacquire(self) -> None:
        previous, _ = self.acquire(epoch=31, required=states(True), passband=1)
        self.assertEqual(previous["gate"]["state"], "CLOSED")
        snapshot, decision = self.acquire(epoch=99, required=states(True), previous=previous, passband=1)
        self.assertIsNone(snapshot)
        self.assertEqual(decision["reason"], "NONE_TERMINAL")

    def test_snapshot_rejects_carrier_reference_regression(self) -> None:
        previous, _ = self.acquire(epoch=31, required=states(False), passband=1)
        with self.assertRaises(ValueError):
            self.acquire(epoch=30, required=states(False), previous=previous, passband=1)

    def test_policy_evaluator_reads_current_state_without_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "control").mkdir(parents=True)
            (root / "receipts").mkdir(parents=True)
            (root / "control" / "carrier.json").write_text(json.dumps(carrier(40)), encoding="utf-8")
            (root / "control" / "registry.json").write_text(json.dumps({"tasks": [{"task_id": "T", "state": "COMPLETED", "claim_id": None}]}), encoding="utf-8")
            test_policy = policy(1)
            test_policy["required_states"] = [
                {
                    "state_id": "CARRIER",
                    "checks": [
                        {"type": "json_path", "source_ref": "control/carrier.json", "path": ["oscillator", "progression_dependency"], "operator": "eq", "expected": "OSCILLATOR_ONLY"}
                    ],
                },
                {
                    "state_id": "TASK",
                    "checks": [
                        {"type": "registry_task_field", "source_ref": "control/registry.json", "task_id": "T", "field": "state", "operator": "eq", "expected": "COMPLETED"},
                        {"type": "registry_task_field", "source_ref": "control/registry.json", "task_id": "T", "field": "claim_id", "operator": "is_none", "expected": None},
                    ],
                },
            ]
            observed = evaluate_required_states(root, test_policy)
            self.assertTrue(all(item["complete"] for item in observed))

    def test_historical_gate_passband_carrier_can_be_observed_without_being_rewritten(self) -> None:
        old = carrier(31, corrected=False)
        before = copy.deepcopy(old)
        snapshot, _ = reacquire_reference_snapshot(
            policy=policy(1),
            carrier=old,
            required_states=states(False),
            previous=None,
            acquired_at="2026-08-18T19:21:00Z",
        )
        self.assertEqual(old, before)
        self.assertEqual(snapshot["reference"]["carrier_frequency_rule_observed"], "GATE_PASSBAND_DERIVED")
        self.assertEqual(snapshot["reacquisition"]["rule"], "GATE_PASSBAND_DERIVED")
        self.assertFalse(snapshot["authority"]["snapshot_controls_carrier_progression"])


if __name__ == "__main__":
    unittest.main()
