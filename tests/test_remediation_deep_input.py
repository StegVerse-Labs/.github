"""remediation_endpoint: a deeply nested --packet is a terminal input fault (F-SCAN-RECURSION).

About 400 KB nested past the parser's recursion limit is the caller's bad
input, like any other: a terminal six-field CLI_INPUT_INVALID, a non-zero exit,
nothing written and no traceback. Supplied epochs are 4096.

Source validation only. No authority effect is claimed.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")


class RemediationDeepInputTests(unittest.TestCase):
    def test_a_deep_packet_is_terminal_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            packet = work / "packet.json"
            packet.write_text('{"a":' + "[" * 200000)
            state = work / "state"
            env = {**os.environ, "STEGVERSE_REPO_LEDGER_ROOT": str(state / "repo"),
                   "STEGVERSE_ORG_LEDGER_ROOT": str(state / "org"), "PYTHONDONTWRITEBYTECODE": "1"}
            completed = subprocess.run(
                [sys.executable, "-B", str(ROOT / "resident-runtime/remediation_endpoint.py"),
                 "--packet", str(packet), "--out", str(work / "out.json"), "--hb-epoch", "4096"],
                capture_output=True, text=True, cwd=work, env=env, timeout=120)
            self.assertNotEqual(completed.returncode, 0)
            self.assertNotIn("Traceback", completed.stderr)
            record = json.loads(completed.stdout.strip().splitlines()[-1])
            self.assertEqual(record["failure_code"], "CLI_INPUT_INVALID")
            self.assertIs(record["terminal"], True)
            self.assertIn("RecursionError", record["detail"])
            for field in SIX_FIELDS:
                self.assertTrue(str(record.get(field) or "").strip(), field)
            self.assertFalse((work / "out.json").exists())
            self.assertFalse(state.exists())


if __name__ == "__main__":
    unittest.main()
