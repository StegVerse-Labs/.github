from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data/goal-task-transport-profiles/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json"
ACTIVE_TASK = ROOT / "data/canonical-task-records/STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001.json"
HISTORICAL_TASK = ROOT / "data/canonical-task-records/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json"
PARENT = ROOT / "data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_runtime_consumption_reuses_only_needed_transport_components():
    profile = load(PROFILE)
    assert profile["schema"] == "stegverse.goal-task-transport-profile/v1"
    assert profile["task_id"] == "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
    assert profile["cosv_task_vector"] == "40000100100000"
    assert profile["selected_components"] == [
        "RTC-MANIFEST-001",
        "RTC-GOVERNED-PROCESSING-002",
        "RTC-ROUNDTRIP-003",
        "RTC-INTERLOCK-INTR-TRANSPORT-008",
        "RTC-EVIDENCE-CUSTODY-004",
    ]
    omitted = {row["component_id"] for row in profile["omitted_components"]}
    assert omitted == {"RTC-PUBLISHER-005", "RTC-SDK-RETURN-006", "RTC-STEGVERSE-EGRESS-007", "RTC-FARSIDE-FINAL-009"}
    assert profile["repeatability"]["RTC-ROUNDTRIP-003"] == 1
    assert profile["round_trip_lifecycle_semantics"]["lifecycle_count"] == 1
    assert profile["round_trip_lifecycle_semantics"]["internal_transition_group_count"] == 2
    assert profile["round_trip_lifecycle_semantics"]["internal_transition_groups_are_separate_round_trip_goals"] is False
    assert profile["runtime_evidence_effect"] == "NONE_SOURCE_COMPOSITION_ONLY"


def test_active_remediation_uses_ephemeral_stegos_without_reopening_retired_goal():
    profile = load(PROFILE)
    substrate = profile["execution_substrate"]
    assert substrate["selected"] == "ADMITTED-EPHEMERAL-STEGOS-NODE"
    assert substrate["interchangeable_node_semantics"] is True
    assert substrate["remote_or_external_device_required"] is False
    assert substrate["second_user_operated_device_allowed"] is False

    active = load(ACTIVE_TASK)
    historical = load(HISTORICAL_TASK)
    assert active["execution_substrate_resolution"]["selected_substrate_id"] == "ADMITTED-EPHEMERAL-STEGOS-NODE"
    assert active["coordination_state"] == "ACTIVE"
    assert active["checkout_state"] == "CHECKED_OUT"
    assert active["completion"]["successful_data_transport_round_trip_identified"] is False
    assert historical["coordination_state"] == "RETIRED"
    assert historical["checkout_state"] == "DECOMPOSED_AT_PROMPT_LIMIT"


def test_original_parent_is_superseded_and_not_reopened_by_successor_profile():
    parent = load(PARENT)
    assert parent["coordination_state"] == "SUPERSEDED"
    assert parent["checkout_state"] == "SUPERSEDED"
    assert parent["continuation_task_id"] == "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
