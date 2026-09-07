from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("monitor", ROOT / "scripts/run_native_email_action_monitor.py")
M = importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(M)


class FakeBroker:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def call(self, operation, **payload):
        self.calls.append((operation, payload))
        assert operation == "SEARCH_MESSAGES"
        token = payload.get("next_page_token")
        page = self.pages[token]
        return {
            "schema": "stegverse.native-email-broker-response/v1",
            "operation": operation,
            "provider": "GMAIL",
            "credential_authority": "TV/TVC",
            "credential_material_exported": False,
            "provider_operation_authority_transferred": False,
            "messages": page["messages"],
            "next_page_token": page.get("next_page_token"),
        }


def message(mid, subject="[StegVerse-Labs/Site] Run failed: Site Task Runner - main (abc1234)"):
    return {
        "message_id": mid,
        "id": mid,
        "from": "StegVerse notifications@github.com",
        "subject": subject,
        "snippet": "All jobs have failed",
    }


def test_replay_page_waits_for_steghealth_ack_and_never_archives():
    pages = {
        None: {"messages": [message("m1")], "next_page_token": "p2"},
        "p2": {"messages": [message("m2")], "next_page_token": None},
    }
    broker = FakeBroker(pages)
    with tempfile.TemporaryDirectory() as tmp:
        checkpoint = Path(tmp) / "replay.checkpoint.json"
        first = M.archived_replay_page(broker, checkpoint)
        assert first["state"] == "PENDING"
        assert first["ack_required"] is True
        assert first["mailbox_mutation_performed"] is False
        assert first["archive_operation_performed"] is False
        assert [op for op, _ in broker.calls] == ["SEARCH_MESSAGES"]

        again = M.archived_replay_page(broker, checkpoint)
        assert again["batch_hash"] == first["batch_hash"]
        assert broker.calls[-1][1].get("next_page_token") is None

        ack = Path(first["ack_ref"])
        ack.write_text(json.dumps({
            "schema": M.REPLAY_ACK_SCHEMA,
            "state": "STEGHEALTH_FAILURE_PAGE_ACCEPTED",
            "batch_hash": first["batch_hash"],
        }), encoding="utf-8")
        second = M.archived_replay_page(broker, checkpoint)
        assert second["ack_required"] is True
        assert broker.calls[-1][1]["next_page_token"] == "p2"


def test_bad_ack_does_not_advance_page():
    broker = FakeBroker({None: {"messages": [message("m1")], "next_page_token": "p2"}})
    with tempfile.TemporaryDirectory() as tmp:
        checkpoint = Path(tmp) / "replay.checkpoint.json"
        first = M.archived_replay_page(broker, checkpoint)
        Path(first["ack_ref"]).write_text(json.dumps({
            "schema": M.REPLAY_ACK_SCHEMA,
            "state": "STEGHEALTH_FAILURE_PAGE_ACCEPTED",
            "batch_hash": "0" * 64,
        }), encoding="utf-8")
        second = M.archived_replay_page(broker, checkpoint)
        assert second["batch_hash"] == first["batch_hash"]
        assert broker.calls[-1][1].get("next_page_token") is None


def test_final_ack_marks_replay_complete_without_replaying_page():
    broker = FakeBroker({None: {"messages": [message("m1")], "next_page_token": None}})
    with tempfile.TemporaryDirectory() as tmp:
        checkpoint = Path(tmp) / "replay.checkpoint.json"
        first = M.archived_replay_page(broker, checkpoint)
        Path(first["ack_ref"]).write_text(json.dumps({
            "schema": M.REPLAY_ACK_SCHEMA,
            "state": "STEGHEALTH_FAILURE_PAGE_ACCEPTED",
            "batch_hash": first["batch_hash"],
        }), encoding="utf-8")
        calls_before = len(broker.calls)
        done = M.archived_replay_page(broker, checkpoint)
        assert done["state"] == "COMPLETE"
        assert done["complete"] is True
        assert done["acknowledged_pages"] == 1
        assert done["acknowledged_messages"] == 1
        assert len(broker.calls) == calls_before
