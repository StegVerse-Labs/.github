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

    def test_any_per_frame_failure_is_quarantined_and_the_valid_frame_proceeds(self):
        self.with_stegcore()
        supplied = K.hb_reference(epoch=1000)
        clock = K.hb_reference(now_ns=K.HB_ANCHOR_UNIX_NS + 5 * K.HB_PERIOD_NS)
        self.publish("bad-generation", {**supplied, "generation": 7})
        self.publish("bad-id", {**supplied, "heartbeat_id": "HB:7"})
        K.publish_frame({**K.carrier_frame({**base.packet(base.work_request({"signal": {}})),
                                            "packet_id": "bad-integrity"}, epoch=1000),
                         "frame_sha256": "sha256:" + "1" * 64}, root=self.work / "mesh")
        self.publish("clock-abc", {**clock, "epoch": "abc"})
        self.publish("clock-no-epoch", {k: v for k, v in clock.items() if k != "epoch"})
        K.publish_frame({**K.carrier_frame({**base.packet(base.work_request({"signal": {}})),
                                            "packet_id": "bad-packet-hash"}, epoch=1000),
                         "packet_sha256": "sha256:" + "0" * 64}, root=self.work / "mesh")
        self.publish("valid")
        entries = self.cycle()
        by_status = {}
        for entry in entries:
            by_status.setdefault(entry["result"]["status"], []).append(entry)
        self.assertEqual(len(by_status.get("CONSUMED", [])), 1)
        codes = sorted(entry["result"]["frame_failure_code"] for entry in by_status["REFUSED"])
        self.assertIn("HB_REFERENCE_INVALID", codes)
        self.assertIn("HB_EPOCH_INVALID", codes)
        self.assertIn("HB_EPOCH_NOT_SUPPLIED", codes)
        self.assertIn("FRAME_INTEGRITY_INVALID", codes)
        for entry in by_status["REFUSED"]:
            for field in SIX:
                self.assertTrue(str(entry["result"].get(field) or "").strip(), field)
            self.assertIsNone(entry["organization_record"])
        for receipt in self.receipts("STEGVERSE_REPO_LEDGER_ROOT"):
            self.assertEqual(receipt["hb_reference"]["epoch"], 1000)
        self.assertEqual(self.cycle(), [])

    def test_unreadable_frame_files_are_quarantined_by_name_and_the_scan_continues(self):
        self.with_stegcore()
        frames = self.work / "mesh" / "frames.d"
        frames.mkdir(parents=True, exist_ok=True)
        (frames / "000-not-json.json").write_text("{not json", encoding="utf-8")
        (frames / "001-a-list.json").write_text("[1,2,3]", encoding="utf-8")
        (frames / "002-not-utf8.json").write_bytes(b"\xff\xfe\x00garbage")
        (frames / "003-oversized.json").write_text(
            json.dumps({"pad": "x" * (K.FRAME_SIZE_CAP_BYTES + 1)}), encoding="utf-8")
        (frames / "004-read-error.json").mkdir()
        self.publish("after-the-corrupt-files")
        with mock.patch.object(K, "datetime", _ClockRead):
            entries = self.cycle()
        refused = [e for e in entries if e["result"]["status"] == "REFUSED"]
        consumed = [e for e in entries if e["result"]["status"] == "CONSUMED"]
        self.assertEqual(len(consumed), 1)
        self.assertEqual(len(refused), 5)
        for entry in refused:
            self.assertEqual(entry["result"]["frame_failure_code"], "FRAME_INGEST_FAILED")
            for field in SIX:
                self.assertTrue(str(entry["result"].get(field) or "").strip(), field)
            self.assertIsNone(entry["organization_record"])
        self.assertEqual(self.cycle(), [])

    def test_a_deeply_nested_frame_file_is_quarantined_and_the_valid_frame_is_consumed_once(self):
        self.with_stegcore()
        frames = self.work / "mesh" / "frames.d"
        frames.mkdir(parents=True, exist_ok=True)
        deep = '{"a":' + "[" * 200000
        self.assertLess(len(deep), K.FRAME_SIZE_CAP_BYTES)
        (frames / "000-deep.json").write_text(deep, encoding="utf-8")
        self.publish("after-the-deep-file")
        with mock.patch.object(K, "datetime", _ClockRead):
            entries = self.cycle()
        statuses = sorted(e["result"]["status"] for e in entries)
        self.assertEqual(statuses, ["CONSUMED", "REFUSED"])
        refused = next(e for e in entries if e["result"]["status"] == "REFUSED")
        self.assertEqual(refused["result"]["frame_failure_code"], "FRAME_INGEST_FAILED")
        self.assertEqual(self.cycle(), [])

    def test_a_wrong_typed_field_is_quarantined_before_and_after_a_valid_frame(self):
        self.with_stegcore()
        for name in ("typed-before", "valid", "typed-after"):
            frame = K.carrier_frame({**base.packet(base.work_request({"signal": {}})), "packet_id": name},
                                    epoch=1000)
            if name != "valid":
                body = {k: v for k, v in frame.items() if k != "frame_sha256"}
                body["packet_base64"] = 123
                frame = {**body, "frame_sha256": K.sha(body)}
            K.publish_frame(frame, root=self.work / "mesh")
        entries = self.cycle()
        statuses = sorted(e["result"]["status"] for e in entries)
        self.assertEqual(statuses, ["CONSUMED", "REFUSED", "REFUSED"])
        for entry in entries:
            if entry["result"]["status"] == "REFUSED":
                self.assertEqual(entry["result"]["frame_failure_code"], "FRAME_INGEST_FAILED")
                self.assertIn("Error", entry["result"]["failed_predicate"])
        self.assertEqual(self.cycle(), [])

    def test_a_bare_sampled_frame_is_clock_consumed_and_lends_no_epoch(self):
        supplied = K.hb_reference(epoch=1000)
        bare = {k: v for k, v in supplied.items() if k != "derived_from_clock"}
        bare["sampled_unix_ns"] = K.HB_ANCHOR_UNIX_NS
        self.assertIsNone(K._frame_epoch({"heartbeat_reference": bare}))
        self.assertTrue(K._is_clock_reference(bare))

    def test_a_verified_carried_claim_is_not_accepted_by_this_destination(self):
        self.with_stegcore()
        self.publish("seed")
        self.cycle()
        org = self.receipts("STEGVERSE_ORG_LEDGER_ROOT")
        head = json.loads((Path(base.os.environ["STEGVERSE_ORG_LEDGER_ROOT"]) / "HEAD.json").read_text())
        carried = {**K.hb_reference(epoch=1000), "source": "ORGANIZATION_LEDGER_HEAD",
                   "head_receipt_sha": head["receipt_sha256"]}
        self.assertTrue(org)
        self.publish("carried-verified", carried)
        entry, = self.cycle()
        self.assertQuarantined(entry, "CARRIED_NOT_ACCEPTED_BY_DESTINATION")
        self.assertIs(K.load_registry(base.ROOT)["accepts_carried_crossings"], False)
        self.assertEqual(entry["result"]["failed_predicate"], "DESTINATION_ACCEPTS_CARRIED_CROSSINGS")
        self.assertEqual(entry["result"]["required_evidence_or_repair"], "re-send with the SUPPLIED epoch")
        self.assertIn("sender", entry["result"]["retry_entrypoint"])
        self.assertEqual(self.receipts("STEGVERSE_ORG_LEDGER_ROOT"), org)

    def test_ingest_frame_refuses_an_unverified_carried_claim(self):
        frame = altered(K.carrier_frame(base.packet(base.work_request({"signal": {}})), epoch=1000),
                        **{**K.hb_reference(epoch=1000), "source": "ORGANIZATION_LEDGER_HEAD",
                           "head_receipt_sha": "f" * 64})
        with self.assertRaises(K.CarrierEpochRefusal) as raised:
            K.ingest_frame(base.ROOT, frame)
        self.assertEqual(raised.exception.record["failure_code"], "CARRIED_PROVENANCE_UNVERIFIED")
        self.assertEqual(self.receipts("STEGVERSE_REPO_LEDGER_ROOT"), [])


