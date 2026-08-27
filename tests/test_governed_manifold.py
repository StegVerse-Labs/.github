import unittest

from heartbeat_runtime.governed_manifold import (
    GOVERNED_MANIFOLD_SCHEMA,
    GovernedProjectionDimension,
    governed_manifold_observation,
)


class GovernedManifoldObservationTests(unittest.TestCase):
    def test_projection_is_non_authorizing_and_not_wall_clock_governed(self):
        observation = governed_manifold_observation(
            carrier_epoch=42,
            carrier_generation=7,
            dimensions=[
                GovernedProjectionDimension(
                    name="worker_control_plane",
                    value={"state": "IDLE"},
                    source_ref="control/worker-control-plane-coordination.json",
                ),
                {
                    "name": "coherent_signal_space",
                    "value": {"many_state_transition_manifold_target": True},
                    "source_ref": "heartbeat_runtime/signal_space.py",
                },
            ],
            transition_refs=["events/heartbeat-runtime.jsonl#heartbeat_epoch:42"],
            authority_boundary_refs=["control/worker-registry.json"],
        )
        self.assertEqual(observation["schema"], GOVERNED_MANIFOLD_SCHEMA)
        self.assertEqual(observation["projection_role"], "GOVERNED_MANIFOLD_OBSERVATION")
        self.assertEqual(observation["state_model"], "MULTI_VARIABLE_CONCURRENT_TRANSITION_SPACE")
        self.assertEqual(observation["authority_effect"], "NONE_OBSERVATION_ONLY")
        self.assertFalse(observation["invariants"]["heartbeat_is_governance_authority"])
        self.assertFalse(observation["invariants"]["wall_clock_is_governance_authority"])
        self.assertFalse(observation["invariants"]["human_review_is_required_per_machine_transition"])
        self.assertTrue(observation["invariants"]["projection_may_be_reviewed_without_advancing_governed_state"])
        self.assertTrue(observation["invariants"]["protected_boundary_crossing_requires_external_authority"])

    def test_invalid_projection_dimension_fails_closed(self):
        with self.assertRaises(ValueError):
            governed_manifold_observation(
                carrier_epoch=1,
                carrier_generation=1,
                dimensions=[{"name": "", "value": 1, "source_ref": "x"}],
            )


if __name__ == "__main__":
    unittest.main()
