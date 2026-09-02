from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from heartbeat_runtime.runtime_presence_projection import project


class RuntimePresenceProjectionTests(unittest.TestCase):
    def write(self, root: Path, rel: str, value: dict) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_missing_runtime_evidence_remains_unobserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = project(Path(tmp), {"request": "receipts/request.json"})
            self.assertFalse(result["resident"]["runtime_alive_observed"])
            self.assertFalse(result["governed_progress"]["request_observed"])
            self.assertFalse(result["heartbeat_reference"]["freshness_correlated"])
            self.assertFalse(result["governed_progress"]["runtime_signal_is_execution_receipt"])

    def test_runtime_presence_requires_direct_activation_predicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "control/heartbeat-carrier-runtime-state.json", {
                "schema": "stegverse.heartbeat-carrier-runtime-state/v1", "epoch": 42, "generation": 42
            })
            self.write(root, "control/worker-runtime-state.json", {
                "schema": "stegverse.worker-runtime-state/v1",
                "runtime_tick": 9,
                "last_observed_carrier_epoch": 42,
                "observation_mode": "TASK_CAPABLE_WORKER_COORDINATOR",
            })
            self.write(root, "receipts/sovereign-host/activation.latest.json", {
                "schema": "stegverse.sovereign-runtime-activation/v1",
                "predicates": {"native_service_active": True, "continuous_runtime_live": True},
                "node_id": "node-7",
            })
            result = project(root)
            self.assertTrue(result["resident"]["runtime_alive_observed"])
            self.assertTrue(result["resident"]["task_capable_worker_observed"])
            self.assertTrue(result["heartbeat_reference"]["freshness_correlated"])
            self.assertEqual(result["resident"]["node_id"], "node-7")

    def test_receipt_presence_is_not_collapsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "receipts/request.json", {"schema": "request/v1", "state": "REQUESTED"})
            self.write(root, "receipts/consumption.json", {"schema": "consume/v1", "state": "CONSUMED"})
            result = project(root, {
                "request": "receipts/request.json",
                "consumption": "receipts/consumption.json",
                "execution": "receipts/execution.json",
                "reconstruction": "receipts/reconstruction.json",
            })
            self.assertTrue(result["governed_progress"]["request_observed"])
            self.assertTrue(result["governed_progress"]["consumption_observed"])
            self.assertFalse(result["governed_progress"]["execution_observed"])
            self.assertFalse(result["governed_progress"]["reconstruction_observed"])


if __name__ == "__main__":
    unittest.main()
