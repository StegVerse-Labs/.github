from __future__ import annotations

import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "materialize_gadi_actuator_observation.py"
spec = importlib.util.spec_from_file_location("gadi_actuator_observation", PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def receipt() -> dict:
    return {
        "task_id": "GADI-001",
        "preauthorized_controlled_surface": True,
        "credential_material_exposed": False,
        "authority_effect": "NONE_EXECUTION_EVIDENCE_ONLY",
        "receipt_pointer": "receipt://stegos/output/1",
        "authority_reference": "tvc://capability/1",
        "target_node": "controlled-node-1",
        "mode": "QUARANTINE_INTERACTION",
        "source": "StegOS",
        "duration": "bounded",
        "risk_class": "actuator",
        "execution_subject": "stegverse:gadi:subject-1",
        "control_surface": "safe-state-control",
        "target_class": "CONTROLLED_SIMULATION",
        "runtime_binding_ref": "runtime://binding/1",
        "intr_decision_ref": "intr://decision/1",
        "observed_state": "SAFE_STATE_REACHED",
        "effect_observed": True,
        "reassessment_required": True,
        "stop_condition_observed": False,
    }


def test_projects_already_receipted_controlled_output_without_minting_authority():
    result = module.project(receipt(), receipt_sha256="abc123")
    assert result["task_id"] == module.TASK_ID
    assert result["parent_task_id"] == module.PARENT_TASK_ID
    assert result["runtime_binding_ref"] == "runtime://binding/1"
    assert result["intr_decision_ref"] == "intr://decision/1"
    assert result["execution_subject"] == "stegverse:gadi:subject-1"
    assert result["control_surface"] == "safe-state-control"
    assert result["target_class"] == "CONTROLLED_SIMULATION"
    assert result["governed_output"]["source_receipt_sha256"] == "abc123"
    assert result["actuator_executed_by_adapter"] is False
    assert result["authority_minted"] is False
    assert result["execution_claimed"] is False


def test_rejects_unreceipted_output():
    value = receipt()
    value["receipt_pointer"] = ""
    with pytest.raises(SystemExit, match="receipt pointer missing"):
        module.project(value, receipt_sha256="abc123")


def test_rejects_uncontrolled_output():
    value = receipt()
    value["preauthorized_controlled_surface"] = False
    with pytest.raises(SystemExit, match="not pre-authorized/controlled"):
        module.project(value, receipt_sha256="abc123")


def test_rejects_authority_drift():
    value = receipt()
    value["authority_effect"] = "EXECUTION_GRANTED"
    with pytest.raises(SystemExit, match="authority drift"):
        module.project(value, receipt_sha256="abc123")


def test_rejects_missing_runtime_or_intr_binding():
    value = receipt()
    value["runtime_binding_ref"] = ""
    with pytest.raises(SystemExit, match="runtime binding missing"):
        module.project(value, receipt_sha256="abc123")
    value = receipt()
    value["intr_decision_ref"] = ""
    with pytest.raises(SystemExit, match="InTr decision reference missing"):
        module.project(value, receipt_sha256="abc123")
