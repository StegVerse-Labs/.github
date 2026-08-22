from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import workers.tvc_repository_broker_validation_worker as worker


def test_handoff_and_adapter_are_credential_clean():
    handoff = json.loads((ROOT / "handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json").read_text())
    adapter = json.loads((ROOT / "control/process-worker-adapters.d/tvc-repository-broker-validation-001.json").read_text())
    registry = json.loads((ROOT / "control/worker-registry.d/tvc-repository-broker-validation-001.json").read_text())
    assert handoff["authority"]["credential_authority"] == "TV/TVC"
    assert handoff["authority"]["github_token_required"] is False
    assert handoff["authority"]["heartbeat_dependency"] is False
    assert handoff["execution"]["expected_tvc_head"] == "8eae9764599817f92aa24a71c64dcd1ba1dccfed"
    assert handoff["activation"]["heartbeat_dependency"] is False
    assert handoff["activation"]["carrier_trigger_required"] is False
    assert adapter["adapters"][0]["env_allowlist"] == ["STEGVERSE_TVC_ROOT"]
    assert registry["credential_authority"] == "TV/TVC"
    assert registry["github_token_required"] is False
    assert registry["tasks"][0]["heartbeat_dependency"] is False
    assert "StegVerse-Labs/TVC#92" in registry["tasks"][0]["evidence_refs"]


def test_cleaned_env_removes_all_forbidden(monkeypatch):
    for name in worker.FORBIDDEN_ENV + ("TVC_EPHEMERAL_GITHUB_TOKEN",):
        monkeypatch.setenv(name, "secret")
    monkeypatch.setenv("STEGVERSE_TVC_ROOT", "/tmp/tvc")
    env = worker.cleaned_env()
    for name in worker.FORBIDDEN_ENV + ("TVC_EPHEMERAL_GITHUB_TOKEN",):
        assert name not in env
    assert env["STEGVERSE_TVC_ROOT"] == "/tmp/tvc"


def test_worker_has_no_source_fetch_transport():
    source = (ROOT / "workers/tvc_repository_broker_validation_worker.py").read_text()
    assert "urllib" not in source
    assert "requests." not in source
    assert "git fetch" not in source
    assert "git clone" not in source
    assert "TVC_EPHEMERAL_GITHUB_TOKEN" in source
    assert "tools/task_dispatcher.py" in source
