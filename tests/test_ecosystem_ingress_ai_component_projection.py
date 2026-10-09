from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data" / "goal-task-component-profiles" / "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json"
CONTRACT = ROOT / "data" / "reusable-ai-ingress-component-contract.json"
HANDOFF = ROOT / "docs" / "ECOSYSTEM_INGRESS_AI_COMPONENT_MODEL_MIRROR_HANDOFF.md"
TASK = ROOT / "data" / "canonical-task-records" / "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json"


def test_profile_reuses_existing_external_adapter_capability():
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    ids = {entry["component_id"] for entry in profile["selected_components"]}
    assert "RT-EXTERNAL-ADAPTER-ESTABLISH-001" in ids
    assert "RTC-MANIFEST-001" in ids
    assert "RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010" in ids


def test_component_projection_preserves_goal_and_runtime_nonclaim():
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    handoff = HANDOFF.read_text(encoding="utf-8")
    assert profile["goal_identity_preserved"] is True
    assert profile["new_goal_task_required"] is False
    assert profile["runtime_evidence_state"] == "NOT_COMPLETE_SOURCE_AND_CI_DO_NOT_PROVE_RUNTIME"
    assert contract["components"][0]["authority_effect"] == "NONE_COORDINATION_ONLY"
    assert "No runtime evidence is claimed" in handoff


def test_component_011_defines_ungoverned_ai_defensive_envelope():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    component = next(
        entry for entry in contract["components"]
        if entry["component_id"] == "RTC-NONCHATGPT-AI-DECISION-SANDBOX-011"
    )
    assert component["capability_provided"] == (
        "ungoverned_ai_defensive_envelope_at_controlled_chokepoints_with_external_ai_sovereignty_preserved"
    )
    invariants = component["defensive_envelope_invariants"]
    assert invariants["govern_the_boundary_not_hidden_model_state"] is True
    assert invariants["external_ai_sovereignty_preserved"] is True
    assert invariants["ambient_credentials_forbidden"] is True
    assert invariants["denial_requires_consequence_unreachability_evidence_when_supported"] is True
    assert invariants["alternate_paths_outside_controlled_boundaries_are_not_claimed_constrained"] is True
    meeting_room = next(x for x in component["instantiations"] if x["name"] == "EXTERNAL_AI_MEETING_ROOM")
    assert meeting_room["role"] == "CONCRETE_INSTANTIATION_NOT_PRIMITIVE"
    assert meeting_room["authority_effect"] == "NONE"


def test_component_011_preserves_existing_authority_owners():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    component = next(
        entry for entry in contract["components"]
        if entry["component_id"] == "RTC-NONCHATGPT-AI-DECISION-SANDBOX-011"
    )
    joined = " ".join(component["preconditions"] + component["expected_evidence"] + [component["authority_owner"]])
    for protected_owner in ("Task Registry", "TV/TVC", "Interlock/InTr", "Master Records", "Publisher"):
        assert protected_owner in joined
    assert component["authority_effect"] == "NONE_COMPONENT_REUSE_DOES_NOT_MINT_AUTHORITY"


def test_profile_completion_predicate_matches_record_organization_append():
    # #3012: the representative runtime boundary gates on its Organization
    # append in both the record and the profile; the observer name is history.
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    task = json.loads(TASK.read_text(encoding="utf-8"))
    appended = "ORGANIZATION_RECEIPT_APPENDED_UNDER_LOCK:REPRESENTATIVE_RUNTIME_BOUNDARY_EVIDENCE"
    assert task["remaining_predicates"][-1] == appended
    assert profile["goal_specific_completion_predicates_preserved"][-1] == appended
    assert "REPRESENTATIVE_RUNTIME_BOUNDARY_EVIDENCE_OBSERVED" not in profile["goal_specific_completion_predicates_preserved"]
    prior = profile["superseded_goal_specific_completion_predicates_preserved"]
    assert prior["value"][-1] == "REPRESENTATIVE_RUNTIME_BOUNDARY_EVIDENCE_OBSERVED"
    assert prior["value"][:-1] == profile["goal_specific_completion_predicates_preserved"][:-1]
    assert prior["authority_effect"] == "NONE_HISTORY_ONLY"
