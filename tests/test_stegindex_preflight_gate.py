import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class StegIndexPreflightGateTests(unittest.TestCase):
    def run_gate(self, *args):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "stegindex_preflight_gate.py"), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(proc.stdout)

    def test_missing_root_is_exact_dependency(self):
        result = self.run_gate("--query", "heartbeat")
        self.assertEqual(result["adapter_state"], "STEGINDEX_ROOT_NOT_DECLARED")
        self.assertEqual(result["decision"], "EXACT_BLOCKER_ONLY")
        self.assertFalse(result["generic_blocker_permitted"])

    def test_missing_preflight_file_is_exact_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_gate(
                "--query", "heartbeat",
                "--stegindex-root", tmp,
            )
        self.assertEqual(result["adapter_state"], "STEGINDEX_SOURCE_UNAVAILABLE")
        self.assertEqual(result["decision"], "EXACT_BLOCKER_ONLY")
        self.assertFalse(result["generic_blocker_permitted"])

if __name__ == "__main__":
    unittest.main()
