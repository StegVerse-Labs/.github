from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize_task_session_close.py"
CONTRACT = ROOT / "data" / "task-session-close-orchestration-contract.json"


def test_session_close_calls_canonical_return_recorder():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'record_task_registry_session_return.py' in text
    assert 'registry disposition task mismatch' in text
    assert 'registry disposition authority widening' in text
    assert 'session return receipt missing canonical event hash' in text
    assert '"stegverse.task-session-close/v1"' in text
    assert '"footer_handoff_emission_admissible": True' in text
    assert '"required_pre_footer_return_event_sha256": return_event_sha256' in text
    assert '"authority_effect": "NONE"' in text


def test_contract_binds_existing_session_close_policy_without_second_engine():
    text = CONTRACT.read_text(encoding="utf-8")
    assert 'data/task-coordination-policy.json#session_close_contract' in text
    assert 'scripts/materialize_task_session_close.py' in text
    assert 'scripts/record_task_registry_session_return.py' in text
    assert 'footer_or_handoff_emission_requires_successful_return_receipt' in text
    assert 'failed_return_recording_blocks_footer_handoff_close' in text
    assert 'FOOTER_HANDOFF_EMISSION_REQUIRES_HASH_LINKED_RETURN_RECEIPT' in text
    assert 'NO_SECOND_COLLISION_ENGINE' in text