class CycleEpochTests(FrameQuarantineTests):
    """B-P36l and NARROW: a cycle's own supplied epoch against a frame's."""

    def cycle(self, **options):
        return K.consume_and_respond(base.ROOT, mesh_root=self.work / "mesh",
                                     node_state_root=self.work / "node-state", seen=set(),
                                     repo_ledger_root=self.work / "repo-ledger",
                                     org_ledger_root=self.work / "org-ledger", **options)

    def test_an_explicit_epoch_that_differs_from_the_frame_is_a_conflict_and_writes_nothing(self):
        self.publish("conflict", epoch=77)
        pending, = self.cycle(hb_epoch=4096)
        self.assertEqual(pending["result"]["failure_code"], "HB_EPOCH_CONFLICT")
        self.assertIs(pending["result"]["terminal"], False)
        for field in SIX:
            self.assertTrue(str(pending["result"].get(field) or "").strip(), field)
        self.assertIsNone(pending["seen_marker"])
        self.assertEqual(self.receipts("STEGVERSE_REPO_LEDGER_ROOT"), [])
        self.assertEqual(len(self.cycle(hb_epoch=4096)), 1)

    def test_an_invalid_explicit_epoch_is_refused_whatever_the_frame(self):
        self.publish("explicit-invalid", epoch=4096)
        for epoch in ("+4096", " 4096", "4096.0", True, 31, "abc"):
            with self.subTest(epoch=epoch):
                with self.assertRaises(K.SuppliedEpochRefused) as raised:
                    self.cycle(hb_epoch=epoch)
                self.assertEqual(raised.exception.refusal["failure_code"], "HB_EPOCH_INVALID")
        self.assertEqual(self.receipts("STEGVERSE_REPO_LEDGER_ROOT"), [])

    def test_a_clock_frame_is_consumed_at_the_cycle_epoch_with_no_clock_read(self):
        self.with_stegcore()
        packet = {**base.packet(base.work_request({"signal": {}})), "packet_id": "clock-frame"}
        K.publish_frame(K.carrier_frame(packet, now_ns=K.HB_ANCHOR_UNIX_NS + 3 * K.HB_PERIOD_NS),
                        root=self.work / "mesh")
        self.assertEqual(self.cycle()[0]["result"]["failure_code"], "HB_EPOCH_NOT_SUPPLIED")
        with mock.patch.object(K, "datetime", _ClockRead):
            consumed, = self.cycle(hb_epoch=4096)
        self.assertEqual(consumed["result"]["status"], "CONSUMED")
        receipts = self.receipts("STEGVERSE_REPO_LEDGER_ROOT") + self.receipts("STEGVERSE_ORG_LEDGER_ROOT")
        self.assertTrue(receipts)
        for receipt in receipts:
            self.assertEqual(receipt["hb_reference"]["epoch"], 4096)
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)


