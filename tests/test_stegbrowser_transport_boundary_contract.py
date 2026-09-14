import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "reusable-transport-component-contract.json"
PROFILE = ROOT / "data" / "goal-task-transport-profiles" / "STEG-BROWSER-RUNTIME-CONSUMPTION-001.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def component_by_id(contract: dict, component_id: str) -> dict:
    return next(row for row in contract["components"] if row["id"] == component_id)


class StegBrowserTransportBoundaryContractTests(unittest.TestCase):
    def test_transport_terminal_predicate_is_owned_by_intr_boundary_not_master_records(self):
        contract = load_json(CONTRACT)
        boundary = contract["transport_boundary_contract"]

        self.assertEqual(boundary["authority_owner"], "Interlock/InTr")
        self.assertEqual(boundary["terminal_boundary"], "FINAL_ALLOWED_INTR_STATE_TRANSITION_EXITING_TRANSPORT")
        self.assertEqual(boundary["terminal_predicate"], "SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED")
        self.assertIs(boundary["terminal_predicate_value_on_success"], True)
        self.assertIs(boundary["master_records_required_to_prove_transport_success"], False)
        self.assertEqual(contract["invariants"]["master_records_transport_success_authority"], "NONE")

    def test_round_trip_success_requires_return_record_and_final_transport_exit(self):
        contract = load_json(CONTRACT)
        boundary = contract["transport_boundary_contract"]

        self.assertIs(boundary["round_trip_requires_governed_return_packet"], True)
        self.assertIs(boundary["return_record_must_be_received"], True)
        self.assertIs(boundary["return_record_must_be_durably_recorded"], True)
        self.assertEqual(
            boundary["terminal_predicate_set_when"],
            [
                "GOVERNED_RETURN_PACKET_RECEIVED",
                "RETURN_RECORD_DURABLY_RECORDED",
                "FINAL_ALLOWED_TRANSPORT_EXIT_TRANSITION_OBSERVED",
            ],
        )
        self.assertIs(boundary["packet_arrival_time_extended_because_lifecycle_is_round_trip"], False)

    def test_internal_transition_groups_do_not_multiply_round_trip_lifecycle(self):
        contract = load_json(CONTRACT)
        boundary = contract["transport_boundary_contract"]
        round_trip = component_by_id(contract, "RTC-ROUNDTRIP-003")
        profile = load_json(PROFILE)
        requirements = profile["transport_requirements"]
        semantics = profile["round_trip_lifecycle_semantics"]

        self.assertIs(boundary["one_round_trip_lifecycle_may_contain_multiple_internal_transition_groups"], True)
        self.assertIs(boundary["internal_transition_groups_do_not_imply_additional_round_trip_lifecycles"], True)
        self.assertIs(round_trip["internal_transition_groups_increment_repeat_count"], False)
        self.assertEqual(requirements["governed_round_trip_lifecycle_count"], 1)
        self.assertEqual(
            requirements["required_round_trips"],
            ["stegbrowser_runtime_consumption_governed_round_trip"],
        )
        self.assertEqual(
            requirements["round_trip_internal_transition_groups"],
            [
                "canonical_work_ingress_and_resident_consumption",
                "tvc_source_promotion_and_runtime_observation",
            ],
        )
        self.assertEqual(profile["repeatability"]["RTC-ROUNDTRIP-003"], 1)
        self.assertEqual(semantics["lifecycle_count"], 1)
        self.assertEqual(semantics["internal_transition_group_count"], 2)
        self.assertIs(semantics["internal_transition_groups_are_separate_round_trip_goals"], False)
        self.assertIs(semantics["internal_transition_groups_increment_round_trip_repeat_count"], False)

    def test_master_records_custody_is_post_transport_and_cannot_negate_transport_success(self):
        contract = load_json(CONTRACT)
        custody = component_by_id(contract, "RTC-EVIDENCE-CUSTODY-004")

        self.assertEqual(custody["canonical_owner"], "Master Records")
        self.assertEqual(custody["transport_phase"], "POST_TRANSPORT")
        self.assertIs(custody["transport_success_authority"], False)
        self.assertIs(contract["transport_boundary_contract"]["post_transport_failure_may_negate_transport_success"], False)

    def test_stegbrowser_profile_splits_transport_from_post_transport_processing(self):
        profile = load_json(PROFILE)

        self.assertIn("RTC-ROUNDTRIP-003", profile["transport_phase_components"])
        self.assertIn("RTC-INTERLOCK-INTR-TRANSPORT-008", profile["transport_phase_components"])
        self.assertNotIn("RTC-EVIDENCE-CUSTODY-004", profile["transport_phase_components"])
        self.assertEqual(profile["post_transport_components"], ["RTC-EVIDENCE-CUSTODY-004"])

        terminal = profile["transport_terminal_contract"]
        self.assertEqual(terminal["terminal_predicate"], "SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED")
        self.assertIs(terminal["return_record_received_required"], True)
        self.assertIs(terminal["return_record_durably_recorded_required"], True)
        self.assertIs(terminal["final_allowed_transport_exit_transition_required"], True)
        self.assertIs(terminal["master_records_reconstruction_required_to_set_terminal_predicate"], False)
        self.assertIs(terminal["post_transport_failure_negates_terminal_predicate"], False)

    def test_callable_and_refreshable_remain_invocation_bound_transition_variables(self):
        profile = load_json(PROFILE)
        variables = profile["invocation_transition_variables"]

        self.assertEqual(variables["callable"], "RESOLVED_PER_INVOCATION_BY_INTERLOCK_INTR")
        self.assertEqual(variables["refreshable"], "RESOLVED_PER_INVOCATION_BY_INTERLOCK_INTR")
        self.assertEqual(variables["source_refresh_task"], "RT-SOVEREIGN-SOURCE-REFRESH-001")
        self.assertEqual(variables["source_refresh_selection_condition"], "callable=true AND refreshable=true")

    def test_post_transport_failure_ownership_does_not_reopen_transport(self):
        profile = load_json(PROFILE)
        ownership = profile["failure_ownership"]

        self.assertEqual(ownership["inside_transport_through_final_exit"], "TRANSPORT_OR_EXACT_IN_LANE_OWNER")
        self.assertEqual(ownership["after_successful_transport_exit"], "POST_TRANSPORT_OWNING_DOMAIN_NOT_TRANSPORT")


if __name__ == "__main__":
    unittest.main()
