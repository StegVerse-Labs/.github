from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import submit_kv_ai_memory_intr_local as submitter
from workers import kv_ai_memory_intr_profile as profile
from workers import kv_ai_memory_intr_transport as transport


def packet() -> dict:
    entries = [{
        "entry_id": "entry-1",
        "source_kv_instance_id": "kv-1",
        "relative_path": "01_Notes/example.md",
        "content": "remember this",
        "content_sha256": hashlib.sha256(b"remember this").hexdigest(),
        "provenance_ref": "kv://kv-1/01_Notes/example.md",
    }]
    return {
        "schema": "stegverse.kv.ai-memory-context-packet/v1",
        "packet_id": "KVMEM-fixture-1",
        "request_id": "req-1",
        "purpose": "continuity",
        "kv_class": "PERSONAL_KV",
        "authority_domain": "PERSON",
        "consumer_ai_role": "PERSONAL_ASSISTANT_AI",
        "entries": entries,
        "selected_item_count": 1,
        "selected_content_bytes": len(b"remember this"),
        "entries_sha256": hashlib.sha256(profile.canonical(entries)).hexdigest(),
        "intr_admission_required": True,
        "secret_material_included": False,
        "cross_authority_content_included": False,
        "model_is_authority": False,
        "context_transfers_authority": False,
        "authority_effect": "NONE_CONTEXT_ONLY",
    }


def admission_for(p: dict) -> dict:
    body = {
        "schema": profile.RECEIPT_SCHEMA,
        "state": "INGRESS_ADMITTED",
        "disposition": "ALLOW",
        "task_id": profile.TASK_ID,
        "packet_id": p["packet_id"],
        "packet_sha256": profile.packet_sha256(p),
        "entries_sha256": p["entries_sha256"],
        "transport_origin": "STEGOS_RESIDENT_LOCAL",
        "transport_payload_sha256": "sha256:" + "1" * 64,
        "exact_packet_validated": True,
        "private_packet_persisted_by_ingress": False,
        "provider_request_materialized": False,
        "provider_ingress_admission_observed": False,
        "provider_execution_observed": False,
        "kv_writeback_observed": False,
        "claim_or_fence_minted": False,
        "credential_material_present": False,
        "heartbeat_grants_execution_authority": False,
        "request_grants_execution_authority": False,
        "authority_effect": "NONE_INGRESS_ADMISSION_ONLY",
        "admitted_at": "2026-09-14T00:00:00Z",
    }
    return {**body, "receipt_hash": profile.sha_uri(body)}


def test_profile_admits_exact_packet_without_runtime_claims(tmp_path: Path):
    p = packet()
    submission = submitter.build_submission(p)
    result = profile.admit(runtime_root=tmp_path, payload=submission, transport_payload_sha256="sha256:" + "1" * 64)
    assert result["disposition"] == "ALLOW"
    assert result["packet_sha256"] == profile.packet_sha256(p)
    assert result["provider_request_materialized"] is False
    assert result["provider_execution_observed"] is False
    assert result["kv_writeback_observed"] is False
    assert result["claim_or_fence_minted"] is False


def test_profile_rejects_tampered_packet():
    p = packet()
    submission = submitter.build_submission(p)
    submission["packet"]["entries"][0]["content"] = "tampered"
    with pytest.raises(ValueError):
        profile.validate_submission(submission)


def test_resident_transport_has_no_tvc_relay_authorization():
    body = b"{}"
    headers = {
        "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": "STEGOS_RESIDENT_LOCAL",
        "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest(),
    }
    result = transport.validate_headers(headers, body)
    assert result["authorization_id"] is None
    bad = dict(headers)
    bad["X-StegVerse-Authorization-Id"] = "fake"
    with pytest.raises(ValueError):
        transport.validate_headers(bad, body)


def test_submitter_stages_only_valid_exact_admission(tmp_path: Path):
    root = tmp_path / "bound"
    (root / "inputs").mkdir(parents=True)
    p = packet()
    (root / submitter.PACKET_REL).write_text(json.dumps(p), encoding="utf-8")
    admission = admission_for(p)

    class Response:
        status = 202
        def read(self):
            return json.dumps(admission).encode("utf-8")
        def getcode(self):
            return self.status

    captured = {}
    def opener(request, timeout=0):
        captured["headers"] = dict(request.header_items())
        captured["body"] = request.data
        return Response()

    result = submitter.submit(
        root,
        env={"STEGVERSE_UNIVERSAL_INTR_INGRESS_URL": "http://127.0.0.1:7777/intr/materialization"},
        opener=opener,
    )
    assert result["state"] == "AUTHENTIC_INGRESS_ADMISSION_STAGED"
    staged = json.loads((root / submitter.ADMISSION_REL).read_text())
    assert staged == admission
    sent = json.loads(captured["body"].decode("utf-8"))
    assert sent["packet_sha256"] == profile.packet_sha256(p)
    assert sent["request_grants_execution_authority"] is False


def test_submitter_rejects_non_loopback_and_hosted(tmp_path: Path):
    root = tmp_path / "bound"
    (root / "inputs").mkdir(parents=True)
    (root / submitter.PACKET_REL).write_text(json.dumps(packet()), encoding="utf-8")
    with pytest.raises(RuntimeError):
        submitter.submit(root, env={"STEGVERSE_UNIVERSAL_INTR_INGRESS_URL": "https://example.com/intr/materialization"})
    with pytest.raises(RuntimeError):
        submitter.submit(root, env={"CI": "true", "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL": "http://127.0.0.1:7777/intr/materialization"})
