from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import repair_resident_worker_presence as repair
from scripts import run_heartbeat_runtime as carrier


class ResidentWorkerPresenceSelfHealTests(unittest.TestCase):
    def test_carrier_supervision_interval_is_hb_scale_and_non_authorizing(self):
        self.assertEqual(carrier.WORKER_SUPERVISION_INTERVAL_REFERENCES, 100)
        source = Path(carrier.__file__).read_text(encoding="utf-8")
        self.assertIn("ensure_worker_presence", source)
        self.assertIn("resident_worker_presence", source)
        self.assertIn("The pulse already exists before this check", source)

    def test_existing_worker_is_reused_without_second_process(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "run_worker_runtime.py").write_text("# present\n", encoding="utf-8")
            receipt = root / repair.PROCESS_RECEIPT
            receipt.parent.mkdir(parents=True)
            receipt.write_text(json.dumps({"carrier_pid": 111, "worker_pid": 222}) + "\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(repair, "_alive", side_effect=lambda pid: pid in {111, 222}), mock.patch.object(repair.subprocess, "Popen") as popen:
                result = repair.ensure_worker_presence(root, carrier_pid=111)
            self.assertEqual(result["state"], "WORKER_ALREADY_PRESENT")
            self.assertFalse(result["worker_repair_attempted"])
            self.assertFalse(result["heartbeat_grants_execution_authority"])
            self.assertTrue(result["worker_coordinator_retains_admission_authority"])
            popen.assert_not_called()

    def test_missing_worker_is_repaired_and_tick_proven(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "run_worker_runtime.py").write_text("# present\n", encoding="utf-8")
            proc = mock.Mock(pid=333)
            alive = {111: True, 333: True}
            with mock.patch.dict(os.environ, {}, clear=True), \
                 mock.patch.object(repair, "_alive", side_effect=lambda pid: alive.get(pid, False)), \
                 mock.patch.object(repair.subprocess, "Popen", return_value=proc) as popen, \
                 mock.patch.object(repair, "_runtime_tick", return_value=7), \
                 mock.patch.object(repair, "_wait_for_tick", return_value={"observed": True, "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_OBSERVED", "baseline_tick": 7, "observed_tick": 8}):
                result = repair.ensure_worker_presence(root, carrier_pid=111)
            self.assertEqual(result["state"], "WORKER_REPAIRED")
            self.assertTrue(result["worker_repair_attempted"])
            self.assertFalse(result["heartbeat_grants_execution_authority"])
            self.assertTrue(result["worker_coordinator_retains_admission_authority"])
            self.assertTrue(result["request_drain_expected_on_worker_start"])
            popen.assert_called_once()
            retained = json.loads((root / repair.PROCESS_RECEIPT).read_text(encoding="utf-8"))
            self.assertEqual(retained["worker_pid"], 333)
            self.assertTrue(retained["worker_task_capable_cycle_observed"])
            self.assertEqual(retained["authority_effect"], "NONE_SUPERVISION_ONLY")

    def test_hosted_environment_cannot_become_runtime_repair_surface(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True):
            result = repair.ensure_worker_presence(Path(td), carrier_pid=111)
        self.assertEqual(result["state"], "HOSTED_ENVIRONMENT_REJECTED")
        self.assertFalse(result["worker_repair_attempted"])


if __name__ == "__main__":
    unittest.main()
