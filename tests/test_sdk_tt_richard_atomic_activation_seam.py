from __future__ import annotations

import importlib.util
from pathlib import Path

from heartbeat_runtime.process_adapter import ProcessWorkerAdapter

ROOT = Path(__file__).resolve().parents[1]
WORKER_PATH = ROOT / "workers" / "stegagents_governed_runtime_worker.py"
RUNTIME_PATH = ROOT / "heartbeat_runtime" / "worker_runtime_legacy.py"
HANDOFF_PATH = ROOT / "handoffs" / "SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001.json"
FRAGMENT_PATH = ROOT / "control" / "worker-registry.d" / "sdk-tt-richard-seam-authentic-runtime-001.json"


def _worker_module():
    spec = importlib.util.spec_from_file_location("test3_worker_bridge", WORKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pending_adapter_fence_does_not_require_live_task_binding(tmp_path):
    adapter = ProcessWorkerAdapter(["python", "-c", "print('x')"], cwd=tmp_path)
    task = {
        "task_id": "SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001",
        "state": "HANDOFF_READY",
        "claim_id": None,
        "worker_id": None,
        "worker_instance_id": None,
        "pending_atomic_activation": {
            "claim_id": "SHWP-SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001-G42",
            "fencing_token": 42,
            "worker_id": "stegagents-governed-runtime-worker",
            "proposed_worker_instance_id": "stegagents-governed-runtime-worker-HB1-G42",
        },
    }
    claim_id, fence = adapter._validate_fence(task)
    assert claim_id.endswith("-G42")
    assert fence == 42
    assert task["claim_id"] is None
    assert task["worker_id"] is None
    assert task["worker_instance_id"] is None


def test_pending_adapter_rejects_preactivation_live_binding(tmp_path):
    adapter = ProcessWorkerAdapter(["python", "-c", "print('x')"], cwd=tmp_path)
    task = {
        "task_id": "SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001",
        "state": "HANDOFF_READY",
        "claim_id": None,
        "worker_id": None,
        "worker_instance_id": "already-live",
        "pending_atomic_activation": {
            "claim_id": "SHWP-SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001-G42",
            "fencing_token": 42,
        },
    }
    try:
        adapter._validate_fence(task)
    except RuntimeError as exc:
        assert "may not expose a live task-bound worker" in str(exc)
    else:
        raise AssertionError("preactivation live worker accepted")


def test_worker_bridge_accepts_only_pending_test3_preactivation_shape():
    worker = _worker_module()
    invocation = {
        "schema": "stegverse.worker-invocation/v0.1",
        "task": {
            "task_id": worker.TEST3_TASK_ID,
            "state": "HANDOFF_READY",
            "claim_id": None,
            "worker_id": None,
            "worker_instance_id": None,
            "pending_atomic_activation": {
                "claim_id": "SHWP-SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001-G42",
                "fencing_token": 42,
                "worker_id": worker.WORKER_ID,
                "proposed_worker_instance_id": "stegagents-governed-runtime-worker-HB1-G42",
            },
        },
        "scope": {
            "claim_id": "SHWP-SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001-G42",
            "fencing_token": 42,
        },
    }
    task, mode = worker.validate_test3_invocation(invocation)
    assert mode == "ATOMIC_ACTIVATION"
    assert task["state"] == "HANDOFF_READY"
    assert task["worker_instance_id"] is None


def test_workercoordinator_projects_active_only_after_closed_constitutive_receipt():
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    branch = source.index('if task_id == "SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001":')
    require_closure = source.index('transition.get("state") == "RECORDED"', branch)
    require_reconstruction = source.index('transition.get("reconstruction_status") == "PASS"', branch)
    require_evidence = source.index('transition.get("required_evidence_validation_status") == "PASS"', branch)
    require_digest = source.index('transition.get("receipt_sha256") == transition.get("reconstructed_receipt_sha256")', branch)
    first_authoritative_projection = source.index('registry["generation"] = generation', branch)
    projection = source.index('"state": "ACTIVE"', first_authoritative_projection)
    invocation = source.index("self._invoke(registry, task, carrier_epoch, cost_log, events)", projection)
    next_worker_path = source.index("        if self._atomic_constitutive_activation_required(handoff):", invocation)
    assert (
        branch
        < require_closure
        < require_reconstruction
        < require_evidence
        < require_digest
        < first_authoritative_projection
        < projection
        < invocation
        < next_worker_path
    )


def test_test3_registration_reuses_existing_worker_provider():
    import json
    handoff = json.loads(HANDOFF_PATH.read_text(encoding="utf-8"))
    fragment = json.loads(FRAGMENT_PATH.read_text(encoding="utf-8"))
    task = fragment["tasks"][0]
    assert handoff["task"]["task_id"] == "SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001"
    assert handoff["activation"]["atomic_task_worker_binding_required"] is True
    assert task["state"] == "HANDOFF_READY"
    assert task["claim_id"] is None
    assert task["worker_id"] is None
    assert task["worker_instance_id"] is None
    assert fragment["workers"] == []
    assert fragment["shared_worker_provider_fragment_refs"] == [
        "control/worker-registry.d/stegagents-governed-runtime-001.json"
    ]


def test_worker_bridge_routes_waiting_test3_task_to_governed_close():
    worker = _worker_module()
    invocation = {
        "schema": "stegverse.worker-invocation/v0.1",
        "task": {
            "task_id": worker.TEST3_TASK_ID,
            "state": "ACTIVE",
            "claim_id": "SHWP-SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001-G42",
            "worker_id": worker.WORKER_ID,
            "worker_instance_id": "stegagents-governed-runtime-worker-HB1-G42",
            "atomic_activation_receipt_ref": "activation.json",
            "last_checkpoint_ref": "execution.json",
            "test3_waiting_for_governed_close": True,
            "heartbeat_timing": {"fencing_token": 42},
        },
        "scope": {
            "claim_id": "SHWP-SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001-G42",
            "fencing_token": 42,
        },
    }
    task, mode = worker.validate_test3_invocation(invocation)
    assert mode == "GOVERNED_CLOSE"
    assert task["test3_waiting_for_governed_close"] is True


def test_worker_bridge_requires_terminal_master_records_and_records_only_result():
    source = WORKER_PATH.read_text(encoding="utf-8")
    assert '"stegverse.stegagents-atomic-task-worker-close-request/v1"' in source
    assert '"GOVERNED_TASK_CLOSED_WORKER_RETIRED_RECORDS_ONLY"' in source
    assert '_require_closed_transition(result.get("close_master_records_transition"), "CLOSE_TASK_AND_RETIRE_WORKER")' in source
    assert 'result.get("worker_live_after_close") is False' in source
    assert 'result.get("continued_authority_after_retirement") is False' in source
    assert 'result.get("callable_retained") is False' in source
    assert 'result.get("executor_reference_retained") is False' in source
    assert '"state": "COMPLETED"' in source
    assert '"transition_id": "STEGAGENTS_GOVERNED_CLOSE_RETIRED"' in source


def test_workercoordinator_invokes_governed_close_and_releases_only_on_completed():
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    start = source.index('if task.get("test3_waiting_for_governed_close") is True:')
    invoke = source.index("self._invoke(registry, task, carrier_epoch, cost_log, events)", start)
    completed = source.index('if task.get("state") == "COMPLETED":', invoke)
    clear = source.index('task["test3_waiting_for_governed_close"] = False', completed)
    end = source.index("            return", clear)
    assert start < invoke < completed < clear < end
    assert '"test3_governed_close_invoked"' in source[start:end]


def test_worker_bridge_requires_post_retirement_stale_fence_refusal():
    source = WORKER_PATH.read_text(encoding="utf-8")
    assert '"post_retirement_stale_fence_invocation_refused"' in source
    assert '"POST_RETIREMENT_STALE_FENCE_INVOCATION_REFUSED"' in source
    assert 'probe.get("disposition") == "DENY"' in source
    assert 'probe.get("executor_invoked") is False' in source
    assert '_require_closed_transition(' in source
    assert 'probe_reconstruction.get("operation_transition_custody_status") == "RECORDED"' in source


def test_worker_bridge_retains_stale_fence_refusal_in_close_receipt():
    source = WORKER_PATH.read_text(encoding="utf-8")
    close_branch = source.index('elif mode == "GOVERNED_CLOSE":')
    retain = source.index('receipt["post_retirement_stale_fence_refusal"]', close_branch)
    retain_flag = source.index('receipt["post_retirement_stale_fence_invocation_refused"]', retain)
    target = source.index("target = root / result_rel", retain_flag)
    assert close_branch < retain < retain_flag < target
