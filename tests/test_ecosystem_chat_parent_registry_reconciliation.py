from __future__ import annotations

import json
import unittest
from pathlib import Path

from heartbeat_runtime.worker_runtime_legacy import WorkerCoordinator


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "control" / "worker-registry.json"
FRAGMENT = ROOT / "control" / "worker-registry.d" / "ecosystem-chat-sovereign-inference-parent-001.json"
HANDOFF = ROOT / "handoffs" / "SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json"
RECOVERY = ROOT / "receipts" / "ecosystem-chat-sovereign-inference" / "orphan-recovery-HB28.json"
VECTOR = ROOT / "control" / "task-vectors" / "SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json"
AUTH = ROOT / "authorizations" / "SHWP-ECOSYSTEM-CHAT-INFERENCE-001-independent-parent.json"

TASK_ID = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class EcosystemChatParentRegistryReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.registry = load(REGISTRY)
        self.fragment = load(FRAGMENT)
        self.handoff = load(HANDOFF)
        self.recovery = load(RECOVERY)
        self.vector = load(VECTOR)
        self.auth = load(AUTH)
        self.task = next(row for row in self.registry["tasks"] if row.get("task_id") == TASK_ID)
        self.fragment_task = next(row for row in self.fragment["tasks"] if row.get("task_id") == TASK_ID)

    def test_terminal_recovery_is_not_reused_as_parent_authority(self):
        self.assertEqual(self.recovery["state"], "PASS")
        self.assertEqual(self.recovery["recovery_fencing_token"], 22)
        self.assertTrue(self.recovery["old_authority_ended"])
        self.assertFalse(self.recovery["old_authority_reused"])
        self.assertFalse(self.recovery["successor_authority_granted"])

        prior = self.task["prior_authority_terminalization"]
        self.assertEqual(prior["old_fencing_token"], 20)
        self.assertEqual(prior["recovery_fencing_token"], 22)
        self.assertTrue(prior["old_authority_ended"])
        self.assertFalse(prior["old_authority_reused"])
        self.assertFalse(prior["recovery_authority_reused"])

    def test_historical_registry_projection_preserves_recovery_evidence(self):
        self.assertEqual(self.task["state"], "HANDOFF_READY")
        self.assertEqual(self.task["executor_binding"], "AUTHORIZED")
        self.assertIsNone(self.task["claim_id"])
        self.assertIsNone(self.task["worker_id"])
        self.assertIsNone(self.task["worker_instance_id"])
        self.assertIsNone(self.task["heartbeat_timing"])
        self.assertIsNone(self.task["lease"])
        self.assertIsNone(self.task["block_ref"])

        historical_admission = self.task["admission"]
        self.assertEqual(historical_admission["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertEqual(historical_admission["claim_state"], "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM")
        self.assertTrue(historical_admission["fresh_fence_required"])
        self.assertEqual(historical_admission["minimum_fencing_token_exclusive"], 22)
        self.assertFalse(historical_admission["heartbeat_grants_execution_authority"])
        self.assertFalse(historical_admission["recovery_grants_parent_execution_authority"])

        self.assertEqual(self.fragment_task["state"], "HANDOFF_READY")
        self.assertEqual(self.fragment_task["executor_binding"], "AUTHORIZED")
        self.assertNotIn("source_state_vector_ref", self.fragment_task)
        self.assertNotIn("machine_readable_state", self.fragment_task)
        self.assertEqual(self.fragment["vector_projection_owner"], "control/worker-registry.json")
        self.assertFalse(self.fragment["vector_duplicate_source_allowed"])

    def test_independent_admission_runtime_will_consider_parent_candidate(self):
        runtime = WorkerCoordinator.__new__(WorkerCoordinator)
        observed: list[str] = []

        def activate(registry, trigger, carrier_epoch, cost_log, events):
            observed.append(trigger["task_id"])
            return True

        runtime._activate_from_trigger = activate
        count = runtime._activate_independently_admitted_tasks(
            {"tasks": [dict(self.task)]},
            31,
            {"records": []},
            [],
            target_task_id=TASK_ID,
        )
        self.assertEqual(count, 1)
        self.assertEqual(observed, [TASK_ID])

    def test_current_parent_fragment_and_handoff_use_authoritative_fence_floor(self):
        historical_admission = self.task["admission"]
        fragment_admission = self.fragment_task["admission"]
        handoff_activation = self.handoff["activation"]
        current_floor = self.auth["minimum_fencing_token_exclusive"]

        self.assertEqual(historical_admission["minimum_fencing_token_exclusive"], 22)
        self.assertEqual(current_floor, 24)
        self.assertEqual(fragment_admission["minimum_fencing_token_exclusive"], current_floor)
        self.assertEqual(handoff_activation["minimum_fencing_token_exclusive"], current_floor)
        self.assertGreater(current_floor, self.recovery["recovery_fencing_token"])
        self.assertTrue(fragment_admission["fresh_fence_required"])
        self.assertTrue(handoff_activation["fresh_fence_required"])
        self.assertFalse(fragment_admission["recovery_grants_parent_execution_authority"])
        self.assertFalse(handoff_activation["recovery_reacquisition_allowed"])

    def test_cosv_vector_is_emitted_and_bound_to_parent(self):
        cosv = self.task["machine_readable_state"]["cosv"]
        self.assertEqual(cosv["profile"], "task.v1")
        self.assertEqual(cosv["notation"], "L R U I V G O C M T B E A P")
        self.assertEqual(cosv["width"], 14)
        self.assertEqual(cosv["vector"], "50000000100000")
        self.assertEqual(cosv["vector_state"], "EMITTED")
        self.assertEqual(self.vector["vector"], cosv["vector"])
        self.assertEqual(self.vector["profile"], cosv["profile"])
        self.assertEqual(self.task["source_state_vector_ref"], "control/task-vectors/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json")


if __name__ == "__main__":
    unittest.main()
