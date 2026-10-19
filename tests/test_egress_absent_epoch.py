"""Egress emit and close: an absent epoch is refused; a supplied one stamps everything (G-a).

`organization_egress_boundary.emit` writes receipts (one repository, one
organization) as well as the frame. Without a supplied epoch it is the
unrecorded six-field NO_EPOCH_CALLER_FAILS_CLOSED before anything is built,
published or recorded: no file under the mesh or either ledger root, and no
clock read. With 4096 the frame and both receipts carry 4096, marked
derived_from_clock false. `close` refuses an absent epoch the same way.

Clock reads are counted, not raised, so a swallowed exception cannot hide one.

Source validation only. No authority effect is claimed.
"""
import time
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

import tests.test_reverse_intr_inter_org_route as route

GENESIS, PEER, egress = route.GENESIS, route.PEER, route.egress
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")


def files(root: Path) -> list:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


class EgressAbsentEpochTests(route.ReverseIntrRouteCase):
    payload = route.GovernanceReverseLegTests.payload

    def counted_clock(self):
        calls = {"n": 0}

        def tick(value):
            def read(*args, **kwargs):
                calls["n"] += 1
                return value
            return read

        class _DateTime:
            @staticmethod
            def now(*args, **kwargs):
                calls["n"] += 1
                raise AssertionError("a clock was read")

        stack = ExitStack()
        kernels = {egress.kernel, egress.repository_ledger.kernel, egress.organization_ledger.kernel}
        for kernel in kernels:
            stack.enter_context(mock.patch.object(kernel, "datetime", _DateTime))
        stack.enter_context(mock.patch.object(time, "time", tick(0.0)))
        stack.enter_context(mock.patch.object(time, "time_ns", tick(0)))
        return stack, calls

    def assertNoEpochRefusal(self, result):
        self.assertEqual(result["disposition"], "FAIL_CLOSED")
        self.assertEqual(result["failure_code"], "NO_EPOCH_CALLER_FAILS_CLOSED")
        self.assertEqual(result["failed_predicate"], "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
        self.assertIs(result["refusal_recorded"], False)
        for field in SIX_FIELDS:
            self.assertTrue(str(result.get(field) or "").strip(), field)

    def test_an_absent_epoch_emits_and_records_nothing_and_reads_no_clock(self):
        work = Path(self._work.name)
        stack, calls = self.counted_clock()
        with stack:
            emitted = egress.emit(PEER, self.payload(), standing=GENESIS, capability="governance",
                                  transition_reference="ecosystem.transition.reverse-intr.v1",
                                  mesh_root=self.mesh)
            closed = egress.close(PEER, "absent-epoch-packet", "absent-epoch-communication",
                                  mesh_root=self.mesh)
        self.assertNoEpochRefusal(emitted)
        self.assertIs(emitted["emitted"], False)
        self.assertNoEpochRefusal(closed)
        self.assertEqual(files(work), [])
        self.assertEqual(calls["n"], 0)

    def test_a_supplied_4096_stamps_the_frame_and_both_receipts(self):
        result = egress.emit(PEER, self.payload(), standing=GENESIS, capability="governance",
                             transition_reference="ecosystem.transition.reverse-intr.v1",
                             mesh_root=self.mesh, hb_epoch=4096)
        self.assertEqual(result["disposition"], "ALLOW", result)
        frame, = self.frames_to(PEER)
        self.assertEqual(frame["heartbeat_reference"]["epoch"], 4096)
        self.assertIs(frame["heartbeat_reference"]["derived_from_clock"], False)
        for root in (self.repo_ledger, self.org_ledger_root):
            receipts = [route.json.loads(p.read_text()) for p in (root / "receipts").glob("*.json")]
            self.assertTrue(receipts, root)
            for receipt in receipts:
                self.assertEqual(receipt["hb_reference"]["epoch"], 4096)
                self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)


if __name__ == "__main__":
    unittest.main()
