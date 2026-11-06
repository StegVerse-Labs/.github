"""`kernel.dispatch` hands a capability-address operation the carrier frame's epoch.

The receiving operation behind a capability address writes receipts at both
ledger levels, and a receipt references the epoch its caller supplies. The
epoch a crossing has is the one its carrier frame carries
(`heartbeat_reference.epoch`). Dispatch checks it with the kernel's shared rule
(`carrier_epoch`) and hands it on; a frame without a supplied one, or with a
clock-derived one, is refused six-field FAIL_CLOSED (CarrierEpochRefusal)
before the operation runs. No clock is read. The registry, standing contract,
processing selection and capability resolver are stubbed: nothing here is a
live crossing.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAME_HB_EPOCH = 4096
ORGANIZATION = "StegVerse-Labs"
ADDRESS = "stegverse-labs.intr-destination"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Standing:
    def load_contract(self, root):
        return {}

    def require(self, contract, packet):
        return {}


class _Selection:
    def select_processing(self, service, payload):
        return {}


class _Receiver:
    def __init__(self):
        self.calls = []

    def receive(self, root, service, packet, **kwargs):
        self.calls.append(kwargs)
        return {"capability_received": True}


class KernelDispatchPassesTheFrameEpoch(unittest.TestCase):
    def setUp(self):
        self.kernel = load("kernel_dispatch_frame_epoch_test", "org-kernel/kernel.py")
        self.receiver = _Receiver()
        registry = {"organization": ORGANIZATION,
                    "services": [{"service_id": ADDRESS, "boundary_role": self.kernel.CAPABILITY_INGRESS_ROLE}]}
        self.kernel.load_registry = lambda root: registry
        self.kernel.node_standing = lambda root: _Standing()
        self.kernel.manifest_selection = lambda root: _Selection()
        self.kernel.capability_ingress = lambda root: self.receiver
        self.packet = {"packet_id": "frame-epoch-packet", "destination": {"org": ORGANIZATION, "service": ADDRESS},
                       "payload": {"schema": "stub"}, "transition": {"authority_effect": "NONE"}}

    def dispatch(self, heartbeat_reference):
        return self.kernel.dispatch(ROOT, self.packet, heartbeat_reference=heartbeat_reference)

    def test_the_frame_epoch_reaches_the_receiving_operation(self):
        # Reproducing: red before WU-B13h, when receive() was handed no epoch at all.
        reference = self.kernel.hb_reference(epoch=FRAME_HB_EPOCH)
        result = self.dispatch(reference)
        self.assertIs(result["consumed"], True)
        self.assertEqual(len(self.receiver.calls), 1)
        self.assertEqual(self.receiver.calls[0].get("hb_epoch", "ABSENT"), FRAME_HB_EPOCH)

    def test_a_frame_without_a_supplied_epoch_is_refused_before_the_operation_runs(self):
        clocked = dict(self.kernel.hb_reference(epoch=FRAME_HB_EPOCH), derived_from_clock=True)
        cases = ((None, "HB_EPOCH_NOT_SUPPLIED"), ({}, "HB_EPOCH_NOT_SUPPLIED"),
                 ({"generation": 64}, "HB_EPOCH_NOT_SUPPLIED"), ("HB:64", "HB_EPOCH_INVALID"),
                 ({"epoch": 31}, "HB_EPOCH_INVALID"), ({"epoch": True}, "HB_EPOCH_INVALID"),
                 ({"epoch": "+64"}, "HB_EPOCH_INVALID"), (clocked, "HB_EPOCH_INVALID"))
        for reference, code in cases:
            self.receiver.calls.clear()
            with self.assertRaises(self.kernel.CarrierEpochRefusal) as refused:
                self.dispatch(reference)
            record = refused.exception.record
            self.assertEqual(record["disposition"], "FAIL_CLOSED", reference)
            self.assertEqual(record["failure_code"], code, reference)
            for field in self.kernel.SIX_FIELDS:
                self.assertTrue(record.get(field), (reference, field))
            self.assertIs(record["derived_from_clock"], False)
            self.assertIs(record["consequence_committed"], False)
            # Not run: no receipt-writing operation was reached.
            self.assertEqual(self.receiver.calls, [], reference)

    def test_other_roles_are_not_handed_an_epoch(self):
        service = self.kernel.load_registry(ROOT)["services"][0]
        service["boundary_role"] = "BOUNDARY_LOCAL_DIAGNOSTIC"
        result = self.dispatch(None)
        self.assertEqual(result["application_result"], {"echo": self.packet["payload"]})
        self.assertEqual(self.receiver.calls, [])


if __name__ == "__main__":
    unittest.main()
