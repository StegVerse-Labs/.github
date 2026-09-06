from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import repair_resident_worker_presence as repair


class HB32SelfHealStartupGraceTests(unittest.TestCase):
    def _root(self, td: str) -> Path:
        root = Path(td)
        (root / "scripts").mkdir(parents=True)
        (root / "scripts" / "run_worker_runtime.py").write_text("# present\n", encoding="utf-8")
        return root

    def test_live_new_worker_timeout_is_retained_not_terminated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            proc = mock.Mock(pid=333)
            timeout_evidence = {
                "observed": False,
                "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_TIMEOUT",
                "baseline_tick": 7,
                "observed_tick": 7,
            }
            projected = {"resident": {"present_worker_runtime_observed": False}}
            with mock.patch.dict(repair.os.environ, {}, clear=True), \
                 mock.patch.object(repair, "_alive", side_effect=lambda pid: pid in {111, 333}), \
                 mock.patch.object(repair.subprocess, "Popen", return_value=proc), \
                 mock.patch.object(repair, "_runtime_tick", return_value=7), \
                 mock.patch.object(repair, "_wait_for_tick", return_value=timeout_evidence), \
                 mock.patch.object(repair, "_persist_presence_projection", return_value=projected), \
                 mock.patch.object(repair, "_terminate_process") as terminate:
                result = repair.ensure_worker_presence(root, carrier_pid=111)

            self.assertEqual(result["state"], "WORKER_REPAIR_PENDING_TASK_CAPABLE_TICK")
            self.assertTrue(result["process_retained_for_next_supervision_check"])
            self.assertFalse(result["present_worker_runtime_observed"])
            terminate.assert_not_called()
            retained = json.loads((root / repair.PROCESS_RECEIPT).read_text(encoding="utf-8"))
            self.assertEqual(retained["worker_pid"], 333)
            self.assertFalse(retained["worker_task_capable_cycle_observed"])
            self.assertEqual(retained["worker_tick_evidence"]["baseline_tick"], 7)

    def test_pending_worker_reuses_exact_pid_until_tick_advances(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            state = root / repair.WORKER_STATE
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps({
                "schema": "stegverse.worker-runtime-state/v1",
                "runtime_tick": 7,
                "observation_mode": "TASK_CAPABLE_WORKER_COORDINATOR",
            }) + "\n", encoding="utf-8")
            receipt = root / repair.PROCESS_RECEIPT
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(json.dumps({
                "carrier_pid": 111,
                "worker_pid": 333,
                "worker_task_capable_cycle_observed": False,
                "worker_tick_evidence": {
                    "observed": False,
                    "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_TIMEOUT",
                    "baseline_tick": 7,
                    "observed_tick": 7,
                },
            }) + "\n", encoding="utf-8")
            projected = {"resident": {"present_worker_runtime_observed": False}}
            with mock.patch.dict(repair.os.environ, {}, clear=True), \
                 mock.patch.object(repair, "_alive", side_effect=lambda pid: pid in {111, 333}), \
                 mock.patch.object(repair, "_persist_presence_projection", return_value=projected), \
                 mock.patch.object(repair, "_terminate_process") as terminate, \
                 mock.patch.object(repair.subprocess, "Popen") as popen:
                result = repair.ensure_worker_presence(root, carrier_pid=111)

            self.assertEqual(result["state"], "WORKER_PRESENT_AWAITING_TASK_CAPABLE_TICK")
            self.assertEqual(result["worker_pid"], 333)
            self.assertTrue(result["process_retained_for_next_supervision_check"])
            terminate.assert_not_called()
            popen.assert_not_called()

            state.write_text(json.dumps({
                "schema": "stegverse.worker-runtime-state/v1",
                "runtime_tick": 8,
                "observation_mode": "TASK_CAPABLE_WORKER_COORDINATOR",
            }) + "\n", encoding="utf-8")
            projected_present = {"resident": {"present_worker_runtime_observed": True}}
            with mock.patch.dict(repair.os.environ, {}, clear=True), \
                 mock.patch.object(repair, "_alive", side_effect=lambda pid: pid in {111, 333}), \
                 mock.patch.object(repair, "_persist_presence_projection", return_value=projected_present), \
                 mock.patch.object(repair, "_persist_presence_master_records_intake", return_value={"state": "MASTER_RECORDS_ROOT_NOT_DECLARED"}), \
                 mock.patch.object(repair, "_terminate_process") as terminate, \
                 mock.patch.object(repair.subprocess, "Popen") as popen:
                result = repair.ensure_worker_presence(root, carrier_pid=111)

            self.assertEqual(result["state"], "WORKER_ALREADY_PRESENT")
            self.assertEqual(result["worker_pid"], 333)
            self.assertEqual(result["worker_tick_evidence"]["baseline_tick"], 7)
            self.assertEqual(result["worker_tick_evidence"]["observed_tick"], 8)
            terminate.assert_not_called()
            popen.assert_not_called()

    def test_previously_proven_stale_worker_still_recycles(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            state = root / repair.WORKER_STATE
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps({
                "schema": "stegverse.worker-runtime-state/v1",
                "runtime_tick": 12,
                "observation_mode": "TASK_CAPABLE_WORKER_COORDINATOR",
            }) + "\n", encoding="utf-8")
            receipt = root / repair.PROCESS_RECEIPT
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(json.dumps({
                "carrier_pid": 111,
                "worker_pid": 222,
                "worker_task_capable_cycle_observed": True,
            }) + "\n", encoding="utf-8")
            proc = mock.Mock(pid=333)
            stale_projection = {"resident": {"worker_cycle_fresh": False}}
            repaired_projection = {"resident": {"present_worker_runtime_observed": True}}
            with mock.patch.dict(repair.os.environ, {}, clear=True), \
                 mock.patch.object(repair, "_alive", side_effect=lambda pid: pid in {111, 222, 333}), \
                 mock.patch.object(repair, "project", return_value=stale_projection), \
                 mock.patch.object(repair, "_terminate_process", return_value=True) as terminate, \
                 mock.patch.object(repair.subprocess, "Popen", return_value=proc), \
                 mock.patch.object(repair, "_runtime_tick", return_value=12), \
                 mock.patch.object(repair, "_wait_for_tick", return_value={
                     "observed": True,
                     "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_OBSERVED",
                     "baseline_tick": 12,
                     "observed_tick": 13,
                 }), \
                 mock.patch.object(repair, "_persist_presence_projection", return_value=repaired_projection), \
                 mock.patch.object(repair, "_persist_presence_master_records_intake", return_value={"state": "MASTER_RECORDS_ROOT_NOT_DECLARED"}):
                result = repair.ensure_worker_presence(root, carrier_pid=111)

            self.assertEqual(result["state"], "STALE_WORKER_RECYCLED")
            self.assertEqual(result["stale_worker_pid"], 222)
            terminate.assert_called_once_with(222)


if __name__ == "__main__":
    unittest.main()
