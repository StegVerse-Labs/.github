from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from workers import universal_intr_profiled_ingress as ingress


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def request():
    body = {
        "schema": "stegverse.universal-intr-materialization-request/v1",
        "materialization_id": "INTR-MAT-" + "1" * 24,
        "state": "QUEUED_FOR_EVENT_EPHEMERAL_MATERIALIZATION",
        "transport_schema": "stegverse.universal-intr-transport/v1",
        "transport_protocol": "InTr",
        "transport_intent_hash": "sha256:" + "2" * 64,
        "operation_id": "rtc007-return-egress",
        "packet_id": "INTR-" + "3" * 24,
        "payload_hash": "sha256:" + "4" * 64,
        "payload_ref": "runtime://sdk-return-bindings/example.json",
        "destination": {"boundary": "EXTERNAL_SYSTEM", "subsystem": "MIR:NODE_MIRROR"},
        "boundary_path": ["STEGOS_ECOSYSTEM", "EXTERNAL_SYSTEM"],
        "downstream_owner_ref": "StegVerse-Labs/StegOS#389",
        "event_triggered": True,
        "always_on_receiver_required": False,
        "second_user_device_required": False,
        "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "exact_packet_transport_retry_allowed": True,
        "blind_consequence_retry_allowed": False,
        "interlock_required": True,
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "transport_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_transfer": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    }
    body["request_hash"] = ingress.sha_uri(body)
    return body


def headers(raw: bytes):
    return {
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": "TVC_RELAY_EGRESS",
        "X-StegVerse-Authorization-Id": "TVC-RTC008-ALLOW-001",
        "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest(),
        "Content-Type": "application/json",
    }


def test_rtc008_admission_is_canonically_custodied(monkeypatch, tmp_path: Path):
    captured = {}

    def fake_submit(receipt):
        captured["receipt"] = receipt
        digest = ingress.sha_uri(dict(receipt)).split(":", 1)[1]
        return {
            "state": "RECORDED",
            "reconstruction_status": "PASS",
            "required_evidence_validation_status": "PASS",
            "receipt_sha256": digest,
            "reconstructed_receipt_sha256": digest,
            "master_records_grants_transition_authority": False,
        }

    monkeypatch.setattr(ingress, "submit_state_receipt", fake_submit)
    req = request()
    raw = canonical(req)
    result = ingress.admit_mir_southbound(runtime_root=tmp_path, body=raw, headers=headers(raw))

    assert result["state"] == "INGRESS_ADMITTED"
    assert result["rtc008_evidence_complete"] is True
    assert result["master_records_state"] == "RECORDED"
    assert result["master_records_reconstruction_status"] == "PASS"
    assert result["master_records_required_evidence_validation_status"] == "PASS"
    assert result["far_side_transition_observed"] is False
    assert result["caller_consequence_observed"] is False
    receipt = captured["receipt"]
    assert receipt["transition_id"] == "RTC-INTERLOCK-INTR-TRANSPORT-008"
    assert receipt["transition_sequence"] == 8
    assert receipt["transition_outcome"] == "COMPLETED"
    assert [x["evidence_type"] for x in receipt["required_evidence_manifest"]] == [
        "UNIVERSAL_INTR_MATERIALIZATION_REQUEST",
        "MIR_SOUTHBOUND_INTR_ADMISSION_RECEIPT",
    ]


def test_rtc008_admission_fails_closed_without_master_records_pass(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        ingress,
        "submit_state_receipt",
        lambda _receipt: {
            "state": "BOUNDARY",
            "reason": "CANONICAL_MASTER_RECORDS_CUSTODY_SURFACE_UNAVAILABLE",
            "authority_effect": "NONE",
        },
    )
    req = request()
    raw = canonical(req)
    with pytest.raises(ValueError, match="rtc008_master_records_not_recorded"):
        ingress.admit_mir_southbound(runtime_root=tmp_path, body=raw, headers=headers(raw))
