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

    def test_refresh_then_dispatch_uses_refreshed_runtime_dispatcher(self):
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
                    "consumer_count": 11,
                    "consumers_visited": 11,
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
            self.assertFalse(result["bridge_grants_execution_authority"])
            self.assertFalse(result["bridge_mints_claim_or_fence"])
            self.assertFalse(result["network_source_fetch_performed"])
            self.assertFalse(result["credential_read_or_acquired"])
            self.assertFalse(result["systemd_required"])
            self.assertFalse(result["second_machine_required"])
            self.assertEqual(len(calls), 1)
            command, kwargs = calls[0]
            self.assertEqual(Path(command[1]), dispatcher)
            self.assertEqual(kwargs["cwd"], runtime)
            self.assertEqual(
                kwargs["env"]["STEGVERSE_SOURCE_PACKAGE_ROOT"],
                str(base / "packages"),
            )
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
                    "request_failures": ["cross_framework_current_basis_v04"],
                }) + "\n", encoding="utf-8")
                return SimpleNamespace(returncode=1, stdout="", stderr="")

            with mock.patch.object(MOD, "refresh", return_value={
                "mutable_runtime_state_preserved": True,
                "network_fetch_performed": False,
                "credential_read_or_acquired": False,
            }):
                result = MOD.refresh_and_dispatch(
                    source,
                    runtime,
                    runner=runner,
                    env={"PATH": "/bin", "HOME": td},
                )
            self.assertEqual(result["state"], "REFRESH_COMPLETE_DISPATCH_INCOMPLETE")
            self.assertEqual(
                result["dispatch_receipt"]["request_failures"],
                ["cross_framework_current_basis_v04"],
            )

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
                    MOD.refresh_and_dispatch(
                        source,
                        runtime,
                        runner=lambda *args, **kwargs: calls.append((args, kwargs)),
                        env={"PATH": "/bin", "HOME": td},
                    )
            self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
