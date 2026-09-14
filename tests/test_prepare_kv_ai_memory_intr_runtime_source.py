from __future__ import annotations

from pathlib import Path

import pytest

from scripts import prepare_kv_ai_memory_intr_runtime_source as prep

ROOT = Path(__file__).resolve().parents[1]


def test_prepare_installs_only_into_local_source_copy(tmp_path: Path):
    source = tmp_path / "repo"
    router = source / prep.ROUTER_REL
    router.parent.mkdir(parents=True)
    original = (ROOT / prep.ROUTER_REL).read_text(encoding="utf-8")
    router.write_text(original, encoding="utf-8")

    result = prep.prepare(source)
    assert result["state"] in {"ROUTE_INSTALLED_LOCAL_SOURCE", "ROUTE_ALREADY_INSTALLED"}
    assert result["listener_started"] is False
    assert result["intr_admission_observed"] is False
    assert result["worker_claim_or_fence_minted"] is False
    assert result["authority_effect"] == "NONE_SOURCE_PREPARATION_ONLY"
    installed = router.read_text(encoding="utf-8")
    assert '"KV:AI-MemoryPacketAdmission"' in installed
    assert "kv_ai_memory_intr.admit(" in installed
    assert "ThreadingHTTPServer" in installed

    second = prep.prepare(source)
    assert second["state"] == "ROUTE_ALREADY_INSTALLED"
    assert second["source_changed"] is False


def test_check_fails_closed_when_route_missing(tmp_path: Path):
    source = tmp_path / "repo"
    router = source / prep.ROUTER_REL
    router.parent.mkdir(parents=True)
    router.write_text((ROOT / prep.ROUTER_REL).read_text(encoding="utf-8"), encoding="utf-8")
    if '"KV:AI-MemoryPacketAdmission"' not in router.read_text(encoding="utf-8"):
        with pytest.raises(RuntimeError, match="route_not_installed"):
            prep.prepare(source, check=True)
