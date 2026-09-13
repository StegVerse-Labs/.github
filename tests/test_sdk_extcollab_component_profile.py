import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data/goal-task-component-profiles/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004.json"
TRANSPORT = ROOT / "data/goal-task-transport-profiles/SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004.json"


def test_component_profile_preserves_goal_identity():
    profile = json.loads(PROFILE.read_text())
    assert profile["task_id"] == "SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004"
    assert profile["cosv_task_vector"] == "71000000100110"
    assert profile["goal_identity_preserved"] is True
    assert profile["authority_effect"] == "NONE_COORDINATION_ONLY"


def test_consent_is_separate_from_generic_round_trip():
    transport = json.loads(TRANSPORT.read_text())
    requirements = transport["transport_requirements"]
    assert "owner_present_provider_consent" not in requirements["required_round_trips"]
    assert requirements["owner_present_provider_consent_is_transport_round_trip"] is False


def test_final_transport_chain_is_target_conditional():
    transport = json.loads(TRANSPORT.read_text())
    assert transport["maximal_chain_is_mandatory_for_every_target"] is False
    applicability = transport["component_applicability"]
    assert applicability["RTC-STEGVERSE-EGRESS-007"] == "CONDITIONAL_PER_TARGET"
    assert applicability["RTC-FARSIDE-FINAL-009"] == "CONDITIONAL_PER_TARGET"


def test_no_new_reusable_component_is_created():
    profile = json.loads(PROFILE.read_text())
    assert profile["new_reusable_components_created_by_this_reconciliation"] == []
