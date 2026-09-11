from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "task_registry_checkin_event_history.py"

spec = importlib.util.spec_from_file_location("task_registry_checkin_event_history", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def disposition(task_id: str, value: str = "CONTINUE") -> dict:
    return {
        "schema": "stegverse.task-registry-checkin-disposition/v1",
        "task_id": task_id,
        "disposition": value,
        "session_action": "CONTINUE_CURRENT_TASK" if value == "CONTINUE" else "END_SESSION",
        "authority_effect": "NONE",
    }


def request(task_id: str, session_id: str, event_type: str, event_at: str, repos=None, comps=None) -> dict:
    return {
        "event_type": event_type,
        "task_id": task_id,
        "session_id": session_id,
        "event_at": event_at,
        "context": {
            "repository": repos[0] if repos else None,
            "branch": "test-branch",
            "pull_request": 1,
            "source_head": "a" * 40,
            "first_unresolved_predicate": "TEST",
            "repositories": repos or [],
            "components": comps or [],
        },
        "registry_disposition": disposition(task_id),
    }


def test_hash_linked_append_and_reload(tmp_path):
    ledger = tmp_path / "events.jsonl"
    one = mod.append_event(ledger, request("TASK-A", "session-a", "CHECK_IN", "2026-09-11T03:00:00Z", ["StegVerse-Labs/.github"], ["registry"]))
    two = mod.append_event(ledger, request("TASK-A", "session-a", "RETURNED", "2026-09-11T03:05:00Z", ["StegVerse-Labs/.github"], ["registry"]))
    rows = mod.load_events(ledger)
    assert len(rows) == 2
    assert one["predecessor_event_sha256"] is None
    assert two["predecessor_event_sha256"] == one["event_sha256"]
    assert rows[-1]["authority_effect"] == "NONE"


def test_recent_returned_overlap_is_candidate(tmp_path):
    ledger = tmp_path / "events.jsonl"
    mod.append_event(ledger, request("TASK-OLD", "session-old", "RETURNED", "2026-09-11T03:20:00Z", ["StegVerse-Labs/StegOS"], ["service-kv"]))
    rows = mod.recent_collision_candidates(
        ledger,
        now=datetime(2026, 9, 11, 3, 30, tzinfo=timezone.utc),
        task_id="TASK-NEW",
        repositories=["StegVerse-Labs/StegOS"],
        components=["different"],
    )
    assert len(rows) == 1
    assert rows[0]["task_id"] == "TASK-OLD"
    assert rows[0]["source"] == "RECENT_EVENT_HISTORY"
    assert rows[0]["overlap"]["repositories"] == ["StegVerse-Labs/StegOS"]


def test_expired_returned_event_is_not_candidate(tmp_path):
    ledger = tmp_path / "events.jsonl"
    mod.append_event(ledger, request("TASK-OLD", "session-old", "RETURNED", "2026-09-11T02:00:00Z", ["StegVerse-Labs/StegOS"], ["service-kv"]))
    rows = mod.recent_collision_candidates(
        ledger,
        now=datetime(2026, 9, 11, 3, 30, tzinfo=timezone.utc),
        task_id="TASK-NEW",
        repositories=["StegVerse-Labs/StegOS"],
        components=["service-kv"],
    )
    assert rows == []


def test_latest_session_state_controls_recent_window(tmp_path):
    ledger = tmp_path / "events.jsonl"
    mod.append_event(ledger, request("TASK-OLD", "session-old", "RETURNED", "2026-09-11T03:20:00Z", ["StegVerse-Labs/StegOS"], ["service-kv"]))
    mod.append_event(ledger, request("TASK-OLD", "session-old", "CHECK_IN", "2026-09-11T03:25:00Z", ["StegVerse-Labs/StegOS"], ["service-kv"]))
    rows = mod.recent_collision_candidates(
        ledger,
        now=datetime(2026, 9, 11, 3, 30, tzinfo=timezone.utc),
        task_id="TASK-NEW",
        repositories=["StegVerse-Labs/StegOS"],
        components=["service-kv"],
    )
    assert rows == []


def test_tampered_event_fails_chain_validation(tmp_path):
    ledger = tmp_path / "events.jsonl"
    mod.append_event(ledger, request("TASK-A", "session-a", "CHECK_IN", "2026-09-11T03:00:00Z"))
    row = json.loads(ledger.read_text(encoding="utf-8").strip())
    row["task_id"] = "TASK-TAMPERED"
    ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
    try:
        mod.load_events(ledger)
    except ValueError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("tampered event should fail")
