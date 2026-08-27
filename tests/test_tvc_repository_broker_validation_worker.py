from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import workers.tvc_repository_broker_validation_worker as worker

EXPECTED_TVC_HEAD = "4e87ad9f3a859ab3b18241640624abd5e1757002"


def test_handoff_and_adapter_are_credential_clean():
    handoff = json.loads((ROOT / "handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json").read_text())
    adapter = json.loads((ROOT / "control/process-worker-adapters.d/tvc-repository-broker-validation-001.json").read_text())
    registry = json.loads((ROOT / "control/worker-registry.d/tvc-repository-broker-validation-001.json").read_text())
    assert handoff["authority"]["credential_authority"] == "TV/TVC"
    assert handoff["authority"]["github_token_required"] is False
    assert handoff["authority"]["heartbeat_dependency"] is False
    assert handoff["execution"]["expected_tvc_head"] == EXPECTED_TVC_HEAD
    assert handoff["activation"]["heartbeat_dependency"] is False
    assert handoff["activation"]["carrier_trigger_required"] is False
    assert adapter["adapters"][0]["env_allowlist"] == ["STEGVERSE_TVC_ROOT"]
    assert registry["credential_authority"] == "TV/TVC"
    assert registry["github_token_required"] is False
    assert registry["tasks"][0]["heartbeat_dependency"] is False
    assert "StegVerse-Labs/TVC#92" in registry["tasks"][0]["evidence_refs"]
    assert f"StegVerse-Labs/TVC@{EXPECTED_TVC_HEAD}" in registry["tasks"][0]["evidence_refs"]


def test_task_control_identity_does_not_require_heartbeat():
    identity = worker._optional_task_control_identity(
        {"schema": "stegverse.worker-invocation/v0.1"},
        {"task_id": worker.TASK_ID},
    )
    assert identity["observed_heartbeat_epoch"] is None
    assert identity["heartbeat_reference_only"] is True
    assert identity["heartbeat_dependency"] is False
    assert identity["claim_id"] is None
    assert identity["fencing_token"] is None


def test_task_control_identity_accepts_heartbeat_as_observation_only():
    identity = worker._optional_task_control_identity(
        {"schema": "stegverse.worker-invocation/v0.1", "heartbeat_epoch": 412},
        {"task_id": worker.TASK_ID, "claim_id": "claim-1", "lease": {"fencing_token": 7}},
    )
    assert identity["observed_heartbeat_epoch"] == 412
    assert identity["heartbeat_reference_only"] is True
    assert identity["heartbeat_dependency"] is False
    assert identity["claim_id"] == "claim-1"
    assert identity["fencing_token"] == 7


def test_cleaned_env_removes_all_forbidden(monkeypatch):
    for name in worker.FORBIDDEN_ENV + ("TVC_EPHEMERAL_GITHUB_TOKEN",):
        monkeypatch.setenv(name, "secret")
    monkeypatch.setenv("STEGVERSE_TVC_ROOT", "/tmp/tvc")
    env = worker.cleaned_env()
    for name in worker.FORBIDDEN_ENV + ("TVC_EPHEMERAL_GITHUB_TOKEN",):
        assert name not in env
    assert env["STEGVERSE_TVC_ROOT"] == "/tmp/tvc"


def test_worker_has_no_source_fetch_transport_or_heartbeat_gate():
    source = (ROOT / "workers/tvc_repository_broker_validation_worker.py").read_text()
    assert "urllib" not in source
    assert "requests." not in source
    assert "git fetch" not in source
    assert "git clone" not in source
    assert "TVC_EPHEMERAL_GITHUB_TOKEN" in source
    assert "tools/task_dispatcher.py" in source
    assert 'if not isinstance(epoch, int)' not in source
    assert 'heartbeat_timing") or {}' not in source
    assert 'source_bundle_file_count' in source
    assert 'source_bundle_sha256' in source
