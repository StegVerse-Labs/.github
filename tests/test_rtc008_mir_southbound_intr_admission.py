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


def test_rtc008_admission_is_authorized_by_intr_without_master_records_organization_record(tmp_path: Path):
    req = request()
    raw = canonical(req)
    result = ingress.admit_mir_southbound(runtime_root=tmp_path, body=raw, headers=headers(raw))
    assert result["state"] == "INGRESS_ADMITTED"
    assert result["rtc008_evidence_complete"] is True
    assert result["master_records_reconstruction_available"] is True
    assert result["master_records_authority_effect"] == "NONE_RECONSTRUCTION_ONLY"
    assert result["far_side_transition_observed"] is False
    assert result["caller_consequence_observed"] is False

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


AUTH_ENV = {"STEGVERSE_TVC_RELAY_AUTHORIZATION_ID": "TVC-RTC008-ALLOW-001"}


def test_rtc008_is_admitted_through_the_existing_durable_queue_without_a_listener(tmp_path: Path):
    """No listener, socket or timeout: the existing write-once ingress admits in-process."""
    consumer = _load_return_consumer()
    req = request()
    admitted = consumer._submit_rtc008_materialization(req, runtime_root=tmp_path, env=AUTH_ENV)
    assert admitted["state"] == "INGRESS_ADMITTED"
    assert admitted["request_hash"] == req["request_hash"]
    assert admitted["transport_authorization_id"] == "TVC-RTC008-ALLOW-001"
    assert admitted["write_once_persisted"] is True
    assert admitted["far_side_transition_observed"] is False
    assert "master_records_state" not in admitted
    queued = json.loads(Path(admitted["queue_ref"]).read_text(encoding="utf-8"))
    assert queued == req
    # Re-admitting the identical request is idempotent at the write-once queue.
    again = consumer._submit_rtc008_materialization(req, runtime_root=tmp_path, env=AUTH_ENV)
    assert again["intr_admission_receipt_sha256"] == admitted["intr_admission_receipt_sha256"]


def test_rtc008_projection_is_queue_admission_only(tmp_path: Path):
    consumer = _load_return_consumer()
    req = request()
    admitted = consumer._submit_rtc008_materialization(req, runtime_root=tmp_path, env=AUTH_ENV)
    projected = consumer.rtc008_ingress_projection(admitted)
    assert projected["rtc008_ingress_state"] == "INGRESS_ADMITTED"
    assert projected["rtc008_request_hash"] == req["request_hash"]
    assert projected["rtc008_write_once_persisted"] is True
    assert json.loads(Path(projected["rtc008_queue_ref"]).read_text(encoding="utf-8")) == req
    assert projected["rtc008_intr_admission_receipt_sha256"] == admitted["intr_admission_receipt_sha256"]
    assert projected["rtc008_downstream_execution_observed"] is False
    assert projected["rtc009_far_side_transition_observed"] is False
    assert not any(key.startswith("rtc008_master_records") for key in projected)


def test_rtc008_consumer_has_no_network_receiver_dependency():
    consumer = _load_return_consumer()
    source = Path(consumer.__file__).read_text(encoding="utf-8")
    assert "urlopen" not in source
    assert "timeout=" not in source


def test_rtc008_submission_fails_closed_without_existing_authorization(tmp_path: Path):
    consumer = _load_return_consumer()
    with pytest.raises(consumer.KVPublisherReturnError, match="existing TVC relay authorization missing"):
        consumer._submit_rtc008_materialization(request(), runtime_root=tmp_path, env={})


def test_rtc008_refused_admission_is_a_typed_refusal(tmp_path: Path):
    consumer = _load_return_consumer()
    req = request()
    req["request_hash"] = "sha256:" + "0" * 64
    with pytest.raises(consumer.KVPublisherReturnError, match="RTC008 InTr admission refused"):
        consumer._submit_rtc008_materialization(req, runtime_root=tmp_path, env=AUTH_ENV)


