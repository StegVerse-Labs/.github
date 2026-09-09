from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "control" / "resident-execution-request.d" / "consume-gadi-resident-execution.py"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "gadi-resident-execution-001.json"


def load_module():
    spec = importlib.util.spec_from_file_location("gadi_resident_execution_consumer_tested", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def install_fake_micro_node(root: Path) -> None:
    target = root / "micro_node" / "gadi_resident_consumer.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        '''from dataclasses import dataclass\n\n@dataclass(frozen=True)\nclass WorkerExecutionContext:\n    worker_claim_ref: str\n    fence_ref: str\n    runtime_binding_ref: str\n    control_surface: str\n    target_class: str\n    execution_subject: str\n    workercoordinator_authority_observed: bool\n    runtime_lease_observed: bool = False\n\ndef consume_resident_defensive_command(*, command, context, actuator):\n    assert command["schema"] == "stegos.gadi-native-defensive-command.v1"\n    assert command["task_id"] == "GADI-001"\n    assert command["cosv_id"] == "10100000100000"\n    assert command["intr_admission_observed"] is True\n    assert command["runtime_binding_ref"] == context.runtime_binding_ref\n    result = actuator(command, context)\n    assert result["execution_subject"] == context.execution_subject\n    assert result["control_surface"] == context.control_surface\n    assert result["target_class"] == context.target_class\n    return {\n        "worker_claim_ref": context.worker_claim_ref,\n        "fence_ref": context.fence_ref,\n        "intr_decision_ref": command["intr_decision_ref"],\n        "runtime_binding_ref": context.runtime_binding_ref,\n        "execution_subject": context.execution_subject,\n        "control_surface": context.control_surface,\n        "target_class": context.target_class,\n        "command_consumed": True,\n        "observed_state": result["observed_state"],\n        "effect_observed": bool(result.get("effect_observed", False)),\n        "reassessment_required": bool(result.get("reassessment_required", True)),\n        "stop_condition_observed": bool(result.get("stop_condition_observed", False)),\n    }\n''',
        encoding="utf-8",
    )


def materialize_request(runtime: Path) -> None:
    target = runtime / "control" / "resident-execution-request.d" / "gadi-resident-execution-001.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(REQUEST.read_text(encoding="utf-8"), encoding="utf-8")


def command() -> dict:
    return {
        "schema": "stegos.gadi-native-defensive-command.v1",
        "task_id": "GADI-001",
        "cosv_id": "10100000100000",
        "command_state": "READY_FOR_RESIDENT_EXECUTION",
        "credential_authority": "TV/TVC",
        "intr_admission_observed": True,
        "runtime_binding_observed": True,
        "execution_authority_claimed_by_stegos": False,
        "interaction_id": "interaction-1",
        "native_ability": "CONSTRAIN_SCOPE",
        "capability_id": "cap-1",
        "capability_action": "constrain_scope",
        "target_class": "CONTROLLED_SIMULATION",
        "control_surface": "safe-state-control",
        "authorization_evidence_ref": "tvc://cap-1",
        "intr_decision_ref": "intr://decision-1",
        "runtime_binding_ref": "runtime://binding-1",
    }


def context() -> dict:
    return {
        "task_id": "GADI-RESIDENT-EXECUTION-001",
        "parent_task_id": "GADI-001",
        "worker_claim_ref": "worker://claim-1",
        "fence_ref": "worker://fence-1",
        "runtime_binding_ref": "runtime://binding-1",
        "control_surface": "safe-state-control",
        "target_class": "CONTROLLED_SIMULATION",
        "execution_subject": "stegverse:gadi:test-subject",
        "workercoordinator_authority_observed": True,
        "runtime_lease_observed": False,
    }


def actuator_result() -> dict:
    return {
        "execution_subject": "stegverse:gadi:test-subject",
        "control_surface": "safe-state-control",
        "target_class": "CONTROLLED_SIMULATION",
        "runtime_binding_ref": "runtime://binding-1",
        "intr_decision_ref": "intr://decision-1",
        "observed_state": "THREAT_INTERRUPTED",
        "effect_observed": True,
        "reassessment_required": True,
        "stop_condition_observed": True,
        "preauthorized_controlled_surface": True,
        "credential_material_exposed": False,
        "authority_effect": "NONE_EXECUTION_EVIDENCE_ONLY",
    }


def test_missing_runtime_evidence_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_module()
    materialize_request(tmp_path)
    micro = tmp_path / "micro-node-runtime"
    install_fake_micro_node(micro)
    monkeypatch.setenv("STEGVERSE_MICRO_NODE_ROOT", str(micro))
    with pytest.raises(RuntimeError, match="current GADI resident command not observed"):
        module.consume(tmp_path, tmp_path)


def test_bound_runtime_evidence_emits_subject_bound_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_module()
    materialize_request(tmp_path)
    micro = tmp_path / "micro-node-runtime"
    install_fake_micro_node(micro)
    monkeypatch.setenv("STEGVERSE_MICRO_NODE_ROOT", str(micro))
    state = tmp_path / "state" / "gadi-resident-execution"
    write_json(state / "command.json", command())
    write_json(state / "execution-context.json", context())
    write_json(state / "actuator-result.json", actuator_result())

    receipt = module.consume(tmp_path, tmp_path)
    assert receipt["state"] == "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED"
    assert receipt["task_id"] == "GADI-RESIDENT-EXECUTION-001"
    assert receipt["parent_task_id"] == "GADI-001"
    assert receipt["worker_claim_ref"] == "worker://claim-1"
    assert receipt["fence_ref"] == "worker://fence-1"
    assert receipt["intr_decision_ref"] == "intr://decision-1"
    assert receipt["runtime_binding_ref"] == "runtime://binding-1"
    assert receipt["execution_subject"] == "stegverse:gadi:test-subject"
    assert receipt["effect_observed"] is True
    assert receipt["execution_authority_minted"] is False
    assert receipt["master_records_reconciliation_claimed"] is False
    assert receipt["second_machine_required"] is False


def test_actuator_binding_mismatch_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_module()
    materialize_request(tmp_path)
    micro = tmp_path / "micro-node-runtime"
    install_fake_micro_node(micro)
    monkeypatch.setenv("STEGVERSE_MICRO_NODE_ROOT", str(micro))
    state = tmp_path / "state" / "gadi-resident-execution"
    write_json(state / "command.json", command())
    write_json(state / "execution-context.json", context())
    bad = actuator_result()
    bad["execution_subject"] = "wrong-subject"
    write_json(state / "actuator-result.json", bad)
    with pytest.raises(RuntimeError, match="actuator subject/context mismatch"):
        module.consume(tmp_path, tmp_path)
