from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "run_test_lanes_with_tvc_registration.py"
SPEC = importlib.util.spec_from_file_location("run_test_lanes_with_tvc_registration", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class TestLanesRegistrationWrapperTests(unittest.TestCase):
    def test_wrapper_uses_hidden_tty_registrar_and_direct_runner_only(self) -> None:
        text = PATH.read_text(encoding="utf-8")
        self.assertIn("scripts/register_tvc_provider_keys_interactive.py", text)
        self.assertIn("scripts/run_test_lanes_direct.py", text)
        self.assertNotIn("OPENAI_API_KEY", text)
        self.assertNotIn("ANTHROPIC_API_KEY", text)
        self.assertNotIn("DEEPSEEK_API_KEY", text)
        self.assertNotIn("MOONSHOT_API_KEY", text)
        self.assertNotIn("heartbeat-carrier-runtime-state", text)
        self.assertNotIn("SHWP-DURABLE-RUNTIME-ACTIVATION", text)

    def test_canonical_workload_defaults_follow_invoking_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp).resolve()
            with patch.object(MODULE, "invoking_home", return_value=home):
                self.assertEqual(MODULE.workload_default("TVC"), home / ".stegverse" / "workloads" / "TVC")
                self.assertEqual(MODULE.workload_default("workflows"), home / ".stegverse" / "workloads" / "workflows")

    def test_wrapper_requires_root_for_registration_lifecycle(self) -> None:
        text = PATH.read_text(encoding="utf-8")
        self.assertIn("os.geteuid() != 0", text)
        self.assertIn("run this wrapper with sudo", text)

    def test_registration_subprocess_receives_sanitized_environment(self) -> None:
        text = PATH.read_text(encoding="utf-8")
        self.assertIn('"PYTHONPATH": str(governance_root)', text)
        self.assertIn('"HOME": str(invoking_home())', text)
        self.assertNotIn('registration = subprocess.run(\n            [sys.executable, str(registrar)],\n            cwd=governance_root,\n            check=False,\n            env=os.environ', text)


if __name__ == "__main__":
    unittest.main()
