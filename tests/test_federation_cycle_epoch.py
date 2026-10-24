"""The federation cycle takes its epoch as supplied, never from a clock (B-P36e row 20).

federation_cycle.py stamped its cycle receipt from the host clock on every
pass. It now takes --hb-epoch (or HB_EPOCH from its dispatcher) under the
kernel's shared rule: absent or invalid is the six-field refusal, exit 1,
before anything is consumed; supplied, the cycle receipt and every crossing of
the pass carry that epoch, derived_from_clock false, with no clock read. The
activation manifest binds the epoch for its declared resident cycle entrypoint.

Source validation only. No authority effect is claimed.
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fc = _load("federation_cycle_epoch", "resident-runtime/federation_cycle.py")


class _ClockRead:
    @staticmethod
    def now(*args, **kwargs):
        raise AssertionError("a clock was read")


class FederationCycleEpochTests(unittest.TestCase):
    def run_cycle(self, hb_epoch):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            with mock.patch.object(fc.K, "datetime", _ClockRead):
                report = fc.cycle(mesh_root=work / "mesh", node_state_root=work / "node",
                                  repo_ledger_root=work / "repo", org_ledger_root=work / "org",
                                  hb_epoch=hb_epoch)
            written = sorted(str(p.relative_to(work)) for p in work.rglob("*") if p.is_file())
        return report, written

    def test_an_absent_or_invalid_cycle_epoch_is_refused_and_nothing_is_written(self):
        for epoch in (None, "", "+33", " 33", "３３", "33.0", "31", "abc"):
            with self.subTest(epoch=epoch):
                report, written = self.run_cycle(epoch)
                self.assertEqual(report["disposition"], "FAIL_CLOSED")
                self.assertEqual(report["failure_code"],
                                 "HB_EPOCH_NOT_SUPPLIED" if epoch is None else "HB_EPOCH_INVALID")
                for field in SIX:
                    self.assertTrue(report[field], field)
                self.assertEqual(written, [])

    def test_a_supplied_4096_stamps_the_cycle_receipt_with_no_clock_read(self):
        report, written = self.run_cycle("4096")
        self.assertEqual(report["heartbeat_reference"]["epoch"], 4096)
        self.assertIs(report["heartbeat_reference"]["derived_from_clock"], False)
        self.assertTrue(any("cycles.d" in path for path in written))

    def test_the_activation_manifest_binds_the_resident_cycle_epoch(self):
        manifest = json.loads((ROOT / "resident-runtime/activation-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["resident_cycle_entrypoint"], "resident-runtime/federation_cycle.py")
        binding = manifest["resident_cycle_hb_epoch"]
        self.assertEqual(binding["argument"], "--hb-epoch")
        self.assertEqual(binding["from"], "dispatch_input")
        self.assertTrue((ROOT / binding["dispatcher"]).is_file())
        # Hosted dispatch is prohibited while Actions is not runtime authority (row 16).
        self.assertIs(manifest["github_actions_is_runtime_authority"], False)
        self.assertEqual(binding["dispatcher_status"], "PROHIBITED_ON_HOSTED")


if __name__ == "__main__":
    unittest.main()
