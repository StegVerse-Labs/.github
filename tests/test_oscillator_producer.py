from __future__ import annotations

import unittest

from heartbeat_runtime.oscillator_producer import OscillatorProducer, due_pulse_batch, next_due_unix_ns


class OscillatorProducerTests(unittest.TestCase):
    def oscillator(self):
        return {
            "period_ns": 10_000_000,
            "anchor_epoch": 31,
            "anchor_unix_ns": 1_000_000_000,
        }

    def test_exact_period_produces_one_reference_without_event(self):
        batch = due_pulse_batch(
            self.oscillator(),
            now_ns=1_010_000_000,
            last_emitted_epoch=31,
        )
        self.assertIsNotNone(batch)
        assert batch is not None
        self.assertEqual(batch.first_epoch, 32)
        self.assertEqual(batch.last_epoch, 32)
        self.assertEqual(batch.count, 1)
        value = batch.as_dict()
        self.assertFalse(value["event_trigger_required"])
        self.assertEqual(value["progression_dependency"], "OSCILLATOR_ONLY")
        self.assertEqual(value["authority_effect"], "NONE")

    def test_next_deadline_is_exact_phase_boundary(self):
        self.assertEqual(
            next_due_unix_ns(self.oscillator(), last_emitted_epoch=31),
            1_010_000_000,
        )
        self.assertEqual(
            next_due_unix_ns(self.oscillator(), last_emitted_epoch=40),
            1_100_000_000,
        )

    def test_subperiod_observation_does_not_create_reference(self):
        self.assertIsNone(
            due_pulse_batch(
                self.oscillator(),
                now_ns=1_009_999_999,
                last_emitted_epoch=31,
            )
        )

    def test_delayed_consumer_compresses_all_due_references(self):
        batch = due_pulse_batch(
            self.oscillator(),
            now_ns=1_095_000_000,
            last_emitted_epoch=31,
        )
        self.assertIsNotNone(batch)
        assert batch is not None
        self.assertEqual(batch.first_epoch, 32)
        self.assertEqual(batch.last_epoch, 40)
        self.assertEqual(batch.count, 9)

    def test_repeated_same_time_cannot_advance_oscillator(self):
        first = due_pulse_batch(
            self.oscillator(),
            now_ns=1_020_000_000,
            last_emitted_epoch=31,
        )
        self.assertIsNotNone(first)
        assert first is not None
        second = due_pulse_batch(
            self.oscillator(),
            now_ns=1_020_000_000,
            last_emitted_epoch=first.last_epoch,
        )
        self.assertIsNone(second)

    def test_producer_requires_only_clock_and_sink_not_task_events(self):
        now = [1_000_000_000]
        emitted = []
        producer = OscillatorProducer(
            self.oscillator(),
            initial_emitted_epoch=31,
            clock_ns=lambda: now[0],
            sink=emitted.append,
        )
        self.assertEqual(producer.next_due_unix_ns, 1_010_000_000)
        self.assertIsNone(producer.run_once())
        now[0] += 10_000_000
        batch = producer.run_once()
        self.assertIsNotNone(batch)
        self.assertEqual(producer.last_emitted_epoch, 32)
        self.assertEqual(producer.next_due_unix_ns, 1_020_000_000)
        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0].last_epoch, 32)

    def test_sink_invocation_cannot_manufacture_future_reference(self):
        now = [1_010_000_000]
        emitted = []
        producer = OscillatorProducer(
            self.oscillator(),
            initial_emitted_epoch=31,
            clock_ns=lambda: now[0],
            sink=emitted.append,
        )
        self.assertIsNotNone(producer.run_once())
        self.assertIsNone(producer.run_once())
        self.assertEqual(len(emitted), 1)


if __name__ == "__main__":
    unittest.main()
