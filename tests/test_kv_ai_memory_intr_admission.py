from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts import install_kv_ai_memory_universal_intr_route as installer
from scripts import submit_kv_ai_memory_packet_local as submitter
from workers import kv_ai_memory_intr_profile as profile
from workers import kv_ai_memory_intr_transport as transport

ROOT = Path(__file__).resolve().parents[1]


def packet():
    entry = {
        "entry_id": "e1",
        "source_kv_instance_id": "kvi_fixture",
        "relative_path": "01_Notes/a.md",
        "title": "A",
        "content": "remember this",
        "content_sha256": hashlib.sha256(b"remember this").hexdigest(),
        "tags": ["memory"],
        "retention_class": "DURABLE",
        "provenance_ref": "kv://fixture/a",
    }
    entries = [entry]
    canonical = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {
        "schema": "stegverse.kv.ai-memory-context-packet/v1",
        "packet_id": "KVMEM-1234567890abcdef12345678",
        "request_id": "req-1",
        "request_sha256": "1" * 64,
        "kv_class": "PERSONAL_KV",
        "authority_domain": "PERSON",
        "consumer_ai_role": "PERSONAL_ASSISTANT_AI",
        "purpose": "continuity",
        "entries": entries,
        "entries_sha256": hashlib.sha256(canonical).hexdigest(),
        "selected_item_count": 1,
        "selected_content_bytes": len(b"remember this"),
        "secret_material_included": False,
        "cross_authority_content_included": False,
        "intr_admission_required": True,
        "model_is_authority": False,
        "context_transfers_authority": False,
        "authority_effect": "NONE_CONTEXT_ONLY",
    }


def submission(value):
    return {
        "schema": profile.SUBMISSION_SCHEMA,
        "task_id": profile.TASK_ID,
        "packet_id": value["packet_id"],
        "packet_sha256": profile.packet_sha256(value),
        "packet": value,
        "transport_origin": "STEGOS_RESIDENT_LOCAL",
        "request_grants_execution_authority": False,
        "claim_or_fence_minted": False,
        "credential_material_present": False,
        "authority_effect": "NONE_SUBMISSION_ONLY",
    }


def test_profile_admits_exact_packet_without_execution_authority(tmp_path):
    value = packet()
    result = profile.admit(runtime_root=tmp_path, payload=submission(value), transport_payload_sha256="sha256:" + "a" * 64)
    assert result["disposition"] == "ALLOW"
    assert result["packet_sha256"] == profile.packet_sha256(value)
    assert result["claim_or_fence_minted"] is False
    assert result["provider_request_materialized"] is False
    assert result["provider_ingress_admission_observed"] is False
    assert result["provider_execution_observed"] is False
    assert result["kv_writeback_observed"] is False
    assert result["receipt_hash"].startswith("sha256:")
    persisted = json.loads((tmp_path / profile.RECEIPT_DIR / f"{value['packet_id']}.json").read_text())
    assert persisted == result


def test_profile_rejects_tampered_packet_hash(tmp_path):
    value = packet()
    payload = submission(value)
    payload["packet_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="packet_hash_mismatch"):
        profile.admit(runtime_root=tmp_path, payload=payload, transport_payload_sha256="sha256:" + "a" * 64)


def test_transport_is_resident_local_and_credential_free():
    body = b"{}"
    digest = hashlib.sha256(body).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr",
        "X-StegVerse-Transport-Origin": "STEGOS_RESIDENT_LOCAL",
        "X-StegVerse-Payload-SHA256": digest,
    }
    result = transport.validate_headers(headers, body)
    assert result["authorization_id"] is None
    bad = dict(headers)
    bad["X-StegVerse-Authorization-Id"] = "forbidden"
    with pytest.raises(ValueError, match="cannot_claim_tvc"):
        transport.validate_headers(bad, body)


def _no_network(*_args, **_kwargs):
    raise AssertionError("in-process admission must not open a socket or listener")


def _staged(tmp_path, value=None):
    root = tmp_path / "state"
    (root / "inputs").mkdir(parents=True)
    value = packet() if value is None else value
    (root / submitter.PACKET_REL).write_text(json.dumps(value), encoding="utf-8")
    return root, value


def _admit_then(mutate):
    def admit(*, runtime_root, body, headers):
        receipt = submitter._admit(runtime_root=runtime_root, body=body, headers=headers)
        return mutate(dict(receipt))
    return admit


