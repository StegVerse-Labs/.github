from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAT_PATH = ROOT / "scripts" / "materialize_gadi_resident_runtime_bundle.py"

spec = importlib.util.spec_from_file_location("gadi_materializer_contract", MAT_PATH)
materializer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(materializer)


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_materializer_accepts_authentic_native_stegos_command_shape(tmp_path):
    base = tmp_path / materializer.SOURCE_DIR
    write(base / "stegos-command.json", {
        "schema": "stegos.gadi-native-defensive-command.v1",
        "task_id": "GADI-001",
        "cosv_id": "10100000100000",
        "interaction_id": "interaction:1",
        "disposition": "CONTAIN",
        "native_ability": "CONTAIN_SOURCE",
        "capability_id": "capability:1",
        "capability_action": "contain_source",
        "target_class": "CONTROLLED_SIMULATION",
        "control_surface": "safe-state-control",
        "authorization_evidence_ref": "tvtvc:capability:1",
        "credential_authority": "TV/TVC",
        "intr_decision_ref": "intr:decision:1",
        "runtime_binding_ref": "runtime:binding:1",
        "intr_admission_observed": True,
        "runtime_binding_observed": True,
        "execution_authority_claimed_by_stegos": False,
        "command_state": "READY_FOR_RESIDENT_EXECUTION",
    })
    write(base / "intr-admission.json", {
        "state": "ADMITTED",
        "intr_decision_ref": "intr:decision:1",
        "runtime_binding_ref": "runtime:binding:1",
    })
    write(base / "worker-claim.json", {
        "task_id": "GADI-RESIDENT-EXECUTION-001",
        "parent_task_id": "GADI-001",
        "state": "CLAIMED",
        "workercoordinator_authority_observed": True,
        "worker_claim_ref": "wc:claim:1",
        "fence_ref": "wc:fence:1",
        "runtime_binding_ref": "runtime:binding:1",
        "control_surface": "safe-state-control",
        "target_class": "CONTROLLED_SIMULATION",
        "execution_subject": "stegverse:gadi:test-subject",
    })
    write(base / "actuator-observation.json", {
        "preauthorized_controlled_surface": True,
        "credential_material_exposed": False,
        "control_surface": "safe-state-control",
        "target_class": "CONTROLLED_SIMULATION",
        "execution_subject": "stegverse:gadi:test-subject",
        "runtime_binding_ref": "runtime:binding:1",
        "intr_decision_ref": "intr:decision:1",
    })

    result = materializer.materialize(tmp_path)

    assert result["ready"] is True
    assert result["blockers"] == []
    projected = json.loads((tmp_path / materializer.COMMAND_OUT).read_text())
    assert projected["task_id"] == "GADI-001"
    assert projected["command_state"] == "READY_FOR_RESIDENT_EXECUTION"


def test_materializer_still_rejects_unrelated_command_task(tmp_path):
    base = tmp_path / materializer.SOURCE_DIR
    write(base / "stegos-command.json", {
        "task_id": "OTHER-TASK",
        "command_state": "READY_FOR_RESIDENT_EXECUTION",
        "intr_admission_observed": True,
        "intr_decision_ref": "intr:decision:1",
        "runtime_binding_ref": "runtime:binding:1",
    })
    result = materializer.materialize(tmp_path)
    assert "COMMAND_TASK_MISMATCH" in result["blockers"]
