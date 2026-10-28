"""The claim-allocator epoch is the Organization ledger HEAD's, never a clock's.

scripts/organization_ledger_head_epoch.py derives the `--hb-epoch` the claim
allocator supplies from the receipt-chain frame epoch: the epoch the verified
Organization ledger HEAD records. The rule checked here is the narrowed one:
no date/time source may feed the epoch, and the ledger-derived epoch is
accepted. It is applied to the helper's own code; the workflow step that
passes the epoch follows StegVerse-Labs/.github#3241. Stdlib only.
"""
from __future__ import annotations

import ast
import datetime
import importlib.util
import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
HELPER_REL = "scripts/organization_ledger_head_epoch.py"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
              "owning_existing_goal", "next_attempt")
TEST_HB_EPOCH = 4096
SOURCE_FILES = (
    "scripts/consume_org_claim_allocator_request.py",
    ".stegverse/transition-ledger/emit.py",
    ".stegverse/transition-ledger/contract.json",
    ".stegverse/transition-ledger/org-contract.json",
    "org-kernel/kernel.py",
    "org-kernel/node_store.py",
    "resident-runtime/ledger_store.py",
    "resident-runtime/aggregate_repo_transition.py",
    "resident-runtime/organization_batch_custody.py",
)

# Date/time sources: a module that reads the clock, or a call that does.
CLOCK_MODULES = {"time", "datetime", "calendar"}
CLOCK_CALLS = {"now", "utcnow", "today", "time", "time_ns", "monotonic", "monotonic_ns", "perf_counter",
               "perf_counter_ns", "gmtime", "localtime", "strftime", "process_time"}
CLOCK_COMMANDS = ("date +", "date -u", "EPOCHSECONDS", "EPOCHREALTIME")


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clock_sources(source: str) -> list[str]:
    """Every date/time source in Python `source` that could feed an epoch; empty when none can.

    A clock-reading import or call, a shell clock command in a string, or a
    heartbeat reference built without a supplied epoch (the kernel then derives
    it from the host clock). Reading an epoch the ledger recorded is none of these.
    """
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found += ["import " + a.name for a in node.names if a.name.split(".")[0] in CLOCK_MODULES]
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in CLOCK_MODULES:
                found.append("from " + str(node.module) + " import")
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None
            if name in CLOCK_CALLS:
                found.append("call " + name + "()")
            if name == "hb_reference" and not any(k.arg == "epoch" for k in node.keywords):
                found.append("hb_reference() without a supplied epoch")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            found += ["shell " + c for c in CLOCK_COMMANDS if c in node.value]
    return found


class RaisingDatetime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        raise AssertionError("clock read: datetime.now")

    @classmethod
    def utcnow(cls):
        raise AssertionError("clock read: datetime.utcnow")

    @classmethod
    def today(cls):
        raise AssertionError("clock read: datetime.today")


def no_clock():
    """Patch every clock entry point to raise; modules loaded under it bind the raising ones."""
    patches = [mock.patch("datetime.datetime", RaisingDatetime)]
    for name in ("time", "time_ns", "monotonic", "monotonic_ns", "perf_counter", "perf_counter_ns",
                 "gmtime", "localtime", "strftime"):
        patches.append(mock.patch.object(time, name, side_effect=AssertionError("clock read: time." + name)))
    return patches


class LedgerHeadEpochHelper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = load("organization_ledger_head_epoch_test", HELPER_REL)
        cls.kernel = load("organization_ledger_head_epoch_kernel_test", "org-kernel/kernel.py")

    def chain(self, hb_reference, *, include=True):
        head = {"receipt_sha256": "sha256:" + "a" * 64}
        if include:
            head["hb_reference"] = hb_reference
        return {"head_sha256": head["receipt_sha256"], "receipts": [{"receipt_sha256": "sha256:" + "b" * 64}, head]}

    def assert_six_field_refusal(self, refused, failure_code):
        self.assertIsNotNone(refused)
        self.assertEqual(refused["disposition"], "FAIL_CLOSED")
        self.assertEqual(refused["failure_code"], failure_code)
        for field in SIX_FIELDS:
            self.assertTrue(refused.get(field), field)
        self.assertIs(refused["derived_from_clock"], False)
        self.assertIs(refused["consequence_committed"], False)

    def test_the_ledger_derived_head_epoch_is_returned(self):
        reference = self.kernel.hb_reference(epoch=TEST_HB_EPOCH)
        epoch, refused = self.helper.head_epoch(self.chain(reference), self.kernel)
        self.assertIsNone(refused)
        self.assertEqual(epoch, str(TEST_HB_EPOCH))

    def test_a_missing_ledger_epoch_is_six_field_fail_closed(self):
        for chain in (self.chain(None, include=False), self.chain(None), self.chain({"generation": 64})):
            epoch, refused = self.helper.head_epoch(chain, self.kernel)
            self.assertIsNone(epoch)
            self.assert_six_field_refusal(refused, "HB_EPOCH_NOT_SUPPLIED")

    def test_a_clock_derived_head_epoch_is_rejected(self):
        reference = dict(self.kernel.hb_reference(epoch=TEST_HB_EPOCH), derived_from_clock=True)
        epoch, refused = self.helper.head_epoch(self.chain(reference), self.kernel)
        self.assertIsNone(epoch)
        self.assert_six_field_refusal(refused, "HB_EPOCH_INVALID")

    def test_an_invalid_head_epoch_is_refused(self):
        for value in (31, True, "0x40", " 64", 64.0):
            epoch, refused = self.helper.head_epoch(self.chain({"epoch": value}), self.kernel)
            self.assertIsNone(epoch, value)
            self.assert_six_field_refusal(refused, "HB_EPOCH_INVALID")

    def test_a_chain_without_its_head_receipt_is_refused(self):
        epoch, refused = self.helper.head_epoch({"head_sha256": "sha256:" + "c" * 64, "receipts": []}, self.kernel)
        self.assertIsNone(epoch)
        self.assert_six_field_refusal(refused, "LEDGER_HEAD_UNVERIFIED")


