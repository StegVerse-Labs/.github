"""Organization receipts take `observed_at` from the supplied hb_epoch, never the wall clock.

The SV-LLM S1 sandbox verifier (SV-LLM/.github#46) refused this head's hop
with DENY HOP_RECEIPTS_DEPEND_ON_AN_UNSUPPLIED_INPUT: two runs at the same
supplied epoch wrote different organization receipts because `observed_at`
read the clock. Here the module's clock is mutated to advance on every read;
the receipts must not change. Temporary git ledgers only; nothing is published.
"""
import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime as _real_datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = "refs/stegverse/organization-ledger"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AdvancingClock:
    """A clock that is never the same twice: any receipt that reads it differs."""
    reads = 0

    @classmethod
    def now(cls, tz=None):
        cls.reads += 1
        return _real_datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=cls.reads)


class SuppliedEpochObservedAtTests(unittest.TestCase):
    def setUp(self):
        self._saved = {key: os.environ.get(key) for key in
                       ("STEGVERSE_ORG_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_GIT_DIR", "STEGVERSE_REPO_LEDGER_ROOT",
                        "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL")}
        os.environ.update({"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
                           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"})

    def tearDown(self):
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def append_once(self, epoch):
        home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, home, True)
        ledger = home / "ledger"
        subprocess.run(["git", "init", "-q", str(ledger)], check=True)
        emit = load("emit_observed_at", ROOT / ".stegverse/transition-ledger/emit.py")
        namespace = __import__("json").loads(
            (ROOT / ".stegverse/transition-ledger/contract.json").read_text())["repository_ledger_location"]["namespace"]
        os.environ.update({"STEGVERSE_ORG_LEDGER_ROOT": str(home / "org"),
                           "STEGVERSE_ORG_LEDGER_GIT_DIR": str(ledger / ".git"),
                           "STEGVERSE_REPO_LEDGER_ROOT": "git+%s#%s:%s" % (ledger, REF, namespace)})
        aggregate = load("aggregate_observed_at", ROOT / "resident-runtime/aggregate_repo_transition.py")
        aggregate.datetime = AdvancingClock
        repo = emit.append("OBSERVED-AT:1", "OBSERVED_AT_TEST", "sha256:" + "0" * 64, "sha256:" + "1" * 64,
                           evidence={"case": "observed_at"}, hb_epoch=epoch)
        return aggregate, aggregate.aggregate_transition(repo, hb_epoch=epoch)

    def test_observed_at_is_the_supplied_epoch_and_reads_no_clock(self):
        before = AdvancingClock.reads
        _, receipt = self.append_once(40)
        self.assertEqual(receipt["observed_at"], "SUPPLIED_HB_EPOCH:40")
        self.assertEqual(receipt["hb_reference"]["epoch"], 40)
        self.assertEqual(AdvancingClock.reads, before)

    def test_the_same_transition_at_the_same_epoch_writes_the_same_receipt_under_an_advancing_clock(self):
        _, first = self.append_once(41)
        _, second = self.append_once(41)
        self.assertEqual(first, second)

    def test_a_clock_derived_reference_is_labelled_derived(self):
        aggregate, _ = self.append_once(42)
        self.assertEqual(aggregate.observed_at_from_hb_reference({"epoch": 7, "derived_from_clock": True}),
                         "HB_EPOCH_DERIVED_FROM_CLOCK:7")
        self.assertEqual(aggregate.observed_at_from_hb_reference({"epoch": 50, "derived_from_clock": False}),
                         "SUPPLIED_HB_EPOCH:50")


if __name__ == "__main__":
    unittest.main()
