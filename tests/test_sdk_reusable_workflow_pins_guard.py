"""Every Labs workflow call into StegVerse-SDK pins a full 40-hex SDK commit (V-P6)."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_sdk_reusable_workflow_pins as guard  # noqa: E402

SHA = "c138cad4c37db0bb675bc2c66515b5558cc5fa7b"
JOB = f"""jobs:
  evaluate:
    uses: StegVerse-org/StegVerse-SDK/.github/workflows/universal-intr-route-installation.yml@{SHA}
    with:
      request_path: control/request.json
      sdk_ref: {SHA}
  other:
    runs-on: ubuntu-latest
    steps:
      - run: echo sdk_ref is not judged outside the call
        with:
          sdk_ref: main
"""
STEP = f"""jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: SDK action
        uses: StegVerse-org/StegVerse-SDK/.github/actions/install@{SHA}
        with:
          sdk_ref: {SHA}
      - uses: actions/setup-python@v5
        with:
          sdk_ref: unrelated
"""
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")


def check(text):
    with tempfile.TemporaryDirectory() as temp:
        Path(temp, "w.yml").write_text(text, encoding="utf-8")
        return guard.check(Path(temp))


class SdkReusableWorkflowPinsTests(unittest.TestCase):
    def test_committed_workflows_pass(self):
        checked, failures = guard.check()
        self.assertEqual(failures, [])
        self.assertGreaterEqual(checked, 0)

    def test_full_commit_job_and_step_calls_pass(self):
        self.assertEqual(check(JOB), (1, []))
        self.assertEqual(check(STEP), (1, []))
        self.assertEqual(check(JOB.replace(f"@{SHA}", f"@{SHA} # pinned")), (1, []))

    def test_a_ref_that_is_not_a_full_commit_fails_closed_with_six_fields(self):
        for ref in ("main", "v1.2.0", SHA[:7], SHA[:39], SHA.upper(), SHA + "0", ""):
            for text in (JOB, STEP):
                with self.subTest(ref=ref, shape=text is JOB and "job" or "step"):
                    checked, failures = check(text.replace(f"@{SHA}", f"@{ref}", 1))
                    self.assertEqual(checked, 1)
                    self.assertEqual(len(failures), 1)
                    self.assertEqual(tuple(sorted(failures[0])), tuple(sorted(SIX)))
                    self.assertTrue(all(failures[0][field] for field in SIX))
                    self.assertEqual(failures[0]["failure_code"], "SDK_WORKFLOW_REF_NOT_FULL_COMMIT")
                    self.assertIn("w.yml:", failures[0]["failed_predicate"])

    def test_sdk_ref_other_than_the_uses_commit_fails_closed(self):
        for value in ("main", SHA[:12], "0" * 40):
            for text in (JOB, STEP):
                with self.subTest(sdk_ref=value):
                    checked, failures = check(text.replace(f"sdk_ref: {SHA}", f"sdk_ref: {value}"))
                    self.assertEqual(checked, 1)
                    self.assertEqual(len(failures), 1)
                    self.assertIn("sdk_ref", failures[0]["failed_predicate"])

    def test_calls_into_other_repositories_are_not_judged(self):
        self.assertEqual(check("      - uses: actions/checkout@v4\n"), (0, []))
        self.assertEqual(check("    uses: StegVerse-org/StegVerse-SDK-other/x.yml@main\n"), (0, []))

    def test_main_prints_six_field_records_and_exits_1(self):
        with tempfile.TemporaryDirectory() as temp:
            Path(temp, "w.yml").write_text(JOB.replace(f"@{SHA}", "@main", 1), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(guard.main(Path(temp)), 1)
            record = json.loads(out.getvalue().split("FAIL_CLOSED ", 1)[1])
            self.assertEqual(sorted(record), sorted(SIX))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(guard.main(Path(temp, "none")), 0)
            self.assertIn("SDK_WORKFLOW_PINS_PASS calls=0", out.getvalue())


if __name__ == "__main__":
    unittest.main()
