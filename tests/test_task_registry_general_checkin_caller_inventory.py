from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "data" / "task-registry-general-checkin-caller-inventory.json"
AI_SURFACES = ROOT / "data" / "task-registry-ai-entry-surface-inventory.json"


def test_general_checkin_production_callers_are_source_classified_without_runtime_upgrade():
    payload = json.loads(INVENTORY.read_text(encoding="utf-8"))
    callers = {row["path"]: row for row in payload["production_callers"]}

    assert callers["scripts/evaluate_task_registry_ai_session_checkin.py"]["classification"] == "AI_SESSION_GATED_COMPONENT_010"
    assert callers["scripts/install_and_run_canonical_work_event_bootstrap.py"]["classification"] == "NON_AI_INTERNAL_CANONICAL_WORK_PREFLIGHT"
    assert payload["conclusions"]["production_callers_source_inventoried"] == "PASS_SOURCE_LEVEL"
    assert payload["conclusions"]["ai_session_route_gated_by_component_010"] == "PASS_SOURCE_LEVEL"
    assert payload["conclusions"]["general_evaluator_external_ai_reachability"] == "NOT_PROVEN"
    assert payload["conclusions"]["authentic_chatgpt_origin"] == "NOT_PROVEN"
    assert payload["authority_effect"] == "NONE_COORDINATION_ONLY"


def test_ai_surface_inventory_preserves_external_reachability_and_origin_nonclaims():
    payload = json.loads(AI_SURFACES.read_text(encoding="utf-8"))
    assert payload["caller_inventory_ref"] == "data/task-registry-general-checkin-caller-inventory.json"
    assert payload["conclusions"]["task_registry_ai_entry_surfaces_inventoried"] == "PASS_SOURCE_LEVEL"
    assert payload["conclusions"]["general_checkin_external_ai_reachability"] == "NOT_PROVEN"
    assert payload["conclusions"]["runtime_identity_attestation_proven"] is False
