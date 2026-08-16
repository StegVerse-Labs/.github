from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from heartbeat_runtime.worker_runtime import WorkerCoordinator


class WorkerRuntimeSeparationTests(unittest.TestCase):
    def test_worker_cycle_observes_but_does_not_advance_carrier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = root / "control"
            control.mkdir(parents=True)
            carrier = {
                "schema": "stegverse.heartbeat-carrier-runtime-state/v1",
                "epoch": 30,
                "generation": 30,
                "role": "REGULATORY_CARRIER_REFERENCE_FRAME",
                "reference_frame": "heartbeat_epoch:30",
                "frequency_rule": "GATE_PASSBAND_DERIVED",
                "authority_effect": "NONE",
                "activation_state": "ACTIVE",
                "legacy_cutover": {
                    "legacy_schema": "stegverse.org-heartbeat-state/v1",
                    "legacy_epoch": 29,
                    "legacy_generation": 29,
                    "legacy_state_sha256": "0" * 64,
                    "source_ref": "control/heartbeat-state.json",
                    "closed": True,
                },
            }
            carrier_path = control / "heartbeat-carrier-runtime-state.json"
            carrier_path.write_text(json.dumps(carrier, indent=2) + "\n", encoding="utf-8")
            before = carrier_path.read_bytes()
            (control / "worker-registry.json").write_text(json.dumps({
                "schema": "stegverse.heartbeat-worker-registry/v0.1",
                "generation": 0,
                "workers": [],
                "tasks": [],
            }, indent=2) + "\n", encoding="utf-8")

            result = WorkerCoordinator(root, adapters={}).cycle(write=True)
            self.assertEqual(result["observed_carrier_epoch"], 30)
            self.assertEqual(result["observed_carrier_generation"], 30)
            self.assertFalse(result["carrier_epoch_advanced_by_worker_runtime"])
            self.assertEqual(result["workers_activated"], 0)
            self.assertEqual(carrier_path.read_bytes(), before)
            state = json.loads((control / "worker-runtime-state.json").read_text())
            self.assertEqual(state["runtime_tick"], 1)
            self.assertEqual(state["last_observed_carrier_epoch"], 30)
            self.assertFalse(state["carrier_controls_timer"])
            self.assertEqual(state["credential_authority"], "TV/TVC")
            self.assertEqual(state["github_token_runtime_authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
