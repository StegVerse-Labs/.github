from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from scripts import run_gadi_targeted_runtime_if_ready as module

ROOT = Path(__file__).resolve().parents[1]
CURRENT_BINDING = "runtime://gadi/current-subject"
CURRENT_NODE = "SV-NODE-0123456789abcdef01234567"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def seed_nonclaim(runtime: Path, *, binding_ref: str = CURRENT_BINDING) -> None:
    write_json(runtime / module.COMMAND, {
        "task_id": "GADI-001",
        "command_state": "READY_FOR_RESIDENT_EXECUTION",
        "intr_admission_observed": True,
        "intr_decision_ref": "intr://gadi/1",
        "runtime_binding_ref": binding_ref,
        "control_surface": "safe-state-control",
        "target_class": "CONTROLLED_SIMULATION",
    })
    write_json(runtime / module.INTR, {
        "state": "ADMITTED",
        "intr_decision_ref": "intr://gadi/1",
    })
    write_json(runtime / module.ACTUATOR, {
        "preauthorized_controlled_surface": True,
        "credential_material_exposed": False,
        "execution_subject": "stegverse:gadi:test-subject",
        "control_surface": "safe-state-control",
        "target_class": "CONTROLLED_SIMULATION",
        "runtime_binding_ref": binding_ref,
        "intr_decision_ref": "intr://gadi/1",
    })
    write_json(runtime / module.CARRIER, {"epoch": 31})


