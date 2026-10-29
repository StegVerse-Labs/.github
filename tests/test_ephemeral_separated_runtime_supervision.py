from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import repair_resident_worker_presence as repair
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

    def _pinned(self, carrier_pid: int, worker_pid: int) -> list:
        # Stand-ins for the pidfds the identity proof pins; the code under test closes them.
        return [
            ("carrier", carrier_pid, os.open(os.devnull, os.O_RDONLY)),
            ("worker", worker_pid, os.open(os.devnull, os.O_RDONLY)),
        ]

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
            with mock.patch.object(supervisor, "_proven_previous_processes", return_value=(self._pinned(11, 12), None)), \
                 mock.patch.object(repair, "_terminate_process", side_effect=[True, True]) as terminate, \
                 mock.patch.object(supervisor, "start", return_value=dict(fresh)):
                result = supervisor.restart(root)

            self.assertEqual([call.args[0] for call in terminate.call_args_list], [11, 12])
            self.assertTrue(result["carrier_restart_observed"])
            self.assertTrue(result["worker_restart_observed"])
            self.assertTrue(result["restart_observed"])

            with mock.patch.object(supervisor, "_proven_previous_processes", return_value=(self._pinned(11, 12), None)), \
                 mock.patch.object(repair, "_terminate_process", side_effect=[True, False]), \
                 mock.patch.object(supervisor, "start") as start:
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
                mock.patch.object(supervisor, "_proven_previous_processes", return_value=(self._pinned(41, 42), None)),
                mock.patch.object(repair, "_terminate_process", side_effect=[True, True]),
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


