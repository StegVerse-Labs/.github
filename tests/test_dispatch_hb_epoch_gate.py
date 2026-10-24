"""The workflow-dispatch epoch gate is the kernel's six-field refusal (B-P36d).

organization-ledger-transition.yml used a shell `case` that emitted a custom
DISPATCH_HB_EPOCH_INVALID and accepted '0' or '31'. Its writer step now runs
scripts/check_dispatch_hb_epoch.py, which applies writer_epoch_refusal. A
workflow_dispatch string input cannot tell empty from absent, so '' and unset
are HB_EPOCH_NOT_SUPPLIED; '+33', ' 33', fullwidth digits, '33.0', '31' and
'abc' are HB_EPOCH_INVALID; '4096' passes.

No workflow keeps an inline epoch check, with one recorded exception. A
workflow that runs in this repository's own checkout (push, pull_request,
workflow_dispatch, workflow_run) has the gate script on disk. A workflow_call
reusable runs in its caller's checkout, where it does not, so such a file may
keep an inline check only when it is named in INLINE_EPOCH_CHECK_EXCEPTIONS.
That list holds only workflow_call-only files that really carry the inline
check, so an exception is dropped once fixed and a new one cannot slip in.

OPEN (coordinator ruling (A), 2026-10-24):
  failure_code: REUSABLE_WORKFLOW_INLINE_EPOCH_CHECK
  failed_predicate: SHARED_EPOCH_GATE_USED
  required_evidence_or_repair: the reusable checks out the component first and gates via
    .ledger-component/scripts/check_dispatch_hb_epoch.py, with a component_ref bump for callers
  retry_entrypoint: .github/workflows/organization-ledger-transition-reusable.yml
  owning_existing_goal: P1 #163, the reusable's owner (commits e29493a, f82c032 authored
    "Rigel Randolph (local draft)")
  next_attempt: the owner's next reusable revision

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
ENTRY = ".github/workflows/organization-ledger-transition.yml (committed self-closure packet hb_epoch)"
#: workflow_call reusables that keep an inline epoch check, with their OPEN record (see the docstring).
INLINE_EPOCH_CHECK_EXCEPTIONS = {"organization-ledger-transition-reusable.yml": "REUSABLE_WORKFLOW_INLINE_EPOCH_CHECK"}
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")


def workflow_triggers(text):
    """The event names under a workflow's top-level `on:` (block or inline form)."""
    lines = text.splitlines()
    start = next(n for n, line in enumerate(lines) if re.match(r"""(on|'on'|"on"):""", line))
    inline = lines[start].split(":", 1)[1].split("#", 1)[0].strip()
    if inline:
        return set(re.findall(r"[a-z_]+", inline))
    events = set()
    for line in lines[start + 1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" "):
            break
        match = re.match(r"  ([a-z_]+):", line)
        if match:
            events.add(match.group(1))
    return events


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
            if path.name in INLINE_EPOCH_CHECK_EXCEPTIONS:
                continue
            with self.subTest(workflow=path.name):
                self.assertIsNone(inline.search(path.read_text(encoding="utf-8")))

    def test_the_only_inline_check_exception_is_the_recorded_workflow_call_reusable(self):
        inline = re.compile(r'case "\$\{?(HB_EPOCH|STEGVERSE_HB_EPOCH)')
        self.assertEqual(set(INLINE_EPOCH_CHECK_EXCEPTIONS), {"organization-ledger-transition-reusable.yml"})
        for name, code in INLINE_EPOCH_CHECK_EXCEPTIONS.items():
            with self.subTest(workflow=name):
                text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
                # Runs only in a caller's checkout, so the gate script is not on disk.
                self.assertEqual(workflow_triggers(text), {"workflow_call"})
                # Still carries the inline check: once fixed, the exception is removed.
                self.assertIsNotNone(inline.search(text))
                self.assertIn(code, __doc__)

if __name__ == "__main__":
    unittest.main()
