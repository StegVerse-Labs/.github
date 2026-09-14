from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request

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


def test_submitter_writes_only_returned_exact_admission(tmp_path):
    root = tmp_path / "state"
    (root / "inputs").mkdir(parents=True)
    value = packet()
    (root / submitter.PACKET_REL).write_text(json.dumps(value), encoding="utf-8")

    def opener(request: Request, *, timeout: float):
        raw = request.data
        payload = json.loads(raw.decode())
        headers = {key: val for key, val in request.header_items()}
        normalized = {
            "Content-Type": headers.get("Content-type", headers.get("Content-Type", "")),
            "X-StegVerse-Transport": headers.get("X-stegverse-transport", headers.get("X-StegVerse-Transport", "")),
            "X-StegVerse-Transport-Origin": headers.get("X-stegverse-transport-origin", headers.get("X-StegVerse-Transport-Origin", "")),
            "X-StegVerse-Payload-SHA256": headers.get("X-stegverse-payload-sha256", headers.get("X-StegVerse-Payload-SHA256", "")),
        }
        tr = transport.validate_headers(normalized, raw)
        receipt = profile.admit(runtime_root=tmp_path / "ingress", payload=payload, transport_payload_sha256=tr["payload_sha256_uri"])
        return 202, json.dumps(receipt).encode()

    result = submitter.submit(
        root,
        env={"HOME": str(tmp_path), "STEGVERSE_UNIVERSAL_INTR_INGRESS_URL": "http://127.0.0.1:7777/intr/materialization"},
        opener=opener,
    )
    assert result["state"] == "AUTHENTIC_INGRESS_ADMISSION_WRITTEN"
    admission = json.loads((root / submitter.ADMISSION_REL).read_text())
    assert admission["disposition"] == "ALLOW"
    assert admission["packet_sha256"] == profile.packet_sha256(value)
    assert admission["receipt_hash"].startswith("sha256:")


def test_submitter_waits_without_explicit_ingress(tmp_path):
    root = tmp_path / "state"
    (root / "inputs").mkdir(parents=True)
    (root / submitter.PACKET_REL).write_text(json.dumps(packet()), encoding="utf-8")
    result = submitter.submit(root, env={"HOME": str(tmp_path)})
    assert result["state"] == "INGRESS_NOT_READY"
    assert result["admission_written"] is False


def test_route_installer_is_idempotent_and_reuses_shared_listener():
    source = (ROOT / "workers/universal_intr_profiled_ingress.py").read_text(encoding="utf-8")
    transformed = installer.transform(source)
    assert '"KV:AI-MemoryPacketAdmission"' in transformed
    assert "kv_ai_memory_intr.admit(" in transformed
    assert "ThreadingHTTPServer" in transformed
    assert installer.transform(transformed) == transformed
