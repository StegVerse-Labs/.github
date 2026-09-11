from __future__ import annotations

import json
import unittest
from pathlib import Path

from heartbeat_runtime.worker_runtime import WorkerCoordinator

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "control" / "worker-registry.d" / "gadi-resident-execution-001.json"
HANDOFF = ROOT / "handoffs" / "GADI-RESIDENT-EXECUTION-001.json"
ADAPTER = ROOT / "control" / "process-worker-adapters.d" / "gadi-resident-execution-001.json"


class GADIWorkerCoordinatorRegistrationTests(unittest.TestCase):
    def load(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def setUp(self) -> None:
        self.registry = self.load(REGISTRY)
        self.task = self.registry["tasks"][0]
        self.worker = self.registry["workers"][0]
        self.handoff = self.load(HANDOFF)
        self.adapter = self.load(ADAPTER)["adapters"][0]

    def test_independent_admission_projects_existing_handoff_authority(self) -> None:
        admission = self.task["admission"]
        self.assertEqual(admission["authority_source"], "handoffs/GADI-RESIDENT-EXECUTION-001.json#authority")
        self.assertEqual(admission["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertEqual(admission["claim_state"], "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM")
        self.assertTrue(admission["fresh_fence_required"])
        self.assertEqual(admission["minimum_fencing_token_exclusive"], 24)
        self.assertFalse(admission["heartbeat_grants_execution_authority"])
        self.assertFalse(admission["carrier_trigger_required"])
        self.assertFalse(self.handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(self.handoff["authority"]["request_grants_execution_authority"])

    def test_worker_uses_enabled_preflight_gated_adapter(self) -> None:
        self.assertTrue(self.adapter["enabled"])
        self.assertEqual(self.worker["adapter_ref"], self.adapter["adapter_ref"])
        self.assertEqual(self.adapter["adapter_ref"], "process:gadi-resident-execution-v2-preflight-gated")
        self.assertIn("gadi_resident_defensive_execution", self.worker["capabilities"])
        self.assertIn("gadi_resident_defensive_execution", self.adapter["capabilities"])

    def test_runtime_predicates_are_not_terminal_worker_dependencies(self) -> None:
        self.assertEqual(self.handoff["task"]["dependencies"], [])
        self.assertEqual(
            self.handoff["task"]["coordination_refs"],
            ["GADI-001", "STEGVERSE-CANONICAL-WORK-COORDINATION-001", "TVC-CAPABILITY-RUNTIME-002"],
        )
        blockers = set(self.handoff["admissible_existence"]["blockers"])
        self.assertIn("CURRENT_GADI_INTR_ADMISSION_NOT_OBSERVED", blockers)
        self.assertIn("CURRENT_GADI_RUNTIME_BINDING_NOT_OBSERVED", blockers)
        self.assertIn("CONTROLLED_PREAUTHORIZED_ACTUATOR_RESULT_NOT_OBSERVED", blockers)

    def test_finite_cost_basis_is_resolvable_without_claiming_runtime_measurement(self) -> None:
        runtime = WorkerCoordinator(ROOT, adapters={})
        budget, basis = runtime._expiry_budget(self.task)
        self.assertEqual(basis, "TASK_CLASS_COST_BASIS")
        self.assertEqual(budget, 16)
        record = self.load(ROOT / self.task["cost_basis_ref"])
        self.assertEqual(record["sample_count"], 0)
        self.assertEqual(record["hb_estimate"]["confidence"], "LOW")
        self.assertEqual(record["estimate_basis"], "CONSERVATIVE_SOURCE_BOUNDED_ONE_SHOT_NOT_EMPIRICAL_RUNTIME_MEASUREMENT")

    def test_worker_selection_contract_is_resolvable_when_adapter_is_loaded(self) -> None:
        runtime = WorkerCoordinator(ROOT, adapters={self.adapter["adapter_ref"]: object()})
        selected = runtime._worker_for(self.task, {"workers": [self.worker]})
        self.assertIsNotNone(selected)
        self.assertEqual(selected["worker_id"], "gadi-resident-execution-worker")


if __name__ == "__main__":
    unittest.main()
