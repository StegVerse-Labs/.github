from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers/ungoverned_ai_defensive_envelope_worker.py"
REGISTRY = ROOT / "control/worker-registry.d/ungoverned-ai-defensive-envelope-001.json"
ADAPTER = ROOT / "control/process-worker-adapters.d/ungoverned-ai-defensive-envelope-001.json"
REQUEST = ROOT / "control/resident-execution-request.d/ungoverned-ai-defensive-envelope-001.json"
HANDOFF = ROOT / "handoffs/ECOSYSTEM-INGRESS-AI-BOUNDARIES-001.json"


def _module():
    spec = importlib.util.spec_from_file_location("defensive_envelope_worker", WORKER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _probe():
    return {
        "component_id": "RTC-NONCHATGPT-AI-DECISION-SANDBOX-011",
        "candidate_origin": "REPRESENTATIVE_UNTRUSTED_SOURCE_NOT_EXTERNAL_PROVIDER_ATTESTATION",
        "external_provider_observed": False,
        "admitted_interaction": {
            "decision": "ALLOW", "consumed": True, "result_observed": 42,
            "filesystem_capability_exposed": False, "network_capability_exposed": False,
            "candidate_source_materialized_to_filesystem": False,
            "temporary_state_destroyed": True,
        },
        "denied_interactions": [
            {"decision": "DENY", "consumed": False, "consequence_reachable": False}
        ],
        "ambient_credential_capability_exposed": False,
        "task_registry_authority_exposed": False,
        "tv_tvc_authority_exposed": False,
        "interlock_intr_authority_exposed": False,
        "master_records_authority_exposed": False,
        "publisher_authority_exposed": False,
        "host_runtime_authority_exposed": False,
        "candidate_internal_sovereignty_preserved": True,
        "governed_egress_disposition": "EVIDENCE_ONLY_NO_CONSEQUENTIAL_EGRESS_REQUESTED",
    }


def test_registry_adapter_request_and_handoff_are_same_existing_runtime_path():
    registry = json.loads(REGISTRY.read_text())
    adapter = json.loads(ADAPTER.read_text())
    request = json.loads(REQUEST.read_text())
    handoff = json.loads(HANDOFF.read_text())
    task = registry["tasks"][0]
    worker = registry["workers"][0]
    process = adapter["adapters"][0]
    assert task["task_id"] == "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001"
    assert task["state"] == "HANDOFF_READY"
    assert task["admission"]["authority_domain"] == "INDEPENDENT_TASK_CONTROL"
    assert task["admission"]["fresh_fence_required"] is True
    assert task["admission"]["heartbeat_grants_execution_authority"] is False
    assert worker["adapter_ref"] == process["adapter_ref"] == request["fail_closed_requirements"]["exact_adapter_ref_required"]
    assert process["env_allowlist"] == ["STEGVERSE_TVC_ROOT", "PATH"]
    assert request["network_source_fetch_allowed"] is False
    assert request["external_provider_origin_required_for_this_probe"] is False
    assert handoff["completion"]["runtime_observation_claimed"] is False
    assert "--cosv-task-vector" not in handoff["completion"]["targeted_command"]


def test_worker_accepts_only_representative_boundary_evidence(tmp_path, monkeypatch):
    mod = _module()
    tvc = tmp_path / "tvc"
    tasks = tvc / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "__init__.py").write_text("")
    (tasks / "ungoverned_ai_defensive_envelope.py").write_text(
        "def run_defensive_envelope_probe():\n"
        "    return " + repr(_probe()) + "\n"
    )
    monkeypatch.setattr(mod, "_tvc_root", lambda: (tvc, mod.TVC_SOURCE_FLOOR))
    monkeypatch.setattr(mod, "RECEIPT_REL", tmp_path / "receipt.json")
    for name in mod.HOSTED + mod.FORBIDDEN_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    invocation = {
        "schema": "stegverse.worker-invocation/v0.1",
        "task": {
            "task_id": mod.TASK_ID, "state": "ACTIVE",
            "claim_id": "claim-G1", "worker_id": "ungoverned-ai-defensive-envelope-worker",
            "heartbeat_timing": {"fencing_token": 1},
        },
        "scope": {"claim_id": "claim-G1", "fencing_token": 1},
        "handoff": {"execution": {"required_capabilities": [mod.CAPABILITY]}},
    }
    response = mod.run(invocation)
    assert response["state"] == "COMPLETED"
    receipt = json.loads((tmp_path / "receipt.json").read_text())
    assert receipt["external_provider_observed"] is False
    assert receipt["goal_runtime_completion_claimed"] is False
    assert receipt["probe"]["denied_interactions"][0]["consumed"] is False
    assert receipt["probe"]["denied_interactions"][0]["consequence_reachable"] is False


def test_worker_rejects_ambient_protected_environment(tmp_path, monkeypatch):
    mod = _module()
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-cross-boundary")
    invocation = {
        "schema": "stegverse.worker-invocation/v0.1",
        "task": {
            "task_id": mod.TASK_ID, "state": "ACTIVE",
            "claim_id": "claim-G2", "worker_id": "ungoverned-ai-defensive-envelope-worker",
            "heartbeat_timing": {"fencing_token": 2},
        },
        "scope": {"claim_id": "claim-G2", "fencing_token": 2},
        "handoff": {"execution": {"required_capabilities": [mod.CAPABILITY]}},
    }
    try:
        mod.run(invocation)
    except RuntimeError as exc:
        assert "AMBIENT_PROTECTED_AUTHORITY_ENVIRONMENT_PRESENT" in str(exc)
    else:
        raise AssertionError("protected environment was not rejected")
