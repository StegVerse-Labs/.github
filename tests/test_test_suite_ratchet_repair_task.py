"""data/test-suite-ratchet-repair-task.json: the scoped repair task for the red Labs ratchet (P4 #166).

Checks the record is sealed by the drift tool's seal, that every group carries the six fields, that every
failing test belongs to exactly one group, and that the task stays non-blocking for unrelated pull requests:
a diff that does not reach the listed tests selects none of them, so the ratchet neither runs nor judges them
(scripts/test_suite_baseline_drift.py in_selection), while a diff that reaches one of them does select it.
Stdlib only, no network, no clock.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import test_set_selection as selection  # noqa: E402
import test_suite_baseline_drift as drift  # noqa: E402
from evaluate_admission_job_observation import seal_verifies  # noqa: E402

TASK_PATH = "data/test-suite-ratchet-repair-task.json"
MANIFEST_PATH = ".stegverse/test-sets.json"
THIS = "tests/test_test_suite_ratchet_repair_task.py"


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def select(diff: list[str]) -> dict:
    return selection.select(ROOT, load(MANIFEST_PATH), diff, manifest_path=MANIFEST_PATH, spec=None,
                            spec_path=None, base=None, head=None)


class RepairTaskRecord(unittest.TestCase):
    def setUp(self) -> None:
        self.task = load(TASK_PATH)

    def test_sealed_with_the_drift_tool_seal(self) -> None:
        self.assertEqual(self.task["schema"], drift.TASK_SCHEMA)
        self.assertTrue(seal_verifies(self.task, drift.SEAL))
        tampered = dict(self.task, observed_at_head="0" * 40)
        self.assertFalse(seal_verifies(tampered, drift.SEAL))

    def test_every_group_carries_the_six_fields(self) -> None:
        self.assertTrue(self.task["groups"])
        for group in self.task["groups"]:
            with self.subTest(group=group["group_id"]):
                self.assertTrue(drift.has_six(group), group["group_id"])

    def test_every_failing_test_is_in_exactly_one_group(self) -> None:
        listed = [t["test"] for t in self.task["tests"]]
        self.assertEqual(len(listed), len(set(listed)))
        self.assertEqual(len(listed), self.task["scope"]["failing_at_head"])
        grouped = [n for g in self.task["groups"] if g["group_id"] != "G12_EXCLUDED_ENVIRONMENT_SENSITIVE"
                   for n in g["tests"]]
        self.assertEqual(sorted(grouped), sorted(listed))
        for t in self.task["tests"]:
            self.assertIn(t["test"], next(g["tests"] for g in self.task["groups"] if g["group_id"] == t["group"]))

    def test_drift_tool_bisect_agrees_with_full_history_bisect(self) -> None:
        for t in self.task["tests"]:
            if t["drift_tool_detect_first_failing_commit"] is not None:
                self.assertEqual(t["drift_tool_detect_first_failing_commit"], t["bisect"]["first_failing_commit"])


class NonBlockingForUnrelatedChanges(unittest.TestCase):
    def setUp(self) -> None:
        self.nodes = [t["test"] for t in load(TASK_PATH)["tests"]]

    def test_an_unrelated_diff_selects_none_of_the_listed_tests(self) -> None:
        for diff in ([THIS], [TASK_PATH]):
            with self.subTest(diff=diff):
                sel = select(diff)
                self.assertTrue(selection.seal_verifies(sel))
                self.assertEqual(sel["mode"], "DIFF")
                self.assertEqual(sel["unmapped_paths"], [])
                judged = [n for n in self.nodes if drift.in_selection(n, sel)]
                self.assertEqual(judged, [], "an unrelated change would run or judge a repair-task test")

    def test_a_diff_that_reaches_a_listed_test_selects_it(self) -> None:
        node = self.nodes[0]
        sel = select([node.split("::", 1)[0]])
        self.assertEqual(sel["mode"], "DIFF")
        self.assertTrue(drift.in_selection(node, sel))


if __name__ == "__main__":
    unittest.main()
