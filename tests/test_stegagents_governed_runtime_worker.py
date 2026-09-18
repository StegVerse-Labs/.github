from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers/stegagents_governed_runtime_worker.py"
REGISTRY = ROOT / "control/worker-registry.d/stegagents-governed-runtime-001.json"
ADAPTER = ROOT / "control/process-worker-adapters.d/stegagents-governed-runtime-001.json"
HANDOFF = ROOT / "handoffs/STEGAGENTS-GOVERNED-RUNTIME-001.json"


def load_worker():
    spec = importlib.util.spec_from_file_location("stegagents_governed_runtime_worker", WORKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def invocation(fence: int = 42):
    claim = f"SHWP-STEGAGENTS-GOVERNED-RUNTIME-001-G{fence}"
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "task": {
            "task_id": "STEGAGENTS-GOVERNED-RUNTIME-001",
            "state": "ACTIVE",
            "claim_id": claim,
            "worker_id": "stegagents-governed-runtime-worker",
            "heartbeat_timing": {"fencing_token": fence},
        },
        "scope": {"claim_id": claim, "fencing_token": fence},
    }


def test_worker_requires_exact_current_claim_fence():
    m = load_worker()
    task = m.validate_invocation(invocation())
    assert task["task_id"] == m.TASK_ID
    bad = invocation()
    bad["scope"]["fencing_token"] = 41
    try:
        m.validate_invocation(bad)
    except RuntimeError as exc:
        assert "claim/fence mismatch" in str(exc)
    else:
        raise AssertionError("mismatched claim/fence accepted")


def test_worker_builds_proposal_only_request():
    m = load_worker()
    task = m.validate_invocation(invocation())
    request = m.build_request(task)
    assert request["task_id"] == m.TASK_ID
    assert request["cosv_task_vector"] == m.COSV
    assert request["agent_id"] == m.AGENT_ID
    assert request["proposal_only"] is True
    assert request["execution_authority"] is False
    assert request["self_authorization_allowed"] is False
    assert request["credential_material_present"] is False
    assert request["code_repair_request"]["authority_effect"] == "NONE"
    purpose = request["purpose_bound_worker_request"]
    assert purpose["schema"] == "stegverse.sdk.tt-purpose-bound-worker.v1"
    candidate = purpose["transition_cell"]["candidate"]
    assert candidate["purpose"] == "Analyze a supplied text payload for a tracked integrity summary."
    assert candidate["required_capability"] == "text.integrity_summary"
    assert candidate["operation_class"] == "ARBITRARY_TRACKED_TASK"
    assert candidate["max_lifetime_seconds"] == 30


def test_registration_reuses_existing_worker_runtime_only():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    adapter = json.loads(ADAPTER.read_text(encoding="utf-8"))
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    task = registry["tasks"][0]
    worker = registry["workers"][0]
    process = adapter["adapters"][0]
    assert task["task_id"] == "STEGAGENTS-GOVERNED-RUNTIME-001"
    assert task["state"] == "HANDOFF_READY"
    assert task["executor_binding"] == "AUTHORIZED"
    assert task["admission"]["fresh_fence_required"] is True
    assert task["admission"]["heartbeat_grants_execution_authority"] is False
    assert worker["adapter_ref"] == process["adapter_ref"] == "process:stegagents-governed-runtime-v1"
    assert process["command"] == ["python", "workers/stegagents_governed_runtime_worker.py"]
    assert handoff["authority"]["credential_authority"] == "TV/TVC"
    assert handoff["authority"]["github_token_production_authority"] == "NONE"
    assert handoff["activation"]["targeted_execution"]["entrypoint"] == "scripts/run_worker_runtime.py"
    assert handoff["activation"]["targeted_execution"]["heartbeat_grants_execution_authority"] is False


def test_exact_registered_manifest_blob_is_pinned():
    m = load_worker()
    assert m.EXPECTED_MANIFEST_GIT_BLOB_SHA == "061649a4b0b43c01f3009ed3e6c8c4829559fb5b"
    assert m.REGISTERED_MANIFEST_SOURCE_MERGE == "b768eeeb0ceca14fcfd50ce665cd6c0885e2774f"
