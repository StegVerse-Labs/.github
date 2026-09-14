from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data/goal-task-transport-profiles/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json"
TASK = ROOT / "data/canonical-task-records/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json"
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
        "RTC-EVIDENCE-CUSTODY-004",
        "RTC-INTERLOCK-INTR-TRANSPORT-008",
    ]
    omitted = {row["component_id"] for row in profile["omitted_components"]}
    assert omitted == {
        "RTC-PUBLISHER-005",
        "RTC-SDK-RETURN-006",
        "RTC-STEGVERSE-EGRESS-007",
        "RTC-FARSIDE-FINAL-009",
    }
    assert profile["repeatability"]["RTC-ROUNDTRIP-003"] == 2
    assert profile["runtime_evidence_effect"] == "NONE_SOURCE_COMPOSITION_ONLY"


def test_runtime_consumption_uses_ephemeral_stegos_without_remote_device_dependency():
    profile = load(PROFILE)
    substrate = profile["execution_substrate"]
    assert substrate["selected"] == "ADMITTED-EPHEMERAL-STEGOS-NODE"
    assert substrate["interchangeable_node_semantics"] is True
    assert substrate["remote_or_external_device_required"] is False
    assert substrate["second_user_operated_device_allowed"] is False
    assert substrate["materialize_only_after_applicable_admission"] is True

    task = load(TASK)
    assert task["execution_substrate_resolution"]["selected_substrate_id"] == "ADMITTED-EPHEMERAL-STEGOS-NODE"
    assert task["coordination_state"] == "ACTIVE"
    assert task["checkout_state"] == "CHECKED_OUT"
    assert task["completion"]["runtime_consumption_observed"] is False


def test_parent_is_superseded_and_not_reopened_by_successor_profile():
    parent = load(PARENT)
    assert parent["coordination_state"] == "SUPERSEDED"
    assert parent["checkout_state"] == "SUPERSEDED"
    assert parent["continuation_task_id"] == "STEG-BROWSER-RUNTIME-CONSUMPTION-001"
