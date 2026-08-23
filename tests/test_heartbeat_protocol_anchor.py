import unittest

from heartbeat_runtime.independent_oscillator import (
    OSCILLATOR_PERIOD_NS,
    PROTOCOL_ANCHOR_EPOCH,
    PROTOCOL_ANCHOR_UNIX_NS,
    current_reference,
    normalize_oscillator,
    sample_state,
)


class HeartbeatProtocolAnchorTests(unittest.TestCase):
    def test_anchor_reference_is_hb32(self):
        ref = current_reference(now_ns=PROTOCOL_ANCHOR_UNIX_NS)
        self.assertEqual(ref["epoch"], PROTOCOL_ANCHOR_EPOCH)
        self.assertEqual(ref["phase_offset_ns"], 0)

    def test_less_than_ten_ms_does_not_increment(self):
        ref = current_reference(now_ns=PROTOCOL_ANCHOR_UNIX_NS + OSCILLATOR_PERIOD_NS - 1)
        self.assertEqual(ref["epoch"], PROTOCOL_ANCHOR_EPOCH)

    def test_exactly_ten_ms_increments_once(self):
        ref = current_reference(now_ns=PROTOCOL_ANCHOR_UNIX_NS + OSCILLATOR_PERIOD_NS)
        self.assertEqual(ref["epoch"], PROTOCOL_ANCHOR_EPOCH + 1)

    def test_delayed_observer_skips_unobserved_references(self):
        ref = current_reference(now_ns=PROTOCOL_ANCHOR_UNIX_NS + 37 * OSCILLATOR_PERIOD_NS)
        self.assertEqual(ref["epoch"], PROTOCOL_ANCHOR_EPOCH + 37)
        self.assertEqual(ref["elapsed_quanta"], 37)

    def test_persisted_or_worker_state_cannot_change_post_cutover_anchor(self):
        now_ns = PROTOCOL_ANCHOR_UNIX_NS + 5 * OSCILLATOR_PERIOD_NS
        hostile_state = {
            "epoch": 999999,
            "worker_state": "BLOCKED",
            "oscillator": {
                "anchor_epoch": 999999,
                "anchor_unix_ns": now_ns,
                "period_ns": OSCILLATOR_PERIOD_NS,
            },
        }
        oscillator = normalize_oscillator(hostile_state, now_ns=now_ns)
        self.assertEqual(oscillator["anchor_epoch"], PROTOCOL_ANCHOR_EPOCH)
        self.assertEqual(oscillator["anchor_unix_ns"], PROTOCOL_ANCHOR_UNIX_NS)
        self.assertFalse(oscillator["continuous_process_required"])
        self.assertFalse(oscillator["resident_sampler_required_for_progression"])

    def test_sampling_is_observation_only_not_progression_authority(self):
        now_ns = PROTOCOL_ANCHOR_UNIX_NS + 9 * OSCILLATOR_PERIOD_NS
        sampled = sample_state({}, now_ns=now_ns)
        self.assertEqual(sampled["epoch"], PROTOCOL_ANCHOR_EPOCH + 9)
        self.assertEqual(sampled["authority_effect"], "NONE")
        self.assertFalse(sampled["continuous_process_required"])
        self.assertFalse(sampled["resident_sampler_required_for_progression"])
        self.assertTrue(sampled["oscillator"]["snapshot_is_observation_only"])
        self.assertEqual(sampled["oscillator"]["progression_dependency"], "OSCILLATOR_ONLY")


if __name__ == "__main__":
    unittest.main()