def test_rtc008_master_records_fields_are_evidence_not_a_gate(tmp_path: Path):
    consumer = _load_return_consumer()
    req = request()

    def admit(*, runtime_root, body, headers):
        admitted = ingress.admit_mir_southbound(runtime_root=runtime_root, body=body, headers=headers)
        # Mismatched Master Records digests are reconstruction evidence only.
        return {**admitted, "master_records_receipt_sha256": "a" * 64,
                "master_records_reconstructed_receipt_sha256": "b" * 64}

    admitted = consumer._submit_rtc008_materialization(req, runtime_root=tmp_path, env=AUTH_ENV, admit=admit)
    assert admitted["master_records_reconstructed_receipt_sha256"] == "b" * 64


def test_missing_exact_rtc008_admission_digest_fails_closed(tmp_path: Path):
    consumer = _load_return_consumer()
    req = request()

    def admit(*, runtime_root, body, headers):
        admitted = ingress.admit_mir_southbound(runtime_root=runtime_root, body=body, headers=headers)
        admitted.pop("intr_admission_receipt_sha256")
        return admitted

    with pytest.raises(consumer.KVPublisherReturnError, match="exact ingress admission digest missing"):
        consumer._submit_rtc008_materialization(req, runtime_root=tmp_path, env=AUTH_ENV, admit=admit)


def test_sdk_return_consumer_retains_exact_failed_invocation_diagnostic(tmp_path: Path):
    consumer = _load_return_consumer()
    mid = "INTR-MAT-" + "8" * 24
    request_path = tmp_path / consumer.REQUEST_DIR / f"{mid}.json"
    request_path.parent.mkdir(parents=True)
    request_path.write_text(json.dumps({
        "downstream_owner_ref": consumer.SDK_DOWNSTREAM_OWNER,
        "request_hash": "sha256:" + "f" * 64,
    }), encoding="utf-8")
    error = consumer.KVPublisherReturnError("RTC008 exact ingress admission digest missing")
    first = consumer.retain_blocked_consumption(tmp_path, mid, error)
    second = consumer.retain_blocked_consumption(tmp_path, mid, error)
    assert first == second
    path = tmp_path / first["diagnostic_receipt_ref"]
    assert path.is_file()
    retained = json.loads(path.read_text(encoding="utf-8"))
    assert retained["state"] == "BLOCKED"
    assert retained["request_hash"] == "sha256:" + "f" * 64
    assert retained["downstream_owner_ref"] == consumer.SDK_DOWNSTREAM_OWNER
    assert retained["first_failed_governed_transition"] == "UNKNOWN_NOT_AUTHENTICALLY_RECONSTRUCTED"
    assert retained["rtc008_admission_observed"] == "UNKNOWN_NOT_AUTHENTICALLY_RECONSTRUCTED"
    assert retained["master_records_organization_record_claimed"] is False
    assert retained["authority_effect"] == "NONE_DIAGNOSTIC_ONLY"
    basis = {key: val for key, val in retained.items() if key != "diagnostic_sha256"}
    assert retained["diagnostic_sha256"] == consumer.sha(basis)
    assert (tmp_path / consumer.SDK_RECEIPT_DIR / "latest.blocked.json").read_bytes() == path.read_bytes()


def test_sdk_return_consumer_retains_missing_request_failure_without_inventing_transition(tmp_path: Path):
    consumer = _load_return_consumer()
    mid = "INTR-MAT-" + "9" * 24
    result = consumer.retain_blocked_consumption(
        tmp_path, mid, RuntimeError("sensitive runtime error detail must not be persisted")
    )
    assert result["state"] == "BLOCKED"
    assert result["request_present"] is False
    assert result["downstream_owner_ref"] is None
    assert result["reason_code"] == "RuntimeError"
    assert result["caller_consequence_observed"] == "UNKNOWN_NOT_AUTHENTICALLY_RECONSTRUCTED"
    assert (tmp_path / consumer.RECEIPT_DIR / "latest.blocked.json").exists()
