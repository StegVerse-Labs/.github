import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "control" / "autonomous-work-independence-policy.json"
SELECTOR = ROOT / "scripts" / "run_task_registry_canonical_work_cycle.py"
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"


class AutonomousWorkIndependencePolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(POLICY.read_text(encoding="utf-8"))

    def test_unrelated_waiting_lane_does_not_serialize_canonical_work(self):
        rules = self.policy["independence_rules"]
        self.assertFalse(rules["blocked_org_ai_lane_blocks_unrelated_machine_work"])
        self.assertFalse(rules["external_human_wait_blocks_unrelated_machine_work"])
        self.assertFalse(rules["counterparty_wait_blocks_unrelated_machine_work"])
        self.assertFalse(rules["ecosystem_chat_parent_is_prerequisite_for_canonical_work"])
        self.assertTrue(rules["canonical_work_may_progress_when_other_lanes_wait"])

    def test_existing_connective_material_is_reused(self):
        model = self.policy["organization_ai_model"]
        self.assertEqual(
            ["WorkerCoordinator", "Interlock/InTr", "TV/TVC", "Master Records", "HB"],
            model["cross_entity_connective_material"],
        )
        self.assertFalse(model["central_ai_dispatcher_required"])
        self.assertFalse(model["second_scheduler_required"])
        self.assertFalse(model["second_workercoordinator_required"])

    def test_existing_registry_first_cycle_remains_execution_path(self):
        selector = SELECTOR.read_text(encoding="utf-8")
        consumer = CONSUMER.read_text(encoding="utf-8")
        self.assertIn('start_point": "CANONICAL_TASK_REGISTRY"', selector)
        self.assertIn("collision_check(task_id)", selector)
        self.assertIn("TASK_REGISTRY_CYCLE_ENTRYPOINT", consumer)
        self.assertIn("run_registry_cycle", consumer)

    def test_policy_preserves_governance_and_evidence_chain(self):
        progression = self.policy["required_progression"]
        self.assertIn("USE_EXISTING_WORKERCOORDINATOR_CLAIM_FENCE_WHERE_REQUIRED", progression)
        self.assertIn("GOVERN_CURRENT_TRANSITION_THROUGH_INTERLOCK_INTR", progression)
        self.assertIn("USE_TV_TVC_ONLY_FOR_CREDENTIAL_CAPABILITY_AUTHORITY", progression)
        self.assertIn("RECONSTRUCT_IN_MASTER_RECORDS", progression)
        self.assertIn("CONTINUE_WITH_NEXT_ELIGIBLE_WORK", progression)


if __name__ == "__main__":
    unittest.main()
