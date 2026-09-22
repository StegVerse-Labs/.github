from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hb_remains_non_authorizing_carrier_and_observation_surface():
    handoff = (ROOT / "docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md").read_text(encoding="utf-8")
    continuity = json.loads((ROOT / "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json").read_text(encoding="utf-8"))

    assert "state-transition gating: false" in handoff
    assert "admission gating: false" in handoff
    assert "claim/fence/lease gating: false" in handoff
    assert "observation is causal: false" in handoff
    assert continuity["oscillator"]["worker_or_task_gating"] is False
    assert continuity["oscillator"]["admission_gating"] is False
    assert continuity["oscillator"]["claim_or_fence_gating"] is False
    assert continuity["oscillator"]["observation_is_causal"] is False


def test_active_checked_out_state_transition_is_not_stranded_by_proposed_only_selection():
    selector = load_module("canonical_work_selector_regression", "scripts/run_task_registry_canonical_work_cycle.py")
    record = {
        "task_id": "REGRESSION-STATE-CHAIN-001",
        "coordination_state": "ACTIVE",
        "checkout_state": "CHECKED_OUT",
        "allowed_next_transitions": ["INGRESS_ADMITTED"],
        "human_action_ref": None,
        "runtime_requirements": {"capabilities": ["canonical_work_ingress"]},
        "worker_claim": {
            "authority": "WORKERCOORDINATOR",
            "claim_ref": None,
            "fence_ref": None,
            "projection_only": True,
        },
        "authority_model": {
            "task_registry_mints_execution_authority": False,
            "interlock_intr_required_for_governed_ingress_egress": True,
        },
    }
    assert selector.machine_ingress_candidate(record) is True


def test_claim_reference_without_workercoordinator_fence_is_not_execution_checkout():
    monitor = load_module("health_monitor_regression", "scripts/evaluate_task_registry_health_monitor.py")
    record = {
        "coordination_state": "ACTIVE",
        "worker_claim": {
            "authority": "WORKERCOORDINATOR",
            "claim_ref": "docs/HANDOFF.md",
            "fence_ref": None,
            "projection_only": True,
        },
    }
    assert monitor._checked_out(record) is False


def test_master_records_absence_without_stegdb_comparison_is_not_runtime_failure(tmp_path):
    monitor = load_module("health_monitor_regression_absence", "scripts/evaluate_task_registry_health_monitor.py")
    now = datetime(2026, 9, 19, 23, 0, tzinfo=timezone.utc)
    record = {
        "task_id": "REGRESSION-STATE-CHAIN-001",
        "worker_return_obligation": {
            "ref": "RETURN-1",
            "expected_return_by": "2026-09-19T22:00:00Z",
            "master_records_subject_binding": "subject-1",
            "master_records_return_ref": str(tmp_path / "missing.json"),
        },
    }
    observed = monitor._worker_return_observation(record, now)
    assert observed["posture"] == "RECONCILIATION_REQUIRED"
    assert observed["recovery_required"] is False


def test_master_records_absence_plus_stegdb_missing_can_enter_health_classification(tmp_path):
    monitor = load_module("health_monitor_regression_coordinated", "scripts/evaluate_task_registry_health_monitor.py")
    now = datetime(2026, 9, 19, 23, 0, tzinfo=timezone.utc)
    record = {
        "task_id": "REGRESSION-STATE-CHAIN-001",
        "worker_return_obligation": {
            "ref": "RETURN-1",
            "expected_return_by": "2026-09-19T22:00:00Z",
            "master_records_subject_binding": "subject-1",
            "master_records_return_ref": str(tmp_path / "missing.json"),
            "stegdb_comparison_ref": "stegdb://RETURN-1",
            "stegdb_comparison_status": "MISSING",
        },
    }
    observed = monitor._worker_return_observation(record, now)
    assert observed["posture"] in {"RETURN_OVERDUE", "WORKER_NONREPORT"}
    assert observed["recovery_required"] is True


def test_existing_minimal_chain_source_semantics_remain_strictly_ordered():
    handoff = (ROOT / "docs/SDK_TT_RICHARD_SEAM_AUTHENTIC_RUNTIME_MIRROR_HANDOFF.md").read_text(encoding="utf-8")
    source = (ROOT / "heartbeat_runtime/worker_runtime_legacy.py").read_text(encoding="utf-8")

    assert "HANDOFF_READY T + no task-bound W" in handoff
    assert "fresh WorkerCoordinator claim/fence" in handoff
    assert "StegCore/InTr admits ONE constitutive ACTIVATE(T)+CREATE_AND_BIND(W,T) transition" in handoff
    assert "state=RECORDED" in handoff
    assert "reconstruction_status=PASS" in handoff
    assert "required_evidence_validation_status=PASS" in handoff
    assert "receipt_sha256 == reconstructed_receipt_sha256" in handoff

    branch = source.index('if task_id == "SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001":')
    closed = source.index('transition.get("state") == "RECORDED"', branch)
    reconstructed = source.index('transition.get("reconstruction_status") == "PASS"', branch)
    evidence = source.index('transition.get("required_evidence_validation_status") == "PASS"', branch)
    digest = source.index('transition.get("receipt_sha256") == transition.get("reconstructed_receipt_sha256")', branch)
    active = source.index('"state": "ACTIVE"', digest)
    invoke = source.index("self._invoke(registry, task, carrier_epoch, cost_log, events)", active)
    assert branch < closed < reconstructed < evidence < digest < active < invoke
