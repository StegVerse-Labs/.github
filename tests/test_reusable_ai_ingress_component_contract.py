from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "reusable-ai-ingress-component-contract.json"
PROFILE = ROOT / "data" / "goal-task-component-profiles" / "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json"
MODEL = ROOT / "data" / "reusable-task-component-model.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_ai_ingress_component_family_is_registered():
    model = load(MODEL)
    assert model["component_families"]["ai_ingress_coordination"] == "data/reusable-ai-ingress-component-contract.json"


def test_session_actor_gate_has_minimum_component_interface():
    contract = load(CONTRACT)
    component = next(item for item in contract["components"] if item["component_id"] == "RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010")
    required = {
        "component_id",
        "capability_provided",
        "inputs",
        "outputs",
        "preconditions",
        "expected_evidence",
        "authority_owner",
        "authority_effect",
        "failure_classes",
        "retry_or_reentry_semantics",
        "version_or_schema_binding",
    }
    assert required.issubset(component)
    assert component["authority_effect"] == "NONE_COORDINATION_ONLY"
    assert "scripts/evaluate_task_registry_ai_session_checkin.py" in component["canonical_implementation"]
    assert "scripts/record_task_registry_session_return.py" in component["canonical_implementation"]
    assert "scripts/materialize_task_session_close.py" in component["canonical_implementation"]


def test_goal_profile_preserves_identity_and_does_not_force_maximal_transport():
    profile = load(PROFILE)
    assert profile["task_id"] == "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001"
    assert profile["cosv_task_vector"] is None
    assert profile["goal_identity_preserved"] is True
    assert profile["new_goal_task_required"] is False
    ids = {item["component_id"] for item in profile["selected_components"]}
    assert "RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010" in ids
    assert "GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001" in ids
    assert "RTC-PUBLISHER-005" in profile["not_selected"]


def test_runtime_evidence_is_not_upgraded_by_componentization():
    profile = load(PROFILE)
    assert profile["runtime_evidence_state"] == "NOT_COMPLETE_SOURCE_AND_CI_DO_NOT_PROVE_RUNTIME"
