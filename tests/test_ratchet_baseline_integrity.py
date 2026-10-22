"""Regression tests for the owner-scoped ratchet baseline integrity gate."""
from __future__ import annotations
import importlib.util
import sys
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


if __name__ == "__main__":
    unittest.main()