class TornWriteTests(FrameQuarantineTests):
    """A fault on the HEAD write leaves the frame pending; the next cycle rolls the
    orphan receipt forward exactly once (POSIX append_transaction writes HEAD last,
    and a receipt at a supplied epoch is rebuilt byte-identically)."""

    def test_a_head_write_fault_on_either_ledger_is_completed_once_by_the_next_cycle(self):
        for which in ("crossing_repository_ledger", "crossing_organization_ledger"):
            with self.subTest(ledger=which):
                self.setUp()
                for name in ("torn-" + which, "torn-later-" + which):
                    packet = K.build_packet(
                        origin_org="Origin", origin_service="origin.org-control",
                        destination_org="StegVerse-Labs", destination_service="stegverse-labs.org-control",
                        payload={"communication_id": name, "message_class": "ecosystem.communication",
                                 "subject": "s", "body": {}},
                        standing={"mode": "ESTABLISH_GENESIS", "node_ref": "torn", "predecessor": None},
                        packet_id=name)
                    K.publish_packet(packet, root=self.work / "mesh", epoch=1000)
                module = K._own_module(which, ".stegverse/transition-ledger/emit.py"
                                       if which == "crossing_repository_ledger"
                                       else "resident-runtime/aggregate_repo_transition.py")
                store_class = module.ledger_store.PosixLedgerStore
                original, faults = store_class.put, {"n": 0}

                def put(store, key, value):
                    if key == module.ledger_store.HEAD_KEY and faults["n"] == 0:
                        faults["n"] += 1
                        raise OSError("simulated HEAD write fault")
                    return original(store, key, value)

                with mock.patch.object(store_class, "put", put):
                    first = self.cycle()
                statuses = sorted(e["result"]["status"] for e in first)
                self.assertIn("PENDING", statuses)
                for entry in first:
                    if entry["result"]["status"] == "PENDING":
                        self.assertIs(entry["result"]["terminal"], False)
                        self.assertIsNone(entry["seen_marker"])
                second = self.cycle()
                self.assertEqual([e["result"]["status"] for e in second], ["CONSUMED"])
                self.assertEqual(self.cycle(), [])
                for variable in ("STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_ROOT"):
                    rows = self.receipts(variable)
                    self.assertEqual(len(rows), len({r["receipt_sha256"] for r in rows}))
                    self.assertEqual(len({r.get("transition_id") or r.get("repo_receipt_sha256")
                                          for r in rows}), len(rows))


