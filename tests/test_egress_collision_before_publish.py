"""An egress collision is refused before anything is published (N11).

With a supplied epoch an emission's frame is reproducible, so a second
emission of the same packet id whose frame differs (here: another standing,
which the packet id does not hash) used to publish its frame and only then
fail `ledger_receipt_collision` at the repository append. It is now refused
six-field (ONE_PACKET_ID_BINDS_ONE_EMISSION) before publishing.

Source validation only. No authority effect is claimed.
"""
import unittest

import tests.test_reverse_intr_inter_org_route as route

GENESIS, PEER, egress = route.GENESIS, route.PEER, route.egress


class EgressCollisionBeforePublishTests(route.ReverseIntrRouteCase):
    payload = route.GovernanceReverseLegTests.payload

    def emit(self, standing):
        return egress.emit(PEER, self.payload(), standing=standing, capability="governance",
                           transition_reference="ecosystem.transition.reverse-intr.v1",
                           mesh_root=self.mesh, hb_epoch=4096)

    def test_a_second_emission_of_the_same_packet_id_publishes_nothing(self):
        first = self.emit(GENESIS)
        self.assertEqual(first["disposition"], "ALLOW", first)
        frames = sorted(p.name for p in (self.mesh / "frames.d").glob("*.json"))
        again = self.emit({**GENESIS, "node_ref": "another-node"})
        self.assertNotEqual(again["disposition"], "ALLOW", again)
        self.assertEqual(again["failed_predicate"], "ONE_PACKET_ID_BINDS_ONE_EMISSION")
        self.assertEqual(sorted(p.name for p in (self.mesh / "frames.d").glob("*.json")), frames)

    def test_an_exact_replay_still_returns_the_recorded_emission(self):
        first = self.emit(GENESIS)
        again = self.emit(GENESIS)
        self.assertEqual(again["disposition"], "ALLOW")
        self.assertEqual(again["packet_id"], first["packet_id"])

    def test_a_digit_string_epoch_is_that_epoch_and_an_invalid_one_writes_nothing(self):
        result = egress.emit(PEER, self.payload(), standing=GENESIS, capability="governance",
                             transition_reference="ecosystem.transition.reverse-intr.v1",
                             mesh_root=self.mesh, hb_epoch="4096")
        self.assertEqual(result["disposition"], "ALLOW", result)
        frame, = self.frames_to(PEER)
        self.assertEqual(frame["heartbeat_reference"]["epoch"], 4096)
        for epoch in ("+4096", " 4096", "4096.0", True, 31):
            with self.subTest(epoch=epoch):
                with self.assertRaises(egress.kernel.SuppliedEpochRefused) as raised:
                    egress.emit(PEER, {**self.payload(), "communication_id": "other:" + str(epoch)},
                                standing=GENESIS, capability="governance",
                                transition_reference="ecosystem.transition.reverse-intr.v1",
                                mesh_root=self.mesh, hb_epoch=epoch)
                self.assertEqual(raised.exception.refusal["failure_code"], "HB_EPOCH_INVALID")
                self.assertEqual(len(self.frames_to(PEER)), 1)


if __name__ == "__main__":
    unittest.main()
