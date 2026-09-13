import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data" / "goal-task-transport-profiles" / "SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004.json"


def load_profile():
    return json.loads(PROFILE.read_text(encoding="utf-8"))


def test_componentization_decision_is_pinned():
    profile = load_profile()
    evaluation = profile["decomposition_evaluation"]
    assert evaluation["score"] == 30
    assert evaluation["decision"] == "STOP_SCOPE_GROWTH_AND_DECOMPOSE_BEFORE_ADDING_MORE_TASK_SPECIFIC_ORCHESTRATION"
    assert evaluation["authority_effect"] == "NONE_COORDINATION_ONLY"


def test_active_and_conditional_components_are_distinct():
    profile = load_profile()
    active = set(profile["selected_components"])
    conditional = set(profile["conditional_components"])
    assert not (active & conditional)
    assert "RTC-ROUNDTRIP-003" in active
    assert "RTC-INTERLOCK-INTR-TRANSPORT-008" in active
    assert "RTC-PUBLISHER-005" in conditional
    assert "RTC-STEGVERSE-EGRESS-007" in conditional
    assert "RTC-FARSIDE-FINAL-009" in conditional


def test_publication_and_far_side_stages_are_not_premature_gates():
    profile = load_profile()
    requirements = profile["transport_requirements"]
    assert requirements["publisher_projection"] == "CONDITIONAL_ON_PUBLIC_DISTRIBUTION_STAGE"
    assert requirements["stegverse_final_egress_transition"] == "CONDITIONAL_ON_DISTRIBUTION_EGRESS_STAGE"
    assert requirements["far_side_final_transition"] == "CONDITIONAL_ON_FAR_SIDE_DISTRIBUTION_STAGE"


def test_user_verification_and_authority_boundaries_remain_separate():
    profile = load_profile()
    invariants = profile["authority_invariants"]
    assert invariants["user_verification"] == "KV/SKAP Vault"
    assert invariants["claim_fence"] == "WorkerCoordinator"
    assert invariants["transition"] == "Interlock/InTr"
    assert invariants["credential_provider_release"] == "TV/TVC"
    assert invariants["reality_reconstruction"] == "Master Records"
    assert invariants["github_runtime_authority"] == "NONE"
    assert "NOT_USER_VERIFIER" in invariants["device_role"]


def test_five_declared_round_trip_instances_remain_task_bound():
    profile = load_profile()
    expected = [
        "resident_client_secret_reseal",
        "resident_consent_listener",
        "sovereign_callback",
        "owner_present_provider_consent",
        "authoritative_provider_file_probe",
    ]
    assert profile["transport_requirements"]["required_round_trips"] == expected
    binding = next(item for item in profile["component_bindings"] if item["component"] == "RTC-ROUNDTRIP-003")
    assert binding["instances"] == expected
    assert binding["cardinality"] == "FIVE_DECLARED_INSTANCES"
