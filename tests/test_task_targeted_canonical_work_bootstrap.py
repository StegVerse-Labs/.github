from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

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


class TaskTargetedCanonicalWorkBootstrapTests(unittest.TestCase):
    def test_exact_proposed_task_is_resolved_without_minting_authority(self):
        module = load_module()
        selected = module.resolve_target_task({"tasks": [task()]}, "T1")
        self.assertEqual(selected["task_id"], "T1")
        self.assertEqual(selected["coordination_state"], "PROPOSED")
        self.assertIsNone(selected["worker_claim"]["claim_ref"])
        self.assertIsNone(selected["worker_claim"]["fence_ref"])

    def test_invalid_target_conditions_fail_closed(self):
        module = load_module()
        cases = [
            ({"tasks": []}, "T1"),
            ({"tasks": [task(), task()]}, "T1"),
            ({"tasks": [task(state="INGRESS_ADMITTED")]}, "T1"),
            ({"tasks": [task(allowed=[])]}, "T1"),
            ({"tasks": [task(claim_ref="claim:1")]}, "T1"),
            ({"tasks": [task(fence_ref="fence:1")]}, "T1"),
        ]
        for registry, task_id in cases:
            with self.subTest(registry=registry, task_id=task_id):
                with self.assertRaises(SystemExit) as ctx:
                    module.resolve_target_task(registry, task_id)
                self.assertTrue(str(ctx.exception).startswith("FAIL_CLOSED:"))

    def test_authority_model_drift_fails_closed(self):
        module = load_module()
        value = task()
        value["authority_model"]["worker_claim_authority"] = "TASK_REGISTRY"
        with self.assertRaisesRegex(SystemExit, r"FAIL_CLOSED: worker_claim_authority_drift"):
            module.resolve_target_task({"tasks": [value]}, "T1")

    def test_wrapper_forwards_task_id_to_bootstrap(self):
        source = WRAPPER.read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--task-id"', source)
        self.assertIn('"--task-id",', source)
        self.assertIn("args.task_id", source)

    def test_bootstrap_projection_is_selected_task_specific(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("def project_registry(*, task_id:", source)
        self.assertIn('task.get("task_id") == task_id', source)
        self.assertIn('f"canonical-task-registry.after-ingress.{task_id}.json"', source)
        self.assertIn('f"canonical-work-event-bootstrap.{args.task_id}.latest.json"', source)


if __name__ == "__main__":
    unittest.main()
