from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize_task_session_close.py"
CONTRACT = ROOT / "data" / "task-session-close-orchestration-contract.json"


def test_session_close_calls_canonical_return_recorder():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'record_task_registry_session_return.py' in text
    assert 'registry disposition task mismatch' in text
    assert 'registry disposition authority widening' in text
    assert '"stegverse.task-session-close/v1"' in text
    assert '"authority_effect": "NONE"' in text


def test_contract_binds_existing_session_close_policy_without_second_engine():
    text = CONTRACT.read_text(encoding="utf-8")
    assert 'data/task-coordination-policy.json#session_close_contract' in text
    assert 'scripts/materialize_task_session_close.py' in text
    assert 'scripts/record_task_registry_session_return.py' in text
    assert 'NO_SECOND_COLLISION_ENGINE' in text