class NoDateTimeSourceFeedsTheEpoch(unittest.TestCase):
    """The narrowed rule, applied to the helper's own code."""

    def test_the_helper_has_no_date_time_source(self):
        self.assertEqual(clock_sources((ROOT / HELPER_REL).read_text(encoding="utf-8")), [])

    def test_a_clock_source_is_rejected(self):
        clocked = (
            "import time\nepoch = int(time.time())",
            "from time import time_ns\nepoch = time_ns()",
            "import datetime\nepoch = datetime.datetime.now().timestamp()",
            "from datetime import datetime, timezone\nepoch = datetime.now(timezone.utc)",
            "epoch = kernel.hb_reference()['epoch']",
            "epoch = subprocess.check_output(['sh', '-c', 'date +%s'])",
            "epoch = os.environ['EPOCHSECONDS']",
        )
        for source in clocked:
            self.assertNotEqual(clock_sources(source), [], source)

    def test_the_ledger_derived_epoch_is_accepted(self):
        source = ("reference = chain['receipts'][-1].get('hb_reference')\n"
                  "epoch = reference.get('epoch')\n"
                  "failure = kernel.supplied_epoch_failure(epoch, reference)\n"
                  "expected = kernel.hb_reference(epoch=4096)\n")
        self.assertEqual(clock_sources(source), [])


class LedgerHeadEpochFromAVerifiedLedger(unittest.TestCase):
    """End to end through the consumer's existing custody and chain verifier, with every clock raising."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="ledger-head-epoch-"))
        self.source = self.base / "source"
        for rel in SOURCE_FILES:
            (self.source / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.source / rel)
        self.org = self.base / "org-ledger"
        self.repo = self.base / "repo-ledger"
        self.helper = load("organization_ledger_head_epoch_e2e", HELPER_REL)
        self.organization = load("organization_ledger_head_epoch_org", "resident-runtime/aggregate_repo_transition.py")

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def write_chain(self, hb_references):
        """A rooted, continuous POSIX chain whose receipts record `hb_references`, HEAD last."""
        org = self.organization
        (self.org / "receipts").mkdir(parents=True, exist_ok=True)
        previous = None
        for index, reference in enumerate(hb_references):
            body = {"schema": "stegverse.organization-transition-receipt/v1",
                    "organization": org.C["organization"], "sequence": index,
                    "previous_receipt_sha256": previous}
            if reference is not None:
                body["hb_reference"] = reference
            digest = org.sha(body)
            (self.org / "receipts" / (digest.split(":", 1)[1] + ".json")).write_text(
                json.dumps({**body, "receipt_sha256": digest}), encoding="utf-8")
            previous = digest
        (self.org / "HEAD.json").write_text(json.dumps(
            {"organization": org.C["organization"], "receipt_sha256": previous}), encoding="utf-8")

    def run_without_clock(self):
        patches = no_clock()
        for patch in patches:
            patch.start()
        try:
            return self.helper.ledger_head_epoch(self.source, self.repo, self.org)
        finally:
            for patch in reversed(patches):
                patch.stop()

    def test_no_clock_is_read_and_the_head_epoch_is_returned(self):
        kernel = self.organization.kernel
        self.write_chain([kernel.hb_reference(epoch=64), kernel.hb_reference(epoch=TEST_HB_EPOCH)])
        epoch, refused = self.run_without_clock()
        self.assertIsNone(refused)
        self.assertEqual(epoch, str(TEST_HB_EPOCH))

    def test_the_patched_clock_does_raise(self):
        patches = no_clock()
        for patch in patches:
            patch.start()
        try:
            with self.assertRaises(AssertionError):
                time.time()
            with self.assertRaises(AssertionError):
                datetime.datetime.now()
        finally:
            for patch in reversed(patches):
                patch.stop()

    def test_a_head_without_a_ledger_epoch_is_six_field_fail_closed_without_a_clock(self):
        self.write_chain([self.organization.kernel.hb_reference(epoch=64), None])
        epoch, refused = self.run_without_clock()
        self.assertIsNone(epoch)
        self.assertEqual(refused["failure_code"], "HB_EPOCH_NOT_SUPPLIED")
        for field in SIX_FIELDS:
            self.assertTrue(refused.get(field), field)

    def test_an_unverified_ledger_is_six_field_fail_closed(self):
        (self.org / "receipts").mkdir(parents=True)
        epoch, refused = self.run_without_clock()
        self.assertIsNone(epoch)
        self.assertEqual(refused["failure_code"], "LEDGER_HEAD_UNVERIFIED")
        for field in SIX_FIELDS:
            self.assertTrue(refused.get(field), field)

    def test_the_command_line_prints_the_epoch_or_the_refusal(self):
        kernel = self.organization.kernel
        self.write_chain([kernel.hb_reference(epoch=TEST_HB_EPOCH)])
        argv = ["--source-root", str(self.source), "--repo-ledger-root", str(self.repo),
                "--org-ledger-root", str(self.org)]
        with mock.patch("builtins.print") as printed:
            self.assertEqual(self.helper.main(argv), 0)
        printed.assert_called_once_with(str(TEST_HB_EPOCH))
        self.write_chain([kernel.hb_reference(epoch=TEST_HB_EPOCH), None])
        with mock.patch("builtins.print") as printed:
            self.assertEqual(self.helper.main(argv), 1)
        self.assertEqual(json.loads(printed.call_args.args[0])["disposition"], "FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()
