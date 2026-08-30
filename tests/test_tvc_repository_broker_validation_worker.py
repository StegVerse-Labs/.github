from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import workers.tvc_repository_broker_validation_worker as worker

EXPECTED_TVC_HEAD = "b5288f9910ada26c6ab2e9bca3f7701afaae2cef"
EXPECTED_SOURCE_BUNDLE_SHA256 = "0369ed677a014a99a983415a9094e6aaa0c570d163d9818d9a086fee6042dd6a"


def test_handoff_and_adapter_are_credential_clean():
    handoff = json.loads((ROOT / "handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json").read_text())
    adapter = json.loads((ROOT / "control/process-worker-adapters.d/tvc-repository-broker-validation-001.json").read_text())
    registry = json.loads((ROOT / "control/worker-registry.d/tvc-repository-broker-validation-001.json").read_text())
    assert handoff["authority"]["credential_authority"] == "TV/TVC"
    assert handoff["authority"]["github_token_required"] is False
    assert handoff["authority"]["heartbeat_dependency"] is False
    assert handoff["execution"]["expected_tvc_head"] == EXPECTED_TVC_HEAD
    assert handoff["execution"]["expected_source_bundle_sha256"] == EXPECTED_SOURCE_BUNDLE_SHA256
    assert handoff["activation"]["heartbeat_dependency"] is False
    assert handoff["activation"]["carrier_trigger_required"] is False
    assert adapter["adapters"][0]["env_allowlist"] == ["STEGVERSE_TVC_ROOT"]
    assert registry["credential_authority"] == "TV/TVC"
    assert registry["github_token_required"] is False
    task = registry["tasks"][0]
    assert task["heartbeat_dependency"] is False
    assert task["cost_basis_ref"] == "cost-basis/worker-runtime/tvc-repository-broker-validation.json"
    assert task["admission"]["authority_domain"] == "INDEPENDENT_TASK_CONTROL"
    assert task["admission"]["claim_state"] == "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM"
    assert task["admission"]["heartbeat_reference_only"] is True
    assert task["admission"]["heartbeat_grants_execution_authority"] is False
    assert task["admission"]["carrier_trigger_required"] is False
    assert task["admission"]["fresh_fence_required"] is True
    assert task["admission"]["minimum_fencing_token_exclusive"] == 22
    assert handoff["task"]["execution_admission_mode"] == "INDEPENDENT_TASK_CONTROL"
    assert handoff["task"]["worker_id"] == "tvc-repository-broker-validation-worker"
    assert handoff["activation"]["authority_domain"] == "INDEPENDENT_TASK_CONTROL"
    assert handoff["activation"]["minimum_fencing_token_exclusive"] == 22
    cost = json.loads((ROOT / task["cost_basis_ref"]).read_text())
    assert cost["hb_estimate"]["expiry_candidate_beats"] == 24000
    assert cost["hb_estimate"]["confidence"] != "NONE"
    assert "StegVerse-Labs/TVC#92" in task["evidence_refs"]
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
    assert 'heartbeat_timing\") or {}' not in source
    assert 'source_bundle_file_count' in source
    assert 'source_bundle_sha256' in source
    assert 'expected_source_bundle_sha256' in source
    assert 'bundle_digest == expected_bundle_digest' in source


def test_canonical_retrospective_ae_record_remains_non_authorizing():
    handoff = json.loads((ROOT / "handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json").read_text())
    retrospective = json.loads((ROOT / "control/admissible-existence-retrospective-conformance.json").read_text())
    assert handoff["admissible_existence"]["phase"] == "DECLARED"
    assert handoff["authority"]["repository_writeback_authority"] is False
    assert handoff["authority"]["merge_authority"] is False
    assert handoff["authority"]["non_tv_tvc_secret_or_token_allowed"] is False
    entries = [e for e in retrospective["entries"] if e.get("task_id") == worker.TASK_ID]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["ae_impact"] == "NONE"
    assert entry["phase"] is None
    assert entry["result"] == "PASS"
    assert entry["task_relationship"] == "validates_capability"
    assert "TVC#92" in entry["continuation_owner"]
