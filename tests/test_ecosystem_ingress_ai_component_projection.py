from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data" / "goal-task-component-profiles" / "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json"
CONTRACT = ROOT / "data" / "reusable-ai-ingress-component-contract.json"
HANDOFF = ROOT / "docs" / "ECOSYSTEM_INGRESS_AI_COMPONENT_MODEL_MIRROR_HANDOFF.md"


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
