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
        self.assertNotIn("STEGVERSE_SOVEREIGN_NODE", env)
        self.assertNotIn("STEGVERSE_HEARTBEAT_SOURCE_ROOT", env)
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("GH_TOKEN", env)
        self.assertNotIn("GITHUB_ACTIONS", env)
        self.assertNotIn("RENDER", env)
        self.assertNotIn("UNRELATED_SECRET", env)


    def test_clean_exec_env_allows_only_nonsecret_sovereign_runtime_locators(self) -> None:
        env = mod.clean_exec_env({
            "PATH": "/bin",
            "HOME": "/home/stegverse",
            "LOCALAPPDATA": "C:/StegVerse",
            "STEGVERSE_SOVEREIGN_NODE": "1",
            "STEGVERSE_HEARTBEAT_ROOT": "/srv/stegverse/runtime",
            "STEGVERSE_HEARTBEAT_SOURCE_ROOT": "/srv/stegverse/source",
            "STEGVERSE_STEGCORE_SOURCE_ROOT": "/srv/stegverse/StegCore",
            "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT": "/srv/stegverse/master-records/core-lite",
            "GITHUB_TOKEN": "forbidden",
            "GH_TOKEN": "forbidden",
            "GITHUB_ACTIONS": "true",
            "ZEROEX_API_KEY": "forbidden",
        })
        self.assertEqual(env["STEGVERSE_SOVEREIGN_NODE"], "1")
        self.assertEqual(env["STEGVERSE_HEARTBEAT_ROOT"], "/srv/stegverse/runtime")
        self.assertEqual(env["STEGVERSE_HEARTBEAT_SOURCE_ROOT"], "/srv/stegverse/source")
        self.assertEqual(env["STEGVERSE_STEGCORE_SOURCE_ROOT"], "/srv/stegverse/StegCore")
        self.assertEqual(
            env["STEGVERSE_MASTER_RECORDS_SOURCE_ROOT"],
            "/srv/stegverse/master-records/core-lite",
        )
        self.assertEqual(env["LOCALAPPDATA"], "C:/StegVerse")
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("GH_TOKEN", env)
        self.assertNotIn("GITHUB_ACTIONS", env)
        self.assertNotIn("ZEROEX_API_KEY", env)

    def _write_claimed_g18_registry(self, runtime: Path, *, state: str = "BLOCKED", claim: bool = True) -> None:
        (runtime / "control").mkdir(parents=True, exist_ok=True)
        task = {
            "task_id": "SHWP-DURABLE-RUNTIME-ACTIVATION",
            "state": state,
            "worker_id": "sovereign-runtime-activation-worker" if claim else None,
            "worker_instance_id": "sovereign-runtime-activation-worker-HB15-G18" if claim else None,
            "claim_id": "SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18" if claim else None,
            "heartbeat_timing": {"fencing_token": 18} if claim else {},
        }
        (runtime / mod.REGISTRY_REF).write_text(
            json.dumps({"generation": 22, "tasks": [task]}) + "\n",
            encoding="utf-8",
        )

    def test_claimed_task_snapshot_requires_existing_claim_and_fence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            self._write_claimed_g18_registry(runtime)
            snapshot = mod.claimed_task_snapshot(runtime, "SHWP-DURABLE-RUNTIME-ACTIVATION")
            self.assertEqual(snapshot["state"], "BLOCKED")
            self.assertEqual(snapshot["claim_id"], "SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18")
            self.assertEqual(snapshot["fencing_token"], 18)

            self._write_claimed_g18_registry(runtime, state="HANDOFF_READY", claim=False)
            with self.assertRaisesRegex(RuntimeError, "ACTIVE/BLOCKED/RETRY"):
                mod.claimed_task_snapshot(runtime, "SHWP-DURABLE-RUNTIME-ACTIVATION")

    def test_resume_existing_claim_uses_targeted_cycle_without_new_claim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / "scripts").mkdir(parents=True)
            (runtime / "scripts/run_worker_runtime.py").write_text("# runner\n", encoding="utf-8")
            (runtime / mod.CARRIER_REF).parent.mkdir(parents=True, exist_ok=True)
            (runtime / mod.CARRIER_REF).write_text('{"epoch":32}\n', encoding="utf-8")
            self._write_claimed_g18_registry(runtime)
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout='{"state":"BLOCKED","transition_id":"SOVEREIGN_RUNTIME_ELIGIBLE_SURFACE_REQUIRED"}\n',
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
                    resume_claimed_task_id="SHWP-DURABLE-RUNTIME-ACTIVATION",
                    runner=runner,
                    env={
                        "PATH": "/bin",
                        "HOME": "/home/stegverse",
                        "STEGVERSE_SOVEREIGN_NODE": "1",
                        "STEGVERSE_HEARTBEAT_SOURCE_ROOT": "/srv/stegverse/source",
                        "GITHUB_TOKEN": "forbidden",
                    },
                )

            self.assertEqual(receipt["mode"], "RESUME_EXISTING_CLAIM")
            self.assertEqual(receipt["existing_claim_preflight"]["fencing_token"], 18)
            self.assertEqual(receipt["existing_claim_postflight"]["fencing_token"], 18)
            self.assertFalse(receipt["new_claim_requested"])
            self.assertTrue(receipt["existing_fence_preserved_by_mode"])
            self.assertIn("--task-id", calls[0][0])
            self.assertIn("SHWP-DURABLE-RUNTIME-ACTIVATION", calls[0][0])
            self.assertNotIn("GITHUB_TOKEN", calls[0][1]["env"])
            self.assertEqual(calls[0][1]["env"]["STEGVERSE_SOVEREIGN_NODE"], "1")
            self.assertEqual(
                receipt["execution_result"]["transition_id"],
                "SOVEREIGN_RUNTIME_ELIGIBLE_SURFACE_REQUIRED",
            )

    def test_resume_existing_claim_refuses_unclaimed_task_before_runner(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            runtime = base / "runtime"
            source.mkdir()
            (runtime / "scripts").mkdir(parents=True)
            (runtime / "scripts/run_worker_runtime.py").write_text("# runner\n", encoding="utf-8")
            (runtime / mod.CARRIER_REF).parent.mkdir(parents=True, exist_ok=True)
            (runtime / mod.CARRIER_REF).write_text('{"epoch":32}\n', encoding="utf-8")
            self._write_claimed_g18_registry(runtime, state="HANDOFF_READY", claim=False)
            runner = mock.Mock()

            with mock.patch.object(
                mod,
                "refresh",
                return_value={
                    "schema": "stegverse.sovereign-worker-runtime-source-refresh/v1",
                    "mutable_runtime_state_preserved": True,
                },
            ):
                with self.assertRaisesRegex(RuntimeError, "ACTIVE/BLOCKED/RETRY"):
                    mod.refresh_and_execute(
                        source,
                        runtime,
                        resume_claimed_task_id="SHWP-DURABLE-RUNTIME-ACTIVATION",
                        runner=runner,
                    )
            runner.assert_not_called()

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
