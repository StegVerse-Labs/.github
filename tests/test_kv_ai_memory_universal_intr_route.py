from __future__ import annotations

from pathlib import Path

from scripts import install_kv_ai_memory_universal_intr_route as installer

ROOT = Path(__file__).resolve().parents[1]


def test_route_transform_is_fail_closed_idempotent_and_preserves_shared_listener():
    source = (ROOT / "workers/universal_intr_profiled_ingress.py").read_text(encoding="utf-8")
    installed = installer.transform(source)
    assert installer.PROFILE_IMPORT in installed
    assert installer.TRANSPORT_IMPORT in installed
    assert installer.PROFILE_TOKEN in installed
    assert "kv_ai_memory_intr.admit(" in installed
    assert "ThreadingHTTPServer" in installed
    assert "KV:KnowledgeVaultInterlock" in installed
    assert installer.transform(installed) == installed


def test_route_is_resident_local_and_does_not_create_relay_authorization():
    source = (ROOT / "scripts/install_kv_ai_memory_universal_intr_route.py").read_text(encoding="utf-8")
    assert "kv_ai_memory_intr_transport.validate_headers" in source
    assert "payload_sha256_uri" in source
    assert "X-StegVerse-Authorization-Id" not in source
