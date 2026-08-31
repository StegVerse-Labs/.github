from __future__ import annotations

import json
from pathlib import Path
import tempfile

from scripts import bootstrap_tvc_pr92_validation_source as bootstrap


def test_stage_writes_exact_nonsecret_request_without_systemd(tmp_path):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    result = bootstrap.stage(runtime)
    path = runtime / bootstrap.REQUEST_REL
    assert result["state"] == "HANDOFF_READY"
    assert result["reason"] == "PRIVATE_SOURCE_REQUEST_STAGED_FOR_TVC_SYSTEMD_PATH"
    assert result["systemd_service_start_requested"] is False
    assert result["consumer_provider_read_performed"] is False
    assert path.is_file()
    value = json.loads(path.read_text(encoding="utf-8"))
    assert value == bootstrap._request()
    assert value["exact_sha"] == bootstrap.EXPECTED_HEAD
    assert value["materialization_id"] == bootstrap.MATERIALIZATION_ID
    raw = path.read_text(encoding="utf-8").lower()
    assert "token" not in raw
    assert "credential" not in raw
    assert "systemctl" not in raw


def test_stage_is_idempotent_and_conflict_fails_closed(tmp_path):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    first = bootstrap.stage(runtime)
    second = bootstrap.stage(runtime)
    assert first["request_sha256"] == second["request_sha256"]
    path = runtime / bootstrap.REQUEST_REL
    value = json.loads(path.read_text(encoding="utf-8"))
    value["exact_sha"] = "0" * 40
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")
    blocked = bootstrap.stage(runtime)
    assert blocked["state"] == "BLOCKED"
    assert blocked["reason"] == "EXISTING_PRIVATE_SOURCE_REQUEST_CONFLICT"


def test_bootstrap_ready_requires_exact_source_and_authentic_receipt(tmp_path, monkeypatch):
    dest = tmp_path / "materialized"
    dest.mkdir()
    (dest / ".git").mkdir()
    receipt = tmp_path / "receipt.json"
    monkeypatch.setattr(bootstrap, "DEST", dest)
    monkeypatch.setattr(bootstrap, "EXECUTION_RECEIPT", receipt)
    monkeypatch.setattr(bootstrap, "_git_head", lambda root: bootstrap.EXPECTED_HEAD)

    pending = bootstrap.bootstrap(tmp_path / "runtime")
    assert pending["state"] == "HANDOFF_READY"
    assert pending["reason"] == "EXACT_SOURCE_PRESENT_EXECUTION_RECEIPT_NOT_VERIFIED"

    receipt.write_text(json.dumps({
        "state": "COMPLETE",
        "credential_authority": "TV/TVC",
        "authorized_exact_sha": bootstrap.EXPECTED_HEAD,
        "observed_exact_sha": bootstrap.EXPECTED_HEAD,
        "credential_value_exposed": False,
        "credential_persisted": False,
    }) + "\n", encoding="utf-8")
    ready = bootstrap.bootstrap(tmp_path / "runtime")
    assert ready["state"] == "READY"
    assert ready["source_head"] == bootstrap.EXPECTED_HEAD
    assert ready["credential_material_observed"] is False


def test_bootstrap_requires_runtime_root_when_source_absent(monkeypatch):
    monkeypatch.setattr(bootstrap, "_git_head", lambda root: None)
    monkeypatch.delenv("STEGVERSE_HEARTBEAT_ROOT", raising=False)
    result = bootstrap.bootstrap()
    assert result["state"] == "HANDOFF_READY"
    assert result["reason"] == "SOVEREIGN_RUNTIME_ROOT_NOT_OBSERVED"
    assert result["systemd_service_start_requested"] is False
