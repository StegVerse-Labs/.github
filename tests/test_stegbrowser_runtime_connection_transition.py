from __future__ import annotations

import unittest

from scripts import resolve_stegbrowser_runtime_connection_transition as module


class StegBrowserRuntimeConnectionTransitionTests(unittest.TestCase):
    def observation(self, *, callable_value: bool, refreshable: bool, protocol_resolved: bool) -> dict:
        return {
            "schema": "stegverse.intr-runtime-connection-transition-observation/v1",
            "task_id": module.TASK_ID,
            "parent_task_id": module.PARENT_TASK_ID,
            "cosv": module.COSV,
            "manifest_ref": module.MANIFEST_REF,
            "authority_owner": "Interlock/InTr",
            "authority_effect": "OBSERVATION_ONLY",
            "callable": callable_value,
            "refreshable": refreshable,
            "applicable_protocol_resolved": protocol_resolved,
        }

    def test_callable_refreshable_selects_source_refresh(self) -> None:
        result = module.resolve(self.observation(callable_value=True, refreshable=True, protocol_resolved=True))
        self.assertEqual(result["selected_reusable_tasks"], [module.SOURCE_REFRESH_RT])
        self.assertTrue(result["workercoordinator_claim_required_before_execution"])
        self.assertTrue(result["intr_admission_required_before_transport"])

    def test_callable_nonrefreshable_does_not_invent_refresh(self) -> None:
        result = module.resolve(self.observation(callable_value=True, refreshable=False, protocol_resolved=True))
        self.assertEqual(result["selected_reusable_tasks"], [])
        self.assertEqual(result["disposition"], "CALLABLE_NO_PRE_INGRESS_REUSABLE_TASK_REQUIRED")

    def test_missing_protocol_selects_existing_protocol_establishment_rt(self) -> None:
        result = module.resolve(self.observation(callable_value=True, refreshable=False, protocol_resolved=False))
        self.assertEqual(result["selected_reusable_tasks"], [module.INTR_PROTOCOL_RT])

    def test_refresh_and_protocol_tasks_compose_when_both_predicates_match(self) -> None:
        result = module.resolve(self.observation(callable_value=True, refreshable=True, protocol_resolved=False))
        self.assertEqual(result["selected_reusable_tasks"], [module.SOURCE_REFRESH_RT, module.INTR_PROTOCOL_RT])

    def test_not_callable_does_not_materialize_execution_or_select_tasks(self) -> None:
        result = module.resolve(self.observation(callable_value=False, refreshable=True, protocol_resolved=False))
        self.assertEqual(result["selected_reusable_tasks"], [])
        self.assertFalse(result["workercoordinator_claim_required_before_execution"])
        self.assertFalse(result["intr_admission_required_before_transport"])
        self.assertEqual(result["disposition"], "NOT_CALLABLE_NO_EXECUTION_MATERIALIZATION")

    def test_resolution_never_grants_transport_or_round_trip_authority(self) -> None:
        result = module.resolve(self.observation(callable_value=True, refreshable=True, protocol_resolved=False))
        self.assertEqual(result["authority_effect"], "NONE_SELECTION_ONLY")
        self.assertFalse(result["round_trip_1_payload_processing_allowed_by_this_resolution"])
        self.assertFalse(result["second_user_operated_device_required"])

    def test_foreign_or_source_asserted_authority_fails_closed(self) -> None:
        observation = self.observation(callable_value=True, refreshable=True, protocol_resolved=True)
        observation["authority_effect"] = "GRANTS_AUTHORITY"
        with self.assertRaises(module.TransitionResolutionError):
            module.resolve(observation)


if __name__ == "__main__":
    unittest.main()
