from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import restart_sovereign_ephemeral_node as supervisor
from scripts.run_sovereign_ephemeral_console import _service_receipt


class EphemeralSeparatedRuntimeSupervisionTests(unittest.TestCase):
    def _runtime_root(self, tmp: str) -> Path:
        root = Path(tmp)
        scripts = root / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "run_heartbeat_runtime.py").write_text("# carrier\n", encoding="utf-8")
        (scripts / "run_worker_runtime.py").write_text("# worker\n", encoding="utf-8")
        return root

    def test_start_launches_separate_carrier_and_worker_without_runtime_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._runtime_root(tmp)
            spawned = []

            def fake_popen(command, **kwargs):
                spawned.append((list(command), dict(kwargs.get("env") or {})))
                return SimpleNamespace(pid=700 + len(spawned))

            env = {
                "GITHUB_TOKEN": "forbidden",
                "GH_TOKEN": "forbidden",
                "STEGVERSE_GITHUB_TOKEN": "forbidden",
                "TVC_TOKEN": "forbidden",
                "PATH": "/usr/bin:/bin",
            }
            with mock.patch.dict(supervisor.os.environ, env, clear=True), mock.patch.object(supervisor.subprocess, "Popen", side_effect=fake_popen):
                result = supervisor.start(root, interval_ms=10.0)

            self.assertEqual(len(spawned), 2)
            self.assertIn("run_heartbeat_runtime.py", spawned[0][0][1])
            self.assertIn("run_worker_runtime.py", spawned[1][0][1])
            self.assertNotEqual(result["carrier_pid"], result["worker_pid"])
            self.assertTrue(result["carrier_active"])
            self.assertTrue(result["worker_active"])
            self.assertTrue(result["separate_carrier_and_worker_processes"])
            self.assertEqual(result["canonical_carrier_runtime"], "heartbeat_runtime.engine_v12.HeartbeatRuntime")
            self.assertEqual(result["worker_runtime"], "heartbeat_runtime.worker_runtime.WorkerCoordinator")
            self.assertFalse(result["non_tv_tvc_secret_or_token_used"])
            for _command, child_env in spawned:
                for name in supervisor.FORBIDDEN_ENV:
                    self.assertEqual(child_env.get(name), "")

    def test_restart_replaces_both_processes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._runtime_root(tmp)
            receipt = root / supervisor.PROCESS_RECEIPT
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text('{"carrier_pid": 11, "worker_pid": 12, "pid": 11}\n', encoding="utf-8")

            fresh = {
                "carrier_pid": 21,
                "worker_pid": 22,
                "pid": 21,
                "active": True,
                "carrier_active": True,
                "worker_active": True,
            }
            with mock.patch.object(supervisor, "_terminate", side_effect=[True, True]) as terminate, mock.patch.object(supervisor, "start", return_value=dict(fresh)):
                result = supervisor.restart(root)

            self.assertEqual([call.args[0] for call in terminate.call_args_list], [11, 12])
            self.assertTrue(result["carrier_restart_observed"])
            self.assertTrue(result["worker_restart_observed"])
            self.assertTrue(result["restart_observed"])

    def test_ephemeral_service_receipt_requires_both_v12_processes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            process = {
                "active": True,
                "carrier_active": True,
                "worker_active": True,
                "carrier_pid": 31,
                "worker_pid": 32,
            }
            receipt = _service_receipt(root, root / "runtime", process, 10.0)
            self.assertTrue(receipt["active"])
            self.assertTrue(receipt["separate_carrier_and_worker_processes"])
            self.assertEqual(receipt["canonical_carrier_runtime"], "heartbeat_runtime.engine_v12.HeartbeatRuntime")
            self.assertEqual(receipt["worker_runtime"], "heartbeat_runtime.worker_runtime.WorkerCoordinator")

            missing_worker = dict(process)
            missing_worker["worker_pid"] = None
            self.assertFalse(_service_receipt(root, root / "runtime", missing_worker, 10.0)["active"])


if __name__ == "__main__":
    unittest.main()
