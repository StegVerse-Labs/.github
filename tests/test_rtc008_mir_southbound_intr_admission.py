from __future__ import annotations

import hashlib
import importlib.util
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
        "predecessor_transition_id": "RTC-STEGVERSE-EGRESS-007",
        "predecessor_master_records_state": "RECORDED",
        "predecessor_master_records_reconstruction_status": "PASS",
        "predecessor_master_records_required_evidence_validation_status": "PASS",
        "predecessor_master_records_receipt_sha256": "5" * 64,
        "predecessor_master_records_reconstructed_receipt_sha256": "5" * 64,
        "predecessor_master_records_digest_equal": True,
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
    assert receipt["prior_state_ref_or_hash"] == "5" * 64
    assert [x["evidence_type"] for x in receipt["required_evidence_manifest"]] == [
        "RTC007_MASTER_RECORDS_CLOSURE",
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


def _load_return_consumer():
    path = Path(__file__).resolve().parents[1] / "scripts" / "consume_kv_publisher_return_materialization_request.py"
    spec = importlib.util.spec_from_file_location("rtc008_return_consumer", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Response:
    def __init__(self, value):
        self.raw = json.dumps(value, sort_keys=True).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.raw


def test_rtc007_continuation_submits_exact_rtc008_to_existing_shared_ingress():
    consumer = _load_return_consumer()
    req = request()
    expected = {
        "schema": consumer.MIR_RTC008_RECEIPT_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "materialization_id": req["materialization_id"],
        "request_hash": req["request_hash"],
        "transport_intent_hash": req["transport_intent_hash"],
        "payload_hash": req["payload_hash"],
        "operation_id": req["operation_id"],
        "packet_id": req["packet_id"],
        "transport_origin": "TVC_RELAY_EGRESS",
        "transport_authorization_id": "TVC-RTC008-ALLOW-001",
        "master_records_state": "RECORDED",
        "master_records_reconstruction_status": "PASS",
        "master_records_required_evidence_validation_status": "PASS",
        "master_records_receipt_sha256": "a" * 64,
        "master_records_reconstructed_receipt_sha256": "a" * 64,
        "rtc008_evidence_complete": True,
        "far_side_transition_observed": False,
        "caller_consequence_observed": False,
    }
    captured = {}

    def opener(http_request, timeout):
        captured["url"] = http_request.full_url
        captured["data"] = http_request.data
        captured["headers"] = dict(http_request.header_items())
        captured["timeout"] = timeout
        return _Response(expected)

    result = consumer._submit_rtc008_materialization(
        req,
        env={
            consumer.MIR_RTC008_INGRESS_ENV: "http://127.0.0.1:8765/intr/materialization",
            consumer.MIR_RTC008_AUTH_ENV: "TVC-RTC008-ALLOW-001",
        },
        opener=opener,
    )
    assert result == expected
    assert captured["data"] == consumer.canonical(req)
    assert captured["url"] == "http://127.0.0.1:8765/intr/materialization"
    assert captured["headers"]["X-stegverse-transport-origin"] == "TVC_RELAY_EGRESS"
    assert captured["headers"]["X-stegverse-authorization-id"] == "TVC-RTC008-ALLOW-001"
    assert captured["headers"]["X-stegverse-payload-sha256"] == hashlib.sha256(consumer.canonical(req)).hexdigest()
    assert captured["timeout"] == 10.0


def test_rtc008_submission_fails_closed_without_existing_authorization():
    consumer = _load_return_consumer()
    with pytest.raises(consumer.KVPublisherReturnError, match="existing TVC relay authorization missing"):
        consumer._submit_rtc008_materialization(
            request(),
            env={consumer.MIR_RTC008_INGRESS_ENV: "http://127.0.0.1:8765/intr/materialization"},
            opener=lambda *_args, **_kwargs: None,
        )


def test_rtc008_submission_fails_closed_on_master_records_digest_mismatch():
    consumer = _load_return_consumer()
    req = request()
    response = {
        "schema": consumer.MIR_RTC008_RECEIPT_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "materialization_id": req["materialization_id"],
        "request_hash": req["request_hash"],
        "transport_intent_hash": req["transport_intent_hash"],
        "payload_hash": req["payload_hash"],
        "operation_id": req["operation_id"],
        "packet_id": req["packet_id"],
        "transport_origin": "TVC_RELAY_EGRESS",
        "transport_authorization_id": "TVC-RTC008-ALLOW-001",
        "master_records_state": "RECORDED",
        "master_records_reconstruction_status": "PASS",
        "master_records_required_evidence_validation_status": "PASS",
        "master_records_receipt_sha256": "a" * 64,
        "master_records_reconstructed_receipt_sha256": "b" * 64,
        "rtc008_evidence_complete": True,
        "far_side_transition_observed": False,
        "caller_consequence_observed": False,
    }
    with pytest.raises(consumer.KVPublisherReturnError, match="RTC008 Master Records digest mismatch"):
        consumer._submit_rtc008_materialization(
            req,
            env={
                consumer.MIR_RTC008_INGRESS_ENV: "http://localhost:8765/intr/materialization",
                consumer.MIR_RTC008_AUTH_ENV: "TVC-RTC008-ALLOW-001",
            },
            opener=lambda *_args, **_kwargs: _Response(response),
        )


def test_rtc008_rejects_nonclosed_rtc007_predecessor(monkeypatch, tmp_path: Path):
    req = request()
    req["predecessor_master_records_required_evidence_validation_status"] = "FAIL"
    req.pop("request_hash")
    req["request_hash"] = ingress.sha_uri(req)
    raw = canonical(req)
    with pytest.raises(ValueError, match="mir_southbound_predecessor_required_evidence_not_pass"):
        ingress.admit_mir_southbound(runtime_root=tmp_path, body=raw, headers=headers(raw))
