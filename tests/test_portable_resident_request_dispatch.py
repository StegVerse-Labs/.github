from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "refresh_and_dispatch_resident_requests.py"
SPEC = importlib.util.spec_from_file_location("portable_resident_dispatch", MODULE_PATH)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class PortableResidentDispatchTests(unittest.TestCase):
    def test_hosted_environment_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "hosted environment"):
            MOD.clean_exec_env({"PATH": "/bin", "HOME": "/tmp", "GITHUB_ACTIONS": "true"})

    def test_credential_environment_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "credential-bearing environment"):
            MOD.clean_exec_env({"PATH": "/bin", "HOME": "/tmp", "GITHUB_TOKEN": "forbidden"})

    def test_refresh_then_dispatch_targets_only_current_basis_consumer(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            runtime.mkdir()
            dispatcher = runtime / MOD.DISPATCHER_REL
            dispatcher.parent.mkdir(parents=True)
            dispatcher.write_text("# refreshed dispatcher\n", encoding="utf-8")
            dispatch_receipt = runtime / MOD.DISPATCH_RECEIPT_REL
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                dispatch_receipt.parent.mkdir(parents=True, exist_ok=True)
                dispatch_receipt.write_text(json.dumps({
                    "schema": "stegverse.resident-request-dispatch/v1",
                    "state": "DISPATCH_COMPLETE",
                    "registered_consumer_count": 12,
                    "consumer_count": 1,
                    "selected_consumers": [MOD.TARGET_CONSUMER],
                    "selection_scope": "EXACT_SELECTOR",
                    "consumers_visited": 1,
                    "request_failures": [],
                    "request_failure_blocks_later_requests": False,
                    "network_source_fetch_performed": False,
                    "credential_authority": "TV/TVC",
                    "github_token_required": False,
                    "github_token_runtime_authority": "NONE",
                    "heartbeat_grants_execution_authority": False,
                    "request_dispatch_grants_authority": False,
                    "second_machine_required": False,
                    "authority_effect": "NONE_DISPATCH_ONLY",
                }) + "\n", encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            refresh_receipt = {
                "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
                "mutable_runtime_state_preserved": True,
                "network_fetch_performed": False,
                "credential_read_or_acquired": False,
                "authority_effect": "NONE_LOCAL_SOURCE_REFRESH",
            }
            with mock.patch.object(MOD, "refresh", return_value=refresh_receipt):
                result = MOD.refresh_and_dispatch(
                    source,
                    runtime,
                    runner=runner,
                    env={
                        "PATH": "/bin",
                        "HOME": td,
                        "STEGVERSE_SOURCE_MATERIALIZATION_ROOT": str(base / "components"),
                        "STEGVERSE_SOURCE_PACKAGE_ROOT": str(base / "packages"),
                    },
                )

            self.assertEqual(result["state"], "REFRESH_AND_DISPATCH_COMPLETE")
            self.assertTrue(result["dispatch_receipt_observed"])
            self.assertTrue(result["exact_consumer_selection_observed"])
            self.assertEqual(result["target_consumer"], MOD.TARGET_CONSUMER)
            self.assertFalse(result["unrelated_consumers_dispatched"])
            self.assertFalse(result["bridge_grants_execution_authority"])
            self.assertFalse(result["bridge_mints_claim_or_fence"])
            self.assertFalse(result["network_source_fetch_performed"])
            self.assertFalse(result["credential_read_or_acquired"])
            self.assertFalse(result["systemd_required"])
            self.assertFalse(result["second_machine_required"])
            self.assertEqual(len(calls), 1)
            command, kwargs = calls[0]
            self.assertEqual(Path(command[1]), dispatcher)
            self.assertIn("--only-consumer", command)
            self.assertEqual(command[command.index("--only-consumer") + 1], MOD.TARGET_CONSUMER)
            self.assertEqual(kwargs["cwd"], runtime)
            self.assertEqual(kwargs["env"]["STEGVERSE_SOURCE_PACKAGE_ROOT"], str(base / "packages"))
            self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
            self.assertTrue((runtime / MOD.RECEIPT_REL).is_file())

    def test_dispatch_failure_is_recorded_without_becoming_success(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            runtime.mkdir()
            dispatcher = runtime / MOD.DISPATCHER_REL
            dispatcher.parent.mkdir(parents=True)
            dispatcher.write_text("# dispatcher\n", encoding="utf-8")
            dispatch_receipt = runtime / MOD.DISPATCH_RECEIPT_REL

            def runner(_command, **_kwargs):
                dispatch_receipt.parent.mkdir(parents=True, exist_ok=True)
                dispatch_receipt.write_text(json.dumps({
                    "schema": "stegverse.resident-request-dispatch/v1",
                    "state": "DISPATCH_INCOMPLETE",
                    "consumer_count": 1,
                    "selected_consumers": [MOD.TARGET_CONSUMER],
                    "selection_scope": "EXACT_SELECTOR",
                    "request_failures": [MOD.TARGET_CONSUMER],
                }) + "\n", encoding="utf-8")
                return SimpleNamespace(returncode=1, stdout="", stderr="")

            with mock.patch.object(MOD, "refresh", return_value={
                "mutable_runtime_state_preserved": True,
                "network_fetch_performed": False,
                "credential_read_or_acquired": False,
            }):
                result = MOD.refresh_and_dispatch(source, runtime, runner=runner, env={"PATH": "/bin", "HOME": td})
            self.assertEqual(result["state"], "REFRESH_COMPLETE_DISPATCH_INCOMPLETE")
            self.assertEqual(result["dispatch_receipt"]["request_failures"], [MOD.TARGET_CONSUMER])

    def test_refresh_then_dispatch_targets_only_hil_when_selected(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            runtime.mkdir()
            dispatcher = runtime / MOD.DISPATCHER_REL
            dispatcher.parent.mkdir(parents=True)
            dispatcher.write_text("# refreshed dispatcher\n", encoding="utf-8")
            dispatch_receipt = runtime / MOD.DISPATCH_RECEIPT_REL
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                dispatch_receipt.parent.mkdir(parents=True, exist_ok=True)
                dispatch_receipt.write_text(json.dumps({
                    "schema": "stegverse.resident-request-dispatch/v1",
                    "state": "DISPATCH_COMPLETE",
                    "consumer_count": 1,
                    "selected_consumers": ["hil"],
                    "selection_scope": "EXACT_SELECTOR",
                    "request_failures": [],
                }) + "\n", encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with mock.patch.object(MOD, "refresh", return_value={
                "mutable_runtime_state_preserved": True,
                "network_fetch_performed": False,
                "credential_read_or_acquired": False,
            }):
                result = MOD.refresh_and_dispatch(
                    source,
                    runtime,
                    target_consumer="hil",
                    runner=runner,
                    env={"PATH": "/bin", "HOME": td},
                )

            self.assertEqual(result["state"], "REFRESH_AND_DISPATCH_COMPLETE")
            self.assertEqual(result["target_consumer"], "hil")
            self.assertEqual(result["dispatch_receipt"]["selected_consumers"], ["hil"])
            self.assertEqual(len(calls), 1)
            command, _ = calls[0]
            self.assertEqual(command[command.index("--only-consumer") + 1], "hil")

    def _assert_sv002_exact_target(self, target_consumer: str) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            runtime.mkdir()
            dispatcher = runtime / MOD.DISPATCHER_REL
            dispatcher.parent.mkdir(parents=True)
            dispatcher.write_text("# refreshed dispatcher\n", encoding="utf-8")
            dispatch_receipt = runtime / MOD.DISPATCH_RECEIPT_REL
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                dispatch_receipt.parent.mkdir(parents=True, exist_ok=True)
                dispatch_receipt.write_text(json.dumps({
                    "schema": "stegverse.resident-request-dispatch/v1",
                    "state": "DISPATCH_COMPLETE",
                    "consumer_count": 1,
                    "selected_consumers": [target_consumer],
                    "selection_scope": "EXACT_SELECTOR",
                    "request_failures": [],
                    "network_source_fetch_performed": False,
                    "credential_authority": "TV/TVC",
                    "github_token_required": False,
                    "github_token_runtime_authority": "NONE",
                    "request_dispatch_grants_authority": False,
                    "authority_effect": "NONE_DISPATCH_ONLY",
                }) + "\n", encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            refresh_receipt = {
                "mutable_runtime_state_preserved": True,
                "network_fetch_performed": False,
                "credential_read_or_acquired": False,
                "authority_effect": "NONE_LOCAL_SOURCE_REFRESH",
            }
            with mock.patch.object(MOD, "refresh", return_value=refresh_receipt) as refresh_call:
                result = MOD.refresh_and_dispatch(
                    source,
                    runtime,
                    target_consumer=target_consumer,
                    runner=runner,
                    env={"PATH": "/bin", "HOME": td},
                )

            refresh_call.assert_called_once_with(source, runtime)
            self.assertEqual(len(calls), 1)
            command, kwargs = calls[0]
            self.assertEqual(Path(command[1]), dispatcher)
            self.assertEqual(command[command.index("--only-consumer") + 1], target_consumer)
            self.assertEqual(kwargs["cwd"], runtime)
            self.assertEqual(result["dispatch_receipt"]["selection_scope"], "EXACT_SELECTOR")
            self.assertEqual(result["dispatch_receipt"]["selected_consumers"], [target_consumer])
            self.assertEqual(result["dispatch_receipt"]["consumer_count"], 1)
            self.assertFalse(result["unrelated_consumers_dispatched"])
            self.assertFalse(result["bridge_grants_execution_authority"])
            self.assertFalse(result["network_source_fetch_performed"])
            self.assertFalse(result["credential_read_or_acquired"])
            self.assertNotIn("GITHUB_TOKEN", kwargs["env"])

    def test_refresh_then_dispatch_targets_only_sv002_self_characterization(self):
        self._assert_sv002_exact_target("sv002_self_characterization")

    def test_refresh_then_dispatch_targets_only_sv002_public_observation(self):
        self._assert_sv002_exact_target("sv002_public_observation")

    def test_refresh_then_dispatch_targets_only_healer_sovereign_scheduler(self):
        self._assert_sv002_exact_target("healer_sovereign_scheduler")
        env = MOD.clean_exec_env({
            "PATH": "/bin",
            "HOME": "/tmp",
            "STEGVERSE_HEALER_ROOT": "/local/healer",
            "STEGVERSE_HIL_INTR_ROUTE_CONFIG": "/local/config/hil-intr-runtime.json",
        })
        self.assertEqual(env["STEGVERSE_HEALER_ROOT"], "/local/healer")
        self.assertEqual(env["STEGVERSE_HIL_INTR_ROUTE_CONFIG"], "/local/config/hil-intr-runtime.json")

    def test_unapproved_consumer_fails_before_refresh(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source"
            runtime = Path(td) / "runtime"
            source.mkdir()
            runtime.mkdir()
            with mock.patch.object(MOD, "refresh") as refresh:
                with self.assertRaisesRegex(RuntimeError, "unsupported portable resident consumer"):
                    MOD.refresh_and_dispatch(
                        source,
                        runtime,
                        target_consumer="g18",
                        env={"PATH": "/bin", "HOME": td},
                    )
                refresh.assert_not_called()

    def test_incomplete_refresh_fails_before_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            runtime.mkdir()
            calls = []
            with mock.patch.object(MOD, "refresh", return_value={
                "mutable_runtime_state_preserved": False,
                "network_fetch_performed": False,
                "credential_read_or_acquired": False,
            }):
                with self.assertRaisesRegex(RuntimeError, "preserve mutable runtime state"):
                    MOD.refresh_and_dispatch(source, runtime, runner=lambda *args, **kwargs: calls.append((args, kwargs)), env={"PATH": "/bin", "HOME": td})
            self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
