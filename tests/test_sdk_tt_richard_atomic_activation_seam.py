from __future__ import annotations

import inspect
import json
import unittest
from pathlib import Path

from heartbeat_runtime.worker_runtime_legacy import WorkerCoordinator


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001"


class TestRichardAtomicActivationSeam(unittest.TestCase):
    def test_executable_handoff_requires_atomic_constitutive_activation(self) -> None:
        handoff = json.loads((ROOT / "handoffs" / f"{TASK_ID}.json").read_text(encoding="utf-8"))
        activation = handoff["activation"]
        self.assertTrue(activation["constitutive_transition_required"])
        self.assertEqual(activation["constitutive_transition_id"], "ACTIVATE_TASK_AND_CREATE_BIND_WORKER")
        self.assertTrue(activation["project_active_only_after_master_records_closure"])
        self.assertFalse(activation["invoke_immediately_after_projection"])

    def test_registry_fragment_starts_without_task_bound_worker(self) -> None:
        fragment = json.loads(
            (ROOT / "control" / "worker-registry.d" / "sdk-tt-richard-seam-authentic-runtime-001.json").read_text(encoding="utf-8")
        )
        task = fragment["tasks"][0]
        self.assertEqual(task["state"], "HANDOFF_READY")
        self.assertIsNone(task["claim_id"])
        self.assertIsNone(task["worker_id"])
        self.assertIsNone(task["worker_instance_id"])
        self.assertEqual(fragment["workers"], [])

    def test_shared_provider_exposes_atomic_activation_capability(self) -> None:
        adapter = json.loads(
            (ROOT / "control" / "process-worker-adapters.d" / "stegagents-governed-runtime-001.json").read_text(encoding="utf-8")
        )
        provider = json.loads(
            (ROOT / "control" / "worker-registry.d" / "stegagents-governed-runtime-001.json").read_text(encoding="utf-8")
        )
        self.assertIn("stegagents_atomic_task_worker_activation", adapter["adapters"][0]["capabilities"])
        self.assertIn("stegagents_atomic_task_worker_activation", provider["workers"][0]["capabilities"])

    def test_workercoordinator_closes_constitutive_transition_before_active_projection(self) -> None:
        source = inspect.getsource(WorkerCoordinator._activate_from_trigger)
        claim_custody = source.index("assignment_custody = self._custody_assignment_transition")
        prepare = source.index("constitutive_activation = self._prepare_constitutive_activation")
        projection = source.index('registry["generation"] = generation')
        active = source.index('"state": "ACTIVE"')
        self.assertLess(claim_custody, prepare)
        self.assertLess(prepare, projection)
        self.assertLess(projection, active)

    def test_constitutive_helper_requires_master_records_exact_closure(self) -> None:
        source = inspect.getsource(WorkerCoordinator._prepare_constitutive_activation)
        self.assertIn('transition.get("transition_id") == "ACTIVATE_TASK_AND_CREATE_BIND_WORKER"', source)
        self.assertIn('transition.get("state") == "RECORDED"', source)
        self.assertIn('transition.get("reconstruction_status") == "PASS"', source)
        self.assertIn('transition.get("required_evidence_validation_status") == "PASS"', source)
        self.assertIn('transition.get("receipt_sha256") == transition.get("reconstructed_receipt_sha256")', source)
        self.assertIn('"task_state_during_admission": "HANDOFF_READY"', source)
        self.assertIn('"task_worker_binding_projected": False', source)
        self.assertIn('"task_invoked": False', source)

    def test_initial_projection_does_not_immediately_invoke_test3(self) -> None:
        source = inspect.getsource(WorkerCoordinator._activate_from_trigger)
        branch = source[source.index("if constitutive_activation is not None:"):]
        self.assertIn("invocation_deferred_until_post_projection_cycle=True", branch)
        self.assertLess(branch.index("return True"), branch.index("self._invoke"))

    def test_shared_worker_bridge_uses_preactivation_mode(self) -> None:
        source = (ROOT / "workers" / "stegagents_governed_runtime_worker.py").read_text(encoding="utf-8")
        self.assertIn('TEST3_TASK_ID = "SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001"', source)
        self.assertIn('"runtime_module": "src.atomic_task_worker_activation_runtime"', source)
        self.assertIn('"operation_mode": "PREPARE_ATOMIC_ACTIVATION"', source)
        self.assertIn('"state": "HANDOFF_READY" if profile["task_id"] == TEST3_TASK_ID else "COMPLETED"', source)
        self.assertIn('"ACTIVATE_TASK_AND_CREATE_BIND_WORKER"', source)


if __name__ == "__main__":
    unittest.main()
