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
    def test_round_trip_component_is_repeatable(self):
        contract = load_json(CONTRACT)
        round_trip = component_by_id(contract, "RTC-ROUNDTRIP-003")
        self.assertIs(round_trip["repeatable"], True)
        self.assertIn("governed_round_trip_lifecycle_count", round_trip["repeat_count_source"])

    def test_stegbrowser_requires_two_distinct_governed_round_trips(self):
        profile = load_json(PROFILE)
        req = profile["transport_requirements"]
        semantics = profile["round_trip_lifecycle_semantics"]
        self.assertEqual(req["governed_round_trip_lifecycle_count"], 2)
        self.assertEqual(
            req["required_round_trips"],
            [
                "records_packet_return_for_recording_and_verification",
                "mirror_boundary_processed_return_to_ecosystem",
            ],
        )
        self.assertEqual(profile["repeatability"]["RTC-ROUNDTRIP-003"], 2)
        self.assertEqual(semantics["lifecycle_count"], 2)

    def test_round_trip_1_returns_records_packet_for_recording_and_verification(self):
        profile = load_json(PROFILE)
        rt1 = profile["round_trip_boundaries"]["round_trip_1"]
        self.assertEqual(rt1["exit_transition"], "FIRST_FINAL_ALLOWED_INTR_EXIT_TO_RECORDING")
        self.assertEqual(rt1["recording_target"], "MASTER_RECORDS_RECORDING_SURFACE")
        self.assertIn("RETURN_RECORD_DURABLY_RECORDED", rt1["success_requires"])
        terminal = profile["transport_terminal_contract"]
        self.assertEqual(
            terminal["round_trip_1_terminal_predicate"],
            "SUCCESSFUL_RECORDING_VERIFICATION_ROUND_TRIP_IDENTIFIED",
        )
        self.assertIs(terminal["durable_recording_is_round_trip_1_verification_evidence"], True)

    def test_master_records_processing_occurs_between_round_trips(self):
        profile = load_json(PROFILE)
        between = profile["round_trip_boundaries"]["between_round_trips"]
        self.assertIn("RTC-EVIDENCE-CUSTODY-004", profile["between_round_trip_processing_components"])
        self.assertIs(between["mirror_boundary_initiates_next_intr"], True)
        self.assertEqual(between["transport_authority"], "NONE")

    def test_round_trip_2_reenters_intr_calls_endpoint_and_reenters_ecosystem(self):
        profile = load_json(PROFILE)
        rt2 = profile["round_trip_boundaries"]["round_trip_2"]
        self.assertEqual(rt2["entry_transition"], "MIRROR_BOUNDARY_INTR_REENTRY")
        self.assertEqual(rt2["endpoint_transition"], "ENDPOINT_INTR_CALLED_AND_ALLOWED")
        self.assertEqual(rt2["terminal_transition"], "ECOSYSTEM_REENTRY_FINAL_ALLOWED_TRANSITION")
        terminal = profile["transport_terminal_contract"]
        self.assertIs(terminal["round_trip_2_reenters_interlock_intr"], True)
        self.assertIs(terminal["round_trip_2_calls_endpoint_interlock_intr"], True)
        self.assertIs(terminal["round_trip_2_enters_ecosystem"], True)
        self.assertEqual(
            terminal["round_trip_2_terminal_predicate"],
            "SUCCESSFUL_ECOSYSTEM_RETURN_ROUND_TRIP_IDENTIFIED",
        )

    def test_internal_transition_groups_do_not_create_the_two_round_trips(self):
        profile = load_json(PROFILE)
        semantics = profile["round_trip_lifecycle_semantics"]
        self.assertEqual(semantics["internal_transition_group_count"], 2)
        self.assertIs(semantics["internal_transition_groups_are_separate_round_trip_goals"], False)
        self.assertIs(semantics["internal_transition_groups_increment_round_trip_repeat_count"], False)

    def test_callable_and_refreshable_remain_invocation_bound(self):
        variables = load_json(PROFILE)["invocation_transition_variables"]
        self.assertEqual(variables["callable"], "RESOLVED_PER_INVOCATION_BY_INTERLOCK_INTR")
        self.assertEqual(variables["refreshable"], "RESOLVED_PER_INVOCATION_BY_INTERLOCK_INTR")
        self.assertEqual(variables["source_refresh_selection_condition"], "callable=true AND refreshable=true")


if __name__ == "__main__":
    unittest.main()
