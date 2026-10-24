"""Report-and-receipt wrapper for the canonical work coordination validator.

Deterministic: each case points the wrapper at a throwaway fake validator in a
temp directory. Nothing reads the live registry or touches the network.
"""
import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "report_canonical_work_coordination_validation.py"
spec = importlib.util.spec_from_file_location("report_canonical_work_coordination_validation", SCRIPT)
report = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(report)


class ReportWrapperTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.summary = self.dir / "summary.md"
        patcher = mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(self.summary)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def fake(self, body):
        path = self.dir / "fake_validator.py"
        path.write_text(body, encoding="utf-8")
        return path

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = report.main(list(args) + ["--cwd", str(self.dir)])
        text = out.getvalue()
        receipt = json.loads(text[: text.rindex("}") + 1])
        return code, receipt, err.getvalue()

    def test_pass_is_reported_as_pass(self):
        validator = self.fake('print("PASS: canonical work coordination source contract is internally consistent")\n')
        code, receipt, _ = self.run_main("--validator", str(validator))
        self.assertEqual(code, 0)
        self.assertEqual(receipt["disposition"], "PASS")
        self.assertEqual(receipt["validator_exit_code"], 0)
        self.assertNotIn("failure_code", receipt)
        self.assertFalse(receipt["event_ledger_written"])

    def test_fail_closed_is_reported_with_six_fields_and_not_blocking(self):
        validator = self.fake('raise SystemExit("FAIL_CLOSED: FIXTURE-001: claim authority drift")\n')
        code, receipt, err = self.run_main("--validator", str(validator))
        self.assertEqual(code, 0)
        self.assertEqual(receipt["disposition"], "FAIL_CLOSED")
        self.assertFalse(receipt["blocking"])
        self.assertEqual(receipt["validator_exit_code"], 1)
        self.assertEqual(receipt["failed_predicate"], "FAIL_CLOSED: FIXTURE-001: claim authority drift")
        for key in report.SIX_FIELDS:
            self.assertIn(key, receipt)
            self.assertIn(f"{key}=", err)
        self.assertIn("claim authority drift", self.summary.read_text(encoding="utf-8"))

    def test_enforce_turns_fail_closed_into_nonzero_exit(self):
        validator = self.fake('raise SystemExit("FAIL_CLOSED: FIXTURE-001: claim authority drift")\n')
        code, receipt, _ = self.run_main("--validator", str(validator), "--enforce")
        self.assertEqual(code, 1)
        self.assertTrue(receipt["blocking"])

    def test_traceback_is_reported_as_fail_closed_not_pass(self):
        validator = self.fake('{}.get("x").get("y")\n')
        code, receipt, _ = self.run_main("--validator", str(validator))
        self.assertEqual(receipt["disposition"], "FAIL_CLOSED")
        self.assertNotEqual(receipt["validator_exit_code"], 0)
        self.assertIn("AttributeError", receipt["failed_predicate"])

    def test_missing_validator_fails_closed_even_without_enforce(self):
        code, receipt, _ = self.run_main("--validator", str(self.dir / "absent.py"))
        self.assertEqual(code, 1)
        self.assertEqual(receipt["failure_code"], report.WRAPPER_ERROR)
        self.assertTrue(receipt["blocking"])


if __name__ == "__main__":
    unittest.main()