@unittest.skipUnless(Path("/proc/self/cmdline").is_file(), "process identity is read from /proc")
class ReceiptPidIdentityBeforeTeardownTests(unittest.TestCase):
    """teardown()/restart() signal only processes proven to be this root's carrier/worker (#1620/#3299)."""

    SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
                  "retry_entrypoint", "owning_existing_goal", "next_attempt")

    def _root(self, tmp: str) -> Path:
        root = Path(tmp).resolve()
        (root / "scripts").mkdir()
        (root / "scripts" / "run_heartbeat_runtime.py").write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
        (root / "scripts" / "run_worker_runtime.py").write_text(
            "import json, sys, time\nfrom pathlib import Path\n"
            "root = Path(sys.argv[sys.argv.index('--root') + 1])\n"
            "(root / 'control').mkdir(exist_ok=True)\n"
            "(root / 'control' / 'worker-runtime-state.json').write_text(json.dumps({'runtime_tick': 1}))\n"
            "time.sleep(60)\n",
            encoding="utf-8",
        )
        return root

    def _spawn(self, command: list[str]) -> subprocess.Popen:
        process = subprocess.Popen(command)
        self.addCleanup(process.wait)
        self.addCleanup(process.kill)
        return process

    def _runner(self, root: Path, role: str) -> subprocess.Popen:
        runner = {"carrier": "run_heartbeat_runtime.py", "worker": "run_worker_runtime.py"}[role]
        return self._spawn([sys.executable, str(root / "scripts" / runner), "--root", str(root)])

    def _write_receipt(self, root: Path, receipt: dict) -> None:
        path = root / supervisor.PROCESS_RECEIPT
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")

    def _assert_refused(self, result: dict, predicate: str) -> None:
        self.assertEqual(result["state"], "FAIL_CLOSED")
        self.assertEqual(result["failure_code"], "STALE_WORKER_IDENTITY_UNPROVEN")
        self.assertEqual(result["failed_predicate"], predicate)
        for field in self.SIX_FIELDS:
            self.assertTrue(result[field], field)
        self.assertFalse(result["process_signalled"])

    def test_teardown_never_signals_an_unrelated_receipt_pid(self):
        victim = self._spawn([sys.executable, "-c", "import time; time.sleep(60)"])
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            self._write_receipt(root, {"carrier_pid": victim.pid, "worker_pid": victim.pid})
            result = supervisor.teardown(root)
            self.assertEqual(json.loads((root / supervisor.TEARDOWN_RECEIPT).read_text())["state"], "FAIL_CLOSED")
        self.assertIsNone(victim.poll())
        self._assert_refused(result, "RECEIPT_PID_RUNS_THIS_ROOT_CARRIER_ENTRYPOINT")
        self.assertEqual(result["retry_entrypoint"], "scripts/restart_sovereign_ephemeral_node.py::teardown")

    def test_restart_kills_nothing_and_starts_nothing_when_one_receipt_pid_is_unproven(self):
        victim = self._spawn([sys.executable, "-c", "import time; time.sleep(60)"])
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            carrier = self._runner(root, "carrier")
            self._write_receipt(root, {
                "carrier_pid": carrier.pid, "carrier_start_ticks": supervisor.proc_start_ticks(carrier.pid),
                "worker_pid": victim.pid,
            })
            with mock.patch.object(supervisor, "start") as start:
                result = supervisor.restart(root)
            self.assertIsNone(carrier.poll())
        self.assertIsNone(victim.poll())
        self._assert_refused(result, "RECEIPT_PID_RUNS_THIS_ROOT_WORKER_ENTRYPOINT")
        self.assertFalse(result["restart_observed"])
        start.assert_not_called()

    def test_teardown_never_signals_a_reused_worker_pid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            worker = self._runner(root, "worker")
            ticks = supervisor.proc_start_ticks(worker.pid)
            self.assertIsInstance(ticks, int)
            self._write_receipt(root, {"worker_pid": worker.pid, "worker_start_ticks": ticks - 1})
            result = supervisor.teardown(root)
            self.assertIsNone(worker.poll())
        self._assert_refused(result, "RECEIPT_PID_START_TIME_MATCHES_RECORDED_WORKER")

    def test_teardown_still_stops_the_processes_start_spawned(self):
        # The console tears down the peers it just started; start() records both start
        # times, so their identity is provable and they are still stopped.
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            spawned = supervisor.start(root)
            pids = (spawned["carrier_pid"], spawned["worker_pid"])
            self.addCleanup(lambda: [supervisor._terminate(pid) for pid in pids])
            self.assertIsInstance(spawned.get("carrier_start_ticks"), int)
            self.assertIsInstance(spawned.get("worker_start_ticks"), int)
            result = supervisor.teardown(root)
        self.assertNotEqual(result["state"], "FAIL_CLOSED")
        self.assertTrue(result["carrier_terminated"])
        self.assertTrue(result["worker_terminated"])
        for pid in pids:
            _, status = os.waitpid(pid, 0)
            self.assertEqual(os.WTERMSIG(status), signal.SIGTERM)

    def test_restart_still_stops_proven_processes_before_starting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            carrier, worker = self._runner(root, "carrier"), self._runner(root, "worker")
            self._write_receipt(root, {
                "carrier_pid": carrier.pid, "carrier_start_ticks": supervisor.proc_start_ticks(carrier.pid),
                "worker_pid": worker.pid, "worker_start_ticks": supervisor.proc_start_ticks(worker.pid),
            })
            reapers = [threading.Thread(target=p.wait, daemon=True) for p in (carrier, worker)]
            for reaper in reapers:  # no zombie left to look alive
                reaper.start()
            fresh = {"carrier_pid": 1, "worker_pid": 2, "worker_task_capable_cycle_observed": True}
            with mock.patch.object(supervisor, "start", return_value=fresh) as start:
                result = supervisor.restart(root)
            for reaper in reapers:
                reaper.join(timeout=5)
        self.assertEqual(carrier.returncode, -signal.SIGTERM)
        self.assertEqual(worker.returncode, -signal.SIGTERM)
        self.assertTrue(result["restart_observed"])
        start.assert_called_once()


if __name__ == "__main__":
    unittest.main()
