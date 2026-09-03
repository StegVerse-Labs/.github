from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from heartbeat_runtime.worker_runtime import WorkerCoordinator


class RuntimeBlockerContinuationProofTests(unittest.TestCase):
    def _fixture(self, root: Path) -> None:
        control = root / "control"
        control.mkdir(parents=True)
        carrier = {
            "schema": "stegverse.heartbeat-carrier-runtime-state/v1",
            "epoch": 40,
            "generation": 40,
            "role": "REGULATORY_CARRIER_REFERENCE_FRAME",
            "reference_frame": "heartbeat_epoch:40",
            "frequency_rule": "GATE_PASSBAND_DERIVED",
            "authority_effect": "NONE",
            "activation_state": "ACTIVE",
            "legacy_cutover": {
                "legacy_schema": "stegverse.org-heartbeat-state/v1",
                "legacy_epoch": 39,
                "legacy_generation": 39,
                "legacy_state_sha256": "0" * 64,
                "source_ref": "control/heartbeat-state.json",
                "closed": True,
            },
        }
        (control / "heartbeat-carrier-runtime-state.json").write_text(
            json.dumps(carrier, indent=2) + "\n",
            encoding="utf-8",
        )
        registry = {
            "schema": "stegverse.heartbeat-worker-registry/v0.1",
            "generation": 2,
            "workers": [],
            "tasks": [
                {
                    "task_id": "SHWP-DURABLE-RUNTIME-ACTIVATION",
                    "state": "BLOCKED",
                    "worker_id": "sovereign-runtime-activation-worker",
                    "worker_instance_id": "sovereign-runtime-activation-worker-HB40-G1",
                    "claim_id": "SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G1",
                    "blocker": {
                        "problem_statement": "deployment-local runtime proof unresolved",
                        "solution_required": True,
                        "workaround_candidates": ["continue admitted native resolution path"],
                        "next_solution_action": "continue native runtime resolution",
                        "durable_owner": "StegVerse-Labs/.github#65",
                        "release_condition": "deployment-local task-capable proof observed",
                    },
                    "heartbeat_timing": {"fencing_token": 1},
                },
                {
                    "task_id": "SHWP-LATER-ADMISSIBLE-WORK",
                    "state": "ACTIVE",
                    "worker_id": "later-worker",
                    "worker_instance_id": "later-worker-HB40-G2",
                    "claim_id": "SHWP-SHWP-LATER-ADMISSIBLE-WORK-G2",
                    "heartbeat_timing": {"fencing_token": 2},
                },
            ],
        }
        (control / "worker-registry.json").write_text(
            json.dumps(registry, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_blocked_runtime_task_does_not_stop_later_active_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            runtime = WorkerCoordinator(root, adapters={})
            observed = []

            def record_tick(task, carrier_epoch, registry, cost_log, events):
                observed.append(task["task_id"])

            with mock.patch.object(runtime, "_tick_active_timer", side_effect=record_tick):
                result = runtime.cycle(write=True)

            self.assertEqual(
                observed,
                [
                    "SHWP-DURABLE-RUNTIME-ACTIVATION",
                    "SHWP-LATER-ADMISSIBLE-WORK",
                ],
            )
            persisted = json.loads((root / "control" / "worker-registry.json").read_text())
            by_id = {row["task_id"]: row for row in persisted["tasks"]}
            self.assertEqual(by_id["SHWP-DURABLE-RUNTIME-ACTIVATION"]["state"], "BLOCKED")
            self.assertEqual(by_id["SHWP-LATER-ADMISSIBLE-WORK"]["state"], "ACTIVE")
            self.assertEqual(
                by_id["SHWP-DURABLE-RUNTIME-ACTIVATION"]["blocker"]["durable_owner"],
                "StegVerse-Labs/.github#65",
            )
            self.assertEqual(result["credential_authority"], "TV/TVC")
            self.assertEqual(result["github_token_runtime_authority"], "NONE")
            self.assertEqual(result["authority_effect"], "EXISTING_ADMITTED_TASK_AUTHORITY_ONLY")

    def test_targeted_cycle_does_not_claim_multi_item_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            runtime = WorkerCoordinator(root, adapters={})
            observed = []

            def record_tick(task, carrier_epoch, registry, cost_log, events):
                observed.append(task["task_id"])

            with mock.patch.object(runtime, "_tick_active_timer", side_effect=record_tick):
                result = runtime.cycle(
                    write=False,
                    target_task_id="SHWP-DURABLE-RUNTIME-ACTIVATION",
                )

            self.assertEqual(observed, ["SHWP-DURABLE-RUNTIME-ACTIVATION"])
            self.assertTrue(result["targeted_independent_task_control"])
            self.assertTrue(result["unrelated_worker_execution_suppressed"])

if __name__ == "__main__":
    unittest.main()
