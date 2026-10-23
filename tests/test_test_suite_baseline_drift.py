"""scripts/test_suite_baseline_drift.py against small temporary git repositories.

Each case builds a toy repository with a baseline, a test file and a flag file the test reads, then
checks detect (first failing commit, classification, six fields, repair task, ledger record) and pr
(PRE_EXISTING_BASELINE_FAILURE proceeds; an introduced or touched failure is FAIL_CLOSED). No network,
no clock: the epoch is supplied.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import test_suite_baseline_drift as drift  # noqa: E402

SIX = drift.SIX
TEST_FILE = '''from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
def test_x():
    assert (HERE / "x.txt").read_text().strip() == "ok"
def test_y():
    assert (HERE / "y.txt").read_text().strip() == "ok"
'''
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@invalid", GIT_COMMITTER_NAME="t",
           GIT_COMMITTER_EMAIL="t@invalid", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
ENV.pop("PYTEST_ADDOPTS", None)


class Toy:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")
        self.write("tests/test_a.py", TEST_FILE)
        self.write("x.txt", "ok\n")
        self.write("y.txt", "ok\n")
        self.write("data/test-suite-baseline.json", json.dumps(
            {"schema": "stegverse.test-suite-baseline/v1", "known_failing": [], "excluded": []}))
        self.baseline = self.commit("write the baseline")

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-C", str(self.path), *args], check=True, capture_output=True,
                              text=True, env=ENV).stdout.strip()

    def write(self, rel: str, text: str) -> None:
        p = self.path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def commit(self, msg: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", msg)
        return self.git("rev-parse", "HEAD")


class BaselineDriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.toy = Toy(Path(self.tmp.name) / "repo")
        self.addCleanup(self.tmp.cleanup)
        self._env = {k: os.environ.get(k) for k in ENV}
        os.environ.update({k: ENV[k] for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME",
                                               "GIT_COMMITTER_EMAIL")})
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def detect(self, failing: list[str], epoch: str | None = "469411750") -> dict:
        return drift.detect(self.toy.path, "HEAD", baseline_path="data/test-suite-baseline.json",
                            observed=set(failing), epoch_arg=epoch, writer_path=None, writer_sha256=None,
                            repository="toy/repo", goal="TOY-GOAL-001",
                            open_prs=[{"number": 7, "files": ["y.txt"]}, {"number": 8, "files": ["z.txt"]}])

    def pr(self, base: str, failing: list[str]) -> dict:
        return drift.pr_disposition(self.toy.path, base, "HEAD", baseline_path="data/test-suite-baseline.json",
                                    observed=set(failing), goal="TOY-GOAL-001", repository="toy/repo",
                                    epoch="469411750")

    def assert_six(self, record: dict) -> None:
        for key in SIX:
            self.assertTrue(record.get(key), key)

    def test_no_drift_is_allow(self) -> None:
        self.toy.commit("unrelated")
        receipt = self.detect([])["receipt"]
        self.assertEqual(receipt["disposition"], "ALLOW")
        self.assertEqual(receipt["drift"], [])
        self.assertFalse(receipt["derived_from_clock"])

    def test_direct_commit_drift_names_first_failing_commit(self) -> None:
        self.toy.commit("one")
        self.toy.write("y.txt", "broken\n")
        bad = self.toy.commit("break y")
        self.toy.commit("two")
        self.toy.commit("three")
        out = self.detect(["tests/test_a.py::test_y"])
        receipt = out["receipt"]
        self.assertEqual(receipt["disposition"], "FAIL_CLOSED")
        self.assertEqual(receipt["failure_code"], "TEST_SUITE_RATCHET_BASELINE_DRIFT_ON_MAIN")
        self.assert_six(receipt)
        [entry] = receipt["drift"]
        self.assertEqual(entry["first_failing_commit"], bad)
        self.assertEqual(entry["introducing_commit"], bad)
        self.assertEqual(entry["classification"], "INTRODUCED_ON_MAIN_AFTER_BASELINE")
        self.assertEqual(receipt["hb_epoch"], "469411750")
        self.assertTrue(receipt["receipt_sha256"].startswith("sha256:"))
        ledger = receipt["ledger_append"]
        self.assertEqual(ledger["failure_code"], "DRIFT_RECEIPT_APPENDER_NOT_AVAILABLE")
        self.assertFalse(ledger["appended"])
        self.assertFalse(ledger["dispatched"])
        self.assert_six(ledger)
        task = out["repair_task"]
        self.assertEqual(task["observed_at_head"], receipt["head"])
        self.assertIn("new=0", task["finish_point"])
        self.assertEqual(receipt["repair_task_id"], task["task_id"])
        [review] = out["review"]["failures"]
        self.assertEqual(review["introducing_changed_paths"], ["y.txt"])
        self.assertEqual(review["blocks"]["open_pull_requests_touching_test_or_introducing_paths"], [7])

    def test_merge_drift_bisects_the_merged_branch(self) -> None:
        self.toy.git("checkout", "-q", "-b", "topic")
        self.toy.commit("topic one")
        self.toy.write("y.txt", "broken\n")
        bad = self.toy.commit("topic breaks y")
        self.toy.commit("topic three")
        self.toy.git("checkout", "-q", "main")
        self.toy.commit("main moves")
        self.toy.git("merge", "-q", "--no-ff", "-m", "Merge pull request #42 from toy/topic", "topic")
        merge = self.toy.git("rev-parse", "HEAD")
        entry = self.detect(["tests/test_a.py::test_y"])["receipt"]["drift"][0]
        self.assertEqual(entry["first_failing_commit"], merge)
        self.assertEqual(entry["introducing_commit"], bad)

    def test_failure_older_than_the_baseline_is_pre_existing(self) -> None:
        self.toy.write("y.txt", "broken\n")
        self.toy.commit("break y before the baseline is rewritten")
        self.toy.write("data/test-suite-baseline.json", json.dumps(
            {"schema": "stegverse.test-suite-baseline/v1", "known_failing": [], "excluded": [], "note": "rewritten"}))
        self.toy.commit("rewrite the baseline without y")
        self.toy.commit("later")
        entry = self.detect(["tests/test_a.py::test_y"])["receipt"]["drift"][0]
        self.assertEqual(entry["classification"], "PRE_EXISTING_NOT_RECORDED_IN_BASELINE")

    def test_epoch_is_never_read_from_a_clock(self) -> None:
        self.toy.write("y.txt", "broken\n")
        self.toy.commit("break y")
        receipt = self.detect(["tests/test_a.py::test_y"], epoch=None)["receipt"]
        self.assertIsNone(receipt["hb_epoch"])
        codes = [i["failure_code"] for i in receipt["items"]]
        self.assertIn("HB_EPOCH_SOURCE_UNOBSERVED", codes)
        for i in receipt["items"]:
            self.assert_six(i)

    def test_unrelated_pr_proceeds_with_pre_existing_disposition(self) -> None:
        self.toy.write("y.txt", "broken\n")
        base = self.toy.commit("main breaks y")
        self.toy.write("docs.md", "unrelated\n")
        self.toy.commit("pr: unrelated")
        record = self.pr(base, ["tests/test_a.py::test_y"])
        self.assertEqual(record["disposition"], "PRE_EXISTING_BASELINE_FAILURE")
        self.assertTrue(record["degraded_not_stopped"])
        self.assertFalse(record["tests"][0]["blocking"])
        self.assert_six(record)

    def test_pr_that_introduces_a_failure_is_fail_closed(self) -> None:
        base = self.toy.commit("main")
        self.toy.write("x.txt", "broken\n")
        self.toy.commit("pr breaks x")
        record = self.pr(base, ["tests/test_a.py::test_x"])
        self.assertEqual(record["disposition"], "FAIL_CLOSED")
        self.assertEqual(record["failure_code"], "TEST_FAILURE_INTRODUCED_BY_CHANGE")
        self.assert_six(record)

    def test_pr_touching_a_failing_test_without_fixing_it_is_fail_closed(self) -> None:
        self.toy.write("y.txt", "broken\n")
        base = self.toy.commit("main breaks y")
        self.toy.write("tests/test_a.py", TEST_FILE + "\n# touched\n")
        self.toy.commit("pr touches the test file")
        record = self.pr(base, ["tests/test_a.py::test_y"])
        self.assertEqual(record["disposition"], "FAIL_CLOSED")
        self.assertEqual(record["failure_code"], "BASELINE_FAILURE_TOUCHED_BY_CHANGE")

    def test_pr_with_no_new_failure_is_allow(self) -> None:
        base = self.toy.commit("main")
        self.toy.write("docs.md", "x\n")
        self.toy.commit("pr")
        self.assertEqual(self.pr(base, [])["disposition"], "ALLOW")

    def test_cli_pr_exit_status(self) -> None:
        self.toy.write("y.txt", "broken\n")
        base = self.toy.commit("main breaks y")
        self.toy.write("docs.md", "unrelated\n")
        self.toy.commit("pr")
        out = Path(self.tmp.name) / "out"
        pytest_out = Path(self.tmp.name) / "pytest.txt"
        pytest_out.write_text("FAILED tests/test_a.py::test_y - AssertionError\n1 failed, 1 passed\n")
        code = drift.main(["pr", "--root", str(self.toy.path), "--base", base, "--hb-epoch", "469411750",
                           "--pytest-output", str(pytest_out), "--out-dir", str(out)])
        self.assertEqual(code, 0)
        record = json.loads((out / "pr-disposition.json").read_text())
        self.assertEqual(record["disposition"], "PRE_EXISTING_BASELINE_FAILURE")


if __name__ == "__main__":
    unittest.main()