class ResponseOnceTests(FrameQuarantineTests):
    """F-REPUB keying: one response id answers one request."""

    def control(self, packet_id, subject):
        return K.build_packet(
            origin_org="Origin", origin_service="origin.org-control",
            destination_org="StegVerse-Labs", destination_service="stegverse-labs.org-control",
            payload={"communication_id": "once", "message_class": "ecosystem.communication",
                     "subject": subject, "body": {}},
            standing={"mode": "ESTABLISH_GENESIS", "node_ref": "once", "predecessor": None},
            packet_id=packet_id)

    def answers(self):
        frames = [json.loads(p.read_text()) for p in (self.work / "mesh" / "frames.d").glob("*.json")]
        return [f for f in frames if f.get("origin_org") == "StegVerse-Labs"]

    def test_a_different_request_under_an_answered_response_id_is_a_collision(self):
        K.publish_packet(self.control("request-a", "a"), root=self.work / "mesh", epoch=1000)
        first, = self.cycle()
        self.assertEqual(first["result"]["status"], "CONSUMED")
        self.assertEqual(len(self.answers()), 1)
        K.publish_packet(self.control("request-b", "b"), root=self.work / "mesh", epoch=1000)
        second, = self.cycle()
        self.assertQuarantined(second, "RESPONSE_ID_COLLISION")
        self.assertEqual(len(self.answers()), 1)

    def test_a_marker_fault_after_publishing_does_not_publish_a_second_answer(self):
        K.publish_packet(self.control("request-once", "x"), root=self.work / "mesh", epoch=1000)
        original = K.mark_federation_frame_seen
        faults = {"n": 0}

        def faulty(*args, **kwargs):
            if faults["n"] == 0:
                faults["n"] += 1
                raise OSError("simulated marker write fault")
            return original(*args, **kwargs)

        with mock.patch.object(K, "mark_federation_frame_seen", faulty):
            pending, = self.cycle()
        self.assertEqual(pending["result"]["failure_code"], "FRAME_DISPATCH_IO_FAILED")
        self.assertIs(pending["result"]["terminal"], False)
        again, = self.cycle()
        self.assertEqual(again["result"]["status"], "CONSUMED")
        self.assertEqual(len(self.answers()), 1)


class IngestFrameReferenceTests(unittest.TestCase):
    """Rows 5/12/15: ingest_frame is six-field on an incoherent reference; "4096" is 4096."""

    def frame(self, **reference):
        frame = K.carrier_frame(base.packet(base.work_request({"signal": {}})), epoch=4096)
        return altered(frame, **{**frame["heartbeat_reference"], **reference})

    def test_an_incoherent_generation_or_id_is_six_field(self):
        for change in ({"generation": 7}, {"heartbeat_id": "HB:7"}):
            with self.subTest(change=change):
                with self.assertRaises(K.CarrierEpochRefusal) as raised:
                    K.ingest_frame(base.ROOT, self.frame(**change))
                self.assertEqual(raised.exception.record["failure_code"], "HB_REFERENCE_INVALID")
                for field in SIX:
                    self.assertTrue(raised.exception.record[field], field)

    def test_a_digit_string_epoch_is_that_epoch(self):
        reference = {**K.hb_reference(epoch=4096), "epoch": "4096"}
        self.assertIs(K.validate_hb_reference(reference), reference)
        self.assertEqual(K._frame_epoch({"heartbeat_reference": reference}), 4096)
        for bad in ("+4096", " 4096", "\uff14\uff10\uff19\uff16"):
            with self.subTest(epoch=bad), self.assertRaises(ValueError):
                K.validate_hb_reference({**reference, "epoch": bad})


class PostHeadFaultTests(TornWriteTests):
    """F-POST-HEAD: a fault after HEAD's replace (its directory fsync) leaves the
    append committed; the retry returns the recorded receipt and appends none."""

    def test_a_durability_fault_after_head_is_retried_without_a_second_receipt(self):
        for which in ("crossing_repository_ledger", "crossing_organization_ledger"):
            with self.subTest(ledger=which):
                self.setUp()
                packet = K.build_packet(
                    origin_org="Origin", origin_service="origin.org-control",
                    destination_org="StegVerse-Labs", destination_service="stegverse-labs.org-control",
                    payload={"communication_id": "post-head-" + which, "message_class": "ecosystem.communication",
                             "subject": "s", "body": {}},
                    standing={"mode": "ESTABLISH_GENESIS", "node_ref": "post-head", "predecessor": None},
                    packet_id="post-head-" + which)
                K.publish_packet(packet, root=self.work / "mesh", epoch=1000)
                module = K._own_module(which, ".stegverse/transition-ledger/emit.py"
                                       if which == "crossing_repository_ledger"
                                       else "resident-runtime/aggregate_repo_transition.py")
                store_class = module.ledger_store.PosixLedgerStore
                original, faults = store_class._sync_directory, {"n": 0}

                def sync(store, directory):
                    if Path(directory) == Path(store.root) and faults["n"] == 0:
                        faults["n"] += 1
                        raise OSError("simulated directory fsync fault after HEAD replace")
                    return original(directory)

                with mock.patch.object(store_class, "_sync_directory", sync):
                    first, = self.cycle()
                self.assertEqual(first["result"]["failure_code"], "FRAME_DISPATCH_IO_FAILED")
                self.assertIn("HEAD committed", first["result"]["detail"])
                self.assertIs(first["result"]["terminal"], False)
                again, = self.cycle()
                self.assertEqual(again["result"]["status"], "CONSUMED")
                for variable in ("STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_ROOT"):
                    self.assertEqual(len(self.receipts(variable)), 1, variable)


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
