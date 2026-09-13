import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "project_task_registry_event_to_sovereign_kv.py"
CONTRACT = ROOT / "data" / "task-registry-sovereign-kv-event-custody-contract.json"
PROFILE = ROOT / "data" / "goal-task-transport-profiles" / "TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001.json"
TASK_RECORD = ROOT / "data" / "canonical-task-records" / "TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001.json"
DECOMPOSITION_POLICY = ROOT / "data" / "reusable-task-component-decomposition-policy.json"
EVIDENCE_COMPONENTS = ROOT / "data" / "reusable-evidence-validation-component-contract.json"


def test_projection_bridge_preserves_exact_event_hash_and_authority_boundary():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'stegverse.task-registry-checkin-event/v1' in text
    assert 'stegverse.task-registry-sovereign-kv-projection-request/v1' in text
    assert 'stegverse.task-registry-sovereign-kv-projection-receipt/v1' in text
    assert 'STEGVERSE_SOVEREIGN_KV' in text
    assert 'stored_event_sha256' in text
    assert 'interlock_intr_receipt_ref' in text
    assert 'provider_adapter_ref' in text
    assert 'kv_instance_ref' in text
    assert 'authority_effect' in text


def test_custody_contract_keeps_github_optional_and_intr_authoritative():
    text = CONTRACT.read_text(encoding="utf-8")
    assert 'github_is_optional_projection' in text
    assert 'missing_sovereign_kv_receipt_does_not_invent_custody' in text
    assert 'INTERLOCK_INTR_REMAINS_TRANSITION_ADMISSION_AUTHORITY' in text
    assert 'TV_TVC_REMAINS_CREDENTIAL_AUTHORITY' in text
    assert 'NO_GITHUB_RUNTIME_AUTHORITY' in text


def test_goal_profile_reuses_current_verification_selector_without_minting_authority():
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    contract = json.loads(EVIDENCE_COMPONENTS.read_text(encoding="utf-8"))
    selector = next(c for c in contract["components"] if c["component_id"] == "RTC-EVIDENCE-CURRENT-SELECTOR-010")

    assert "RTC-EVIDENCE-CURRENT-SELECTOR-010" in profile["selected_components"]
    assert profile["transport_requirements"]["current_applicable_verification_selection"] is True
    assert "CURRENT_APPLICABLE_KV_SKAP_VERIFICATION_RECORD_SELECTED_WHEN_REQUIRED" in profile["task_specific_completion_predicates"]
    assert "ANY_TASK_SPECIFIC_CURRENT_VERIFICATION_SELECTOR" in profile["superseded_bespoke_orchestration"]
    assert selector["authority_effect"] == "NONE_EVIDENCE_SELECTION_ONLY"
    assert selector["invariants"]["creates_user_verification"] is False
    assert selector["invariants"]["device_identity_is_user_verification"] is False
    assert selector["invariants"]["secret_material_output"] is False


def test_prompt_ceiling_successor_does_not_replace_canonical_runtime_owner():
    record = json.loads(TASK_RECORD.read_text(encoding="utf-8"))
    policy = json.loads(DECOMPOSITION_POLICY.read_text(encoding="utf-8"))
    transition = record["runtime_owner_transition_observation"]

    assert "reset_prompt_count" in policy["component_split_rule"]["do_not_split_merely_to"]
    assert "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001" in record["dependencies"]
    assert "STEGOS-DEVICE-KV-SKAP-AUTHENTIC-RUNTIME-002" not in record["adjacent_task_refs"]
    assert transition["canonical_owner"] == "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001"
    assert transition["disposition"] == "SUPERSEDED_PROMPT_CEILING_ONLY_SUCCESSOR"
    assert transition["canonical_dependency_replaced"] is False
