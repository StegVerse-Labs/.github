from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "project_task_registry_event_to_sovereign_kv.py"
CONTRACT = ROOT / "data" / "task-registry-sovereign-kv-event-custody-contract.json"


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
