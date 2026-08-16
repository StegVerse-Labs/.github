import unittest

from heartbeat_runtime.signal_space import (
    SignalCoordinate,
    coherent_signal_space_candidate,
    harmonic_family,
)


class CoherentSignalSpaceTests(unittest.TestCase):
    def test_hb_is_fundamental_mode_not_whole_mechanism(self):
        candidate = coherent_signal_space_candidate()
        self.assertEqual(candidate["fundamental_mode"], "HB")
        self.assertTrue(candidate["interpretation"]["heartbeat_is_fundamental_mode_not_whole_mechanism"])
        self.assertTrue(candidate["interpretation"]["frequency_parameterizes_state_transformation"])
        self.assertTrue(candidate["interpretation"]["many_state_transition_manifold_target"])

    def test_family_contains_harmonic_subharmonic_and_phase_coordinates(self):
        modes = harmonic_family(harmonics=(1, 2), phase_slots=4, include_subharmonic_half=True)
        ratios = {mode.frequency_ratio for mode in modes}
        phases = {round(mode.phase_radians, 9) for mode in modes if mode.frequency_ratio == 1.0}
        self.assertEqual(ratios, {0.5, 1.0, 2.0})
        self.assertEqual(len(phases), 4)

    def test_coordinates_are_non_authorizing(self):
        mode = SignalCoordinate(mode_id="H2:P0", frequency_ratio=2.0)
        self.assertEqual(mode.as_dict()["authority_effect"], "NONE")
        candidate = coherent_signal_space_candidate()
        self.assertFalse(candidate["authority"]["signal_grants_execution_authority"])
        self.assertFalse(candidate["authority"]["frequency_grants_execution_authority"])
        self.assertFalse(candidate["authority"]["phase_grants_execution_authority"])

    def test_candidate_does_not_claim_completeness_or_operator_family_proof(self):
        candidate = coherent_signal_space_candidate()
        self.assertFalse(candidate["coordinate_system_complete"])
        self.assertTrue(candidate["operator_family_hypothesis"])
        self.assertFalse(candidate["operator_family_proved"])
        self.assertTrue(candidate["interpretation"]["physical_time_is_not_assumed_primitive"])


if __name__ == "__main__":
    unittest.main()
