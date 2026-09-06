from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_canonical_work_event_bootstrap.py"
WRAPPER = ROOT / "scripts" / "install_and_run_canonical_work_event_bootstrap.py"


def load_module():
    spec = importlib.util.spec_from_file_location("task_targeted_canonical_work_bootstrap", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def task(task_id="T1", *, state="PROPOSED", allowed=None, claim_ref=None, fence_ref=None):
    return {
        "task_id": task_id,
        "correlation_id": task_id,
        "coordination_state": state,
        "allowed_next_transitions": ["INGRESS_ADMITTED"] if allowed is None else allowed,
        "worker_claim": {
            "authority": "WORKERCOORDINATOR",
            "claim_ref": claim_ref,
            "fence_ref": fence_ref,
            "projection_only": True,
        },
        "authority_model": {
            "task_registry_mints_execution_authority": False,
            "source_state_proves_execution": False,
            "worker_claim_authority": "WORKERCOORDINATOR",
            "master_records_reality_authority": True,
            "interlock_intr_required_for_governed_ingress_egress": True,
        },
    }


def test_exact_proposed_task_is_resolved_without_minting_authority():
    module = load_module()
    selected = module.resolve_target_task({"tasks": [task()]}, "T1")
    assert selected["task_id"] == "T1"
    assert selected["coordination_state"] == "PROPOSED"
    assert selected["worker_claim"]["claim_ref"] is None
    assert selected["worker_claim"]["fence_ref"] is None


@pytest.mark.parametrize(
    "registry,task_id",
    [
        ({"tasks": []}, "T1"),
        ({"tasks": [task(), task()]}, "T1"),
        ({"tasks": [task(state="INGRESS_ADMITTED")]}, "T1"),
        ({"tasks": [task(allowed=[])]}, "T1"),
        ({"tasks": [task(claim_ref="claim:1")]}, "T1"),
        ({"tasks": [task(fence_ref="fence:1")]}, "T1"),
    ],
)
def test_invalid_target_conditions_fail_closed(registry, task_id):
    module = load_module()
    with pytest.raises(SystemExit) as exc:
        module.resolve_target_task(registry, task_id)
    assert str(exc.value).startswith("FAIL_CLOSED:")


def test_authority_model_drift_fails_closed():
    module = load_module()
    value = task()
    value["authority_model"]["worker_claim_authority"] = "TASK_REGISTRY"
    with pytest.raises(SystemExit, match="FAIL_CLOSED: worker_claim_authority_drift"):
        module.resolve_target_task({"tasks": [value]}, "T1")


def test_wrapper_forwards_task_id_to_bootstrap():
    source = WRAPPER.read_text(encoding="utf-8")
    assert 'parser.add_argument("--task-id"' in source
    assert '"--task-id",' in source
    assert "args.task_id" in source


def test_bootstrap_projection_is_selected_task_specific():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "def project_registry(*, task_id:" in source
    assert 'task.get("task_id") == task_id' in source
    assert 'f"canonical-task-registry.after-ingress.{task_id}.json"' in source
    assert 'f"canonical-work-event-bootstrap.{args.task_id}.latest.json"' in source
