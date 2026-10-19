"""A capability-address crossing hands the carrier frame's epoch to the operation.

`kernel.dispatch` passes the epoch the frame's `heartbeat_reference` supplies
to `capability_ingress.receive(hb_epoch=)`, which hands it to the receiving
operation, so the operation's receipts reference that frame epoch. A frame
without a supplied epoch is dispatched as before. No clock is read for the epoch.

Both ledger roots and the mesh are redirected, as in
test_intr_destination_capability. Nothing here is an authentic production receipt.
"""
from __future__ import annotations

import os
from pathlib import Path

from tests import test_intr_destination_capability as base

kernel = base.kernel
capability = base.capability
FRAME_EPOCH = 4096


class CapabilityFrameEpochTests(base.RedirectedLedgers):
    def publish(self, packet_id, *, epoch=None):
        packet = kernel.build_packet(
            origin_org=base.PEER,
            origin_service=kernel.organization_slug(base.PEER) + "." + base.PROFILE_ID,
            destination_org=base.THIS, destination_service=base.ADDRESS,
            payload=base.diagnostic(packet_id), standing=base.GENESIS,
            transition_reference="intr:transition:" + packet_id,
            authority_effect="NONE", packet_id=packet_id)
        kernel.publish_packet(packet, root=self.mesh, epoch=epoch)

    def consume(self):
        return kernel.consume_addressed_frames(
            base.ROOT, mesh_root=self.mesh,
            repo_ledger_root=os.environ["STEGVERSE_REPO_LEDGER_ROOT"],
            org_ledger_root=os.environ["STEGVERSE_ORG_LEDGER_ROOT"])

    def operation_receipt(self):
        repository, = self.receipts("STEGVERSE_REPO_LEDGER_ROOT",
                                    "stegverse.repo-transition-receipt/v1", base.OPERATION_ID)
        organization, = [record for record in self.receipts(
            "STEGVERSE_ORG_LEDGER_ROOT", "stegverse.organization-transition-receipt/v1")
            if record.get("repo_receipt_sha256") == repository["receipt_sha256"]]
        return repository, organization

    def test_the_operation_receipts_reference_the_frame_epoch(self):
        self.publish("frame-epoch-diagnostic", epoch=FRAME_EPOCH)
        result, = self.consume()
        operation = result["result"]["execution_result"]["application_result"]["receiving_operation_result"]
        self.assertEqual(operation["disposition"], "ALLOW", operation.get("detail"))
        for receipt in self.operation_receipt():
            self.assertEqual(receipt["hb_reference"]["epoch"], FRAME_EPOCH)
            self.assertIs(receipt["hb_reference"]["derived_from_clock"], False)

    def test_a_frame_without_a_supplied_epoch_is_dispatched_as_before(self):
        self.publish("no-frame-epoch-diagnostic")
        result, = self.consume()
        operation = result["result"]["execution_result"]["application_result"]["receiving_operation_result"]
        self.assertEqual(operation["disposition"], "ALLOW", operation.get("detail"))
        # Unchanged from main: the operation is handed no epoch, so its
        # repository writer still takes its own default reference.
        repository, _ = self.operation_receipt()
        self.assertIsNot(repository["hb_reference"]["derived_from_clock"], False)


class CapabilityIngressPassthroughTests(base.unittest.TestCase):
    def receive(self, calls, **kwargs):
        class Operation:
            @staticmethod
            def receive(submission, **given):
                calls.append(given)
                return {"disposition": "ALLOW"}
        resolved = {"capability_profile_id": base.PROFILE_ID, "capability_operation": base.OPERATION,
                    "receiving_operation_id": base.OPERATION_ID, "receiving_operation_module": "stub",
                    "resolution_source": "stub"}
        saved = {name: getattr(capability, name)
                 for name in ("resolve", "binding_for_service", "submission_for", "load_operation")}
        capability.resolve = lambda root, service: resolved
        capability.binding_for_service = lambda root, service_id: {}
        capability.submission_for = lambda binding, payload: payload
        capability.load_operation = lambda resolved: Operation
        try:
            return capability.receive(Path("."), {"service_id": base.ADDRESS},
                                      {"payload": {}, "packet_id": "p"}, registry={}, **kwargs)
        finally:
            for name, value in saved.items():
                setattr(capability, name, value)

    def test_the_supplied_epoch_is_handed_to_the_operation_as_given(self):
        calls = []
        self.receive(calls, hb_epoch=FRAME_EPOCH)
        self.assertEqual(calls[0]["hb_epoch"], FRAME_EPOCH)

    def test_without_an_epoch_the_operation_is_called_as_before(self):
        calls = []
        self.receive(calls)
        self.assertNotIn("hb_epoch", calls[0])
