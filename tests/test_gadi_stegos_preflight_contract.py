from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_PATH = ROOT / "scripts" / "preflight_gadi_resident_execution.py"

spec = importlib.util.spec_from_file_location("gadi_preflight_contract", PREFLIGHT_PATH)
preflight = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(preflight)


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_preflight_accepts_native_stegos_command_state_field(tmp_path):
    request = {
        "task_id": "GADI-RESIDENT-EXECUTION-001",
        "parent_task_id": "GADI-001",
        "state": "REQUESTED",
        "command_state_ref": "state/gadi-resident-execution/command.json",
        "execution_context_ref": "state/gadi-resident-execution/execution-context.json",
        "actuator_result_ref": "state/gadi-resident-execution/actuator-result.json",
    }
    write(tmp_path / preflight.REQUEST_REL, request)
    write(tmp_path / request["command_state_ref"], {
        "schema": "stegos.gadi-native-defensive-command.v1",
        "task_id": "GADI-001",
        "command_state": "READY_FOR_RESIDENT_EXECUTION",
        "intr_decision_ref": "intr:decision:1",
        "runtime_binding_ref": "runtime:binding:1",
    })
    write(tmp_path / request["execution_context_ref"], {
        "task_id": "GADI-RESIDENT-EXECUTION-001",
        "parent_task_id": "GADI-001",
        "workercoordinator_authority_observed": True,
        "worker_claim_ref": "wc:claim:1",
        "fence_ref": "wc:fence:1",
        "runtime_binding_ref": "runtime:binding:1",
        "runtime_lease_observed": False,
        "execution_subject": "stegverse:gadi:test-subject",
        "control_surface": "safe-state-control",
        "target_class": "CONTROLLED_SIMULATION",
    })
    write(tmp_path / request["actuator_result_ref"], {
        "preauthorized_controlled_surface": True,
        "credential_material_exposed": False,
        "execution_subject": "stegverse:gadi:test-subject",
        "control_surface": "safe-state-control",
        "target_class": "CONTROLLED_SIMULATION",
        "intr_decision_ref": "intr:decision:1",
    })

    result = preflight.preflight(tmp_path, tmp_path)

    assert result["ready"] is True
    assert result["state"] == "READY_FOR_RESIDENT_CONSUMPTION"
    assert result["blockers"] == []
