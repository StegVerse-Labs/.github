from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "record_task_registry_session_return.py"
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


def test_return_recorder_appends_non_authorizing_event(tmp_path):
    ledger = tmp_path / "events.jsonl"
    task_id = "TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--task-id", task_id,
        "--session-id", "session-return-test",
        "--actor-kind", "NON_AI_SYSTEM_COORDINATOR",
        "--event-type", "RETURNED",
        "--repository", "StegVerse-Labs/.github",
        "--branch", "task-registry-checkin-event-history-001",
        "--pull-request", "1390",
        "--source-head", "d" * 40,
        "--first-unresolved-predicate", "RETURN_TEST",
        "--repositories", "StegVerse-Labs/.github",
        "--components", "task-registry",
        "--event-at", "2026-09-11T04:00:00Z",
        "--ledger", str(ledger),
    ], input=json.dumps(disposition(task_id)), text=True, capture_output=True, check=True)
    receipt = json.loads(proc.stdout)
    row = json.loads(ledger.read_text(encoding="utf-8").strip())
    assert receipt["schema"] == "stegverse.task-registry-session-return-receipt/v1"
    assert receipt["authority_effect"] == "NONE"
    assert receipt["reusable_component_id"] == COMPONENT_ID
    assert row["context"]["reusable_component_id"] == COMPONENT_ID
    assert row["context"]["actor_kind"] == "NON_AI_SYSTEM_COORDINATOR"


def test_return_recorder_rejects_missing_actor_kind(tmp_path):
    ledger = tmp_path / "events.jsonl"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--task-id", "TASK-A",
        "--session-id", "session-a",
        "--ledger", str(ledger),
    ], input=json.dumps(disposition("TASK-A")), text=True, capture_output=True)
    assert proc.returncode != 0
    assert not ledger.exists()


def test_return_recorder_rejects_non_chatgpt_ai(tmp_path):
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


def test_chatgpt_return_requires_matching_gated_checkin(tmp_path):
    ledger = tmp_path / "events.jsonl"
    bad = subprocess.run([
        sys.executable, str(SCRIPT), "--task-id", "TASK-A", "--session-id", "session-a",
        "--actor-kind", "CHATGPT_SESSION", "--ledger", str(ledger),
    ], input=json.dumps(disposition("TASK-A")), text=True, capture_output=True)
    assert bad.returncode != 0
    assert not ledger.exists()

    forged = disposition("TASK-A", "CHATGPT_SESSION")
    forged["ai_session_ingress"]["runtime_identity_attestation_proven"] = True
    forged["ai_session_ingress"]["authenticated_origin"] = True
    for payload in (disposition("TASK-A", "CHATGPT_SESSION"), forged):
        denied = subprocess.run([
            sys.executable, str(SCRIPT), "--task-id", "TASK-A", "--session-id", "session-a",
            "--actor-kind", "CHATGPT_SESSION", "--ledger", str(ledger),
        ], input=json.dumps(payload), text=True, capture_output=True)
        assert denied.returncode != 0
        assert "STOP_AUTHENTIC_ORIGIN_UNAVAILABLE" in denied.stderr
        assert not ledger.exists()


def test_return_recorder_rejects_wrong_task_disposition(tmp_path):
    ledger = tmp_path / "events.jsonl"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--task-id", "TASK-A",
        "--session-id", "session-a",
        "--actor-kind", "NON_AI_SYSTEM_COORDINATOR",
        "--ledger", str(ledger),
    ], input=json.dumps(disposition("TASK-B")), text=True, capture_output=True)
    assert proc.returncode != 0
    assert not ledger.exists()
