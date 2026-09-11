from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "scripts" / "evaluate_task_registry_collision_checkin.py"
LEDGER = ROOT / "scripts" / "task_registry_checkin_event_history.py"


def run_ledger(path: Path, payload: dict) -> dict:
    proc = subprocess.run(
        [sys.executable, str(LEDGER), "--ledger", str(path)],
        input=json.dumps(payload), text=True, capture_output=True, check=True,
    )
    return json.loads(proc.stdout)


def run_evaluator(path: Path, payload: dict) -> dict:
    env = dict(os.environ)
    env["STEGVERSE_TASK_REGISTRY_EVENT_LEDGER"] = str(path)
    proc = subprocess.run(
        [sys.executable, str(EVALUATOR)],
        input=json.dumps(payload), text=True, capture_output=True, check=True, env=env,
    )
    return json.loads(proc.stdout)


def disposition(task_id: str) -> dict:
    return {
        "schema": "stegverse.task-registry-checkin-disposition/v1",
        "task_id": task_id,
        "disposition": "CONTINUE",
        "session_action": "CONTINUE_CURRENT_TASK",
        "authority_effect": "NONE",
    }


def test_recent_returned_session_augments_existing_evaluator(tmp_path):
    ledger = tmp_path / "events.jsonl"
    old_task = "STEGOS-NODE-MANIFOLD-001"
    run_ledger(ledger, {
        "event_type": "RETURNED",
        "task_id": old_task,
        "session_id": "recent-node-session",
        "event_at": "2026-09-11T03:30:00Z",
        "context": {
            "repository": "StegVerse-Labs/StegOS",
            "branch": "recent-node-branch",
            "pull_request": 328,
            "source_head": "a" * 40,
            "first_unresolved_predicate": "SERVICE_KV_WRITE_READBACK",
            "repositories": ["StegVerse-Labs/StegOS"],
            "components": ["service-kv"],
        },
        "registry_disposition": disposition(old_task),
    })

    current_task = "TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001"
    out = run_evaluator(ledger, {
        "task_id": current_task,
        "checkin_context": {
            "session_id": "new-session",
            "checked_in_at": "2026-09-11T03:40:00Z",
            "repository": "StegVerse-Labs/.github",
            "branch": "task-registry-checkin-event-history-001",
            "pull_request": 1390,
            "source_head": "b" * 40,
            "first_unresolved_predicate": "RECENT_WINDOW_TEST",
            "repositories_under_mutation": ["StegVerse-Labs/StegOS"],
            "components_under_mutation": ["service-kv"],
        },
    })
    recent = [x for x in out.get("collision_candidates", []) if x.get("source") == "RECENT_EVENT_HISTORY"]
    assert any(x["task_id"] == old_task for x in recent)
    assert out["disposition"] in {"COORDINATE_CONVERGENCE", "STOP_COLLISION"}
    assert out["checkin_event_sha256"].startswith("sha256:")


def test_evaluator_records_checkin_event_before_returning(tmp_path):
    ledger = tmp_path / "events.jsonl"
    current_task = "TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001"
    out = run_evaluator(ledger, {
        "task_id": current_task,
        "checkin_context": {
            "session_id": "recorded-session",
            "checked_in_at": "2026-09-11T03:45:00Z",
            "repository": "StegVerse-Labs/.github",
            "branch": "task-registry-checkin-event-history-001",
            "pull_request": 1390,
            "source_head": "c" * 40,
            "first_unresolved_predicate": "CHECKIN_EVENT",
            "repositories_under_mutation": ["StegVerse-Labs/.github"],
            "components_under_mutation": ["task-registry"],
        },
    })
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows[-1]["event_type"] == "CHECK_IN"
    assert rows[-1]["session_id"] == "recorded-session"
    assert rows[-1]["event_sha256"] == out["checkin_event_sha256"]
    assert rows[-1]["authority_effect"] == "NONE"


def test_rejected_checkin_is_immediately_closed_with_stopped_event(tmp_path):
    ledger = tmp_path / "events.jsonl"
    out = run_evaluator(ledger, {
        "task_id": "UNREGISTERED-COLLISION-TEST-TASK",
        "checkin_context": {
            "session_id": "rejected-session",
            "checked_in_at": "2026-09-11T03:50:00Z",
            "repository": "StegVerse-Labs/.github",
            "branch": "rejected-branch",
            "source_head": "d" * 40,
            "first_unresolved_predicate": "REGISTRATION",
            "repositories_under_mutation": ["StegVerse-Labs/.github"],
            "components_under_mutation": ["task-registry"],
        },
    })
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert out["disposition"] == "STOP_NOT_REGISTERED"
    assert [row["event_type"] for row in rows] == ["CHECK_IN", "STOPPED"]
    assert rows[-1]["session_id"] == "rejected-session"
    assert rows[-1]["event_sha256"] == out["stopped_event_sha256"]
    assert rows[-1]["authority_effect"] == "NONE"
