from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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


class GADIResidentExecutionRequestTests(unittest.TestCase):
    def test_missing_runtime_evidence_fails_closed(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            materialize_request(runtime)
            micro = runtime / "micro-node-runtime"
            install_fake_micro_node(micro)
            with patch.dict(os.environ, {"STEGVERSE_MICRO_NODE_ROOT": str(micro)}):
                with self.assertRaisesRegex(RuntimeError, "current GADI resident command not observed"):
                    module.consume(runtime, runtime)

    def test_bound_runtime_evidence_emits_subject_bound_receipt(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            materialize_request(runtime)
            micro = runtime / "micro-node-runtime"
            install_fake_micro_node(micro)
            state = runtime / "state" / "gadi-resident-execution"
            write_json(state / "command.json", command())
            write_json(state / "execution-context.json", context())
            write_json(state / "actuator-result.json", actuator_result())

            with patch.dict(os.environ, {"STEGVERSE_MICRO_NODE_ROOT": str(micro)}):
                receipt = module.consume(runtime, runtime)

            self.assertEqual(receipt["state"], "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED")
            self.assertEqual(receipt["task_id"], "GADI-RESIDENT-EXECUTION-001")
            self.assertEqual(receipt["parent_task_id"], "GADI-001")
            self.assertEqual(receipt["worker_claim_ref"], "worker://claim-1")
            self.assertEqual(receipt["fence_ref"], "worker://fence-1")
            self.assertEqual(receipt["intr_decision_ref"], "intr://decision-1")
            self.assertEqual(receipt["runtime_binding_ref"], "runtime://binding-1")
            self.assertEqual(receipt["execution_subject"], "stegverse:gadi:test-subject")
            self.assertTrue(receipt["effect_observed"])
            self.assertFalse(receipt["execution_authority_minted"])
            self.assertFalse(receipt["master_records_reconciliation_claimed"])
            self.assertFalse(receipt["second_machine_required"])

    def test_actuator_binding_mismatch_fails_closed(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            materialize_request(runtime)
            micro = runtime / "micro-node-runtime"
            install_fake_micro_node(micro)
            state = runtime / "state" / "gadi-resident-execution"
            write_json(state / "command.json", command())
            write_json(state / "execution-context.json", context())
            bad = actuator_result()
            bad["execution_subject"] = "wrong-subject"
            write_json(state / "actuator-result.json", bad)

            with patch.dict(os.environ, {"STEGVERSE_MICRO_NODE_ROOT": str(micro)}):
                with self.assertRaisesRegex(RuntimeError, "actuator subject/context mismatch"):
                    module.consume(runtime, runtime)


if __name__ == "__main__":
    unittest.main()
