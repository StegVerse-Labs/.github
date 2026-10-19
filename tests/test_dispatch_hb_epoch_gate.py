"""The workflow-dispatch epoch gate is the kernel's six-field refusal (B-P36d).

organization-ledger-transition.yml used a shell `case` that emitted a custom
DISPATCH_HB_EPOCH_INVALID and accepted '0' or '31'. Its writer step now runs
scripts/check_dispatch_hb_epoch.py, which applies writer_epoch_refusal. A
workflow_dispatch string input cannot tell empty from absent, so '' and unset
are HB_EPOCH_NOT_SUPPLIED; '+33', ' 33', fullwidth digits, '33.0', '31' and
'abc' are HB_EPOCH_INVALID; '4096' passes.

Source validation only. No authority effect is claimed.
"""
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "check_dispatch_hb_epoch.py"
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
ENTRY = ".github/workflows/organization-ledger-transition.yml (workflow_dispatch input hb_epoch)"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")


def gate(value):
    env = {k: v for k, v in os.environ.items() if k != "HB_EPOCH"}
    if value is not None:
        env["HB_EPOCH"] = value
    return subprocess.run([sys.executable, "-B", str(GATE), "HB_EPOCH", ENTRY],
                          capture_output=True, text=True, env=env, timeout=60)


class DispatchEpochGateTests(unittest.TestCase):
    def assertRefused(self, value, code):
        completed = gate(value)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        refusal = json.loads(completed.stdout)
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
        self.assertEqual(refusal["failure_code"], code)
        self.assertEqual(refusal["failed_predicate"], "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
        self.assertEqual(refusal["retry_entrypoint"], ENTRY)
        for field in SIX_FIELDS:
            self.assertTrue(refusal[field], field)

    def test_empty_and_unset_are_not_supplied(self):
        for value in ("", None):
            with self.subTest(value=value):
                self.assertRefused(value, "HB_EPOCH_NOT_SUPPLIED")

    def test_coerced_fractional_sub_anchor_and_non_digit_values_are_invalid(self):
        for value in ("+33", " 33", "３３", "33.0", "31", "abc"):
            with self.subTest(value=value):
                self.assertRefused(value, "HB_EPOCH_INVALID")

    def test_4096_passes(self):
        completed = gate("4096")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(completed.stdout, "")

    def test_the_writer_step_gates_through_the_kernel_before_the_append(self):
        text = (ROOT / ".github/workflows/organization-ledger-transition.yml").read_text(encoding="utf-8")
        self.assertNotIn("DISPATCH_HB_EPOCH_INVALID", text)
        self.assertNotIn('case "$HB_EPOCH"', text)
        gate_at = text.index("python scripts/check_dispatch_hb_epoch.py HB_EPOCH")
        self.assertLess(gate_at, text.index('--hb-epoch "$HB_EPOCH"'))

    def test_no_workflow_keeps_an_inline_epoch_check(self):
        inline = re.compile(r'case "\$\{?(HB_EPOCH|STEGVERSE_HB_EPOCH)|int\(os\.environ\[["\'](HB_EPOCH|STEGVERSE_HB_EPOCH)')
        for path in WORKFLOWS:
            with self.subTest(workflow=path.name):
                self.assertIsNone(inline.search(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
