from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from scripts import run_gadi_targeted_runtime_if_ready as module

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def seed_nonclaim(runtime: Path) -> None:
    write_json(runtime / module.COMMAND, {
        "task_id": "GADI-001",
        "command_state": "READY_FOR_RESIDENT_EXECUTION",
        "intr_admission_observed": True,
        "intr_decision_ref": "intr://gadi/1",
        "runtime_binding_ref": "runtime://gadi/1",
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
        "runtime_binding_ref": "runtime://gadi/1",
        "intr_decision_ref": "intr://gadi/1",
    })
    write_json(runtime / module.CARRIER, {"epoch": 31})


class GADITargetedRuntimeReadinessTests(unittest.TestCase):
    def resolver_success(self, *args, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"state": "SOURCE_RESOLUTION_COMPLETE"}) + "\n",
            stderr="",
        )

    def test_missing_nonclaim_inputs_never_attempt_targeted_execution(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            result = module.execute(ROOT, runtime, runner=self.resolver_success)
        self.assertEqual(result["state"], "NONCLAIM_RUNTIME_EVIDENCE_PENDING")
        self.assertFalse(result["targeted_execution_attempted"])
        self.assertIn("COMMAND_SOURCE_MISSING", result["blockers"])
        self.assertIn("INTR_SOURCE_MISSING", result["blockers"])
        self.assertIn("ACTUATOR_SOURCE_MISSING", result["blockers"])

    def test_unchanged_old_consumption_receipt_cannot_satisfy_new_visit(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_nonclaim(runtime)
            write_json(runtime / module.CONSUMPTION, {"state": "AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED", "old": True})

            def runner(command, **kwargs):
                command_text = " ".join(str(item) for item in command)
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
