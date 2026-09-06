from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("native_mail", ROOT / "scripts/run_native_email_action_monitor.py")
M = importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(M)


class FakeBroker:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def call(self, operation, **payload):
        self.calls.append((operation, payload))
        value = self.responses.pop(0)
        assert value["operation"] == operation
        return value


def response(operation, **kwargs):
    return {
        "schema": "stegverse.native-email-broker-response/v1",
        "operation": operation,
        "credential_authority": "TV/TVC",
        "credential_material_exported": False,
        "provider_operation_authority_transferred": False,
        **kwargs,
    }


def test_exact_ids_are_resolved_before_archive_and_backlog_is_lower_bound():
    messages = [{
        "id": "m1", "from": "notifications@github.com", "subject": "CI failed",
        "repository": "StegVerse-Labs/Site", "workflow": "Site Task Runner", "snippet": "failed abcdef1"
    }]
    ids = [f"m{i}" for i in range(1, 101)]
    broker = FakeBroker([
        response("SEARCH_MESSAGES", provider="GMAIL", messages=messages, next_page_token="page"),
        response("SEARCH_IDS", provider="GMAIL", message_ids=ids, next_page_token="page"),
        response("ARCHIVE_IDS", provider="GMAIL", archived_ids=ids, failed_ids=[]),
        response("SEARCH_IDS", provider="GMAIL", message_ids=[f"a{i}" for i in range(100)], next_page_token="more"),
        response("GET_LABEL_COUNTS", provider="GMAIL", labels={"INBOX": {"messagesTotal": 123, "messagesUnread": 120}}),
    ])
    receipt = M.run(broker)
    assert [name for name, _ in broker.calls][:3] == ["SEARCH_MESSAGES", "SEARCH_IDS", "ARCHIVE_IDS"]
    assert broker.calls[2][1]["message_ids"] == ids
    assert receipt["processed_exact_count"] == 100
    assert receipt["archived_count"] == 100
    assert receipt["actionable_more_than_returned"] is True
    assert receipt["actionable_minimum"] == 101
    assert receipt["email_observation_is_runtime_evidence"] is False
    assert receipt["incident_proposals_require_canonical_task_ingress"] is True


def test_incident_clustering_reuses_non_authorizing_email_signature_semantics():
    rows = [
        {"id": "1", "from": "notifications@github.com", "repository": "x/y", "workflow": "Build", "snippet": "failed abcdef1"},
        {"id": "2", "from": "notifications@github.com", "repository": "x/y", "workflow": "Build", "snippet": "failed 1234567"},
        {"id": "3", "from": "news@example.com", "subject": "ordinary mail"},
    ]
    incidents = M.cluster_incidents(rows)
    assert len(incidents) == 1
    assert incidents[0]["observation_count"] == 2
    assert incidents[0]["state"] == "INCIDENT_PROPOSED_NOT_ADMITTED"
    assert incidents[0]["email_observation_is_execution_evidence"] is False
    assert incidents[0]["incident_proposal_mints_execution_authority"] is False


def test_partial_archive_fails_monitor_receipt_without_dropping_identity():
    broker = FakeBroker([
        response("SEARCH_MESSAGES", provider="GMAIL", messages=[]),
        response("SEARCH_IDS", provider="GMAIL", message_ids=["m1", "m2"]),
        response("ARCHIVE_IDS", provider="GMAIL", archived_ids=["m1"], failed_ids=["m2"]),
        response("SEARCH_IDS", provider="GMAIL", message_ids=[]),
        response("GET_LABEL_COUNTS", provider="GMAIL", labels={"INBOX": {"messagesTotal": 2, "messagesUnread": 2}}),
    ])
    receipt = M.run(broker)
    assert receipt["state"] == "PARTIAL_ARCHIVE_FAILURE"
    assert receipt["archive_failed_ids"] == ["m2"]


def test_broker_rejects_credential_export(monkeypatch):
    class Done:
        returncode = 0
        stdout = '{"schema":"stegverse.native-email-broker-response/v1","operation":"SEARCH_IDS","credential_authority":"TV/TVC","credential_material_exported":true,"provider_operation_authority_transferred":false,"message_ids":[]}'
    monkeypatch.setattr(M.subprocess, "run", lambda *a, **k: Done())
    try:
        M.Broker(["mail-broker"]).call("SEARCH_IDS")
    except RuntimeError as exc:
        assert "exported credential material" in str(exc)
    else:
        raise AssertionError("credential export must fail closed")
