from __future__ import annotations

import unittest

from heartbeat_runtime.independent_oscillator import PROTOCOL_ANCHOR_EPOCH, REFERENCE_FREQUENCY_HZ
from heartbeat_runtime.machine_continuation import (
    DEFAULT_CONTINUATION_QUANTA,
    build_continuation_trigger,
    derive_continuation_window,
)


class HBMachineContinuationTests(unittest.TestCase):
    def test_default_cadence_is_one_hour_of_100hz_quanta(self) -> None:
        self.assertEqual(REFERENCE_FREQUENCY_HZ, 100)
        self.assertEqual(DEFAULT_CONTINUATION_QUANTA, 360000)

    def test_window_is_anchored_to_canonical_protocol_anchor(self) -> None:
        first = derive_continuation_window(PROTOCOL_ANCHOR_EPOCH)
        self.assertEqual(first.window_id, 0)
        self.assertEqual(first.start_epoch, PROTOCOL_ANCHOR_EPOCH)
        self.assertEqual(first.end_epoch_exclusive, PROTOCOL_ANCHOR_EPOCH + DEFAULT_CONTINUATION_QUANTA)

        second = derive_continuation_window(PROTOCOL_ANCHOR_EPOCH + DEFAULT_CONTINUATION_QUANTA)
        self.assertEqual(second.window_id, 1)
        self.assertEqual(second.start_epoch, PROTOCOL_ANCHOR_EPOCH + DEFAULT_CONTINUATION_QUANTA)

    def test_new_window_is_due_once(self) -> None:
        epoch = PROTOCOL_ANCHOR_EPOCH + DEFAULT_CONTINUATION_QUANTA * 4 + 17
        trigger = build_continuation_trigger(epoch, last_consumed_window_id=3)
        self.assertTrue(trigger["continuation_due"])
        self.assertEqual(trigger["window"]["window_id"], 4)
        self.assertFalse(trigger["heartbeat_grants_execution_authority"])
        self.assertFalse(trigger["trigger_grants_execution_authority"])
        self.assertEqual(trigger["authority_effect"], "NONE_TRIGGER_ONLY")

        repeated = build_continuation_trigger(epoch, last_consumed_window_id=4)
        self.assertFalse(repeated["continuation_due"])

    def test_missed_windows_collapse_to_current_window(self) -> None:
        epoch = PROTOCOL_ANCHOR_EPOCH + DEFAULT_CONTINUATION_QUANTA * 9 + 1
        trigger = build_continuation_trigger(epoch, last_consumed_window_id=2)
        self.assertTrue(trigger["continuation_due"])
        self.assertEqual(trigger["window"]["window_id"], 9)
        self.assertFalse(trigger["missed_windows_replayed"])

    def test_invalid_reference_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            derive_continuation_window(PROTOCOL_ANCHOR_EPOCH - 1)


if __name__ == "__main__":
    unittest.main()
