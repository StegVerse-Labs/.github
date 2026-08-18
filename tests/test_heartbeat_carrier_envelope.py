from __future__ import annotations

import unittest

from heartbeat_runtime.carrier_envelope import (
    CarrierEnvelopeError,
    SignalConstraint,
    assess_carrier_observation,
    derive_carrier_envelope,
)


class HeartbeatCarrierEnvelopeTests(unittest.TestCase):
    def sample_constraints(self):
        return [
            SignalConstraint(
                signal_id="worker-closure",
                min_frequency_hz=50.0,
                max_frequency_hz=400.0,
                required_event_rate_hz=40.0,
                deadline_ms=20.0,
                simultaneous_units=3.0,
                requested_phase_slots=4,
                max_jitter_ms=1.5,
                max_phase_error_deg=12.0,
                max_frequency_drift_hz=8.0,
            ),
            SignalConstraint(
                signal_id="mcp-return",
                min_frequency_hz=80.0,
                max_frequency_hz=300.0,
                required_event_rate_hz=24.0,
                deadline_ms=12.5,
                simultaneous_units=2.0,
                requested_phase_slots=2,
                max_jitter_ms=1.0,
                max_phase_error_deg=10.0,
                max_frequency_drift_hz=5.0,
            ),
        ]

    def test_frequency_is_fixed_by_independent_10ms_oscillator(self):
        envelope = derive_carrier_envelope(
            self.sample_constraints(),
            sustainable_max_hz=500.0,
            events_per_reference_capacity=2.0,
            growth_reserve_ratio=0.25,
        )
        frequency = envelope["frequency"]
        self.assertEqual("INDEPENDENT_OSCILLATOR_10MS_PHASE_TRAVEL", frequency["rule"])
        self.assertEqual(100.0, frequency["nominal_hz"])
        self.assertEqual(10.0, frequency["nominal_period_ms"])
        self.assertEqual("OSCILLATOR_ONLY", frequency["progression_dependency"])
        self.assertFalse(frequency["downstream_constraints_may_change_frequency"])
        self.assertEqual(4, envelope["phase_plan"]["phase_slots"])
        self.assertFalse(envelope["phase_plan"]["phase_plan_changes_reference_interval"])

    def test_strictest_tolerance_wins(self):
        envelope = derive_carrier_envelope(
            self.sample_constraints(),
            sustainable_max_hz=500.0,
            events_per_reference_capacity=2.0,
        )
        self.assertEqual(1.0, envelope["tolerances"]["max_jitter_ms"])
        self.assertEqual(10.0, envelope["tolerances"]["max_phase_error_deg"])
        self.assertEqual(5.0, envelope["tolerances"]["max_frequency_drift_hz"])

    def test_rejects_consumer_that_requires_different_heartbeat_frequency(self):
        with self.assertRaises(CarrierEnvelopeError):
            derive_carrier_envelope(
                [SignalConstraint(signal_id="impossible", min_frequency_hz=250.0)],
                sustainable_max_hz=500.0,
                events_per_reference_capacity=1.0,
            )
        with self.assertRaises(CarrierEnvelopeError):
            derive_carrier_envelope(
                [SignalConstraint(signal_id="too-slow", max_frequency_hz=50.0)],
                sustainable_max_hz=500.0,
                events_per_reference_capacity=1.0,
            )

    def test_detects_frequency_and_phase_deviation_without_authority(self):
        envelope = derive_carrier_envelope(
            self.sample_constraints(),
            sustainable_max_hz=500.0,
            events_per_reference_capacity=2.0,
        )
        observation = assess_carrier_observation(
            envelope,
            observed_frequency_hz=112.0,
            observed_phase_deg=30.0,
            expected_phase_deg=0.0,
            observed_jitter_ms=2.0,
        )
        self.assertEqual("DEVIATION", observation["state"])
        self.assertIn("FREQUENCY_DRIFT_EXCEEDED", observation["reasons"])
        self.assertIn("PHASE_ERROR_EXCEEDED", observation["reasons"])
        self.assertIn("JITTER_EXCEEDED", observation["reasons"])
        self.assertEqual("NONE", observation["authority_effect"])
        self.assertEqual("TV/TVC", observation["credential_authority"])
        self.assertFalse(observation["heartbeat_grants_execution_authority"])

    def test_within_envelope_does_not_change_heartbeat(self):
        envelope = derive_carrier_envelope(
            self.sample_constraints(),
            sustainable_max_hz=500.0,
            events_per_reference_capacity=2.0,
        )
        observation = assess_carrier_observation(
            envelope,
            observed_frequency_hz=101.0,
            observed_phase_deg=5.0,
            expected_phase_deg=0.0,
            observed_jitter_ms=0.5,
        )
        self.assertEqual("WITHIN_ENVELOPE", observation["state"])
        self.assertEqual([], observation["reasons"])
        self.assertFalse(envelope["recalculation"]["recalculation_changes_heartbeat_frequency"])

    def test_authority_contract_is_zero_authority(self):
        envelope = derive_carrier_envelope(
            self.sample_constraints(),
            sustainable_max_hz=500.0,
            events_per_reference_capacity=2.0,
        )
        authority = envelope["authority"]
        self.assertFalse(authority["heartbeat_grants_execution_authority"])
        self.assertFalse(authority["alternate_phase_grants_execution_authority"])
        self.assertFalse(authority["signal_grants_execution_authority"])
        self.assertFalse(authority["github_token_runtime_authority"])
        self.assertFalse(authority["master_records_action_authority"])
        self.assertEqual("TV/TVC", authority["credential_authority"])


if __name__ == "__main__":
    unittest.main()
