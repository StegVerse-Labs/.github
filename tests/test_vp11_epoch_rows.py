"""V-P11 rows on #3290: no coercion before the shared rule, and no unstamped write.

- governance_endpoint.record handed '+33', ' 33', 33.7, True or fullwidth digits
  used to run str(int(x)) and write a repository receipt at epoch 33. The value
  now reaches emit.py uncoerced, is refused six-field and nothing is written.
- manage_heartbeat_subsignal --epoch was type=int and wrote '+33', ' 33', 31 or
  fullwidth digits to the lease file. It is now text, checked by the kernel's
  writer_epoch_refusal, and a refusal leaves the file untouched.
- authorize_site_production_promotion no longer appends a refusal receipt
  without a supplied epoch (tests/test_site_production_promotion_authorization.py).

Source validation only. No authority effect is claimed.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
INVALID = ("+33", " 33", "３３", "33.0", "33.7", "31", "abc", "")


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


governance = _load("governance_endpoint_vp11", "resident-runtime/governance_endpoint.py")


class GovernanceRecordTests(unittest.TestCase):
    def test_a_coerced_epoch_is_refused_and_nothing_is_written(self):
        for epoch in ("+33", " 33", "３３", 33.7, True, "33.0"):
            with self.subTest(epoch=epoch), tempfile.TemporaryDirectory() as work:
                roots = {"STEGVERSE_REPO_LEDGER_ROOT": str(Path(work) / "repo"),
                         "STEGVERSE_ORG_LEDGER_ROOT": str(Path(work) / "org")}
                with mock.patch.dict(os.environ, roots):
                    with self.assertRaises(SystemExit) as raised:
                        governance.record({"packet_id": "vp11"}, {"governance_request_sha256": "0" * 64},
                                          hb_epoch=epoch)
                self.assertIn("SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH", str(raised.exception))
                self.assertEqual(list(Path(work).iterdir()), [])

    def test_a_retried_decision_is_recorded_once(self):
        with tempfile.TemporaryDirectory() as work:
            roots = {"STEGVERSE_REPO_LEDGER_ROOT": str(Path(work) / "repo"),
                     "STEGVERSE_ORG_LEDGER_ROOT": str(Path(work) / "org")}
            with mock.patch.dict(os.environ, roots):
                first = governance.record({"packet_id": "retried"}, {"governance_request_sha256": "0" * 64,
                                                                    "disposition": "ALLOW"}, hb_epoch=4096)
                again = governance.record({"packet_id": "retried"}, {"governance_request_sha256": "0" * 64,
                                                                    "disposition": "ALLOW"}, hb_epoch=4096)
            receipts = list((Path(work) / "repo" / "receipts").glob("*.json"))
        self.assertEqual(first, again)
        self.assertEqual(len(receipts), 1)


class HeartbeatSubsignalEpochTests(unittest.TestCase):
    def open_lease(self, epoch):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "subsignals.json"
            data = json.loads((ROOT / "control/heartbeat-subsignals.json").read_text(encoding="utf-8"))
            data["subsignals"]["steggate_transport_lease"]["state"] = "IDLE"
            path.write_text(json.dumps(data), encoding="utf-8")
            before = path.read_bytes()
            completed = subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts/manage_heartbeat_subsignal.py"), "open",
                 "--lease-id", "lease-vp11", "--epoch=" + epoch, "--path", str(path)],
                capture_output=True, text=True, timeout=60)
            return completed, before, path.read_bytes()

    def test_a_coerced_or_sub_anchor_epoch_is_refused_and_the_lease_is_untouched(self):
        for epoch in INVALID:
            with self.subTest(epoch=epoch):
                completed, before, after = self.open_lease(epoch)
                self.assertEqual(completed.returncode, 1, completed.stderr)
                refusal = json.loads(completed.stdout)
                self.assertEqual(refusal["failed_predicate"], "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
                self.assertEqual(refusal["failure_code"], "HB_EPOCH_INVALID")
                for field in ("required_evidence_or_repair", "retry_entrypoint",
                              "owning_existing_goal", "next_attempt"):
                    self.assertTrue(refusal[field], field)
                self.assertEqual(after, before)

    def test_4096_opens_the_lease_at_that_epoch(self):
        completed, before, after = self.open_lease("4096")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        lease = json.loads(after)["subsignals"]["steggate_transport_lease"]
        self.assertEqual(lease["opened_epoch"], 4096)


if __name__ == "__main__":
    unittest.main()
