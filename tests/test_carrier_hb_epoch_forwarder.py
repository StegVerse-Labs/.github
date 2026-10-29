"""Carrier heartbeat epoch forwarder (Lane D, CARRIER_HB_EPOCH_FORWARDER, stacked on Labs#3241).

The resident dispatcher hands the org claim allocator consumer the carrier's
heartbeat epoch exactly as its caller supplied it, the way the kernel hands an
endpoint adapter declared CARRIER_SUPPLIED the epoch of the frame that
delivered the packet (org-kernel/kernel.py run_endpoint_adapter, INDEX H34b).
Nothing derives an epoch; absent, nothing is forwarded.
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dispatcher = load("carrier_epoch_dispatcher", "scripts/dispatch_resident_execution_requests.py")
OTHER = "cross_framework_current_basis_v04"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


class CarrierHbEpochForwarderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        base = Path(self._td.name)
        self.source = base / "source"
        self.runtime = base / "runtime"
        self.source.mkdir()
        consumers = dict(dispatcher.CONSUMERS)
        for name in ("org_claim_allocator", OTHER):
            path = self.runtime / consumers[name]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# consumer\n", encoding="utf-8")
        # An oscillator observation snapshot in the runtime: never a supplied epoch.
        (self.runtime / "control").mkdir(parents=True, exist_ok=True)
        (self.runtime / "control/heartbeat-carrier-runtime-state.json").write_text(json.dumps(
            {"epoch": 987654321, "oscillator": {"snapshot_is_observation_only": True}}), encoding="utf-8")
        self.calls: list[list[str]] = []

    def tearDown(self) -> None:
        self._td.cleanup()

    def runner(self, command, **kwargs):
        self.calls.append(list(command))
        return SimpleNamespace(returncode=0, stdout='{"state":"ATTEMPT_RECORDED"}\n', stderr="")

    def dispatch(self, **kwargs):
        return dispatcher.dispatch(self.source, self.runtime, runner=self.runner,
                                   env={"PATH": "/bin", "HOME": self._td.name},
                                   only_consumers=("org_claim_allocator", OTHER), **kwargs)

    def command_for(self, name: str) -> list[str] | None:
        rel = str(self.runtime / dict(dispatcher.CONSUMERS)[name])
        return next((c for c in self.calls if c[1] == rel), None)

    def test_supplied_epoch_is_forwarded_only_to_carrier_epoch_consumers(self):
        receipt = self.dispatch(hb_epoch="4096")
        allocator = self.command_for("org_claim_allocator")
        self.assertEqual(allocator[allocator.index("--hb-epoch") + 1], "4096")
        self.assertNotIn("--hb-epoch", self.command_for(OTHER))
        self.assertEqual(receipt["carrier_hb_epoch_forwarded"], "4096")
        self.assertEqual(receipt["carrier_hb_epoch_forwarded_to"], ["org_claim_allocator"])
        self.assertIs(receipt["carrier_hb_epoch_derived_from_clock"], False)
        self.assertEqual(self.dispatch(hb_epoch="0033")["carrier_hb_epoch_forwarded"], "33")

    def test_absent_epoch_forwards_nothing_and_reads_no_snapshot(self):
        receipt = self.dispatch()
        for command in self.calls:
            self.assertNotIn("--hb-epoch", command)
        self.assertIsNone(receipt["carrier_hb_epoch_forwarded"])
        self.assertEqual(receipt["carrier_hb_epoch_forwarded_to"], [])
        self.assertEqual(len(self.calls), 2)

    def test_invalid_epoch_fails_closed_before_the_consumer_runs(self):
        for bad in ("+33", " 33", "3_3", "33.0", "31", True, 31.0):
            self.calls.clear()
            receipt = self.dispatch(hb_epoch=bad)
            self.assertIsNone(self.command_for("org_claim_allocator"), bad)
            self.assertIsNotNone(self.command_for(OTHER), bad)
            row = next(r for r in receipt["outcomes"] if r["consumer"] == "org_claim_allocator")
            self.assertEqual(row["state"], "FAIL_CLOSED")
            self.assertFalse(row["attempted"])
            self.assertEqual(row["result"]["failure_code"], "HB_EPOCH_INVALID", bad)
            for field in SIX:
                self.assertTrue(row["result"].get(field), field)
            self.assertIn("org_claim_allocator", receipt["request_failures"])
            self.assertIsNone(receipt["carrier_hb_epoch_forwarded"])

    def test_forwarder_reads_no_clock_and_no_runtime_heartbeat_snapshot(self):
        text = inspect.getsource(dispatcher.carrier_hb_epoch)
        for forbidden in ("time_ns", "time.", "datetime", "hb_reference(", "heartbeat-carrier-runtime-state",
                          "sample_state", "current_reference"):
            self.assertNotIn(forbidden, text)
        whole = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text(encoding="utf-8")
        self.assertNotIn("heartbeat-carrier-runtime-state", whole)
        self.assertEqual(dispatcher.CARRIER_EPOCH_CONSUMERS, frozenset({"org_claim_allocator"}))

    def test_consumer_cli_applies_the_shared_rule_to_the_raw_text(self):
        for bad in ("+33", " 33", "31"):
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts/consume_org_claim_allocator_request.py"),
                 "--source-root", str(ROOT), "--runtime-root", str(self.runtime), "--hb-epoch", bad],
                capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 1, bad)
            result = json.loads(completed.stdout.strip().splitlines()[-1])
            self.assertEqual(result["failure_code"], "GRANT_EPOCH_INVALID")
            self.assertFalse(result["runtime_execution_attempted"])
            for field in SIX:
                self.assertTrue(result.get(field), field)
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/consume_org_claim_allocator_request.py"),
             "--source-root", str(ROOT), "--runtime-root", str(self.runtime), "--hb-epoch", "0033"],
            capture_output=True, text=True, check=False)
        self.assertEqual(json.loads(completed.stdout.strip().splitlines()[-1])["state"], "NO_REQUEST")

    def test_hosted_workflow_still_supplies_no_epoch(self):
        # No carrier frame reaches the hosted event (JDQ Q-D-4); the workflow forwards none and derives none.
        text = (ROOT / ".github/workflows/organization-claim-allocator-transition.yml").read_text(encoding="utf-8")
        self.assertNotIn("--hb-epoch", text)


if __name__ == "__main__":
    unittest.main()
