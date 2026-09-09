from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "trigger_reusable_task.py"

spec = importlib.util.spec_from_file_location("trigger_reusable_task", SCRIPT)
assert spec and spec.loader
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


class ReusableNativeEmailTriggerTests(unittest.TestCase):
    def test_native_email_runner_receives_source_and_runtime_roots(self) -> None:
        runner = ROOT / "scripts" / "consume_native_email_action_monitor_request.py"
        command = subject.build_runner_command(
            "scripts/consume_native_email_action_monitor_request.py",
            runner,
            {"source_root": str(ROOT), "runtime_root": str(ROOT)},
        )
        self.assertEqual(command[1], str(runner))
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


if __name__ == "__main__":
    unittest.main()
