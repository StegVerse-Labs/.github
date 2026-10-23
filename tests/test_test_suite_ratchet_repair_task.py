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


OWNER_GROUPS = ("G6_", "G7_", "G8_", "G9_", "G10_", "G11_")


class OwnerDerivationForG6ToG11(unittest.TestCase):
    """Candidate owners follow the Labs#3329 lineage rule: one registered Goal in the introducing PR body."""

    def setUp(self) -> None:
        self.task = load(TASK_PATH)
        self.custody = self.task["owning_existing_goal"]
        self.groups = [g for g in self.task["groups"] if g["group_id"].startswith(OWNER_GROUPS)]
        self.tests = [t for t in self.task["tests"] if t["group"].startswith(OWNER_GROUPS)]

    def test_rule_is_recorded(self) -> None:
        rule = self.task["method"]["owner_derivation"]
        self.assertIn("#3329", rule["rule"])
        self.assertEqual(rule["evidence_class"], "OBSERVED_TEXT_NOT_A_LEDGER_RECEIPT")

    def test_every_test_status_follows_the_rule(self) -> None:
        self.assertEqual(len(self.tests), sum(g["test_count"] for g in self.groups))
        for t in self.tests:
            o = t["owner_derivation"]
            with self.subTest(test=t["test"]):
                named = [r["goal_id"] for r in o["goal_references"] if r["registered"]]
                self.assertEqual(o["registered_goals_named"], named)
                self.assertEqual(o["introducing_commit"], t["bisect"]["first_failing_commit"])
                self.assertEqual(o["evidence_class"], "OBSERVED_TEXT_NOT_A_LEDGER_RECEIPT")
                if not o["sources"]:
                    self.assertIsNone(t["introducing_pull_request"])
                    expected = "NO_INTRODUCING_PR_BODY"
                elif len(named) == 1:
                    expected = "CANDIDATE_DERIVED_FROM_PR_BODY"
                elif named:
                    expected = "CANDIDATE_OWNER_AMBIGUOUS"
                else:
                    expected = "NO_REGISTERED_GOAL_IN_PR_BODY"
                self.assertEqual(o["status"], expected)
                if expected == "CANDIDATE_DERIVED_FROM_PR_BODY":
                    self.assertEqual(o["candidate_owner"], named[0])
                    self.assertIsNone(o["custody"])
                else:
                    self.assertIsNone(o["candidate_owner"])
                    self.assertEqual(o["custody"], self.custody)

    def test_group_candidates_aggregate_the_tests_and_custody_stays_non_blocking(self) -> None:
        for g in self.groups:
            mine = [t for t in self.tests if t["group"] == g["group_id"]]
            with self.subTest(group=g["group_id"]):
                expect: dict = {}
                for t in mine:
                    c = t["owner_derivation"]["candidate_owner"]
                    if c:
                        expect.setdefault(c, []).append(t["test"])
                self.assertEqual({c["goal_id"]: c["tests"] for c in g["candidate_owners"]},
                                 {k: sorted(v) for k, v in expect.items()})
                for c in g["candidate_owners"]:
                    self.assertEqual(c["assignment"], "NOT_ASSIGNED")
                    self.assertEqual(c["test_count"], len(c["tests"]))
                self.assertEqual(sum(g["owner_derivation_counts"].values()), len(mine))
                self.assertEqual(g["custody_tests"], len(mine) - sum(len(v) for v in expect.values()))
                self.assertTrue(g["owning_existing_goal"].startswith(self.custody))
                self.assertEqual(g["failure_code"], "TEST_SUITE_BASELINE_PRE_EXISTING_FAILURE")


if __name__ == "__main__":
    unittest.main()
