from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_worker_runtime.py"
SPEC = importlib.util.spec_from_file_location("run_worker_runtime_native_dispatch", MODULE_PATH)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class NativeResidentRequestDispatchTests(unittest.TestCase):
    def test_missing_dispatcher_is_non_authorizing(self):
        with tempfile.TemporaryDirectory() as td:
            result = MOD.dispatch_local_resident_requests(Path(td))
        self.assertEqual(result["state"], "DISPATCHER_NOT_MATERIALIZED")
        self.assertFalse(result["runtime_execution_attempted"])
        self.assertFalse(result["request_dispatch_grants_authority"])
        self.assertFalse(result["heartbeat_grants_execution_authority"])

    def test_dispatcher_receipt_is_retained_as_runtime_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dispatcher = root / MOD.LOCAL_REQUEST_DISPATCHER_REL
            dispatcher.parent.mkdir(parents=True, exist_ok=True)
            dispatcher.write_text("# dispatcher\n", encoding="utf-8")
            receipt_path = root / MOD.LOCAL_REQUEST_DISPATCH_RECEIPT_REL
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                receipt_path.parent.mkdir(parents=True, exist_ok=True)
                receipt_path.write_text(json.dumps({
                    "schema": "stegverse.resident-request-dispatch/v1",
                    "state": "DISPATCH_COMPLETE",
                    "selection_scope": "ALL_REGISTERED",
                    "consumers_visited": 16,
                    "request_failures": [],
                    "request_dispatch_grants_authority": False,
                    "heartbeat_grants_execution_authority": False,
                    "credential_authority": "TV/TVC",
                    "github_token_runtime_authority": "NONE",
                }) + "\n", encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            result = MOD.dispatch_local_resident_requests(root, runner=runner)

        self.assertEqual(result["state"], "DISPATCH_COMPLETE")
        self.assertEqual(result["returncode"], 0)
        self.assertTrue(result["runtime_execution_attempted"])
        self.assertFalse(result["request_dispatch_grants_authority"])
        self.assertFalse(result["heartbeat_grants_execution_authority"])
        self.assertTrue(result["worker_coordinator_remains_execution_admission_authority"])
        self.assertEqual(result["credential_authority"], "TV/TVC")
        self.assertEqual(len(calls), 1)
        command, kwargs = calls[0]
        self.assertEqual(Path(command[1]), dispatcher)
        self.assertEqual(command[command.index("--source-root") + 1], str(root))
        self.assertEqual(command[command.index("--runtime-root") + 1], str(root))
        self.assertEqual(kwargs["cwd"], root)

    def test_local_source_refresh_uses_only_already_local_canonical_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            runtime = base / "runtime"
            source = base / "source"
            runtime.mkdir()
            source.mkdir()
            script = runtime / MOD.LOCAL_SOURCE_REFRESH_REL
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text("# refresh\n", encoding="utf-8")
            receipt_path = runtime / "receipts" / "sovereign-host" / "worker-source-refresh.latest.json"
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                receipt_path.parent.mkdir(parents=True, exist_ok=True)
                receipt_path.write_text(json.dumps({
                    "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
                    "state": "REFRESH_COMPLETE",
                    "network_fetch_performed": False,
                    "credential_read_or_acquired": False,
                    "mutable_runtime_state_preserved": True,
                }) + "\n", encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            result = MOD.refresh_local_worker_source(
                runtime,
                runner=runner,
                env={
                    "PATH": "/bin",
                    "HOME": td,
                    "STEGVERSE_HEARTBEAT_SOURCE_ROOT": str(source),
                },
            )

        self.assertEqual(result["state"], "REFRESH_COMPLETE")
        self.assertTrue(result["attempted"])
        self.assertFalse(result["network_fetch_performed"])
        self.assertFalse(result["credential_read_or_acquired"])
        self.assertFalse(result["heartbeat_grants_execution_authority"])
        self.assertEqual(len(calls), 1)
        command, kwargs = calls[0]
        self.assertEqual(Path(command[1]), script)
        self.assertEqual(command[command.index("--source-root") + 1], str(source.resolve()))
        self.assertEqual(command[command.index("--runtime-root") + 1], str(runtime.resolve()))
        self.assertEqual(kwargs["cwd"], runtime.resolve())

    def test_local_source_refresh_is_optional_without_source_locator(self):
        with tempfile.TemporaryDirectory() as td:
            result = MOD.refresh_local_worker_source(
                Path(td),
                env={"PATH": "/bin", "HOME": td},
            )
        self.assertIsNone(result)

    def test_native_sweep_is_hb_scale_logical_tick_paced_not_wall_clock_authority(self):
        self.assertEqual(MOD.LOCAL_REQUEST_DISPATCH_INTERVAL_TICKS, 100)
        self.assertEqual(MOD.LOCAL_SOURCE_REFRESH_INTERVAL_TICKS, 100)
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertIn("index % LOCAL_REQUEST_DISPATCH_INTERVAL_TICKS == 0", source)
        self.assertIn("index % LOCAL_SOURCE_REFRESH_INTERVAL_TICKS == 0", source)
        self.assertIn("heartbeat_grants_execution_authority\": False", source)
        self.assertNotIn("LOCAL_REQUEST_DISPATCH_INTERVAL_SECONDS", source)

    def test_worker_cycle_precedes_potentially_long_initial_maintenance(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        loop_start = source.index("while running and (args.continuous or index < args.cycles):")
        loop = source[loop_start:]
        cycle = loop.index("result = runtime.cycle(write=not args.dry_run, target_task_id=args.task_id)")
        rendezvous = loop.index("rendezvous_result = poll_resident_rendezvous(root)")
        refresh = loop.index("local_source_refresh = refresh_local_worker_source(root)")
        dispatch = loop.index("local_request_dispatch = dispatch_local_resident_requests(root)")
        continuation = loop.index("result[\"hb_machine_continuation\"] = maybe_dispatch_machine_continuation")
        self.assertLess(cycle, rendezvous)
        self.assertLess(cycle, refresh)
        self.assertLess(cycle, dispatch)
        self.assertLess(cycle, continuation)
        self.assertIn("Persist the task-capable WorkerCoordinator tick before any potentially", loop)


if __name__ == "__main__":
    unittest.main()
