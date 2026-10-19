"""WU-B13a: the kernel's receipt-writer helper for a supplied heartbeat epoch.

`writer_epoch_refusal` returns the six-field FAIL_CLOSED of a writer's epoch, or
None when it is supplied; `supplied_hb_reference` returns the heartbeat
reference of a supplied epoch or raises `SuppliedEpochRefused`. Both apply the
shared rule (`supplied_epoch_failure`):

- no epoch supplied  -> FAIL_CLOSED HB_EPOCH_NOT_SUPPLIED
- malformed or < 32  -> FAIL_CLOSED HB_EPOCH_INVALID

and neither reads a clock. The slice defines the helper only; no caller is
required to pass an epoch yet, so existing writers behave as before.

Stdlib only.
"""
from __future__ import annotations

import datetime as _datetime
import importlib.util
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


K = _load("kernel_wu_b13a", "org-kernel/kernel.py")

SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")
GOAL = "INTERLOCK-INTR-RUNTIME-INDEPENDENT-PROTOCOL-001"
ENTRY = "tests/test_kernel_writer_supplied_epoch.py::writer (hb_epoch=)"
INVALID = ("31", 0, 31, "+33", " 33", "3_3", "33.0", "", "x", "٣٣", 33.0, True, False, [33], {"epoch": 33})


class _Clock(AssertionError):
    pass


class _ExplodingDatetime(_datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        raise _Clock("datetime.now was read")

    @classmethod
    def utcnow(cls):
        raise _Clock("datetime.utcnow was read")


def _no_clock():
    """Make every clock the kernel could read raise."""
    boom = mock.Mock(side_effect=_Clock("a clock was read"))
    return [mock.patch.object(K, "datetime", _ExplodingDatetime),
            mock.patch.object(time, "time", boom),
            mock.patch.object(time, "time_ns", boom),
            mock.patch.object(time, "monotonic", boom),
            mock.patch.object(time, "monotonic_ns", boom)]


class NoClockCase(unittest.TestCase):
    def setUp(self):
        for patcher in _no_clock():
            patcher.start()
            self.addCleanup(patcher.stop)


class WriterEpochRefusalTest(NoClockCase):
    def assert_refusal(self, refusal, code):
        self.assertIsInstance(refusal, dict)
        for field in SIX:
            self.assertIn(field, refusal)
            self.assertTrue(refusal[field], field)
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
        self.assertEqual(refusal["failure_code"], code)
        self.assertEqual(refusal["failed_predicate"], K.HB_EPOCH_PREDICATE)
        self.assertEqual(refusal["retry_entrypoint"], ENTRY)
        self.assertEqual(refusal["owning_existing_goal"], GOAL)
        self.assertIs(refusal["derived_from_clock"], False)
        self.assertIs(refusal["consequence_committed"], False)

    def test_absent_epoch_is_not_supplied(self):
        self.assert_refusal(K.writer_epoch_refusal(None, retry_entrypoint=ENTRY), K.HB_EPOCH_NOT_SUPPLIED)

    def test_invalid_epochs_are_invalid(self):
        for value in INVALID:
            with self.subTest(value=value):
                self.assert_refusal(K.writer_epoch_refusal(value, retry_entrypoint=ENTRY), K.HB_EPOCH_INVALID)

    def test_supplied_epoch_is_not_refused(self):
        for value in (32, "32", 33, "1000"):
            with self.subTest(value=value):
                self.assertIsNone(K.writer_epoch_refusal(value, retry_entrypoint=ENTRY))

    def test_retry_entrypoint_is_required(self):
        with self.assertRaises(TypeError):
            K.writer_epoch_refusal(None)


class SuppliedHbReferenceTest(NoClockCase):
    def test_supplied_epoch_yields_its_reference(self):
        for value, epoch in ((32, 32), ("33", 33), (1000, 1000)):
            with self.subTest(value=value):
                ref = K.supplied_hb_reference(value, retry_entrypoint=ENTRY)
                self.assertEqual(ref, K.hb_reference(epoch=epoch))
                self.assertEqual(ref["epoch"], epoch)
                self.assertEqual(ref["heartbeat_id"], f"HB:{epoch}")
                self.assertIs(ref["derived_from_clock"], False)

    def test_refusals_raise_with_six_fields(self):
        for value, code in [(None, K.HB_EPOCH_NOT_SUPPLIED)] + [(v, K.HB_EPOCH_INVALID) for v in INVALID]:
            with self.subTest(value=value):
                with self.assertRaises(K.SuppliedEpochRefused) as raised:
                    K.supplied_hb_reference(value, retry_entrypoint=ENTRY)
                err = raised.exception
                self.assertIsInstance(err, ValueError)
                self.assertEqual(err.disposition, "FAIL_CLOSED")
                self.assertEqual(err.failed_predicate, K.HB_EPOCH_PREDICATE)
                self.assertEqual(err.refusal["failure_code"], code)
                self.assertTrue(str(err).startswith(code + ": "))
                for field in SIX:
                    self.assertTrue(err.refusal[field], field)

    def test_refusal_is_a_copy(self):
        refusal = K.writer_epoch_refusal(None, retry_entrypoint=ENTRY)
        err = K.SuppliedEpochRefused(refusal)
        refusal["failure_code"] = "changed"
        self.assertEqual(err.refusal["failure_code"], K.HB_EPOCH_NOT_SUPPLIED)


class ClockGuardTest(unittest.TestCase):
    def test_guard_catches_the_clock_path(self):
        """The guard is live: the clock-derived path of hb_reference trips it."""
        for patcher in _no_clock():
            patcher.start()
            self.addCleanup(patcher.stop)
        with self.assertRaises(_Clock):
            K.hb_reference()


class ExportsAndAliasesTest(unittest.TestCase):
    def test_kernel_exports(self):
        for name in ("SuppliedEpochRefused", "writer_epoch_refusal", "supplied_hb_reference"):
            self.assertIn(name, K.__all__)

    def test_writer_modules_alias_the_kernel_refusal(self):
        agg = _load("aggregate_repo_transition_wu_b13a", "resident-runtime/aggregate_repo_transition.py")
        self.assertIs(agg.OrgLedgerEpochRefused, agg.kernel.SuppliedEpochRefused)
        refusal = agg.epoch_refusal(None)
        self.assertEqual(refusal["failure_code"], K.HB_EPOCH_NOT_SUPPLIED)
        self.assertEqual(refusal["retry_entrypoint"], agg.EPOCH_RETRY_ENTRYPOINT)
        self.assertIsNone(agg.epoch_refusal(40))
        self.assertEqual(agg.require_supplied_epoch(40)["epoch"], 40)
        with self.assertRaises(agg.OrgLedgerEpochRefused):
            agg.require_supplied_epoch("x")
        emit = _load("transition_ledger_emit_wu_b13a", ".stegverse/transition-ledger/emit.py")
        self.assertIs(emit.RepoLedgerEpochRefused, emit.kernel.SuppliedEpochRefused)
        self.assertTrue(emit.EPOCH_RETRY_ENTRYPOINT.startswith(".stegverse/transition-ledger/emit.py::append"))


if __name__ == "__main__":
    unittest.main()