def test_submitter_writes_only_returned_exact_admission(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", _no_network)
    monkeypatch.setattr("socket.socket", _no_network)
    monkeypatch.setattr("socket.create_connection", _no_network)
    root, value = _staged(tmp_path)
    result = submitter.submit(root, runtime_root=tmp_path / "ingress", env={"HOME": str(tmp_path)})
    assert result["state"] == "AUTHENTIC_INGRESS_ADMISSION_WRITTEN"
    assert result["ingress_state"] == "INGRESS_ADMITTED"
    assert result["in_process_write_once_admission"] is True
    assert result["receiver_liveness_predicate"] is False
    admission = json.loads((root / submitter.ADMISSION_REL).read_text())
    assert admission["disposition"] == "ALLOW"
    assert admission["packet_sha256"] == profile.packet_sha256(value)
    assert admission["receipt_hash"].startswith("sha256:")
    assert admission["ingress_receipt"]["exact_packet_validated"] is True
    assert admission["ingress_receipt"]["authority_effect"] == "NONE_INGRESS_ADMISSION_ONLY"
    queued = Path(result["ingress_receipt_ref"])
    assert queued.parent == tmp_path / "ingress" / profile.RECEIPT_DIR
    assert json.loads(queued.read_text())["receipt_hash"] == admission["receipt_hash"]


def test_submitter_absent_listener_does_not_block_without_configured_endpoint(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", _no_network)
    monkeypatch.setattr("socket.socket", _no_network)
    root, _value = _staged(tmp_path)
    result = submitter.submit(root, runtime_root=tmp_path / "ingress", env={"HOME": str(tmp_path)})
    assert result["state"] == "AUTHENTIC_INGRESS_ADMISSION_WRITTEN"
    assert result["state"] != "INGRESS_NOT_READY"
    assert result["admission_written"] is True


def test_submitter_same_packet_admitted_twice_is_idempotent(tmp_path):
    root, _value = _staged(tmp_path)
    first = submitter.submit(root, runtime_root=tmp_path / "ingress", env={"HOME": str(tmp_path)})
    admission = (root / submitter.ADMISSION_REL).read_bytes()
    queued = Path(first["ingress_receipt_ref"]).read_bytes()
    second = submitter.submit(root, runtime_root=tmp_path / "ingress", env={"HOME": str(tmp_path)})
    assert second["receipt_hash"] == first["receipt_hash"]
    assert (root / submitter.ADMISSION_REL).read_bytes() == admission
    assert Path(first["ingress_receipt_ref"]).read_bytes() == queued


def test_submitter_malformed_packet_is_refused_typed_without_effect(tmp_path):
    value = packet()
    value["entries_sha256"] = "0" * 64
    root, _value = _staged(tmp_path, value)
    with pytest.raises(RuntimeError, match="^intr_admission_refused:"):
        submitter.submit(root, runtime_root=tmp_path / "ingress", env={"HOME": str(tmp_path)})
    assert not (root / submitter.ADMISSION_REL).exists()
    assert not (tmp_path / "ingress" / profile.RECEIPT_DIR).exists()


def test_submitter_ingress_admitted_never_claims_downstream_completion(tmp_path):
    root, _value = _staged(tmp_path)
    result = submitter.submit(root, runtime_root=tmp_path / "ingress", env={"HOME": str(tmp_path)})
    assert result["provider_request_materialized"] is False
    assert result["provider_execution_observed"] is False
    assert result["kv_writeback_observed"] is False
    receipt = json.loads((root / submitter.ADMISSION_REL).read_text())["ingress_receipt"]
    assert receipt["provider_execution_observed"] is False
    assert receipt["kv_writeback_observed"] is False


def test_submitter_rejects_tampered_receipt_hash(tmp_path):
    root, _value = _staged(tmp_path)

    def tamper(receipt):
        receipt["receipt_hash"] = "sha256:" + "0" * 64
        return receipt

    with pytest.raises(RuntimeError, match="receipt_hash_mismatch"):
        submitter.submit(root, runtime_root=tmp_path / "ingress", env={"HOME": str(tmp_path)}, admit=_admit_then(tamper))
    assert not (root / submitter.ADMISSION_REL).exists()


def test_submitter_rejects_promoted_provider_execution_claim(tmp_path):
    root, _value = _staged(tmp_path)

    def promote(receipt):
        receipt["provider_execution_observed"] = True
        body = dict(receipt)
        body.pop("receipt_hash")
        receipt["receipt_hash"] = submitter.receipt_sha256(body)
        return receipt

    with pytest.raises(RuntimeError, match="provider_execution_claim_forbidden"):
        submitter.submit(root, runtime_root=tmp_path / "ingress", env={"HOME": str(tmp_path)}, admit=_admit_then(promote))


def test_submitter_opens_no_loopback_connection():
    source = (ROOT / "scripts/submit_kv_ai_memory_packet_local.py").read_text(encoding="utf-8")
    for forbidden in ("urlopen", "urllib.request", "http.client", "import socket", "socket.", "timeout=", "Request("):
        assert forbidden not in source
    assert "profile.admit(" in source and "transport.validate_headers(" in source


def test_submitter_rejects_non_loopback_and_hosted(tmp_path):
    root = tmp_path / "state"
    (root / "inputs").mkdir(parents=True)
    (root / submitter.PACKET_REL).write_text(json.dumps(packet()), encoding="utf-8")
    with pytest.raises(RuntimeError, match="loopback"):
        submitter.submit(root, runtime_root=tmp_path / "ingress", env={"STEGVERSE_UNIVERSAL_INTR_INGRESS_URL": "https://example.com/intr/materialization"})
    with pytest.raises(RuntimeError, match="hosted_environment_forbidden"):
        submitter.submit(root, env={"CI": "true", "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL": "http://127.0.0.1:7777/intr/materialization"})


def test_route_installer_is_idempotent_and_reuses_shared_listener():
    source = (ROOT / "workers/universal_intr_profiled_ingress.py").read_text(encoding="utf-8")
    transformed = installer.transform(source)
    assert '"KV:AI-MemoryPacketAdmission"' in transformed
    assert "kv_ai_memory_intr.admit(" in transformed
    assert "ThreadingHTTPServer" in transformed
    assert "X-StegVerse-Authorization-Id" not in (ROOT / "scripts/install_kv_ai_memory_universal_intr_route.py").read_text(encoding="utf-8")
    assert installer.transform(transformed) == transformed
