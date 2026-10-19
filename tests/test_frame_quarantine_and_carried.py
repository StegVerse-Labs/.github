"""A refused frame is terminal, and a CARRIED claim is verified or refused (B-P36j/k).

consume_and_respond quarantines a frame that can never be consumed -- an absent
or invalid epoch, an unmarked reference, or a self-asserted CARRIED claim whose
head_receipt_sha is not this organization's verified ledger head -- with a
six-field seen-marker (FRAME_REFUSED_QUARANTINED). Nothing is recorded or
answered, no clock is read, the frame is never offered again and it does not
stop the frames behind it. ingest_frame refuses an unverified CARRIED claim
(CARRIED_PROVENANCE_UNVERIFIED) rather than accepting it as SUPPLIED.

Source validation only. No authority effect is claimed.
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

_spec = importlib.util.spec_from_file_location(
    "governance_endpoint_harness_b_p36j", Path(__file__).with_name("test_governance_endpoint.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)
K = base.K

SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")


class _ClockRead:
    @staticmethod
    def now(*args, **kwargs):
        raise AssertionError("a clock was read")


def altered(frame, **reference):
    """The frame with its heartbeat_reference replaced, re-addressed by its own digest."""
    body = {k: v for k, v in frame.items() if k != "frame_sha256"}
    body["heartbeat_reference"] = reference
    return {**body, "frame_sha256": K.sha(body)}


class FrameQuarantineTests(unittest.TestCase):
    VARIABLES = base.GovernanceEndpointTests.VARIABLES
    setUp = base.GovernanceEndpointTests.setUp
    with_stegcore = base.GovernanceEndpointTests.with_stegcore
    ledger = base.GovernanceEndpointTests.ledger

    def receipts(self, variable):
        return self.ledger(variable) if (Path(base.os.environ[variable]) / "receipts").is_dir() else []

    def publish(self, packet_id, reference=None, epoch=1000):
        packet = {**base.packet(base.work_request({"signal": {}})), "packet_id": packet_id}
        frame = K.carrier_frame(packet, epoch=epoch)
        if reference is not None:
            frame = altered(frame, **reference)
        K.publish_frame(frame, root=self.work / "mesh")
        return frame

    def cycle(self):
        return K.consume_and_respond(base.ROOT, mesh_root=self.work / "mesh",
                                     node_state_root=self.work / "node-state", seen=set(),
                                     repo_ledger_root=self.work / "repo-ledger",
                                     org_ledger_root=self.work / "org-ledger")

    def assertQuarantined(self, entry, code):
        result = entry["result"]
        self.assertEqual(result["failure_code"], "FRAME_REFUSED_QUARANTINED")
        self.assertEqual(result["frame_failure_code"], code)
        for field in SIX:
            self.assertTrue(str(result.get(field) or "").strip(), field)
        self.assertIsNone(entry["organization_record"])
        self.assertIsNone(entry["response_publication"])
        marker = json.loads(Path(entry["seen_marker"]).read_text(encoding="utf-8"))
        self.assertEqual(marker["status"], "REFUSED")
        self.assertEqual(marker["failure_code"], "FRAME_REFUSED_QUARANTINED")

    def test_refused_frames_are_quarantined_with_no_clock_and_no_receipt(self):
        supplied = K.hb_reference(epoch=1000)
        cases = {
            "unmarked": ({k: v for k, v in supplied.items() if k != "derived_from_clock"},
                         "HB_EPOCH_PROVENANCE_UNMARKED"),
            "sampled": ({**supplied, "sampled_unix_ns": K.HB_ANCHOR_UNIX_NS}, "HB_EPOCH_INVALID"),
            "coerced": ({**supplied, "epoch": "+1000"}, "HB_EPOCH_INVALID"),
            "forged-carried": ({**supplied, "source": "ORGANIZATION_LEDGER_HEAD", "head_receipt_sha": "f" * 64},
                               "CARRIED_PROVENANCE_UNVERIFIED"),
        }
        for name, (reference, code) in cases.items():
            with self.subTest(case=name):
                self.setUp()
                self.publish("quarantine-" + name, reference)
                with mock.patch.object(K, "datetime", _ClockRead):
                    entry, = self.cycle()
                self.assertQuarantined(entry, code)
                self.assertEqual(self.receipts("STEGVERSE_REPO_LEDGER_ROOT"), [])
                self.assertEqual(self.receipts("STEGVERSE_ORG_LEDGER_ROOT"), [])

    def test_a_quarantined_frame_never_blocks_a_mixed_batch_and_is_not_retried(self):
        self.with_stegcore()
        supplied = K.hb_reference(epoch=1000)
        self.publish("mixed-good")
        self.publish("mixed-unmarked", {k: v for k, v in supplied.items() if k != "derived_from_clock"})
        first = {entry["result"].get("packet_id") or entry["result"].get("status"): entry for entry in self.cycle()}
        self.assertEqual(len(first), 2)
        statuses = sorted(entry["result"]["status"] for entry in first.values())
        self.assertEqual(statuses, ["CONSUMED", "REFUSED"])
        for receipt in self.receipts("STEGVERSE_REPO_LEDGER_ROOT"):
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)
        self.assertEqual(self.cycle(), [])

    def test_ingest_frame_refuses_an_unverified_carried_claim(self):
        frame = altered(K.carrier_frame(base.packet(base.work_request({"signal": {}})), epoch=1000),
                        **{**K.hb_reference(epoch=1000), "source": "ORGANIZATION_LEDGER_HEAD",
                           "head_receipt_sha": "f" * 64})
        with self.assertRaises(K.CarrierEpochRefusal) as raised:
            K.ingest_frame(base.ROOT, frame)
        self.assertEqual(raised.exception.record["failure_code"], "CARRIED_PROVENANCE_UNVERIFIED")
        self.assertEqual(self.receipts("STEGVERSE_REPO_LEDGER_ROOT"), [])


class MonitorAnswerEpochTests(unittest.TestCase):
    def test_a_monitor_answer_takes_the_frame_epoch_with_no_clock_read(self):
        packet = {"packet_id": "monitor-4096", "transition": {"authority_effect": "NONE"},
                  "payload": {"message_class": "ecosystem.monitor.request"}}
        with mock.patch.object(K, "datetime", _ClockRead):
            result = K.handle_control_message(base.ROOT, packet, K.load_registry(base.ROOT), epoch=4096)
        reference = result["monitor_status"]["heartbeat_reference"]
        self.assertEqual(reference["epoch"], 4096)
        self.assertIs(reference["derived_from_clock"], False)
        self.assertNotIn("sampled_unix_ns", reference)

    def test_only_a_supplied_frame_reference_lends_dispatch_its_epoch(self):
        self.assertEqual(K._frame_epoch({"heartbeat_reference": K.hb_reference(epoch=4096)}), 4096)
        self.assertIsNone(K._frame_epoch({"heartbeat_reference": None}))


if __name__ == "__main__":
    unittest.main()