class GADITargetedRuntimeReadinessTests(unittest.TestCase):
    def discovery_success(self, node: str = CURRENT_NODE) -> SimpleNamespace:
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "state": "CURRENT_RETAINED_RESIDENT_DISCOVERY_OBSERVED",
                "target_node_ref": node,
                "authority_effect": "NONE_DISCOVERY_ONLY",
            }) + "\n",
            stderr="",
        )

    def receipt_success(self, node: str = CURRENT_NODE) -> SimpleNamespace:
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "state": "CURRENT_RETAINED_RESIDENT_CURRENT_IPHONE_RECEIPT_READBACK_OBSERVED",
                "target_node_ref": node,
                "authority_effect": "NONE_EVIDENCE_READ_ONLY",
            }) + "\n",
            stderr="",
        )

    def binding_success(self, node: str = CURRENT_NODE) -> SimpleNamespace:
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "state": "CURRENT_RUNTIME_SUBJECT_BOUND",
                "runtime_binding_ref": CURRENT_BINDING,
                "node_id": node,
                "authority_effect": "NONE_OBSERVATION_ONLY",
            }) + "\n",
            stderr="",
        )

    def resolver_success(self) -> SimpleNamespace:
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"state": "SOURCE_RESOLUTION_COMPLETE"}) + "\n",
            stderr="",
        )

    def nonclaim_runner(self, command, **kwargs):
        command_text = " ".join(str(item) for item in command)
        if "observe_gadi_retained_resident_discovery.py" in command_text:
            return self.discovery_success()
        if "observe_gadi_current_iphone_discovery_receipt.py" in command_text:
            return self.receipt_success()
        if "materialize_gadi_runtime_binding.py" in command_text:
            return self.binding_success()
        if "resolve_gadi_resident_runtime_sources.py" in command_text:
            return self.resolver_success()
        raise AssertionError(command)

    def test_missing_nonclaim_inputs_never_attempt_targeted_execution(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            result = module.execute(ROOT, runtime, runner=self.nonclaim_runner)
        self.assertEqual(result["state"], "NONCLAIM_RUNTIME_EVIDENCE_PENDING")
        self.assertFalse(result["targeted_execution_attempted"])
        self.assertIn("COMMAND_SOURCE_MISSING", result["blockers"])
        self.assertIn("INTR_SOURCE_MISSING", result["blockers"])
        self.assertIn("ACTUATOR_SOURCE_MISSING", result["blockers"])

    def test_missing_retained_discovery_never_visits_receipt_binding_or_workercoordinator(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_nonclaim(runtime)

            def runner(command, **kwargs):
                command_text = " ".join(str(item) for item in command)
                if "observe_gadi_retained_resident_discovery.py" in command_text:
                    return SimpleNamespace(returncode=2, stdout=json.dumps({
                        "state": "RETAINED_RESIDENT_DISCOVERY_UNOBSERVED_FAIL_CLOSED",
                        "target_node_ref": None,
                    }) + "\n", stderr="")
                if "observe_gadi_current_iphone_discovery_receipt.py" in command_text:
                    raise AssertionError("receipt observer must not run without current discovery")
                if "materialize_gadi_runtime_binding.py" in command_text:
                    raise AssertionError("runtime binding must not run without current receipt readback")
                if "resolve_gadi_resident_runtime_sources.py" in command_text:
                    return self.resolver_success()
                if "run_worker_runtime.py" in command_text:
                    raise AssertionError("WorkerCoordinator must not be visited")
                raise AssertionError(command)

            result = module.execute(ROOT, runtime, runner=runner)
        self.assertIn("CURRENT_RETAINED_RESIDENT_DISCOVERY_NOT_OBSERVED", result["blockers"])
        self.assertIn("CURRENT_RETAINED_RESIDENT_CURRENT_IPHONE_RECEIPT_NOT_OBSERVED", result["blockers"])
        self.assertIn("CURRENT_RUNTIME_SUBJECT_BINDING_NOT_OBSERVED", result["blockers"])
        self.assertFalse(result["targeted_execution_attempted"])

    def test_missing_current_iphone_receipt_never_materializes_runtime_binding(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_nonclaim(runtime)

            def runner(command, **kwargs):
                command_text = " ".join(str(item) for item in command)
                if "observe_gadi_retained_resident_discovery.py" in command_text:
                    return self.discovery_success()
                if "observe_gadi_current_iphone_discovery_receipt.py" in command_text:
                    return SimpleNamespace(returncode=2, stdout=json.dumps({
                        "state": "CURRENT_IPHONE_RECEIPT_READBACK_UNOBSERVED_FAIL_CLOSED",
                        "target_node_ref": CURRENT_NODE,
                    }) + "\n", stderr="")
                if "materialize_gadi_runtime_binding.py" in command_text:
                    raise AssertionError("runtime binding must not run without current receipt readback")
                if "resolve_gadi_resident_runtime_sources.py" in command_text:
                    return self.resolver_success()
                if "run_worker_runtime.py" in command_text:
                    raise AssertionError("WorkerCoordinator must not be visited")
                raise AssertionError(command)

            result = module.execute(ROOT, runtime, runner=runner)
        self.assertIn("CURRENT_RETAINED_RESIDENT_CURRENT_IPHONE_RECEIPT_NOT_OBSERVED", result["blockers"])
        self.assertIn("CURRENT_RUNTIME_SUBJECT_BINDING_NOT_OBSERVED", result["blockers"])
        self.assertFalse(result["targeted_execution_attempted"])

    def test_discovery_and_receipt_subject_must_match_current_runtime_subject(self) -> None:
        retained = "SV-NODE-aaaaaaaaaaaaaaaaaaaaaaaa"
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_nonclaim(runtime)

            def runner(command, **kwargs):
                command_text = " ".join(str(item) for item in command)
                if "observe_gadi_retained_resident_discovery.py" in command_text:
                    return self.discovery_success(retained)
                if "observe_gadi_current_iphone_discovery_receipt.py" in command_text:
                    return self.receipt_success(retained)
                if "materialize_gadi_runtime_binding.py" in command_text:
                    return self.binding_success(CURRENT_NODE)
                if "resolve_gadi_resident_runtime_sources.py" in command_text:
                    return self.resolver_success()
                if "run_worker_runtime.py" in command_text:
                    raise AssertionError("WorkerCoordinator must not be visited")
                raise AssertionError(command)

            result = module.execute(ROOT, runtime, runner=runner)
        self.assertIn("DISCOVERY_RUNTIME_SUBJECT_MISMATCH", result["blockers"])
        self.assertIn("CURRENT_IPHONE_RECEIPT_RUNTIME_SUBJECT_MISMATCH", result["blockers"])
        self.assertFalse(result["targeted_execution_attempted"])

    def test_command_binding_must_match_current_runtime_subject(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_nonclaim(runtime, binding_ref="runtime://gadi/stale-subject")
            result = module.execute(ROOT, runtime, runner=self.nonclaim_runner)
        self.assertEqual(result["state"], "NONCLAIM_RUNTIME_EVIDENCE_PENDING")
        self.assertFalse(result["targeted_execution_attempted"])
        self.assertIn("COMMAND_RUNTIME_BINDING_NOT_CURRENT_SUBJECT", result["blockers"])

    def test_missing_current_runtime_subject_binding_never_visits_workercoordinator(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_nonclaim(runtime)

            def runner(command, **kwargs):
                command_text = " ".join(str(item) for item in command)
                if "observe_gadi_retained_resident_discovery.py" in command_text:
                    return self.discovery_success()
                if "observe_gadi_current_iphone_discovery_receipt.py" in command_text:
                    return self.receipt_success()
                if "materialize_gadi_runtime_binding.py" in command_text:
                    return SimpleNamespace(
                        returncode=2,
                        stdout=json.dumps({"state": "RUNTIME_BINDING_UNOBSERVED_FAIL_CLOSED", "runtime_binding_ref": None}) + "\n",
                        stderr="",
                    )
                if "resolve_gadi_resident_runtime_sources.py" in command_text:
                    return self.resolver_success()
                if "run_worker_runtime.py" in command_text:
                    raise AssertionError("WorkerCoordinator must not be visited")
                raise AssertionError(command)

            result = module.execute(ROOT, runtime, runner=runner)
        self.assertEqual(result["state"], "NONCLAIM_RUNTIME_EVIDENCE_PENDING")
        self.assertIn("CURRENT_RUNTIME_SUBJECT_BINDING_NOT_OBSERVED", result["blockers"])
        self.assertFalse(result["targeted_execution_attempted"])

    def test_unchanged_old_consumption_receipt_cannot_satisfy_new_visit(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_nonclaim(runtime)
            write_json(runtime / module.CONSUMPTION, {"state": "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED", "old": True})

            def runner(command, **kwargs):
                command_text = " ".join(str(item) for item in command)
                if "observe_gadi_retained_resident_discovery.py" in command_text:
                    return self.discovery_success()
                if "observe_gadi_current_iphone_discovery_receipt.py" in command_text:
                    return self.receipt_success()
                if "materialize_gadi_runtime_binding.py" in command_text:
                    return self.binding_success()
                if "resolve_gadi_resident_runtime_sources.py" in command_text:
                    return self.resolver_success()
                if "run_worker_runtime.py" in command_text:
                    return SimpleNamespace(returncode=0, stdout=json.dumps({"state": "HANDOFF_READY"}) + "\n", stderr="")
                raise AssertionError(command)

            result = module.execute(ROOT, runtime, runner=runner)
        self.assertEqual(result["state"], "TARGETED_WORKER_RUNTIME_VISITED_NO_NEW_CONSUMPTION")
        self.assertTrue(result["targeted_execution_attempted"])
        self.assertFalse(result["consumption_receipt_changed_by_invocation"])
        self.assertFalse(result["consumption_receipt_observed"])

    def test_changed_consumption_receipt_can_satisfy_new_visit(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_nonclaim(runtime)
            write_json(runtime / module.CONSUMPTION, {"state": "GADI_RESIDENT_EXECUTION_BLOCKED_FAIL_CLOSED"})

            def runner(command, **kwargs):
                command_text = " ".join(str(item) for item in command)
                if "observe_gadi_retained_resident_discovery.py" in command_text:
                    return self.discovery_success()
                if "observe_gadi_current_iphone_discovery_receipt.py" in command_text:
                    return self.receipt_success()
                if "materialize_gadi_runtime_binding.py" in command_text:
                    return self.binding_success()
                if "resolve_gadi_resident_runtime_sources.py" in command_text:
                    return self.resolver_success()
                if "run_worker_runtime.py" in command_text:
                    write_json(runtime / module.CONSUMPTION, {
                        "state": "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED",
                        "worker_claim_ref": "SHWP-GADI-RESIDENT-EXECUTION-001-G25",
                    })
                    return SimpleNamespace(returncode=0, stdout=json.dumps({"state": "COMPLETED"}) + "\n", stderr="")
                raise AssertionError(command)

            result = module.execute(ROOT, runtime, runner=runner)
        self.assertEqual(result["state"], "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED")
        self.assertTrue(result["consumption_receipt_changed_by_invocation"])
        self.assertTrue(result["consumption_receipt_observed"])
        self.assertFalse(result["workercoordinator_claim_created_by_wrapper"])

    def test_claimless_dispatcher_cli_is_readiness_gated(self) -> None:
        text = (ROOT / "scripts/dispatch_gadi_resident_execution.py").read_text(encoding="utf-8")
        self.assertIn("run_gadi_targeted_runtime_if_ready", text)
        self.assertIn("execute_if_ready", text)
        self.assertIn("--defer-worker-claim", text)


if __name__ == "__main__":
    unittest.main()
