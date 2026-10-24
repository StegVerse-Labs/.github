"""Callers keep the processor's exit-code split (PB-EXIT-SPLIT, DC#10), and every
route refuses a CARRIED or incoherent reference before any write (rows 7, 12, 14).

- organization_manifest_ingress: a crossing whose processor exited 75 (its own
  write fault, `retry_permitted`) is a NON-terminal six-field record and nothing
  is recorded, so the redelivered submission is consumed once; 65, 1, any
  other exit and a crash keep the recorded terminal refusal.
- kernel.run_endpoint_adapter: exit 75 is EndpointWriteFault (the frame stays
  pending, no marker); 65, 1, others and a crash are EndpointInputFault
  (terminal: quarantined FRAME_INGEST_FAILED with a marker).
- kernel.dispatch and carrier_epoch refuse a CARRIED reference
  (CARRIED_NOT_ACCEPTED_BY_DESTINATION) and an incoherent one
  (HB_REFERENCE_INVALID) with nothing written; a wrong-typed frame field is
  FRAME_INGEST_FAILED.

Source validation only. No authority effect is claimed.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import tests.test_manifest_ingress_idempotent as manifest_case
import tests.test_frame_quarantine_and_carried as frame_case

K = frame_case.K
ingress = manifest_case.ingress
SIX = frame_case.SIX


class ManifestIngressExitSplitTests(manifest_case.IngressLedgerCase):
    def crossing(self, returncode):
        record = {"disposition": "FAIL_CLOSED", "terminal": returncode != 65,
                  "failure_code": {75: "PROCESS_BOUNDARY_WRITE_FAULT", 65: "PROCESS_BOUNDARY_INPUT_FAULT"}.get(
                      returncode, "PROCESS_BOUNDARY_FAILED"),
                  "failed_predicate": "P", "detail": "processor exit " + str(returncode),
                  "required_evidence_or_repair": "R", "retry_entrypoint": "E",
                  "owning_existing_goal": "G", "next_attempt": "N"}
        return lambda *a, **k: {"crossing_completed": False, "processor_exit": returncode,
                                "far_side_fault": record, "retry_permitted": returncode == 75,
                                "far_side_disposition": record["detail"], "resolved_service_id": "s"}

    def test_exit_75_is_non_terminal_and_records_nothing(self):
        with mock.patch.object(ingress.crossing_module, "cross", self.crossing(75)):
            result = self.receive()
        self.assertEqual(result["failure_code"], "PROCESS_BOUNDARY_WRITE_FAULT")
        self.assertIs(result["terminal"], False)
        for field in SIX:
            self.assertTrue(result[field], field)
        self.assertEqual(self.receipts(self.repo_root), [])
        self.assertEqual(self.receipts(self.org_root), [])
        # Redelivered once the processor can write: consumed exactly once.
        self.assertEqual(self.receive()["disposition"], "ALLOW")
        self.assertEqual(self.receive()["disposition"], "ALLOW")
        self.assertEqual(len(self.receipts(self.repo_root, ingress.OPERATION_ID)), 1)

    def test_exit_65_1_and_a_crash_keep_the_recorded_terminal_refusal(self):
        for returncode in (65, 1, -9):
            with self.subTest(returncode=returncode):
                self.setUp()
                with mock.patch.object(ingress.crossing_module, "cross", self.crossing(returncode)):
                    result = self.receive()
                self.assertEqual(result["disposition"], "FAIL_CLOSED")
                self.assertNotEqual(result.get("failure_code"), "PROCESS_BOUNDARY_WRITE_FAULT")
                self.assertTrue(self.receipts(self.repo_root, ingress.REFUSED_CLASS))


class EndpointAdapterExitSplitTests(unittest.TestCase):
    def run_adapter(self, body):
        with tempfile.TemporaryDirectory() as work:
            adapter = Path(work) / "adapter.py"
            adapter.write_text(body, encoding="utf-8")
            return K.run_endpoint_adapter(Path(work), adapter, {"packet_id": "p"})

    def test_exit_75_is_a_write_fault_and_every_other_failure_is_terminal(self):
        with self.assertRaises(K.EndpointWriteFault):
            self.run_adapter("import sys; sys.exit(75)\n")
        for body in ("import sys; sys.exit(65)\n", "import sys; sys.exit(1)\n", "raise RuntimeError('crash')\n"):
            with self.subTest(body=body), self.assertRaises(K.EndpointInputFault):
                self.run_adapter(body)


class ConsumeExitSplitTests(frame_case.FrameQuarantineTests):
    def test_a_write_fault_leaves_the_frame_pending_and_an_input_fault_quarantines_it(self):
        self.with_stegcore()
        self.publish("adapter-75")
        with mock.patch.object(K, "run_endpoint_adapter", side_effect=K.EndpointWriteFault("exit 75")):
            pending, = self.cycle()
        self.assertEqual(pending["result"]["status"], "PENDING")
        self.assertIs(pending["result"]["terminal"], False)
        self.assertIsNone(pending["seen_marker"])
        consumed, = self.cycle()
        self.assertEqual(consumed["result"]["status"], "CONSUMED")
        self.assertEqual(self.cycle(), [])

        self.setUp()
        self.with_stegcore()
        self.publish("adapter-65")
        with mock.patch.object(K, "run_endpoint_adapter", side_effect=K.EndpointInputFault("exit 65")):
            quarantined, = self.cycle()
        self.assertQuarantined(quarantined, "FRAME_INGEST_FAILED")
        self.assertEqual(self.cycle(), [])


class ReferenceRoutesTests(frame_case.FrameQuarantineTests):
    def test_dispatch_refuses_a_carried_or_incoherent_reference_with_nothing_written(self):
        self.with_stegcore()
        packet = frame_case.base.packet(frame_case.base.work_request({"signal": {}}))
        supplied = K.hb_reference(epoch=4096)
        cases = {
            "CARRIED_NOT_ACCEPTED_BY_DESTINATION": {**supplied, "source": "ORGANIZATION_LEDGER_HEAD",
                                                    "head_receipt_sha": "f" * 64},
            "HB_REFERENCE_INVALID": {**supplied, "generation": 7},
        }
        for code, reference in cases.items():
            with self.subTest(code=code):
                with self.assertRaises(K.CarrierEpochRefusal) as raised:
                    K.dispatch(frame_case.base.ROOT, packet, heartbeat_reference=reference)
                self.assertEqual(raised.exception.record["failure_code"], code)
                self.assertEqual(self.receipts("STEGVERSE_REPO_LEDGER_ROOT"), [])
                self.assertEqual(self.receipts("STEGVERSE_ORG_LEDGER_ROOT"), [])

    def test_wrong_typed_frame_fields_are_frame_ingest_failed(self):
        for name, value in (("packet_sha256", 123), ("heartbeat_reference", [1, 2])):
            with self.subTest(field=name):
                self.setUp()
                frame = K.carrier_frame({**frame_case.base.packet(frame_case.base.work_request({"signal": {}})),
                                         "packet_id": "typed-" + name}, epoch=4096)
                body = {k: v for k, v in frame.items() if k != "frame_sha256"}
                body[name] = value
                K.publish_frame({**body, "frame_sha256": K.sha(body)}, root=self.work / "mesh")
                entry, = self.cycle()
                self.assertQuarantined(entry, "FRAME_INGEST_FAILED")


if __name__ == "__main__":
    unittest.main()
