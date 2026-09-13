import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SITE-PUBLICATION-NATIVE-RUNTIME-EXECUTION-001"


def load(rel):
    return json.loads((ROOT / rel).read_text())


def test_source_refresh_component_is_registered_and_non_authorizing():
    model = load("data/reusable-task-component-model.json")
    contract = load("data/reusable-sovereign-source-refresh-component-contract.json")
    assert model["component_families"]["sovereign_source_refresh"] == "data/reusable-sovereign-source-refresh-component-contract.json"
    assert contract["component_id"] == "RTC-SOVEREIGN-SOURCE-REFRESH-010"
    assert contract["canonical_implementation"] == "scripts/refresh_sovereign_worker_runtime_source.py"
    assert contract["authority_effect"] == "NONE_LOCAL_SOURCE_REFRESH"
    assert contract["creates_new_runtime_owner"] is False
    assert contract["creates_new_source_transport"] is False


def test_site_publication_profile_preserves_identity_and_runtime_predicates():
    profile = load(f"data/goal-task-component-profiles/{TASK_ID}.json")
    task = load(f"data/canonical-task-records/{TASK_ID}.json")
    assert profile["task_id"] == TASK_ID
    assert profile["cosv_task_vector"] == "50000000102000"
    assert profile["decomposition_evaluation"]["score"] == 21
    assert profile["goal_identity_preserved"] is True
    assert profile["new_goal_task_required"] is False
    assert task["component_model_projection"]["goal_runtime_predicates_changed"] is False
    assert task["remaining_predicates"] == profile["goal_specific_completion_predicates_preserved"]


def test_site_publication_selects_only_needed_transport_components():
    profile = load(f"data/goal-task-component-profiles/{TASK_ID}.json")
    selected = {item["component_id"] for item in profile["selected_components"]}
    assert "RTC-GOVERNED-PROCESSING-002" in selected
    assert "RTC-PUBLISHER-005" in selected
    assert "RTC-STEGVERSE-EGRESS-007" in selected
    assert "RTC-INTERLOCK-INTR-TRANSPORT-008" in selected
    assert "RTC-EVIDENCE-CUSTODY-004" in selected
    assert "RTC-SDK-RETURN-006" not in selected
    assert "RTC-FARSIDE-FINAL-009" not in selected


def test_authority_separation_is_explicit():
    profile = load(f"data/goal-task-component-profiles/{TASK_ID}.json")
    authority = profile["authority_invariants"]
    assert authority["task_registry"] == "COORDINATION_ONLY"
    assert authority["worker_claim_fence"] == "WorkerCoordinator"
    assert authority["user_verification"] == "KV/SKAP Vault"
    assert authority["governed_transition"] == "Interlock/InTr"
    assert authority["observed_reality_custody_reconstruction"] == "Master Records"
    assert authority["github_runtime_authority"] == "NONE"
