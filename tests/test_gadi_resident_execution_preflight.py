import json
from pathlib import Path
import importlib.util

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "preflight_gadi_resident_execution.py"
spec = importlib.util.spec_from_file_location("gadi_preflight", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def seed_request(root: Path):
    write(root / "control/resident-execution-request.d/gadi-resident-execution-001.json", {
        "schema": "stegverse.resident-execution-request/v1",
        "request_id": "RESIDENT-EXEC-GADI-001",
        "state": "REQUESTED",
        "task_id": "GADI-RESIDENT-EXECUTION-001",
        "parent_task_id": "GADI-001",
        "command_state_ref": "state/gadi-resident-execution/command.json",
        "execution_context_ref": "state/gadi-resident-execution/execution-context.json",
        "actuator_result_ref": "state/gadi-resident-execution/actuator-result.json",
    })


def test_missing_bundle_reports_deterministic_blockers(tmp_path):
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    seed_request(source)
    result = mod.preflight(source, runtime)
    assert result["ready"] is False
    codes = [b["code"] for b in result["blockers"]]
    assert codes == sorted(codes)
    assert "COMMAND_MISSING" in codes
    assert "EXECUTION_CONTEXT_MISSING" in codes
    assert "ACTUATOR_RESULT_MISSING" in codes
    assert result["execution_claimed"] is False


def test_coherent_bundle_is_ready(tmp_path):
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    seed_request(source)
    write(runtime / "state/gadi-resident-execution/command.json", {
        "state": "READY_FOR_RESIDENT_EXECUTION",
        "intr_decision_ref": "intr:decision:1",
        "runtime_binding_ref": "runtime:binding:1",
    })
    write(runtime / "state/gadi-resident-execution/execution-context.json", {
        "task_id": "GADI-RESIDENT-EXECUTION-001",
        "parent_task_id": "GADI-001",
        "workercoordinator_authority_observed": True,
        "worker_claim_ref": "wc:claim:1",
        "fence_ref": "wc:fence:1",
        "runtime_binding_ref": "runtime:binding:1",
        "runtime_lease_observed": False,
        "execution_subject": "subject:controlled",
        "control_surface": "surface:controlled",
        "target_class": "CONTROLLED_SIMULATION",
    })
    write(runtime / "state/gadi-resident-execution/actuator-result.json", {
        "preauthorized_controlled_surface": True,
        "credential_material_exposed": False,
        "execution_subject": "subject:controlled",
        "control_surface": "surface:controlled",
        "target_class": "CONTROLLED_SIMULATION",
        "runtime_binding_ref": "runtime:binding:1",
        "intr_decision_ref": "intr:decision:1",
    })
    result = mod.preflight(source, runtime)
    assert result["ready"] is True
    assert result["state"] == "READY_FOR_RESIDENT_CONSUMPTION"
    assert result["blocker_count"] == 0
    assert set(result["evidence_sha256"]) == {"command", "execution_context", "actuator_result"}


def test_mismatches_fail_closed(tmp_path):
    source = tmp_path / "source"
    runtime = tmp_path / "runtime"
    seed_request(source)
    write(runtime / "state/gadi-resident-execution/command.json", {
        "state": "READY_FOR_RESIDENT_EXECUTION",
        "intr_decision_ref": "intr:decision:1",
        "runtime_binding_ref": "runtime:binding:A",
    })
    write(runtime / "state/gadi-resident-execution/execution-context.json", {
        "task_id": "GADI-RESIDENT-EXECUTION-001",
        "parent_task_id": "GADI-001",
        "workercoordinator_authority_observed": True,
        "worker_claim_ref": "wc:claim:1",
        "fence_ref": "wc:fence:1",
        "runtime_binding_ref": "runtime:binding:B",
        "runtime_lease_observed": False,
        "execution_subject": "subject:A",
        "control_surface": "surface:A",
        "target_class": "CONTROLLED_SIMULATION",
    })
    write(runtime / "state/gadi-resident-execution/actuator-result.json", {
        "preauthorized_controlled_surface": True,
        "credential_material_exposed": False,
        "execution_subject": "subject:B",
        "control_surface": "surface:A",
        "target_class": "CONTROLLED_SIMULATION",
        "intr_decision_ref": "intr:decision:DIFFERENT",
    })
    result = mod.preflight(source, runtime)
    codes = {b["code"] for b in result["blockers"]}
    assert "RUNTIME_BINDING_MISMATCH" in codes
    assert "SUBJECT_BINDING_MISMATCH" in codes
    assert "ACTUATOR_INTR_DECISION_MISMATCH" in codes
    assert result["ready"] is False
