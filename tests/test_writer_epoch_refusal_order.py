"""A receipt writer refuses an invalid supplied epoch before any store opens.

The repository ledger (emit.append), the organization ledger
(aggregate_transition, release_custody, assume_custody), the batch submission
step (submit_pending_released_batch) and frame ingress (kernel.ingest_frame)
check the epoch with the kernel's shared rule (supplied_epoch_failure) first.
A coerced, non-ASCII, fractional, boolean or sub-anchor epoch is the six-field
FAIL_CLOSED: no ledger directory is created and no clock is read. A supplied
4096 is recorded as given, and the organization receipt's observed_at is its
heartbeat, not a clock reading.

Source validation only. No authority effect is claimed.
"""
import importlib.util
import os
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resident-runtime"))


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


emit = _load("transition_ledger_emit_refusal_order", ".stegverse/transition-ledger/emit.py")
import aggregate_repo_transition as org  # noqa: E402
import organization_batch_custody as batches  # noqa: E402

PREDICATE = "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH"
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")
INVALID = ("33.0", True, 31, "+33", " 33", "３３", "abc", "33.7", 33.0)
SHA_A, SHA_B = "sha256:" + "a" * 64, "sha256:" + "b" * 64


class _ClockRead:
    @staticmethod
    def now(*args, **kwargs):
        raise AssertionError("a clock was read")


def no_clock():
    stack = ExitStack()
    for kernel in (emit.kernel, org.kernel):
        stack.enter_context(mock.patch.object(kernel, "datetime", _ClockRead))
    stack.enter_context(mock.patch.object(time, "time", side_effect=AssertionError("time.time read")))
    stack.enter_context(mock.patch.object(time, "time_ns", side_effect=AssertionError("time.time_ns read")))
    return stack


class WriterEpochRefusalOrderTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name)
        self.repo_root = self.work / "repo-ledger"
        self.org_root = self.work / "org-ledger"
        env = mock.patch.dict(os.environ, {"STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root),
                                           "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root)})
        env.start()
        self.addCleanup(env.stop)

    def assertSixFields(self, refusal, entrypoint):
        self.assertEqual(refusal["disposition"], "FAIL_CLOSED")
        for field in SIX_FIELDS:
            self.assertTrue(str(refusal.get(field) or "").strip(), field)
        self.assertEqual(refusal["failed_predicate"], PREDICATE)
        self.assertEqual(refusal["failure_code"], "HB_EPOCH_INVALID")
        self.assertIn(entrypoint, refusal["retry_entrypoint"])
        self.assertIs(refusal["consequence_committed"], False)

    def assertNothingCreated(self):
        self.assertEqual(sorted(p.name for p in self.work.iterdir()), [])

    def test_the_repository_ledger_refuses_before_its_store_is_initialized(self):
        for epoch in INVALID:
            with self.subTest(epoch=epoch), no_clock():
                with self.assertRaises(emit.RepoLedgerEpochRefused) as raised:
                    emit.append("t-order", "TEST", SHA_A, SHA_B, hb_epoch=epoch)
                self.assertSixFields(raised.exception.refusal, ".stegverse/transition-ledger/emit.py::append")
                self.assertNothingCreated()

    def test_the_organization_ledger_refuses_before_its_store_is_created(self):
        calls = {
            "aggregate_transition": lambda e: org.aggregate_transition({}, hb_epoch=e),
            "release_custody": lambda e: org.release_custody({}, hb_epoch=e),
            "assume_custody": lambda e: org.assume_custody({}, materialization_id="m", hb_epoch=e),
            "_aggregate_transition_locked": lambda e: org._aggregate_transition_locked({}, hb_epoch=e),
        }
        for name, call in calls.items():
            for epoch in INVALID:
                with self.subTest(writer=name, epoch=epoch), no_clock():
                    with self.assertRaises(org.OrgLedgerEpochRefused) as raised:
                        call(epoch)
                    self.assertSixFields(raised.exception.refusal,
                                         "resident-runtime/aggregate_repo_transition.py::aggregate_transition")
                    self.assertNothingCreated()

    def test_the_batch_submission_refuses_before_its_outbox_is_read(self):
        for epoch in INVALID:
            with self.subTest(epoch=epoch), no_clock():
                result = batches.submit_pending_released_batch(self.org_root, hb_epoch=epoch)
                self.assertSixFields(result, "organization_batch_custody.py::submit_pending_released_batch")
                self.assertEqual(result["submission_receipts"], [])
                self.assertNothingCreated()

    def test_frame_ingress_refuses_an_invalid_epoch_six_field_before_recovery(self):
        frame = org.kernel.carrier_frame(
            {"packet_id": "p-order", "origin": {"org": "StegVerse-org"},
             "destination": {"org": "StegVerse-Labs", "service": "s"},
             "intr_profile": "x", "payload": {}}, epoch=40)
        cases = {repr(e): e for e in INVALID}
        cases["absent"] = None
        for label, epoch in cases.items():
            with self.subTest(epoch=label), no_clock():
                altered = dict(frame)
                if epoch is None:
                    altered.pop("heartbeat_reference")
                else:
                    altered["heartbeat_reference"] = {**frame["heartbeat_reference"], "epoch": epoch}
                with self.assertRaises(org.kernel.CarrierEpochRefusal) as raised:
                    org.kernel.ingest_frame(self.work / "absent-root", altered)
                record = raised.exception.record
                for field in SIX_FIELDS:
                    self.assertTrue(str(record.get(field) or "").strip(), field)
                self.assertEqual(record["failure_code"],
                                 "HB_EPOCH_NOT_SUPPLIED" if epoch is None else "HB_EPOCH_INVALID")
                self.assertNothingCreated()

    def test_a_supplied_4096_is_recorded_as_given_with_no_clock_read(self):
        with no_clock():
            repository = emit.append("t-order-4096", "TEST", SHA_A, SHA_B, hb_epoch="4096")
            organization = org.aggregate_transition(
                repository, predecessor_org_state_sha256=SHA_A, successor_org_state_sha256=SHA_B,
                hb_epoch=4096, ledger=self.org_root)
        for receipt in (repository, organization):
            self.assertEqual(receipt["hb_reference"]["epoch"], 4096)
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)
        self.assertEqual(organization["observed_at"], "HB:4096")


if __name__ == "__main__":
    unittest.main()
