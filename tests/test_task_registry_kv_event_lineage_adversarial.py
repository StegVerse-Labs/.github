"""Adversarial exact-hash and predecessor-chain checks for the existing sovereign-KV projector.

Synthetic events are test fixtures only; no provider or resident operation is performed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from task_registry_checkin_event_history import sha256_value
from project_task_registry_event_to_sovereign_kv import (
    build_request,
    load_event,
    validate_receipt,
)


@pytest.fixture
def events(tmp_path):
    ledger = tmp_path / "canonical-history.jsonl"
    event_file = tmp_path / "exact-event.json"

    def make_event(predecessor, session):
        event = {
            "schema": "stegverse.task-registry-checkin-event/v1",
            "event_type": "CHECK_IN",
            "task_id": "SYNTHETIC-TEST-ONLY",
            "session_id": session,
            "event_at": "2026-09-24T10:00:00Z",
            "context": {},
            "registry_disposition": "CONTINUE",
            "registry_disposition_sha256": "sha256:" + "a" * 64,
            "coordination_state": "ACTIVE",
            "predecessor_event_sha256": predecessor,
            "authority_effect": "NONE",
        }
        event["event_sha256"] = sha256_value(event)
        return event

    def write(*rows):
        ledger.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        event_file.write_text(json.dumps(rows[-1]), encoding="utf-8")

    first = make_event(None, "session-a")
    second = make_event(first["event_sha256"], "session-b")
    write(first, second)
    return ledger, event_file, first, second, make_event, write


def test_valid_second_event_has_exact_predecessor(events):
    ledger, event_file, first, second, _, _ = events
    actual = load_event(event_file, ledger)
    assert actual == second
    assert build_request(actual)["predecessor_event_sha256"] == first["event_sha256"]


def test_missing_ledger_fails_closed(events, tmp_path):
    _, event_file, *_ = events
    with pytest.raises(SystemExit, match="ledger unavailable"):
        load_event(event_file, tmp_path / "not-present.jsonl")


def test_changed_event_payload_fails_digest(events):
    ledger, event_file, _, second, *_ = events
    event_file.write_text(json.dumps({**second, "task_id": "FORGED"}), encoding="utf-8")
    with pytest.raises(SystemExit, match="event hash mismatch"):
        load_event(event_file, ledger)


def test_forged_hash_fails_digest(events):
    ledger, event_file, _, second, *_ = events
    event_file.write_text(json.dumps({**second, "event_sha256": "sha256:" + "0" * 64}), encoding="utf-8")
    with pytest.raises(SystemExit, match="event hash mismatch"):
        load_event(event_file, ledger)


def test_broken_predecessor_fails_even_if_digest_recomputed(events):
    ledger, event_file, first, _, make_event, write = events
    second = make_event("sha256:" + "0" * 64, "session-b")
    write(first, second)
    with pytest.raises(SystemExit, match="predecessor"):
        load_event(event_file, ledger)


def test_valid_but_unretained_event_is_denied(events):
    ledger, event_file, first, _, make_event, _ = events
    unretained = make_event(first["event_sha256"], "unretained")
    event_file.write_text(json.dumps(unretained), encoding="utf-8")
    with pytest.raises(SystemExit, match="absent from verified"):
        load_event(event_file, ledger)


def test_empty_ledger_fails_closed(events):
    ledger, event_file, *_ = events
    ledger.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit, match="absent from verified"):
        load_event(event_file, ledger)


def test_valid_request_never_widens_authority(events):
    ledger, event_file, _, second, *_ = events
    request = build_request(load_event(event_file, ledger))
    assert request["event_sha256"] == second["event_sha256"]
    assert request["authority_effect"] == "NONE"


def test_provider_readback_must_match_same_event(events):
    _, _, _, second, *_ = events
    request = build_request(second)
    receipt = {
        "schema": "stegverse.task-registry-sovereign-kv-projection-receipt/v1",
        "authority_effect": "NONE",
        "custody_class": "STEGVERSE_SOVEREIGN_KV",
        "event_sha256": request["event_sha256"],
        "stored_event_sha256": "sha256:forged",
        "provider_adapter_ref": "test-provider",
        "interlock_intr_receipt_ref": "test-intr",
        "kv_instance_ref": "test-instance",
    }
    with pytest.raises(SystemExit, match="stored event hash mismatch"):
        validate_receipt(receipt, request)
