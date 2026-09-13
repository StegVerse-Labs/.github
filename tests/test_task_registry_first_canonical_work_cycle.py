import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_task_registry_canonical_work_cycle.py"
spec = importlib.util.spec_from_file_location("registry_cycle", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def record(task_id, *, checkout="CHECKED_OUT", state="PROPOSED", human_action=None):
    return {
        "schema": "stegverse.canonical-task-record/v1",
        "task_id": task_id,
        "coordination_state": state,
        "checkout_state": checkout,
        "allowed_next_transitions": ["INGRESS_ADMITTED"],
        "human_action_ref": human_action,
        "runtime_requirements": {"capabilities": ["canonical_work_ingress"]},
        "worker_claim": {"authority": "WORKERCOORDINATOR", "claim_ref": None, "fence_ref": None, "projection_only": True},
        "authority_model": {"task_registry_mints_execution_authority": False, "interlock_intr_required_for_governed_ingress_egress": True},
    }


class TaskRegistryFirstCanonicalWorkCycleTests(unittest.TestCase):
    def test_candidate_requires_existing_registry_identity_and_machine_ingress_contract(self):
        self.assertTrue(module.machine_ingress_candidate(record("A-001")))
        self.assertFalse(module.machine_ingress_candidate(record("A-001", state="INGRESS_ADMITTED")))
        self.assertFalse(module.machine_ingress_candidate(record("A-001", human_action="USER_ONLY")))

    def test_progression_controller_is_not_selected_as_product_work(self):
        controller = record(module.PROGRESSION_CONTROLLER_TASK_ID)
        self.assertFalse(module.machine_ingress_candidate(controller))

    def test_explicit_request_task_can_be_excluded_from_registry_pool(self):
        self.assertFalse(module.machine_ingress_candidate(record("A-001"), {"A-001"}))
        self.assertTrue(module.machine_ingress_candidate(record("B-001"), {"A-001"}))

    def test_checked_out_candidates_sort_before_unclaimed_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "B-001.json").write_text(json.dumps(record("B-001", checkout="UNCLAIMED")), encoding="utf-8")
            (root / "A-001.json").write_text(json.dumps(record("A-001")), encoding="utf-8")
            rows = module.load_candidates(root)
            self.assertEqual([r["task_id"] for r in rows], ["A-001", "B-001"])

    def test_excluded_task_is_absent_from_sorted_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "A-001.json").write_text(json.dumps(record("A-001")), encoding="utf-8")
            (root / "B-001.json").write_text(json.dumps(record("B-001")), encoding="utf-8")
            rows = module.load_candidates(root, {"A-001"})
            self.assertEqual([r["task_id"] for r in rows], ["B-001"])

    def test_selection_skips_collision_and_uses_existing_continue_disposition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "A-001.json").write_text(json.dumps(record("A-001")), encoding="utf-8")
            (root / "B-001.json").write_text(json.dumps(record("B-001")), encoding="utf-8")
            dispositions = {
                "A-001": {"schema": "stegverse.task-registry-checkin-disposition/v1", "task_id": "A-001", "disposition": "STOP_COLLISION", "authority_effect": "NONE"},
                "B-001": {"schema": "stegverse.task-registry-checkin-disposition/v1", "task_id": "B-001", "disposition": "CONTINUE", "authority_effect": "NONE"},
            }
            with mock.patch.object(module, "collision_check", side_effect=lambda task_id: dispositions[task_id]):
                selected, considered = module.select_task(root)
            self.assertEqual(selected["task_id"], "B-001")
            self.assertEqual([row["disposition"] for row in considered], ["STOP_COLLISION", "CONTINUE"])

    def test_selection_does_not_mint_claim_or_transition_authority(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"workercoordinator_claim_or_fence_minted": False', text)
        self.assertIn('"interlock_intr_transition_authority_preserved": True', text)
        self.assertIn('"task_registry_mints_execution_authority": False', text)
        self.assertIn('CALLER_SURFACE = "INTERNAL_CANONICAL_WORK_BOOTSTRAP"', text)


if __name__ == "__main__":
    unittest.main()
