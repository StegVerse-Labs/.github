"""A capability crossing stamps its receipts with the carrier's epoch, or is refused.

``kernel.dispatch`` handed a capability-addressed packet to
``capability_ingress.receive`` without the epoch of the frame that carried it.
The bound operation then appended at both ledger levels with no ``hb_epoch``,
and the repository writer fell back to ``kernel.hb_reference()``, which reads
the host clock. The epoch is now taken from the carrier frame and passed
through; a frame without a supplied epoch is refused six-field FAIL_CLOSED
before the operation is loaded and before any ledger store is opened.

Both ledger roots and the mesh are redirected. Nothing here is an authentic
production receipt.
"""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THIS = "StegVerse-Labs"
PEER = "StegVerse-org"
ADDRESS = "stegverse-labs.intr-destination"
OPERATION_ID = "ORGANIZATION_INTR_DESTINATION_INGRESS"
GENESIS = {"mode": "ESTABLISH_GENESIS", "node_ref": "capability-epoch-test", "predecessor": None}
SIX_FIELDS = ("failure_code", "failed_predicate", "required_evidence_or_repair",
              "retry_entrypoint", "owning_existing_goal", "next_attempt")


def _module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kernel = _module("kernel", "org-kernel/kernel.py")
capability = _module("capability_ingress", "org-boundary/runtime/capability_ingress.py")
REGISTRY = json.loads((ROOT / "org-boundary/registry/services.json").read_text(encoding="utf-8"))


def diagnostic(communication_id):
    return {
        "message_class": "ecosystem.communication",
        "communication_id": communication_id,
        "subject": "purpose-neutral mesh diagnostic",
        "body": {"schema": "stegverse.org-intr-destination-diagnostic/v1",
                 "probe": "diagnostic-crossing"},
    }


def packet(packet_id):
    return kernel.build_packet(
        origin_org=PEER, origin_service="stegverse-org.intr-destination",
        destination_org=THIS, destination_service=ADDRESS,
        payload=diagnostic(packet_id), standing=GENESIS,
        transition_reference="intr:transition:" + packet_id,
        authority_effect="NONE", packet_id=packet_id)


class CapabilityCrossingEpochTests(unittest.TestCase):
    LEDGER_ROOTS = ("STEGVERSE_REPO_LEDGER_ROOT", "STEGVERSE_ORG_LEDGER_ROOT")

    def setUp(self):
        self._work = tempfile.TemporaryDirectory()
        self.addCleanup(self._work.cleanup)
        previous = {name: os.environ.get(name) for name in self.LEDGER_ROOTS}
        for name in self.LEDGER_ROOTS:
            os.environ[name] = str(Path(self._work.name) / name.lower())

        def restore():
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
        self.addCleanup(restore)

    def ledger_opened(self):
        return any(Path(os.environ[name]).exists() for name in self.LEDGER_ROOTS)

    def receipts(self, variable, schema):
        root = Path(os.environ[variable])
        found = []
        for path in root.rglob("*.json") if root.exists() else ():
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("schema") == schema:
                found.append(record)
        return found

    def assert_refused(self, refused, failure_code):
        record = refused.exception.record
        self.assertEqual(record["disposition"], "FAIL_CLOSED")
        self.assertEqual(record["failure_code"], failure_code)
        self.assertEqual(record["failed_predicate"], "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH")
        for field in SIX_FIELDS:
            self.assertTrue(record[field], field)
        self.assertIs(record["derived_from_clock"], False)
        self.assertIs(record["consequence_committed"], False)
        self.assertFalse(self.ledger_opened(), "a refused crossing opened a ledger store")

    def test_a_crossing_without_a_carrier_epoch_is_refused_before_any_store_opens(self):
        with self.assertRaises(kernel.CarrierEpochRefusal) as refused:
            kernel.dispatch(ROOT, packet("no-carrier-epoch"), heartbeat_reference=None)
        self.assert_refused(refused, "HB_EPOCH_NOT_SUPPLIED")

    def test_a_crossing_whose_epoch_was_derived_from_a_clock_is_refused(self):
        derived = kernel.hb_reference(now_ns=kernel.HB_ANCHOR_UNIX_NS + 10 * kernel.HB_PERIOD_NS)
        self.assertIs(derived["derived_from_clock"], True)
        with self.assertRaises(kernel.CarrierEpochRefusal) as refused:
            kernel.dispatch(ROOT, packet("clock-derived-epoch"), heartbeat_reference=derived)
        self.assert_refused(refused, "HB_EPOCH_INVALID")

    def test_both_receipts_carry_the_epoch_the_carrier_supplied(self):
        supplied = kernel.hb_reference(epoch=4096)
        result = kernel.dispatch(ROOT, packet("supplied-epoch"), heartbeat_reference=supplied)
        operation = result["application_result"]["receiving_operation_result"]
        self.assertEqual(operation["disposition"], "ALLOW", operation.get("detail"))
        repository, = [r for r in self.receipts("STEGVERSE_REPO_LEDGER_ROOT",
                                                 "stegverse.repo-transition-receipt/v1")
                       if r.get("transition_class") == OPERATION_ID]
        organization, = [r for r in self.receipts("STEGVERSE_ORG_LEDGER_ROOT",
                                                   "stegverse.organization-transition-receipt/v1")
                         if r.get("repo_receipt_sha256") == repository["receipt_sha256"]]
        for receipt in (repository, organization):
            self.assertEqual(receipt["hb_reference"]["epoch"], 4096)
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)

    def test_the_capability_surface_refuses_an_absent_epoch_before_loading_the_operation(self):
        service = next(s for s in REGISTRY["services"] if s["service_id"] == ADDRESS)
        loaded = []
        original = capability.load_operation
        capability.load_operation = lambda resolved: loaded.append(resolved) or original(resolved)
        self.addCleanup(setattr, capability, "load_operation", original)
        with self.assertRaises(SystemExit) as refused:
            capability.receive(ROOT, service, packet("direct-no-epoch"), registry=REGISTRY)
        self.assertEqual(str(refused.exception),
                         "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH:HB_EPOCH_NOT_SUPPLIED")
        self.assertEqual(loaded, [])
        self.assertFalse(self.ledger_opened())


if __name__ == "__main__":
    unittest.main()
