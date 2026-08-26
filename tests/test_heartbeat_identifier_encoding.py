import unittest

from heartbeat_runtime.independent_oscillator import (
    HEARTBEAT_ID_MAX_EPOCH,
    OSCILLATOR_PERIOD_NS,
    PROTOCOL_ANCHOR_EPOCH,
    PROTOCOL_ANCHOR_UNIX_NS,
    current_reference,
    decode_heartbeat_id,
    encode_heartbeat_id,
    sample_state,
)


class HeartbeatIdentifierEncodingTests(unittest.TestCase):
    def test_known_values(self):
        self.assertEqual(encode_heartbeat_id(0), "HB-00000000")
        self.assertEqual(encode_heartbeat_id(32), "HB-0000000W")
        self.assertEqual(encode_heartbeat_id(35), "HB-0000000Z")
        self.assertEqual(encode_heartbeat_id(36), "HB-00000010")

    def test_round_trip(self):
        for epoch in (0, 1, 32, 36, 26_473_432, HEARTBEAT_ID_MAX_EPOCH):
            identifier = encode_heartbeat_id(epoch)
            self.assertEqual(decode_heartbeat_id(identifier), epoch)

    def test_fixed_width_lexical_order_matches_numeric_order(self):
        epochs = [0, 1, 35, 36, 100, 1_000_000, 26_473_432, HEARTBEAT_ID_MAX_EPOCH]
        identifiers = [encode_heartbeat_id(epoch) for epoch in epochs]
        self.assertEqual(identifiers, sorted(identifiers))

    def test_anchor_has_base36_display_identifier(self):
        ref = current_reference(now_ns=PROTOCOL_ANCHOR_UNIX_NS)
        self.assertEqual(ref["epoch"], PROTOCOL_ANCHOR_EPOCH)
        self.assertEqual(ref["heartbeat_id"], "HB-0000000W")

    def test_ten_ms_successor_changes_identifier_once(self):
        first = current_reference(now_ns=PROTOCOL_ANCHOR_UNIX_NS)
        same = current_reference(now_ns=PROTOCOL_ANCHOR_UNIX_NS + OSCILLATOR_PERIOD_NS - 1)
        next_ref = current_reference(now_ns=PROTOCOL_ANCHOR_UNIX_NS + OSCILLATOR_PERIOD_NS)
        self.assertEqual(first["heartbeat_id"], same["heartbeat_id"])
        self.assertNotEqual(first["heartbeat_id"], next_ref["heartbeat_id"])
        self.assertEqual(decode_heartbeat_id(next_ref["heartbeat_id"]), PROTOCOL_ANCHOR_EPOCH + 1)

    def test_sample_state_preserves_legacy_machine_frame_and_adds_display_alias(self):
        sampled = sample_state({}, now_ns=PROTOCOL_ANCHOR_UNIX_NS)
        self.assertEqual(sampled["epoch"], 32)
        self.assertEqual(sampled["heartbeat_id"], "HB-0000000W")
        self.assertEqual(sampled["display_reference_frame"], "HB-0000000W")
        self.assertEqual(sampled["reference_frame"], "heartbeat_epoch:32")

    def test_rejects_noncanonical_values(self):
        for bad in (-1, HEARTBEAT_ID_MAX_EPOCH + 1):
            with self.assertRaises(ValueError):
                encode_heartbeat_id(bad)
        with self.assertRaises(TypeError):
            encode_heartbeat_id(True)
        for bad in ("HB-0000000w", "hb-0000000W", "HB-000000W", "HB-0000000!", "0000000W"):
            with self.assertRaises(ValueError):
                decode_heartbeat_id(bad)


if __name__ == "__main__":
    unittest.main()
