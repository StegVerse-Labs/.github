from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "trigger_reusable_task.py"
CONSTRUCTOR = ROOT / "scripts" / "materialize_reusable_task_construct.py"
REUSABLE_TASK_ID = "RT-NATIVE-EMAIL-ACTION-MONITOR-001"
TASK_ID = "STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001"
COSV_TASK_VECTOR = "10100000100000"

spec = importlib.util.spec_from_file_location("trigger_reusable_task", SCRIPT)
assert spec and spec.loader
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


class ReusableNativeEmailTriggerTests(unittest.TestCase):
    def test_native_email_runner_receives_source_and_runtime_roots_through_kv_wrapper(self) -> None:
        declared_runner = ROOT / "scripts" / "consume_native_email_action_monitor_request.py"
        command = subject.build_runner_command(
            "scripts/consume_native_email_action_monitor_request.py",
            declared_runner,
            {"source_root": str(ROOT), "runtime_root": str(ROOT)},
        )
        self.assertEqual(command[1], str(ROOT / "scripts" / "consume_native_email_action_monitor_request_kv.py"))
        self.assertIn("--source-root", command)
        self.assertIn("--runtime-root", command)
        self.assertEqual(command[command.index("--runtime-root") + 1], str(ROOT.resolve()))

    def test_native_email_runner_fails_closed_without_runtime_root(self) -> None:
        runner = ROOT / "scripts" / "consume_native_email_action_monitor_request.py"
        with self.assertRaises(SystemExit):
            subject.build_runner_command(
                "scripts/consume_native_email_action_monitor_request.py",
                runner,
                {"source_root": str(ROOT)},
            )

    def test_other_reusable_runners_are_unchanged(self) -> None:
        runner = ROOT / "scripts" / "check_example.py"
        command = subject.build_runner_command("scripts/check_example.py", runner, {"runtime_root": "/tmp/runtime"})
        self.assertEqual(command, [subject.sys.executable, str(runner)])


