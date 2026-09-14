import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "reusable-transport-component-contract.json"
PROFILE = ROOT / "data" / "goal-task-transport-profiles" / "STEG-BROWSER-RUNTIME-CONSUMPTION-001.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def component_by_id(contract: dict, component_id: str) -> dict:
    return next(row for row in contract["components"] if row["id"] == component_id)


def test_transport_terminal_predicate_is_owned_by_intr_boundary_not_master_records():
    contract = load_json(CONTRACT)
    boundary = contract["transport_boundary_contract"]

    assert boundary["authority_owner"] == "Interlock/InTr"
    assert boundary["terminal_boundary"] == "FINAL_ALLOWED_INTR_STATE_TRANSITION_EXITING_TRANSPORT"
    assert boundary["terminal_predicate"] == "SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED"
    assert boundary["terminal_predicate_value_on_success"] is True
    assert boundary["master_records_required_to_prove_transport_success"] is False
    assert contract["invariants"]["master_records_transport_success_authority"] == "NONE"


def test_round_trip_success_requires_return_record_and_final_transport_exit():
    contract = load_json(CONTRACT)
    boundary = contract["transport_boundary_contract"]

    assert boundary["round_trip_requires_governed_return_packet"] is True
    assert boundary["return_record_must_be_received"] is True
    assert boundary["return_record_must_be_durably_recorded"] is True
    assert boundary["terminal_predicate_set_when"] == [
        "GOVERNED_RETURN_PACKET_RECEIVED",
        "RETURN_RECORD_DURABLY_RECORDED",
        "FINAL_ALLOWED_TRANSPORT_EXIT_TRANSITION_OBSERVED",
    ]
    assert boundary["packet_arrival_time_extended_because_lifecycle_is_round_trip"] is False


def test_master_records_custody_is_post_transport_and_cannot_negate_transport_success():
    contract = load_json(CONTRACT)
    custody = component_by_id(contract, "RTC-EVIDENCE-CUSTODY-004")

    assert custody["canonical_owner"] == "Master Records"
    assert custody["transport_phase"] == "POST_TRANSPORT"
    assert custody["transport_success_authority"] is False
    assert contract["transport_boundary_contract"]["post_transport_failure_may_negate_transport_success"] is False


def test_stegbrowser_profile_splits_transport_from_post_transport_processing():
    profile = load_json(PROFILE)

    assert "RTC-ROUNDTRIP-003" in profile["transport_phase_components"]
    assert "RTC-INTERLOCK-INTR-TRANSPORT-008" in profile["transport_phase_components"]
    assert "RTC-EVIDENCE-CUSTODY-004" not in profile["transport_phase_components"]
    assert profile["post_transport_components"] == ["RTC-EVIDENCE-CUSTODY-004"]

    terminal = profile["transport_terminal_contract"]
    assert terminal["terminal_predicate"] == "SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED"
    assert terminal["return_record_received_required"] is True
    assert terminal["return_record_durably_recorded_required"] is True
    assert terminal["final_allowed_transport_exit_transition_required"] is True
    assert terminal["master_records_reconstruction_required_to_set_terminal_predicate"] is False
    assert terminal["post_transport_failure_negates_terminal_predicate"] is False


def test_callable_and_refreshable_remain_invocation_bound_transition_variables():
    profile = load_json(PROFILE)
    variables = profile["invocation_transition_variables"]

    assert variables["callable"] == "RESOLVED_PER_INVOCATION_BY_INTERLOCK_INTR"
    assert variables["refreshable"] == "RESOLVED_PER_INVOCATION_BY_INTERLOCK_INTR"
    assert variables["source_refresh_task"] == "RT-SOVEREIGN-SOURCE-REFRESH-001"
    assert variables["source_refresh_selection_condition"] == "callable=true AND refreshable=true"


def test_post_transport_failure_ownership_does_not_reopen_transport():
    profile = load_json(PROFILE)
    ownership = profile["failure_ownership"]

    assert ownership["inside_transport_through_final_exit"] == "TRANSPORT_OR_EXACT_IN_LANE_OWNER"
    assert ownership["after_successful_transport_exit"] == "POST_TRANSPORT_OWNING_DOMAIN_NOT_TRANSPORT"
