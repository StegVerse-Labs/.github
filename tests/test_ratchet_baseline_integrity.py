"""Regression tests for the owner-scoped ratchet baseline integrity gate."""
from __future__ import annotations
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("ratchet_policy", ROOT / "scripts/check_test_suite_ratchet.py")
ratchet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ratchet)


class BaselineIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.base = {"known_failing": ["tests/test_a.py::a", "tests/test_b.py::b"],
                     "excluded": [{"test": "tests/test_c.py::c", "reason": "legacy"}]}

    def test_unchanged_baseline_cannot_masquerade_as_full_pass(self):
        report = ratchet.baseline_integrity(self.base, self.base)
        self.assertEqual(report["added_known_failures"], [])
        self.assertEqual(report["added_exclusions"], [])
        self.assertEqual(len(self.base["known_failing"]), 2)

    def test_a_pr_cannot_make_failures_green_by_expanding_ceiling(self):
        current = {**self.base, "known_failing": self.base["known_failing"] + ["tests/new.py::broken"]}
        self.assertEqual(ratchet.baseline_integrity(current, self.base)["added_known_failures"],
                         ["tests/new.py::broken"])

    def test_a_pr_cannot_avoid_a_failure_by_excluding_it(self):
        current = {**self.base, "excluded": self.base["excluded"] +
                   [{"test": "tests/new.py::broken", "reason": "hide failure"}]}
        self.assertEqual(ratchet.baseline_integrity(current, self.base)["added_exclusions"],
                         ["tests/new.py::broken"])

    def test_moving_a_known_failure_to_excluded_is_rejected(self):
        current = {"known_failing": ["tests/test_b.py::b"],
                   "excluded": self.base["excluded"] +
                   [{"test": "tests/test_a.py::a", "reason": "move"}]}
        report = ratchet.baseline_integrity(current, self.base)
        self.assertEqual(report["moved_from_known_to_excluded"], ["tests/test_a.py::a"])

    def test_fixes_can_shrink_baseline_without_being_suppressed(self):
        current = {"known_failing": ["tests/test_b.py::b"], "excluded": []}
        report = ratchet.baseline_integrity(current, self.base)
        self.assertEqual(report["removed_known_failures"], ["tests/test_a.py::a"])
        self.assertEqual(report["removed_exclusions"], ["tests/test_c.py::c"])
        self.assertFalse(report["added_known_failures"] or report["added_exclusions"] or
                         report["moved_from_known_to_excluded"])


SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")


def _head_sha() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout.strip()


def _check(current) -> tuple[int, str]:
    """Run the --base-sha check on a head benchmark held outside the repository."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test-suite-baseline.json"
        path.write_text(current if isinstance(current, str) else json.dumps(current), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.chdir(ROOT):
            status = ratchet.check_baseline_against_base(_head_sha(), path)
    return status, out.getvalue()


class BaselineIntegrityRefusalTests(unittest.TestCase):
    """#3304 review finding 4: a malformed benchmark is a six-field refusal, never a bare exception."""

    def assert_six_field_refusal(self, current):
        status, out = _check(current)
        self.assertEqual(status, 1)
        self.assertIn("FAIL_CLOSED invalid benchmark", out)
        refusal = json.loads(out[out.index("{\""):])
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
        for key in SIX_FIELDS:
            self.assertTrue(refusal.get(key), key)

    def test_excluded_row_without_test_is_not_a_bare_key_error(self):
        with self.assertRaises(ValueError):
            ratchet.baseline_integrity({"excluded": [{"reason": "x"}]}, {})

    def test_excluded_row_without_test_is_six_field_refusal(self):
        self.assert_six_field_refusal({"known_failing": [], "excluded": [{"reason": "x"}]})

    def test_non_object_benchmark_or_rows_are_six_field_refusals(self):
        for bad in ([], "\"text\"", {"excluded": "tests/x.py::x"}, {"excluded": ["tests/x.py::x"]}):
            with self.subTest(bad=bad):
                self.assert_six_field_refusal(bad if isinstance(bad, str) else bad)


class RuntimeComparisonRefusalTests(unittest.TestCase):
    """The runtime comparison (no --base-sha) refuses a malformed benchmark in six fields; it never passes."""

    def run_main(self, benchmark):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "suite"
            target.mkdir()
            (target / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            path = Path(tmp) / "test-suite-baseline.json"
            path.write_text(json.dumps(benchmark), encoding="utf-8")
            return subprocess.run([sys.executable, str(ROOT / "scripts/check_test_suite_ratchet.py"),
                                   "--target", str(target), "--baseline", str(path)],
                                  cwd=tmp, capture_output=True, text=True)

    def test_malformed_benchmark_is_a_six_field_refusal_not_a_traceback_or_pass(self):
        for bad in ({"known_failing": "tests/x.py::x"}, {"known_failing": [1]},
                    {"known_failing": [], "excluded": [{"reason": "x"}]}, []):
            with self.subTest(bad=bad):
                done = self.run_main(bad)
                self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
                self.assertNotIn("Traceback", done.stderr)
                self.assertIn("FAIL_CLOSED invalid benchmark", done.stdout)
                refusal = json.loads(done.stdout[done.stdout.index("{\""):])
                for key in SIX_FIELDS:
                    self.assertTrue(refusal.get(key), key)

    def test_known_failing_must_be_a_list_of_test_ids(self):
        with self.assertRaises(ValueError):
            ratchet.compare(set(), {"known_failing": "tests/x.py::x"})
        with self.assertRaises(ValueError):
            ratchet.baseline_integrity({"known_failing": {"tests/x.py::x": 1}}, {})


class BaseCheckerTests(unittest.TestCase):
    """#3304 review finding 3: the integrity gate runs the base's checker, reading the PR's benchmark as data."""

    def test_head_benchmark_outside_the_base_tree_is_compared_to_the_base_path(self):
        head = subprocess.run(["git", "show", f"{_head_sha()}:{ratchet.BASELINE.as_posix()}"],
                              cwd=ROOT, capture_output=True, text=True, check=True).stdout
        status, out = _check(head)
        self.assertEqual(status, 0, out)
        self.assertIn("BASELINE_INTEGRITY_PASS", out)

    def test_workflow_runs_integrity_gate_from_a_base_worktree(self):
        workflow = (ROOT / ".github/workflows/test-suite-ratchet.yml").read_text(encoding="utf-8")
        self.assertNotIn("python scripts/check_test_suite_ratchet.py --base-sha", workflow)
        steps = [s for s in workflow.split("      - name: ") if "--base-sha \"$RATCHET_BASE_SHA\"" in s]
        self.assertEqual(len(steps), 1)
        step = steps[0]
        self.assertIn('git worktree add -q --detach "$RUNNER_TEMP/ratchet-base" "$RATCHET_BASE_SHA"', step)
        self.assertIn('checker="$RUNNER_TEMP/ratchet-base/scripts/check_test_suite_ratchet.py"', step)
        self.assertIn('cd "$RUNNER_TEMP/ratchet-base"', step)
        self.assertIn('--baseline "$GITHUB_WORKSPACE/data/test-suite-baseline.json"', step)


if __name__ == "__main__":
    unittest.main()
