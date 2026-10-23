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
UNITTEST_FILE = '''import unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
class U(unittest.TestCase):
    def test_x(self):
        self.assertEqual((HERE / "x.txt").read_text().strip(), "ok")
    def test_y(self):
        self.assertEqual((HERE / "y.txt").read_text().strip(), "ok")
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
        code, record = self.pr_pytest(base)
        self.assertEqual(code, 0)
        self.assertEqual(record["disposition"], "PRE_EXISTING_BASELINE_FAILURE")
        self.assertEqual(record["verification"]["required_verification_skipped"], 0)
        self.assertEqual(record["verification"]["counts"].get("skipped", 0), 0)
        out = Path(self.tmp.name) / "out-nojunit"
        code = drift.main(["pr", "--root", str(self.toy.path), "--base", base, "--hb-epoch", "469411750",
                           "--pytest-output", str(Path(self.tmp.name) / "pytest.txt"), "--out-dir", str(out)])
        record = json.loads((out / "pr-disposition.json").read_text())
        self.assertEqual(code, 1)
        self.assert_rvs(record, "SUITE_ACCOUNTING_UNOBSERVED")

    # -- unittest-run jobs (cross-task-coordination-validation.yml) -----------------------------------------

    def unittest_toy(self) -> None:
        self.toy.write("tests/__init__.py", "")
        self.toy.write("tests/test_u.py", UNITTEST_FILE)

    def run_unittest(self) -> tuple[int, Path]:
        done = subprocess.run([sys.executable, "-m", "unittest", "-v", "tests.test_u"], cwd=self.toy.path,
                              capture_output=True, text=True)
        out = Path(self.tmp.name) / "unittest.txt"
        out.write_text(done.stdout + done.stderr)
        return done.returncode, out

    def pr_cli(self, base: str, out_file: Path, status: int, modules: list[str] | None = None,
               extra: list[str] | None = None) -> tuple[int, dict]:
        out = Path(self.tmp.name) / "out-u"
        code = drift.main(["pr", "--root", str(self.toy.path), "--base", base, "--hb-epoch", "469411750",
                           "--unittest-output", str(out_file), "--suite-status", str(status), "--out-dir", str(out),
                           "--retry-entrypoint", "toy.yml", *(["--unittest-modules", *modules] if modules else []),
                           *(extra or [])])
        return code, json.loads((out / "pr-disposition.json").read_text())

    def test_unittest_outcome_lines_map_to_ratchet_node_ids(self) -> None:
        node = drift.unittest_node
        self.assertEqual(node("test_y", "tests.test_u.U.test_y"), "tests/test_u.py::U::test_y")
        self.assertEqual(node("test_y", "tests.test_u.U"), "tests/test_u.py::U::test_y")
        self.assertIsNone(node("setUpClass", "tests.test_u.U"))
        self.assertIsNone(node("test_u", "unittest.loader._FailedTest.test_u"))

    def test_unittest_job_pre_existing_failure_proceeds(self) -> None:
        self.unittest_toy()
        self.toy.write("y.txt", "broken\n")
        base = self.toy.commit("main breaks y")
        self.toy.write("docs.md", "unrelated\n")
        self.toy.commit("pr: unrelated")
        status, out_file = self.run_unittest()
        self.assertNotEqual(status, 0)
        code, record = self.pr_cli(base, out_file, status)
        self.assertEqual(code, 0)
        self.assertEqual(record["runner"], "unittest")
        self.assertEqual(record["disposition"], "PRE_EXISTING_BASELINE_FAILURE")
        self.assertEqual([r["test"] for r in record["tests"]], ["tests/test_u.py::U::test_y"])
        self.assertEqual(record["tests"][0]["status_at_base"], "FAIL")
        self.assert_six(record)

    def test_unittest_job_introduced_failure_still_fails(self) -> None:
        self.unittest_toy()
        base = self.toy.commit("main")
        self.toy.write("x.txt", "broken\n")
        self.toy.commit("pr breaks x")
        status, out_file = self.run_unittest()
        code, record = self.pr_cli(base, out_file, status)
        self.assertEqual(code, 1)
        self.assertEqual(record["failure_code"], "TEST_FAILURE_INTRODUCED_BY_CHANGE")
        self.assertEqual(record["retry_entrypoint"], "toy.yml")
        self.assert_six(record)

    def test_unittest_outcome_naming_no_test_fails_closed(self) -> None:
        self.unittest_toy()
        base = self.toy.commit("main")
        out_file = Path(self.tmp.name) / "u.txt"
        out_file.write_text("ERROR: setUpClass (tests.test_u.U)\n----\nFAILED (errors=1)\n")
        code, record = self.pr_cli(base, out_file, 1)
        self.assertEqual(code, 1)
        self.assert_rvs(record, "COLLECTION_ERROR")
        out_file.write_text("Traceback (most recent call last):\nSyntaxError\n")
        code, record = self.pr_cli(base, out_file, 1)
        self.assertEqual(code, 1)
        self.assert_rvs(record, "SUITE_ACCOUNTING_UNOBSERVED")

    # -- required verification: skipped, not run or missing is FAIL_CLOSED, never pre-existing ---------------

    def assert_rvs(self, record: dict, kind: str) -> dict:
        self.assertEqual(record["disposition"], "FAIL_CLOSED")
        self.assertNotEqual(record["disposition"], "PRE_EXISTING_BASELINE_FAILURE")
        rows = [r for r in record["tests"] if r.get("failure_code") == "REQUIRED_VERIFICATION_SKIPPED"]
        hits = [r for r in rows if r["kind"] == kind]
        self.assertTrue(hits, (kind, [r.get("kind") for r in rows]))
        for r in hits:
            self.assertEqual(r["disposition"], "FAIL_CLOSED")
            self.assertTrue(r["blocking"])
            self.assert_six(r)
        self.assertEqual(record["failure_code"], "REQUIRED_VERIFICATION_SKIPPED")
        self.assert_six(record)
        return hits[0]

    def run_pytest(self, *extra: str) -> tuple[Path, Path]:
        out = Path(self.tmp.name) / "pytest.txt"
        junit = Path(self.tmp.name) / "pytest.xml"
        env = {k: v for k, v in os.environ.items() if not k.startswith("PYTEST_")}
        done = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "--tb=no", "-p", "no:cacheprovider",
                               "-rfEsxX", f"--junitxml={junit}", *extra], cwd=self.toy.path, capture_output=True,
                              text=True, env=env)
        out.write_text(done.stdout)
        return out, junit

    def pr_pytest(self, base: str, *extra: str, run: tuple[str, ...] = ()) -> tuple[int, dict]:
        out, junit = self.run_pytest(*run)
        dest = Path(self.tmp.name) / "out-p"
        code = drift.main(["pr", "--root", str(self.toy.path), "--base", base, "--hb-epoch", "469411750",
                           "--pytest-output", str(out), "--junit-xml", str(junit), "--out-dir", str(dest),
                           "--retry-entrypoint", "toy.yml", *extra])
        return code, json.loads((dest / "pr-disposition.json").read_text())

    def test_pytest_skip_present_on_main_too_is_never_pre_existing(self) -> None:
        self.toy.write("tests/test_s.py", "import pytest\ndef test_s():\n    pytest.skip('tool not installed')\n")
        base = self.toy.commit("main has a skipped test")
        self.toy.write("docs.md", "unrelated\n")
        self.toy.commit("pr: unrelated")
        code, record = self.pr_pytest(base)
        self.assertEqual(code, 1)
        row = self.assert_rvs(record, "SKIPPED")
        self.assertEqual(row["test"], "tests/test_s.py::test_s")
        self.assertEqual(record["verification"]["counts"]["skipped"], 1)

    def test_module_level_skip_names_the_module(self) -> None:
        self.toy.write("tests/test_m.py", "import pytest\npytest.skip('sdk absent', allow_module_level=True)\n"
                       "def test_m():\n    pass\n")
        base = self.toy.commit("main")
        self.toy.commit("pr")
        code, record = self.pr_pytest(base)
        self.assertEqual(code, 1)
        self.assertEqual(self.assert_rvs(record, "SKIPPED")["test"], "tests/test_m.py")

    def test_pytest_xfail_and_xpass_fail_closed(self) -> None:
        self.toy.write("tests/test_s.py", "import pytest\n@pytest.mark.xfail(reason='r')\ndef test_xf():\n"
                       "    assert False\n@pytest.mark.xfail(reason='r')\ndef test_xp():\n    assert True\n")
        base = self.toy.commit("main")
        self.toy.commit("pr")
        code, record = self.pr_pytest(base)
        self.assertEqual(code, 1)
        self.assertEqual(self.assert_rvs(record, "XFAIL")["test"], "tests/test_s.py::test_xf")
        self.assertEqual(self.assert_rvs(record, "XPASS")["test"], "tests/test_s.py::test_xp")

    def test_collection_error_failing_on_base_too_is_never_pre_existing(self) -> None:
        self.toy.write("tests/test_bad.py", "import not_a_module_anywhere\ndef test_b():\n    pass\n")
        base = self.toy.commit("main has an uncollectable module")
        self.toy.write("docs.md", "unrelated\n")
        self.toy.commit("pr: unrelated")
        code, record = self.pr_pytest(base)
        self.assertEqual(code, 1)
        self.assertEqual(self.assert_rvs(record, "COLLECTION_ERROR")["test"], "tests/test_bad.py")
        self.assertNotIn("PRE_EXISTING_BASELINE_FAILURE", [r["disposition"] for r in record["tests"]])

    def test_test_present_at_base_and_missing_at_head_fails_closed(self) -> None:
        base = self.toy.commit("main")
        self.toy.write("tests/test_a.py", TEST_FILE.split("def test_y")[0])
        self.toy.commit("pr deletes test_y")
        code, record = self.pr_pytest(base)
        self.assertEqual(code, 1)
        self.assertEqual(self.assert_rvs(record, "TEST_MISSING_AT_HEAD")["test"], "tests/test_a.py::test_y")

    def test_deselected_test_is_missing_at_head(self) -> None:
        base = self.toy.commit("main")
        self.toy.commit("pr")
        code, record = self.pr_pytest(base, run=("--deselect", "tests/test_a.py::test_x"))
        self.assertEqual(code, 1)
        self.assertEqual(self.assert_rvs(record, "TEST_MISSING_AT_HEAD")["test"], "tests/test_a.py::test_x")

    def test_failure_skipped_on_the_base_is_not_pre_existing(self) -> None:
        self.toy.write("tests/test_w.py", "import pytest\nfrom pathlib import Path\nHERE = Path(__file__).resolve()"
                       ".parent.parent\ndef test_w():\n    v = (HERE / 'w.txt').read_text().strip()\n    if v == 'skip':\n"
                       "        pytest.skip('w')\n    assert v == 'ok'\n")
        self.toy.write("w.txt", "skip\n")
        base = self.toy.commit("main skips w")
        self.toy.write("w.txt", "broken\n")
        self.toy.commit("pr flips w")
        record = self.pr(base, ["tests/test_w.py::test_w"])
        self.assert_rvs(record, "BASE_PROBE_SKIPPED")

    def test_required_module_tests_must_run_in_the_pytest_job(self) -> None:
        self.toy.write(".github/workflows/unit.yml", "name: unit\non:\n  pull_request:\n    paths:\n"
                       "      - 'tests/test_f.py'\njobs:\n  validate:\n    runs-on: ubuntu-latest\n    steps:\n"
                       "      - run: |\n          python -m unittest -v \\\n            tests.test_f\n")
        self.toy.write("tests/test_f.py", "def test_f1():\n    assert True\n")
        self.toy.write(".github/workflows/unit2.yml", "name: unit2\non: pull_request\njobs:\n  v:\n    runs-on: x\n"
                       "    steps:\n      - env:\n          MODS: >-\n            tests.test_g\n"
                       "        run: python -m unittest -v $MODS\n")
        self.toy.write("tests/test_g.py", "import unittest\nclass G(unittest.TestCase):\n    def test_g1(self):\n"
                       "        pass\n")
        base = self.toy.commit("main")
        self.toy.commit("pr")
        self.assertEqual(drift.required_modules((self.toy.path / ".github/workflows/unit2.yml").read_text()),
                         ["tests.test_g"])
        code, record = self.pr_pytest(base, "--required-unittest-modules-from", ".github/workflows/unit2.yml",
                                      run=("--deselect", "tests/test_g.py::G::test_g1"))
        self.assertEqual(self.assert_rvs(record, "REQUIRED_TEST_NOT_RUN_IN_REQUIRED_JOB")["test"],
                         "tests/test_g.py::G::test_g1")
        args = ("--required-unittest-modules-from", ".github/workflows/unit.yml")
        code, record = self.pr_pytest(base, *args, run=("--deselect", "tests/test_f.py::test_f1"))
        self.assertEqual(self.assert_rvs(record, "REQUIRED_TEST_NOT_RUN_IN_REQUIRED_JOB")["test"],
                         "tests/test_f.py::test_f1")
        code, record = self.pr_pytest(base, *args)
        self.assertEqual(code, 0, record)
        self.assertEqual(record["verification"]["required_by_workflows"][0]["tests_required"], 1)

    def test_path_filter_leaving_a_required_job_unrun_fails_closed(self) -> None:
        wf = ("name: unit\non:\n  pull_request:\n    paths:\n      - 'tests/test_a.py'\n{extra}jobs:\n  v:\n"
              "    runs-on: ubuntu-latest\n    steps:\n      - run: python scripts/tool.py && python -m pytest tests/test_a.py\n")
        self.toy.write(".github/workflows/unit.yml", wf.format(extra=""))
        self.toy.write("scripts/tool.py", "print(1)\n")
        base = self.toy.commit("main")
        self.toy.write("scripts/tool.py", "print(2)\n")
        self.toy.commit("pr edits a file the filtered job runs")
        code, record = self.pr_pytest(base, "--path-filter-check")
        row = self.assert_rvs(record, "REQUIRED_JOB_PATH_FILTERED_OUT")
        self.assertEqual(row["test"], ".github/workflows/unit.yml")
        self.assertEqual(row["changed_files"], ["scripts/tool.py"])
        self.toy.write(".github/workflows/unit.yml", wf.format(extra="").replace(
            "      - 'tests/test_a.py'\n", "      - 'tests/test_a.py'\n      - 'scripts/**'\n"))
        self.toy.commit("pr widens the filter")
        code, record = self.pr_pytest(base, "--path-filter-check")
        self.assertEqual(code, 0, record)
        self.assertTrue(record["verification"]["workflows_triggered"][0]["triggered"])

    def test_workflow_filter_forms(self) -> None:
        f = drift.workflow_pr_filter
        self.assertEqual(f("on:\n  pull_request:\n  push:\n"), (True, None, []))
        self.assertEqual(f("on: [push, pull_request]\n"), (True, None, []))
        self.assertEqual(f("on:\n  pull_request:\n    paths: ['a/**', 'b.py']\n"), (True, ["a/**", "b.py"], []))
        self.assertEqual(f("on:\n  push:\n    paths:\n      - 'x'\n"), (False, None, []))
        self.assertTrue(drift._glob_regex("tests/**").match("tests/a/b.py"))
        self.assertTrue(drift._glob_regex("**/*.json").match("x.json"))
        self.assertFalse(drift._glob_regex("tests/*.py").match("tests/a/b.py"))

    def test_detect_on_main_with_a_skipped_test_fails_closed(self) -> None:
        self.toy.write("tests/test_s.py", "import pytest\ndef test_s():\n    pytest.skip('r')\n")
        self.toy.commit("main skips")
        out, junit = self.run_pytest()
        dest = Path(self.tmp.name) / "out-d"
        code = drift.main(["detect", "--root", str(self.toy.path), "--hb-epoch", "469411750", "--pytest-output",
                           str(out), "--junit-xml", str(junit), "--out-dir", str(dest)])
        receipt = json.loads((dest / "receipt.json").read_text())
        self.assertEqual(code, 1)
        self.assertEqual(receipt["failure_code"], "REQUIRED_VERIFICATION_SKIPPED")
        self.assert_six(receipt)
        self.assertEqual(receipt["verification"]["rows"][0]["kind"], "SKIPPED")

    def test_unittest_skip_expected_failure_and_unexpected_success_fail_closed(self) -> None:
        self.unittest_toy()
        self.toy.write("tests/test_k.py", "import unittest\nclass K(unittest.TestCase):\n"
                       "    @unittest.skip('r')\n    def test_skip(self):\n        pass\n"
                       "    @unittest.expectedFailure\n    def test_xf(self):\n        self.fail()\n"
                       "    @unittest.expectedFailure\n    def test_xp(self):\n        pass\n"
                       "    def test_ok(self):\n        pass\n")
        base = self.toy.commit("main")
        self.toy.commit("pr")
        done = subprocess.run([sys.executable, "-m", "unittest", "-v", "tests.test_k"], cwd=self.toy.path,
                              capture_output=True, text=True)
        out_file = Path(self.tmp.name) / "uk.txt"
        out_file.write_text(done.stdout + done.stderr)
        code, record = self.pr_cli(base, out_file, done.returncode, ["tests.test_k"])
        self.assertEqual(code, 1)
        self.assertEqual(self.assert_rvs(record, "SKIPPED")["test"], "tests.test_k.K.test_skip")
        self.assert_rvs(record, "EXPECTED_FAILURE")
        self.assert_rvs(record, "UNEXPECTED_SUCCESS")

    def test_unittest_listed_pytest_only_module_is_not_run_unless_a_required_job_runs_it(self) -> None:
        self.unittest_toy()
        self.toy.write("tests/test_f.py", "def test_f1():\n    assert True\n")
        base = self.toy.commit("main")
        self.toy.commit("pr")
        mods = ["tests.test_u", "tests.test_f"]
        done = subprocess.run([sys.executable, "-m", "unittest", "-v", *mods], cwd=self.toy.path,
                              capture_output=True, text=True)
        out_file = Path(self.tmp.name) / "uf.txt"
        out_file.write_text(done.stdout + done.stderr)
        self.assertEqual(done.returncode, 0)
        code, record = self.pr_cli(base, out_file, 0, mods)
        self.assertEqual(code, 1)
        self.assertEqual(self.assert_rvs(record, "TEST_NOT_RUN")["test"], "tests/test_f.py::test_f1")
        code, record = self.pr_cli(base, out_file, 0, mods, ["--pytest-proof", "toy-ratchet"])
        self.assertEqual(code, 0, record)
        self.assertEqual(record["verification"]["delegated"][0]["verified_by"], "toy-ratchet")

    def test_unittest_listed_module_that_does_not_import_fails_closed(self) -> None:
        self.unittest_toy()
        self.toy.write("tests/test_bad.py", "import not_a_module_anywhere\n")
        base = self.toy.commit("main")
        self.toy.commit("pr")
        mods = ["tests.test_u", "tests.test_bad"]
        done = subprocess.run([sys.executable, "-m", "unittest", "-v", *mods], cwd=self.toy.path,
                              capture_output=True, text=True)
        out_file = Path(self.tmp.name) / "ub.txt"
        out_file.write_text(done.stdout + done.stderr)
        code, record = self.pr_cli(base, out_file, done.returncode, mods)
        self.assertEqual(code, 1)
        self.assert_rvs(record, "COLLECTION_ERROR")

    def test_unittest_test_missing_at_head_fails_closed(self) -> None:
        self.unittest_toy()
        base = self.toy.commit("main")
        self.toy.write("tests/test_u.py", UNITTEST_FILE.split("    def test_y")[0])
        self.toy.commit("pr removes test_y")
        status, out_file = self.run_unittest()
        code, record = self.pr_cli(base, out_file, status, ["tests.test_u"])
        self.assertEqual(code, 1)
        self.assertEqual(self.assert_rvs(record, "TEST_MISSING_AT_HEAD")["test"], "tests.test_u.U.test_y")

    def test_unittest_clean_listed_run_is_allow(self) -> None:
        self.unittest_toy()
        base = self.toy.commit("main")
        self.toy.commit("pr")
        status, out_file = self.run_unittest()
        code, record = self.pr_cli(base, out_file, status, ["tests.test_u"])
        self.assertEqual((code, record["disposition"]), (0, "ALLOW"))
        self.assertEqual(record["verification"]["ran"], 2)


    # -- a repository's first baseline: receipted by detect (unittest, bisected), linked by pr -----------------

    def first_baseline_toy(self) -> tuple[str, Path]:
        """main: tests pass, then one commit breaks test_y, then a module with a skipped test lands. The baseline
        file exists only in the checkout (the change under review introduces it)."""
        self.addCleanup(setattr, drift, "RETRY_DETECT", drift.DEFAULT_RETRY_DETECT)
        self.unittest_toy()
        self.toy.commit("tests pass")
        self.toy.commit("unrelated 1")
        self.toy.write("y.txt", "broken\n")
        breaking = self.toy.commit("breaks y")
        self.toy.write("tests/test_s.py", "import unittest\nclass S(unittest.TestCase):\n"
                       "    @unittest.skip('needs an input this runner lacks')\n    def test_s(self):\n        pass\n")
        self.toy.commit("a skipped test lands")
        self.toy.write("org/baseline.json", json.dumps({"known_failing": [], "pre_existing_until": "genesis"}))
        done = subprocess.run([sys.executable, "-m", "unittest", "-v", "tests.test_u", "tests.test_s"],
                              cwd=self.toy.path, capture_output=True, text=True)
        out_file = Path(self.tmp.name) / "main-unittest.txt"
        out_file.write_text(done.stdout + done.stderr)
        return breaking, out_file

    def detect_cli(self, out_file: Path, modules: list[str]) -> tuple[int, dict, Path]:
        out = Path(self.tmp.name) / "out-detect"
        code = drift.main(["detect", "--root", str(self.toy.path), "--baseline", "org/baseline.json",
                           "--unittest-output", str(out_file), "--unittest-modules", *modules,
                           "--bisect-start", self.toy.baseline, "--detect-entrypoint", "toy-detect.yml",
                           "--hb-epoch", "469411750", "--repository", "toy/repo", "--owning-goal", "TOY-GOAL-001",
                           "--out-dir", str(out)])
        return code, json.loads((out / "receipt.json").read_text()), out / "receipt.json"

    def test_first_baseline_is_receipted_by_unittest_detect_bisected_from_the_supplied_start(self) -> None:
        breaking, out_file = self.first_baseline_toy()
        code, receipt, _ = self.detect_cli(out_file, ["tests.test_u", "tests.test_s"])
        self.assertEqual(code, 1)
        self.assertEqual(receipt["runner"], "unittest")
        self.assertEqual((receipt["baseline"]["read_from"], receipt["baseline"]["bisect_start"],
                          receipt["baseline"]["written_at_commit"]), ("CHECKOUT", self.toy.baseline, None))
        self.assertEqual(receipt["baseline"]["pre_existing_until"], "genesis")
        [entry] = receipt["drift"]
        self.assertEqual((entry["test"], entry["first_failing_commit"], entry["classification"]),
                         ("tests/test_u.py::U::test_y", breaking, "INTRODUCED_ON_MAIN_AFTER_BASELINE"))
        # the skip is never drift and never pre-existing: it leads the receipt as REQUIRED_VERIFICATION_SKIPPED
        self.assertEqual((receipt["failure_code"], receipt["verification"]["rows"][0]["kind"],
                          receipt["verification"]["rows"][0]["test"]),
                         ("REQUIRED_VERIFICATION_SKIPPED", "SKIPPED", "tests.test_s.S.test_s"))
        self.assertEqual(receipt["retry_entrypoint"], "toy-detect.yml")
        self.assert_six(receipt)

    def test_pre_existing_rows_name_their_baseline_receipt_entry_and_skips_stay_fail_closed(self) -> None:
        breaking, out_file = self.first_baseline_toy()
        _, _, receipt_path = self.detect_cli(out_file, ["tests.test_u"])
        base = self.toy.git("rev-parse", "HEAD")
        self.toy.write("docs.md", "unrelated\n")
        self.toy.commit("pr: adds the baseline and docs")
        extra = ["--baseline", "org/baseline.json", "--baseline-receipt", str(receipt_path),
                 "--detect-entrypoint", "toy-detect.yml"]
        status, head_out = self.run_unittest()
        code, record = self.pr_cli(base, head_out, status, ["tests.test_u"], extra)
        self.assertEqual((code, record["disposition"]), (0, "PRE_EXISTING_BASELINE_FAILURE"), record)
        [row] = record["tests"]
        self.assertEqual((row["baseline_receipt"]["receipted"], row["baseline_receipt"]["first_failing_commit"]),
                         (True, breaking))
        self.assertEqual((row["pre_existing_until"], row["retry_entrypoint"], row["blocking"]),
                         ("genesis", "toy-detect.yml", False))
        self.assertTrue(record["verification"]["baseline_receipt"]["seal_verifies"])
        # a receipt whose seal does not verify links nothing
        tampered = json.loads(receipt_path.read_text())
        tampered["drift"][0]["first_failing_commit"] = "0" * 40
        receipt_path.write_text(json.dumps(tampered))
        code, record = self.pr_cli(base, head_out, status, ["tests.test_u"], extra)
        self.assertEqual(record["tests"][0]["baseline_receipt"]["receipted"], False)
        self.assertFalse(record["verification"]["baseline_receipt"]["seal_verifies"])
        # the skipped test is REQUIRED_VERIFICATION_SKIPPED with the receipt supplied, never pre-existing
        done = subprocess.run([sys.executable, "-m", "unittest", "-v", "tests.test_u", "tests.test_s"],
                              cwd=self.toy.path, capture_output=True, text=True)
        both = Path(self.tmp.name) / "both.txt"
        both.write_text(done.stdout + done.stderr)
        code, record = self.pr_cli(base, both, done.returncode, ["tests.test_u", "tests.test_s"], extra)
        self.assertEqual(code, 1)
        self.assertEqual(self.assert_rvs(record, "SKIPPED")["test"], "tests.test_s.S.test_s")
        self.assertEqual([r["test"] for r in record["tests"] if r["disposition"] == "PRE_EXISTING_BASELINE_FAILURE"],
                         ["tests/test_u.py::U::test_y"])

    def test_unittest_outcomes_after_the_tests_own_output_and_in_subtests_are_read(self) -> None:
        text = "\n".join([
            "test_a (tests.test_m.C.test_a) ... {\"printed\": true}",
            "more printed output",
            "ok",
            "test_b (tests.test_m.C.test_b) ... ",
            "  test_b (tests.test_m.C.test_b) (epoch='+33') ... ERROR",
            "  test_b (tests.test_m.C.test_b) (epoch='33') ... ok",
            "test_c (tests.test_m.C.test_c)",
            "A docstring line ... skipped 'needs an input'",
            "test_d (tests.test_m.C.test_d) ... ok",
            "test_e (tests.test_m.C.test_e) ... ",
            "{", "  \"printed\": true", "}ok",
            "test_f (tests.test_m.C.test_f) ... ",
            "status: ok",
            "FAIL",
            "", "======", "FAIL: test_f (tests.test_m.C.test_f)", "------", "AssertionError",
            "", "Ran 6 tests in 0.1s", "", "FAILED (failures=1, errors=1, skipped=1)"])
        results, counts, ran = drift.unittest_results(text)
        self.assertEqual(results, {"tests.test_m.C.test_a": "ok", "tests.test_m.C.test_b": "ERROR",
                                   "tests.test_m.C.test_c": "skipped 'needs an input'", "tests.test_m.C.test_d": "ok",
                                   "tests.test_m.C.test_e": "ok", "tests.test_m.C.test_f": "FAIL"})
        self.assertEqual((counts, ran), ({"failures": 1, "errors": 1, "skipped": 1}, 6))

if __name__ == "__main__":
    unittest.main()
