"""An ingress never forwards a clock-derived epoch as if it were supplied (B-P36f).

intr_destination_ingress and organization_manifest_ingress used to read the
epoch back out of the repository receipt they had just written and hand it to
aggregate_transition. With no epoch supplied that value came from the host
clock, so the organization receipt recorded a clock epoch with
derived_from_clock false. Now only a supplied epoch, or one carried by a
receipt whose reference is derived_from_clock false and passes the shared rule,
is forwarded (`emit.forwarded_epoch`).

Source validation only. No authority effect is claimed.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.test_intr_destination_capability import REGISTRY, diagnostic, ingress

emit = ingress.repository_ledger
FIXED_NS = emit.kernel.HB_ANCHOR_UNIX_NS + 1234 * emit.kernel.HB_PERIOD_NS


def receipts(root):
    return [json.loads(p.read_text(encoding="utf-8")) for p in Path(root).rglob("*.json")
            if "receipt_sha256" in json.loads(p.read_text(encoding="utf-8"))]


class _FixedClock:
    @staticmethod
    def now(tz=None):
        from datetime import datetime, timezone
        return datetime.fromtimestamp(FIXED_NS / 1e9, tz or timezone.utc)


class IngressEpochProvenanceTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.repo_root, self.org_root = Path(work.name) / "repo", Path(work.name) / "org"
        env = mock.patch.dict(os.environ, {"STEGVERSE_REPO_LEDGER_ROOT": str(self.repo_root),
                                           "STEGVERSE_ORG_LEDGER_ROOT": str(self.org_root)})
        env.start()
        self.addCleanup(env.stop)

    def written(self):
        return [r for root in (self.repo_root, self.org_root) if root.exists() for r in receipts(root)
                if isinstance(r.get("hb_reference"), dict)]

    def test_an_absent_epoch_is_never_recorded_as_supplied(self):
        kernels = {emit.kernel, ingress.organization_ledger.kernel}
        patches = [mock.patch.object(k, "datetime", _FixedClock) for k in kernels]
        for patch in patches:
            patch.start()
        try:
            ingress.receive(diagnostic(), registry=REGISTRY, packet_id="absent-epoch")
        finally:
            for patch in patches:
                patch.stop()
        written = self.written()
        self.assertTrue(written)
        for receipt in written:
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], True, receipt.get("schema"))

    def test_a_supplied_4096_is_carried_at_both_levels(self):
        ingress.receive(diagnostic(), registry=REGISTRY, packet_id="supplied-epoch", hb_epoch=4096)
        schemas = {}
        for receipt in self.written():
            self.assertEqual(receipt["hb_reference"]["epoch"], 4096)
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)
            schemas[receipt["schema"]] = True
        self.assertIn("stegverse.repo-transition-receipt/v1", schemas)
        self.assertIn("stegverse.organization-transition-receipt/v1", schemas)

    def test_only_a_supplied_receipt_epoch_is_forwarded(self):
        supplied = {"hb_reference": emit.kernel.hb_reference(epoch=40)}
        clock = {"hb_reference": emit.kernel.hb_reference(now_ns=FIXED_NS)}
        unmarked = {"hb_reference": {k: v for k, v in supplied["hb_reference"].items()
                                     if k != "derived_from_clock"}}
        self.assertEqual(emit.forwarded_epoch(supplied, None), 40)
        self.assertIsNone(emit.forwarded_epoch(clock, None))
        self.assertEqual(emit.forwarded_epoch(clock, 77), 77)
        self.assertIsNone(emit.forwarded_epoch(unmarked, None))
        self.assertIsNone(emit.forwarded_epoch({"hb_reference": {**supplied["hb_reference"], "epoch": "+40"}},
                                               None))


if __name__ == "__main__":
    unittest.main()
