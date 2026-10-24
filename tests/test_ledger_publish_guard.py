"""Regression: the dry run's publish guard tolerates a writer append during the run (clock-free, network-free).

StegVerse-Labs/.github intr-path-transfer-validation dry-run compared the published tip to the copied tip, which
fails whenever the ledger writer appends while the dry run runs (the same race as SV-LLM/.github push run
40123764551). resident-runtime/ledger_publish_guard.py checks append-only growth and that no scratch append is
published instead.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
GIT_ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t", "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
           "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

_spec = importlib.util.spec_from_file_location("ledger_publish_guard_under_test", ROOT / "resident-runtime/ledger_publish_guard.py")
guard = importlib.util.module_from_spec(_spec)
sys.modules["ledger_publish_guard_under_test"] = guard
_spec.loader.exec_module(guard)


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
                          env=GIT_ENV).stdout.strip()


def _commit(cwd, message, parent=None):
    tree = _git(cwd, "write-tree")
    return _git(cwd, "commit-tree", tree, "-m", message, *(["-p", parent] if parent else []))


class _Repo:
    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name)
        _git(self.path, "init", "-q")
        return self

    def __exit__(self, *exc):
        self._tmp.cleanup()


def _six_ok(record):
    return all(isinstance(record.get(f), str) and record.get(f) and record[f].strip() == record[f] for f in SIX_FIELDS)


class PublishGuardTests(unittest.TestCase):
    """The writer may append to the published ref during a dry run; a scratch append must never be published."""

    def setUp(self):
        self.repo = _Repo().__enter__()
        p = self.repo.path
        self.copied = _commit(p, "ledger append 1")
        self.writer = _commit(p, "ledger append 2 (writer, published)", self.copied)
        self.scratch = _commit(p, "ledger append 2 (dry run, scratch)", self.copied)
        self.rewritten = _commit(p, "rewritten ledger root")

    def tearDown(self):
        self.repo.__exit__(None, None, None)

    def check(self, copied, now, scratch):
        return guard.check(str(self.repo.path), copied, now, scratch)

    def test_unchanged_published_tip_allows(self):
        self.assertEqual(self.check(self.copied, self.copied, self.scratch)["disposition"], "ALLOW")
        self.assertEqual(self.check(self.copied, self.copied, self.copied)["disposition"], "ALLOW")

    def test_writer_append_during_the_dry_run_allows(self):
        result = self.check(self.copied, self.writer, self.scratch)
        self.assertEqual(result["disposition"], "ALLOW", result)
        self.assertEqual(result["published_grew_by"], 1)
        self.assertEqual(result["scratch_appends"], 1)

    def test_published_scratch_append_denies(self):
        for now in (self.scratch, _commit(self.repo.path, "on top of scratch", self.scratch)):
            result = self.check(self.copied, now, self.scratch)
            self.assertEqual((result["disposition"], result["failure_code"]), ("DENY", "DRY_RUN_APPEND_PUBLISHED"))
            self.assertTrue(_six_ok(result), result)

    def test_rewritten_published_ref_denies(self):
        result = self.check(self.copied, self.rewritten, self.scratch)
        self.assertEqual((result["disposition"], result["failure_code"]), ("DENY", "LEDGER_PUBLISHED_REF_NOT_APPEND_ONLY"))
        self.assertTrue(_six_ok(result), result)

    def test_unreadable_tips_fail_closed(self):
        for args in (("", self.writer, self.scratch), (self.copied, "", self.scratch), (self.copied, "e" * 40, self.scratch),
                     (self.copied, self.writer, "not-a-sha")):
            result = self.check(*args)
            self.assertEqual((result["disposition"], result["failure_code"]), ("FAIL_CLOSED", "LEDGER_PUBLISHED_TIP_UNREADABLE"))
            self.assertTrue(_six_ok(result), result)

    def test_guard_reads_no_clock_and_no_network(self):
        source = (ROOT / "resident-runtime/ledger_publish_guard.py").read_text(encoding="utf-8")
        for token in ("import time", "datetime", "urllib", "socket", "requests", '"ls-remote"', '"fetch"', '"push"'):
            self.assertNotIn(token, source)



if __name__ == "__main__":
    unittest.main()
