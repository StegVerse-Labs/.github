from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import refresh_and_execute_resident_task as mod


class PortableRefreshTargetedExecutionTests(unittest.TestCase):
    def test_clean_exec_env_strips_github_and_hosted_authority(self) -> None:
        source = {
            "PATH": "/bin",
            "HOME": "/home/stegverse",
            "LANG": "C.UTF-8",
            "STEGVERSE_TVC_ROOT": "/srv/stegverse/TVC",
            "STEGVERSE_LLM_ADAPTER_ROOT": "/srv/stegverse/LLM-adapter",
            "GITHUB_TOKEN": "forbidden",
            "GH_TOKEN": "forbidden",
            "GITHUB_ACTIONS": "true",
            "RENDER": "true",
            "UNRELATED_SECRET": "forbidden",
        }
        env = mod.clean_exec_env(source)
        self.assertEqual(env["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"], "TV/TVC")
        self.assertEqual(env["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"], "NONE")
        self.assertEqual(env["STEGVERSE_TVC_ROOT"], "/srv/stegverse/TVC")
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("GH_TOKEN", env)
        self.assertNotIn("GITHUB_ACTIONS", env)
        self.assertNotIn("RENDER", env)
        self.assertNotIn("UNRELATED_SECRET", env)

    def test_generic_command_targets_exactly_one_task(self) -> None:
        runtime = Path("/tmp/stegverse-runtime")
        command = mod.execution_command(
            runtime,
            task_id="COSV-LIVE-PACKET-AUTOMATION-006",
            ecosystem_chat_parent=False,
        )
        self.assertEqual(
            command,
            [
                sys.executable,
                str(runtime / "scripts/run_worker_runtime.py"),
                "--root",
                str(runtime),
                "--task-id",
                "COSV-LIVE-PACKET-AUTOMATION-006",
            ],
        )

    def test_ecosystem_chat_uses_dedicated_parent_executor(self) -> None:
        runtime = Path("/tmp/stegverse-runtime")
        command = mod.execution_command(
            runtime,
            task_id=None,
            ecosystem_chat_parent=True,
        )
        self.assertEqual(
            command,
            [
                sys.executable,
                str(runtime / "scripts/run_independent_ecosystem_chat_parent.py"),
                "--root",
                str(runtime),
            ],
        )
        with self.assertRaises(ValueError):
            mod.execution_command(
                runtime,
                task_id="SHWP-ECOSYSTEM-CHAT-INFERENCE-001",
                ecosystem_chat_parent=True,
            )

    def test_generic_refresh_then_execute_requires_preserved_carrier(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / "scripts").mkdir(parents=True)
            (runtime / "scripts/run_worker_runtime.py").write_text("# runner\n", encoding="utf-8")
            with mock.patch.object(
                mod,
                "refresh",
                return_value={
                    "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
                    "mutable_runtime_state_preserved": True,
                },
            ):
                with self.assertRaisesRegex(RuntimeError, "preserved separated carrier"):
                    mod.refresh_and_execute(
                        source,
                        runtime,
                        task_id="COSV-LIVE-PACKET-AUTOMATION-006",
                    )

    def test_generic_refresh_then_execute_writes_secret_free_attempt_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / "scripts").mkdir(parents=True)
            (runtime / "control").mkdir(parents=True)
            (runtime / "scripts/run_worker_runtime.py").write_text("# runner\n", encoding="utf-8")
            (runtime / mod.CARRIER_REF).write_text('{"epoch":31}\n', encoding="utf-8")
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout='{"state":"HANDOFF_READY","transition_id":"NO_NEW_REFERENCE"}\n',
                    stderr="",
                )

            with mock.patch.object(
                mod,
                "refresh",
                return_value={
                    "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
                    "mutable_runtime_state_preserved": True,
                    "network_fetch_performed": False,
                },
            ):
                receipt = mod.refresh_and_execute(
                    source,
                    runtime,
                    task_id="COSV-LIVE-PACKET-AUTOMATION-006",
                    runner=runner,
                    env={
                        "PATH": "/bin",
                        "HOME": "/home/stegverse",
                        "GITHUB_TOKEN": "forbidden",
                    },
                )

            self.assertEqual(len(calls), 1)
            self.assertIn("--task-id", calls[0][0])
            self.assertNotIn("GITHUB_TOKEN", calls[0][1]["env"])
            self.assertTrue(receipt["runtime_execution_attempted"])
            self.assertFalse(receipt["source_refresh_is_runtime_execution"])
            self.assertFalse(receipt["systemd_required_for_one_shot"])
            self.assertFalse(receipt["second_machine_required"])
            self.assertFalse(receipt["github_token_required"])
            self.assertEqual(receipt["github_token_runtime_authority"], "NONE")
            self.assertEqual(receipt["credential_authority"], "TV/TVC")
            self.assertFalse(receipt["credential_value_exposed"])
            self.assertEqual(receipt["execution_result"]["transition_id"], "NO_NEW_REFERENCE")
            saved = json.loads((runtime / mod.RECEIPT_REL).read_text(encoding="utf-8"))
            self.assertEqual(saved["task_id"], "COSV-LIVE-PACKET-AUTOMATION-006")

    def test_dedicated_parent_does_not_require_carrier_bootstrap_or_systemd(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / "scripts").mkdir(parents=True)
            (runtime / "scripts/run_independent_ecosystem_chat_parent.py").write_text("# parent\n", encoding="utf-8")

            def runner(command, **kwargs):
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout='{"state":"HANDOFF_READY","transition_id":"SOVEREIGN_LOCAL_MODEL_CAPSULE_NOT_MATERIALIZED"}\n',
                    stderr="",
                )

            with mock.patch.object(
                mod,
                "refresh",
                return_value={
                    "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
                    "mutable_runtime_state_preserved": True,
                },
            ):
                receipt = mod.refresh_and_execute(
                    source,
                    runtime,
                    ecosystem_chat_parent=True,
                    runner=runner,
                )
            self.assertEqual(receipt["mode"], "DEDICATED_ECOSYSTEM_CHAT_PARENT")
            self.assertEqual(receipt["task_id"], "SHWP-ECOSYSTEM-CHAT-INFERENCE-001")
            self.assertFalse(receipt["systemd_required_for_one_shot"])
            self.assertEqual(
                receipt["execution_result"]["transition_id"],
                "SOVEREIGN_LOCAL_MODEL_CAPSULE_NOT_MATERIALIZED",
            )


if __name__ == "__main__":
    unittest.main()
