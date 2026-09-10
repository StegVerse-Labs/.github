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

    def test_start_launches_separate_carrier_and_worker_and_requires_worker_tick(self):
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
                "OPENAI_API_KEY": "must-not-leak",
                "AWS_SECRET_ACCESS_KEY": "must-not-leak",
                "RANDOM_PROVIDER_TOKEN": "must-not-leak",
                "SESSION_COOKIE": "must-not-leak",
                "PATH": "/usr/bin:/bin",
                "LANG": "C.UTF-8",
                "STEGVERSE_STEGOS_ROOT": "/srv/stegos",
            }
            tick = {
                "observed": True,
                "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_OBSERVED",
                "baseline_tick": 2,
                "observed_tick": 3,
                "observed_carrier_epoch": 31,
                "observed_carrier_generation": 31,
            }
            with (
                mock.patch.dict(supervisor.os.environ, env, clear=True),
                mock.patch.object(supervisor.subprocess, "Popen", side_effect=fake_popen),
                mock.patch.object(supervisor, "_runtime_tick", return_value=2),
                mock.patch.object(supervisor, "_wait_for_worker_tick", return_value=tick) as wait_tick,
                mock.patch.object(supervisor, "_alive", return_value=True),
            ):
                result = supervisor.start(root, interval_ms=10.0)

            self.assertEqual(len(spawned), 2)
            self.assertIn("run_heartbeat_runtime.py", spawned[0][0][1])
            self.assertIn("run_worker_runtime.py", spawned[1][0][1])
            self.assertIn("--continuous", spawned[0][0])
            self.assertIn("--continuous", spawned[1][0])
            self.assertNotEqual(result["carrier_pid"], result["worker_pid"])
            self.assertTrue(result["carrier_active"])
            self.assertTrue(result["worker_active"])
            self.assertTrue(result["worker_task_capable_cycle_observed"])
            self.assertEqual(result["worker_tick_evidence"]["observed_tick"], 3)
            self.assertTrue(result["separate_carrier_and_worker_processes"])
            self.assertEqual(result["canonical_carrier_runtime"], "heartbeat_runtime.engine_v13.HeartbeatRuntime")
            self.assertEqual(result["worker_runtime"], "heartbeat_runtime.worker_runtime.WorkerCoordinator")
            self.assertFalse(result["non_tv_tvc_secret_or_token_used"])
            self.assertFalse(result["parent_environment_inherited"])
            self.assertTrue(result["child_environment_allowlist_enforced"])
            wait_tick.assert_called_once()
            for _command, child_env in spawned:
                for name in (
                    *supervisor.FORBIDDEN_ENV,
                    "OPENAI_API_KEY",
                    "AWS_SECRET_ACCESS_KEY",
                    "RANDOM_PROVIDER_TOKEN",
                    "SESSION_COOKIE",
                ):
                    self.assertNotIn(name, child_env)
                self.assertEqual(child_env["PATH"], "/usr/bin:/bin")
                self.assertEqual(child_env["LANG"], "C.UTF-8")
                self.assertEqual(child_env["STEGVERSE_STEGOS_ROOT"], "/srv/stegos")
                self.assertEqual(child_env["STEGVERSE_SOVEREIGN_NODE"], "1")
                self.assertEqual(child_env["STEGVERSE_HEARTBEAT_ROOT"], str(root.resolve()))
                self.assertEqual(child_env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")
                self.assertEqual(child_env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"], "NONE")

    def test_child_env_is_explicit_allowlist_not_pattern_guessing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = supervisor.child_env(
                root,
                {
                    "PATH": "/bin",
                    "STEGVERSE_STEGOS_ROOT": "/stegos",
                    "STEGVERSE_MADE_UP_SECRET": "do-not-forward",
                    "UNKNOWN_TOKEN": "do-not-forward",
                    "DATABASE_URL": "do-not-forward",
                },
            )
            self.assertEqual(result["PATH"], "/bin")
            self.assertEqual(result["STEGVERSE_STEGOS_ROOT"], "/stegos")
            self.assertNotIn("STEGVERSE_MADE_UP_SECRET", result)
            self.assertNotIn("UNKNOWN_TOKEN", result)
            self.assertNotIn("DATABASE_URL", result)

    def test_start_fails_closed_when_worker_tick_is_not_observed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._runtime_root(tmp)
            spawned = []

            def fake_popen(command, **kwargs):
                spawned.append(list(command))
                return SimpleNamespace(pid=800 + len(spawned))

            with (
                mock.patch.object(supervisor.subprocess, "Popen", side_effect=fake_popen),
                mock.patch.object(supervisor, "_runtime_tick", return_value=2),
                mock.patch.object(
                    supervisor,
                    "_wait_for_worker_tick",
                    return_value={
                        "observed": False,
                        "reason": "TASK_CAPABLE_WORKER_RUNTIME_TICK_TIMEOUT",
                        "baseline_tick": 2,
                        "observed_tick": 2,
                    },
                ),
                mock.patch.object(supervisor, "_terminate", return_value=True) as terminate,
            ):
                with self.assertRaisesRegex(RuntimeError, "TASK_CAPABLE_WORKER_RUNTIME_TICK_TIMEOUT"):
                    supervisor.start(root, interval_ms=10.0)

            self.assertEqual(len(spawned), 2)
            self.assertEqual(terminate.call_count, 2)

    def test_wait_for_worker_tick_requires_state_advance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._runtime_root(tmp)
            ticks = iter([2, 2, 3])
            with (
                mock.patch.object(supervisor, "_alive", return_value=True),
                mock.patch.object(supervisor, "_runtime_tick", side_effect=lambda _root: next(ticks)),
                mock.patch.object(supervisor.time, "sleep", return_value=None),
            ):
                result = supervisor._wait_for_worker_tick(root, 2, 999, timeout=1.0)
            self.assertTrue(result["observed"])
            self.assertEqual(result["observed_tick"], 3)

    def test_restart_replaces_both_processes_only_with_task_capable_tick(self):
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
                "worker_task_capable_cycle_observed": True,
            }
            with mock.patch.object(supervisor, "_terminate", side_effect=[True, True]) as terminate, mock.patch.object(supervisor, "start", return_value=dict(fresh)):
                result = supervisor.restart(root)

            self.assertEqual([call.args[0] for call in terminate.call_args_list], [11, 12])
            self.assertTrue(result["carrier_restart_observed"])
            self.assertTrue(result["worker_restart_observed"])
            self.assertTrue(result["restart_observed"])

            with mock.patch.object(supervisor, "_terminate", side_effect=[True, False]), mock.patch.object(supervisor, "start") as start:
                with self.assertRaisesRegex(RuntimeError, "previous_ephemeral_process_teardown_incomplete"):
                    supervisor.restart(root)
            start.assert_not_called()

    def test_teardown_verifies_no_supervised_process_residue_and_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._runtime_root(tmp)
            process = root / supervisor.PROCESS_RECEIPT
            process.parent.mkdir(parents=True, exist_ok=True)
            process.write_text('{"carrier_pid": 41, "worker_pid": 42}\n', encoding="utf-8")
            durable = root / "return-queue" / "sovereign-relay" / "evidence.json"
            durable.parent.mkdir(parents=True, exist_ok=True)
            durable.write_text('{"durable":true}\n', encoding="utf-8")

            with (
                mock.patch.object(supervisor, "_terminate", side_effect=[True, True]),
                mock.patch.object(supervisor, "_alive", side_effect=[False, False]),
            ):
                result = supervisor.teardown(root)

            self.assertEqual(result["state"], "TEARDOWN_COMPLETE")
            self.assertTrue(result["no_supervised_process_residue"])
            self.assertFalse(result["durable_evidence_deleted"])
            self.assertFalse(result["same_root_reinstantiation_allowed"])
            self.assertTrue(result["same_root_continuation_requires_restart"])
            self.assertTrue(durable.is_file())
            self.assertTrue((root / supervisor.TEARDOWN_RECEIPT).is_file())

    def test_new_ephemeral_instance_requires_unused_or_empty_runtime_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            missing = base / "missing"
            empty = base / "empty"
            empty.mkdir()
            supervisor.assert_fresh_runtime_root(missing)
            supervisor.assert_fresh_runtime_root(empty)

            reused = base / "reused"
            (reused / "control").mkdir(parents=True)
            (reused / "control" / "worker-runtime-state.json").write_text('{"runtime_tick":99}\n', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "fresh_ephemeral_runtime_root_required"):
                supervisor.assert_fresh_runtime_root(reused)

    def test_ephemeral_service_receipt_requires_both_v13_processes(self):
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
            self.assertEqual(receipt["canonical_runtime"], "heartbeat_runtime.engine_v13.HeartbeatRuntime")
            self.assertEqual(receipt["canonical_carrier_runtime"], "heartbeat_runtime.engine_v13.HeartbeatRuntime")
            self.assertEqual(receipt["worker_runtime"], "heartbeat_runtime.worker_runtime.WorkerCoordinator")
            self.assertFalse(receipt["heartbeat_grants_execution_authority"])

            missing_worker = dict(process)
            missing_worker["worker_pid"] = None
            self.assertFalse(_service_receipt(root, root / "runtime", missing_worker, 10.0)["active"])


if __name__ == "__main__":
    unittest.main()
