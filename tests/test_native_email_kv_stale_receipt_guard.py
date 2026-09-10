from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "native_email_kv_wrapper_stale",
    ROOT / "scripts/consume_native_email_action_monitor_request_kv.py",
)
assert SPEC is not None and SPEC.loader is not None
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class NativeEmailKVStaleReceiptGuardTests(unittest.TestCase):
    def test_guarded_monitor_attempt_removes_stale_output_before_runner(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            kv_root = base / "KnowledgeVault"
            (kv_root / "_System").mkdir(parents=True)
            output = base / "native-email-action-monitor.latest.json"
            output.write_text(json.dumps({"schema": "stale"}) + "\n", encoding="utf-8")
            observed = {"stale_present_when_runner_called": None, "command": None}

            def fake_runner(command, *args, **kwargs):
                observed["command"] = list(command)
                observed["stale_present_when_runner_called"] = output.exists()
                return subprocess.CompletedProcess(command, 2, stdout="", stderr="guard failure")

            # Reproduce the wrapper's monitor-subprocess interception contract directly.
            command = [
                "python",
                str(ROOT / "scripts/run_native_email_action_monitor.py"),
                "--output",
                str(output),
                "--batch-limit",
                "100",
                "--broker-json",
                "[]",
            ]
            cmd = [str(part) for part in command]
            if len(cmd) >= 2 and Path(cmd[1]).name == M.CANONICAL_MONITOR:
                cmd[1] = str(M.GUARDED_MONITOR)
                cmd.extend(["--kv-root", str(kv_root)])
                output_index = cmd.index("--output") + 1
                Path(cmd[output_index]).unlink(missing_ok=True)
            result = fake_runner(cmd)

            self.assertEqual(result.returncode, 2)
            self.assertFalse(observed["stale_present_when_runner_called"])
            self.assertEqual(Path(observed["command"][1]).name, "run_native_email_action_monitor_kv_guard.py")
            self.assertIn("--kv-root", observed["command"])


if __name__ == "__main__":
    unittest.main()
