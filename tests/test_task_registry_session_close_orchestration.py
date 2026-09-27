import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize_task_session_close.py"
CONTRACT = ROOT / "data" / "task-session-close-orchestration-contract.json"
COMPONENT_ID = "RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010"


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
            "reusable_component_id": COMPONENT_ID,
            "source_policy": "data/task-registry-ai-ingress-policy.json",
            "chatgpt_is_only_permitted_ai_kind": True,
            "runtime_identity_attestation_proven": False,
            "authority_effect": "NONE",
        }
    return payload


def test_session_close_binds_reusable_actor_component():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'RTC-TASK-REGISTRY-SESSION-ACTOR-GATE-010' in text
    assert '"--actor-kind", args.actor_kind' in text
    assert 'session return receipt reusable component mismatch' in text
    assert '"runtime_identity_attestation_proven": False' in text


def test_session_close_rejects_non_chatgpt_ai(tmp_path):
    ledger = tmp_path / "events.jsonl"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--task-id", "TASK-A", "--session-id", "session-a",
        "--actor-kind", "AI_AGENT", "--ledger", str(ledger),
    ], input=json.dumps(disposition("TASK-A")), text=True, capture_output=True)
    assert proc.returncode != 0
    assert not ledger.exists()


def test_session_close_preserves_non_ai_actor_kind(tmp_path):
    ledger = tmp_path / "events.jsonl"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--task-id", "TASK-A", "--session-id", "session-a",
        "--actor-kind", "NON_AI_SYSTEM_COORDINATOR", "--ledger", str(ledger),
    ], input=json.dumps(disposition("TASK-A")), text=True, capture_output=True, check=True)
    payload = json.loads(proc.stdout)
    assert payload["actor_kind"] == "NON_AI_SYSTEM_COORDINATOR"
    assert payload["reusable_component_id"] == COMPONENT_ID
    assert payload["return_receipt"]["reusable_component_id"] == COMPONENT_ID
    assert payload["authority_effect"] == "NONE"


def test_chatgpt_session_close_requires_gated_checkin(tmp_path):
    ledger = tmp_path / "events.jsonl"
    bad = subprocess.run([
        sys.executable, str(SCRIPT), "--task-id", "TASK-A", "--session-id", "session-a",
        "--actor-kind", "CHATGPT_SESSION", "--ledger", str(ledger),
    ], input=json.dumps(disposition("TASK-A")), text=True, capture_output=True)
    assert bad.returncode != 0
    assert not ledger.exists()

    forged = disposition("TASK-A", "CHATGPT_SESSION")
    forged["ai_session_ingress"]["runtime_identity_attestation_proven"] = True
    denied = subprocess.run([
        sys.executable, str(SCRIPT), "--task-id", "TASK-A", "--session-id", "session-a",
        "--actor-kind", "CHATGPT_SESSION", "--ledger", str(ledger),
    ], input=json.dumps(forged), text=True, capture_output=True)
    assert denied.returncode != 0
    assert not ledger.exists()


def test_contract_still_preserves_non_authorizing_session_close():
    text = CONTRACT.read_text(encoding="utf-8")
    assert 'NO_SECOND_COLLISION_ENGINE' in text
    assert 'RETURN_EVENT_GRANTS_NO_EXECUTION_OR_TRANSITION_AUTHORITY' in text
