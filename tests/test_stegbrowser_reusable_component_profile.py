import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "data" / "canonical-task-records" / "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json"
PROFILE = ROOT / "data" / "goal-task-transport-profiles" / "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json"
HANDOFF = ROOT / "docs" / "STEGBROWSER_REUSABLE_COMPONENT_MODEL_MIRROR_HANDOFF.md"


def test_stegbrowser_goal_identity_and_runtime_truth_are_preserved():
    task = json.loads(TASK.read_text(encoding="utf-8"))
    projection = task["component_model_projection"]
    assert task["task_id"] == "STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001"
    assert task["cosv_task_vector"] == "40000100100000"
    assert projection["goal_identity_preserved"] is True
    assert projection["cosv_identity_preserved"] is True
    assert projection["runtime_predicates_changed"] is False
    assert projection["runtime_handoff_remains_runtime_truth"] is True
    assert projection["new_goal_task_required"] is False
    assert projection["new_reusable_component_required"] is False


def test_stegbrowser_transport_profile_selects_only_required_components():
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    selected = set(profile["selected_components"])
    assert "RTC-MANIFEST-001" in selected
    assert "RTC-GOVERNED-PROCESSING-002" in selected
    assert "RTC-ROUNDTRIP-003" in selected
    assert "RTC-EVIDENCE-CUSTODY-004" in selected
    assert "RTC-PUBLISHER-005" in selected
    assert "RTC-STEGVERSE-EGRESS-007" in selected
    assert "RTC-INTERLOCK-INTR-TRANSPORT-008" in selected
    assert "RTC-FARSIDE-FINAL-009" in selected
    assert "RTC-SDK-RETURN-006" not in selected
    assert profile["transport_requirements"]["sdk_return_assembly"] is False
    assert len(profile["transport_requirements"]["required_round_trips"]) == 4


def test_stegbrowser_componentization_is_non_authorizing_and_requires_reuse():
    task = json.loads(TASK.read_text(encoding="utf-8"))
    projection = task["component_model_projection"]
    assert projection["decomposition_score"] >= 13
    assert projection["decomposition_decision"] == "STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION"
    assert projection["componentization_mints_authority"] is False
    text = HANDOFF.read_text(encoding="utf-8")
    assert "Do not add another task-specific scheduler" in text
    assert "No authentic runtime predicate advances through this componentization" in text
