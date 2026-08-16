from __future__ import annotations

import unittest

from heartbeat_runtime.external_timing_match import (
    ExternalTimingCapability,
    ExternalTimingMatchError,
    assess_timing_observation,
    assess_workload_health,
    capability_profile,
    select_fixed_logical_period,
)


class ExternalTimingMatchTests(unittest.TestCase):
    def setUp(self):
        self.cap = ExternalTimingCapability(
            source_id="device-1",
            source_class="hardware_clock",
            monotonic_resolution_ns=1000,
            timer_floor_ms=1.0,
            observed_jitter_ms=0.05,
            sustainable_period_min_ms=2.0,
            sustainable_period_max_ms=10.0,
            phase_capacity=4,
            waveform_family="pulse",
            waveform_signature="pulse:v1:device-1",
            workload_capacity_per_pulse=100.0,
            deployment_class="NS",
        )
        self.profile = capability_profile(self.cap)

    def test_profile_is_zero_authority_and_identity_is_explicit(self):
        self.assertEqual("TV/TVC", self.profile["authority"]["credential_authority"])
        self.assertEqual("NONE", self.profile["authority"]["github_token_runtime_authority"])
        self.assertFalse(self.profile["authority"]["external_timing_source_grants_authority"])
        self.assertFalse(self.profile["source"]["deployment_class_inferred_from_frequency"])
        self.assertEqual("NS", self.profile["source"]["deployment_class"])

    def test_fixed_cadence_does_not_change_with_workload(self):
        lock = select_fixed_logical_period(self.profile, requested_period_ms=5.0)
        self.assertEqual(5.0, lock["fixed_logical_period_ms"])
        self.assertFalse(lock["period_changes_with_workload"])
        low = assess_workload_health(self.profile, work_units_per_pulse=5)
        high = assess_workload_health(self.profile, work_units_per_pulse=110)
        self.assertEqual("UNDERLOAD", low["state"])
        self.assertEqual("OVERLOADED", high["state"])
        self.assertFalse(low["heartbeat_period_changes_with_load"])
        self.assertFalse(high["heartbeat_period_changes_with_load"])
        self.assertEqual(5.0, lock["fixed_logical_period_ms"])

    def test_workload_health_bands_are_separate_from_timing_lock(self):
        states = [
            assess_workload_health(self.profile, work_units_per_pulse=5)["state"],
            assess_workload_health(self.profile, work_units_per_pulse=50)["state"],
            assess_workload_health(self.profile, work_units_per_pulse=80)["state"],
            assess_workload_health(self.profile, work_units_per_pulse=97)["state"],
            assess_workload_health(self.profile, work_units_per_pulse=120)["state"],
        ]
        self.assertEqual(["UNDERLOAD", "NORMAL", "ELEVATED", "SATURATED", "OVERLOADED"], states)

    def test_phase_waveform_matching_supports_lock_and_loss_of_lock(self):
        lock = select_fixed_logical_period(self.profile, requested_period_ms=5.0)
        good = assess_timing_observation(
            lock,
            expected_reference_ms=100.0,
            observed_reference_ms=100.05,
            expected_phase_deg=90.0,
            observed_phase_deg=90.5,
            observed_period_ms=5.02,
            observed_jitter_ms=0.03,
            max_clock_offset_ms=0.2,
            max_phase_error_deg=2.0,
            max_period_drift_ms=0.1,
            max_jitter_ms=0.1,
        )
        bad = assess_timing_observation(
            lock,
            expected_reference_ms=100.0,
            observed_reference_ms=101.0,
            expected_phase_deg=90.0,
            observed_phase_deg=110.0,
            observed_period_ms=5.5,
            observed_jitter_ms=0.5,
            max_clock_offset_ms=0.2,
            max_phase_error_deg=2.0,
            max_period_drift_ms=0.1,
            max_jitter_ms=0.1,
        )
        self.assertEqual("LOCKED", good["state"])
        self.assertEqual("LOSS_OF_LOCK", bad["state"])
        self.assertIn("CLOCK_OFFSET_EXCEEDED", bad["reasons"])
        self.assertIn("PHASE_ERROR_EXCEEDED", bad["reasons"])
        self.assertIn("PERIOD_DRIFT_EXCEEDED", bad["reasons"])
        self.assertIn("JITTER_EXCEEDED", bad["reasons"])
        self.assertFalse(good["workload_activity_considered_timing_deviation"])

    def test_arbitrary_exterior_source_classes_use_same_contract(self):
        for source_class in (
            "os_monotonic_clock",
            "network_time_source",
            "bus",
            "radio",
            "sensor",
            "industrial_controller",
            "bci_device",
        ):
            profile = capability_profile(ExternalTimingCapability(
                source_id=f"source-{source_class}",
                source_class=source_class,
                monotonic_resolution_ns=1000,
                timer_floor_ms=1.0,
                observed_jitter_ms=0.1,
                sustainable_period_min_ms=2.0,
                sustainable_period_max_ms=8.0,
                phase_capacity=2,
                waveform_family="profiled",
                waveform_signature=f"sig:{source_class}",
                workload_capacity_per_pulse=10.0,
            ))
            lock = select_fixed_logical_period(profile)
            self.assertEqual("LOCK_PROFILE_READY", lock["state"])
            self.assertEqual(source_class, profile["source"]["source_class"])

    def test_requested_period_outside_capability_fails_closed(self):
        with self.assertRaises(ExternalTimingMatchError):
            select_fixed_logical_period(self.profile, requested_period_ms=0.5)

    def test_invalid_deployment_class_is_rejected(self):
        with self.assertRaises(ExternalTimingMatchError):
            capability_profile(ExternalTimingCapability(
                source_id="bad",
                source_class="sensor",
                monotonic_resolution_ns=1000,
                timer_floor_ms=1,
                observed_jitter_ms=0,
                sustainable_period_min_ms=2,
                sustainable_period_max_ms=5,
                phase_capacity=1,
                waveform_family="pulse",
                waveform_signature="bad",
                workload_capacity_per_pulse=1,
                deployment_class="LARGE",
            ))


if __name__ == "__main__":
    unittest.main()
