import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize_task_session_close.py"
CONTRACT = ROOT / "data" / "task-session-close-orchestration-contract.json"


def disposition(task_id: str, actor_kind: str | None = None) -> dict:
    payload = {
        "schema": "stegverse.task-registry-checkin-disposition/v1",
        "task_id": task_id,
        "disposition": "CONTINUE",
        "session_action": "CONTINUE_CURRENT_TASK",
        "authority_effect": "NONE",
    }
    if actor_kind == "CHATGPT_SESSION":
        payload["ai_session_ingress"] = {
            "actor_kind": actor_kind,
            "source_policy": "data/task-registry-ai-ingress-policy.json",
            "chatgpt_is_only_permitted_ai_kind": True,
            "runtime_identity_attestation_proven": False,
            "authority_effect": "NONE",
        }
    return payload


def test_session_close_calls_canonical_return_recorder():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'record_task_registry_session_return.py' in text
    assert '"--actor-kind", args.actor_kind' in text
    assert 'registry disposition task mismatch' in text
    assert 'registry disposition authority widening' in text
    assert 'session return receipt missing canonical event hash' in text
    assert 'session return receipt actor mismatch' in text
    assert '"stegverse.task-session-close/v1"' in text
    assert '"footer_handoff_emission_admissible": True' in text
    assert '"required_pre_footer_return_event_sha256": return_event_sha256' in text
    assert '"runtime_identity_attestation_proven": False' in text
    assert '"authority_effect": "NONE"' in text


def test_session_close_rejects_non_chatgpt_ai_before_footer(tmp_path):
    ledger = tmp_path / "events.jsonl"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--task-id", "TASK-A",
        "--session-id", "session-a",
        "--actor-kind", "AI_AGENT",
        "--ledger", str(ledger),
    ], input=json.dumps(disposition("TASK-A")), text=True, capture_output=True)
    assert proc.returncode != 0
    assert not ledger.exists()
    assert proc.stdout == ""


def test_session_close_preserves_non_ai_actor_kind(tmp_path):
    ledger = tmp_path / "events.jsonl"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--task-id", "TASK-A",
        "--session-id", "session-a",
        "--actor-kind", "NON_AI_SYSTEM_COORDINATOR",
        "--ledger", str(ledger),
    ], input=json.dumps(disposition("TASK-A")), text=True, capture_output=True, check=True)
    payload = json.loads(proc.stdout)
    assert payload["actor_kind"] == "NON_AI_SYSTEM_COORDINATOR"
    assert payload["return_receipt"]["actor_kind"] == "NON_AI_SYSTEM_COORDINATOR"
    assert payload["runtime_identity_attestation_proven"] is False
    assert payload["authority_effect"] == "NONE"


def test_chatgpt_session_close_requires_gated_checkin_disposition(tmp_path):
    ledger = tmp_path / "events.jsonl"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--task-id", "TASK-A",
        "--session-id", "session-a",
        "--actor-kind", "CHATGPT_SESSION",
        "--ledger", str(ledger),
    ], input=json.dumps(disposition("TASK-A")), text=True, capture_output=True)
    assert proc.returncode != 0
    assert not ledger.exists()


def test_chatgpt_session_close_accepts_matching_gated_checkin(tmp_path):
    ledger = tmp_path / "events.jsonl"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--task-id", "TASK-A",
        "--session-id", "session-a",
        "--actor-kind", "CHATGPT_SESSION",
        "--ledger", str(ledger),
    ], input=json.dumps(disposition("TASK-A", "CHATGPT_SESSION")), text=True, capture_output=True, check=True)
    payload = json.loads(proc.stdout)
    assert payload["actor_kind"] == "CHATGPT_SESSION"
    assert payload["return_receipt"]["actor_kind"] == "CHATGPT_SESSION"
    assert payload["runtime_identity_attestation_proven"] is False


def test_contract_binds_existing_session_close_policy_without_second_engine():
    text = CONTRACT.read_text(encoding="utf-8")
    assert 'data/task-coordination-policy.json#session_close_contract' in text
    assert 'data/task-registry-ai-ingress-policy.json' in text
    assert 'scripts/materialize_task_session_close.py' in text
    assert 'scripts/record_task_registry_session_return.py' in text
    assert '"actor_kind"' in text
    assert 'footer_or_handoff_emission_requires_successful_return_receipt' in text
    assert 'failed_return_recording_blocks_footer_handoff_close' in text
    assert 'NON_CHATGPT_AI_SESSION_RETURN_MUST_FAIL_CLOSED' in text
    assert 'CHATGPT_SESSION_RETURN_REQUIRES_GATED_CHECKIN_DISPOSITION' in text
    assert 'FOOTER_HANDOFF_EMISSION_REQUIRES_HASH_LINKED_RETURN_RECEIPT' in text
    assert 'NO_SECOND_COLLISION_ENGINE' in text