def _last_json_object(text: str) -> dict:
    """Parse the final JSON object a runner printed (its stdout tail may carry prose first)."""
    starts = [i for i, ch in enumerate(text) if ch == "{" and (i == 0 or text[i - 1] == "\n")]
    for start in reversed(starts):
        try:
            value = json.loads(text[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise AssertionError(f"no JSON object in runner stdout tail: {text[-500:]!r}")


class NativeEmailCanonicalPointerRegressionTests(unittest.TestCase):
    """Issue #3039: the hourly child invocation died before doing anything with
    `canonical COSV task pointer must resolve exactly once` because the
    effective COSV index carried no row for the tracking task the Healer
    scheduler pairs with RT-NATIVE-EMAIL-ACTION-MONITOR-001."""

    def test_canonical_cosv_task_pointer_resolves_exactly_once(self) -> None:
        spec = importlib.util.spec_from_file_location("materialize_reusable_task_construct_native_email", CONSTRUCTOR)
        assert spec and spec.loader
        constructor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(constructor)

        index = constructor.load_effective_cosv_index()
        rows = [row for row in index["tasks"] if row.get("task_id") == TASK_ID]
        self.assertEqual(len(rows), 1, rows)
        row = rows[0]
        self.assertEqual(row["vector"], COSV_TASK_VECTOR)
        self.assertEqual(row["cosv_task_vector"], COSV_TASK_VECTOR)
        self.assertEqual(row["vector_state"], "EMITTED")
        self.assertEqual(row["authority_effect"], "NONE")
        self.assertEqual(row["source_state_vector_ref"], f"control/task-vectors/{TASK_ID}.json")
        self.assertEqual(row["registry_ref"], f"data/canonical-task-records/{TASK_ID}.json")
        self.assertTrue((ROOT / row["registry_ref"]).is_file())
        self.assertTrue((ROOT / row["handoff_ref"]).is_file())
        # Must not raise: this is exactly the check the trigger runs before any runner.
        constructor.verify_task_pointer(TASK_ID, COSV_TASK_VECTOR, index)

    def test_trigger_passes_canonical_pointer_and_reaches_runner_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            receipt = runtime / "r.json"
            # Mirror scripts/run_reusable_task_scheduler.py: a minimal environment,
            # no GitHub token, TV/TVC credential authority, runtime root separated
            # from the source root.
            env = {
                "PATH": os.getenv("PATH", ""),
                "HOME": os.getenv("HOME", ""),
                "STEGVERSE_REPO_ROOTS_JSON": json.dumps({"StegVerse-Labs/.github": str(ROOT)}, sort_keys=True),
                "STEGVERSE_HEARTBEAT_ROOT": str(runtime),
                "STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY": "NONE",
                "STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY": "TV/TVC",
            }
            command = [
                sys.executable, str(SCRIPT),
                "--reusable-task-id", REUSABLE_TASK_ID,
                "--invocation-id", "test",
                "--parameters-json", json.dumps({"source_root": str(ROOT), "runtime_root": str(runtime)}, sort_keys=True),
                "--receipt", str(receipt),
                "--task-id", TASK_ID,
                "--cosv-task-vector", COSV_TASK_VECTOR,
            ]
            completed = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)

            self.assertNotIn("canonical COSV task pointer", completed.stderr)
            self.assertNotIn("task_id/COSV vector binding mismatch", completed.stderr)
            self.assertNotIn("canonical COSV index/source state-vector parity mismatch", completed.stderr)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(receipt.is_file(), completed.stderr)

            payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "stegverse.reusable-task-trigger-receipt/v1")
            self.assertEqual(payload["task_id"], TASK_ID)
            self.assertEqual(payload["cosv_task_vector"], COSV_TASK_VECTOR)
            self.assertTrue(payload["trigger_accepted"])
            self.assertFalse(payload["completion_claimed"])
            self.assertEqual(payload["authority_effect"], "NONE_ORCHESTRATION_ONLY")
            self.assertEqual(payload["effective_runner_ref"], "scripts/consume_native_email_action_monitor_request_kv.py")

            # The trigger now reaches the declared runner. Without a materialized
            # KnowledgeVault root the KV-enforcing runner fails closed before any
            # runtime execution; that is the legitimate boundary, not the pointer.
            self.assertEqual(payload["state"], "BOUNDARY_RECORDED")
            self.assertEqual(payload["boundary"]["kind"], subject.BOUNDARY_RUNNER_FAILED)
            self.assertEqual(payload["boundary"]["runner_ref"], "scripts/consume_native_email_action_monitor_request_kv.py")
            steps = payload["automatic_steps_attempted"]
            self.assertEqual(len(steps), 1)
            self.assertEqual(steps[0]["runner_ref"], "scripts/consume_native_email_action_monitor_request_kv.py")
            runner_result = _last_json_object(steps[0]["stdout_tail"])
            self.assertEqual(runner_result["schema"], "stegverse.native-email-action-monitor-request-consumption/v1")
            self.assertEqual(runner_result["task_id"], TASK_ID)
            self.assertEqual(runner_result["handoff_task_id"], TASK_ID)
            self.assertEqual(runner_result["handoff_cosv_task_vector"], COSV_TASK_VECTOR)
            self.assertEqual(runner_result["state"], "ATTEMPT_RECORDED")
            self.assertEqual(runner_result["pending_reason"], "KV_ROOT_NOT_MATERIALIZED")
            self.assertFalse(runner_result["runtime_execution_attempted"])
            self.assertFalse(runner_result["archive_permitted"])
            self.assertFalse(runner_result["credential_material_exported"])
            self.assertEqual(runner_result["github_token_runtime_authority"], "NONE")
            self.assertEqual(runner_result["credential_authority"], "TV/TVC")


if __name__ == "__main__":
    unittest.main()
