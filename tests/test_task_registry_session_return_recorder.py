from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "record_task_registry_session_return.py"


def disposition(task_id: str) -> dict:
    return {
        "schema": "stegverse.task-registry-checkin-disposition/v1",
        "task_id": task_id,
        "disposition": "CONTINUE",
        "session_action": "CONTINUE_CURRENT_TASK",
        "authority_effect": "NONE",
    }


def test_return_recorder_appends_non_authorizing_event(tmp_path):
    ledger = tmp_path / "events.jsonl"
    task_id = "TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--task-id", task_id,
        "--session-id", "session-return-test",
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
    assert row["event_type"] == "RETURNED"
    assert row["session_id"] == "session-return-test"
    assert row["event_sha256"] == receipt["event_sha256"]


def test_return_recorder_rejects_wrong_task_disposition(tmp_path):
    ledger = tmp_path / "events.jsonl"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--task-id", "TASK-A",
        "--session-id", "session-a",
        "--ledger", str(ledger),
    ], input=json.dumps(disposition("TASK-B")), text=True, capture_output=True)
    assert proc.returncode != 0
    assert not ledger.exists()
