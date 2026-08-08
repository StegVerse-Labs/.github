from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.project_heartbeat_workers import evaluate as evaluate_status
from scripts.query_worker_status import query
from scripts.evaluate_goal_convergence import evaluate as evaluate_convergence
from tests.test_heartbeat_runtime import handoff, write


class StatusFailClosedConvergenceTests(unittest.TestCase):
    def test_invalid_fence_is_non_archivable(self):
        h = handoff("TASK-A")
        task = {
            "task_id": "TASK-A", "goal_id": "TASK-A", "state": "ACTIVE", "executor_binding": "BOUND",
            "worker_id": "worker", "worker_instance_id": "instance", "claim_id": "claim",
            "heartbeat_timing": {"start_epoch": 1, "last_response_epoch": 1, "last_transition_epoch": 1, "current_transition": "WORK", "transition_sequence": 1, "max_missing_response_beats": 2, "expiry_epoch": 10, "expiry_basis": "TASK_CLASS_COST_BASIS", "fencing_token": 0},
            "last_checkpoint_ref": "checkpoints/workers/TASK-A/HB1-G1.json", "archive_reason_codes": [], "evidence_refs": ["master-records:checkpoint"]
        }
        projection, errors = evaluate_status(task, h, [], 2)
        self.assertTrue(errors)
        self.assertFalse(projection["archive_eligible"])
        self.assertIn("VALIDATION_ERROR_FAIL_CLOSED", projection["archive_reason_codes"])

    def test_ambiguous_executor_is_observable_and_not_resolved(self):
        h = handoff("TASK-A")
        h["activation"]["executor_binding"] = "AUTHORIZED"
        h["activation"]["authorization_ref"] = "auth/TASK-A.json"
        task = {"task_id": "TASK-A", "goal_id": "TASK-A", "state": "HANDOFF_READY", "executor_binding": "AUTHORIZED", "worker_id": None, "worker_instance_id": None, "claim_id": None, "heartbeat_timing": None, "archive_reason_codes": [], "evidence_refs": []}
        workers = [
            {"worker_id": "a", "status": "AVAILABLE", "adapter_ref": "x", "capabilities": ["fixture_execute"]},
            {"worker_id": "b", "status": "AVAILABLE", "adapter_ref": "x", "capabilities": ["fixture_execute"]},
        ]
        projection, _ = evaluate_status(task, h, workers, 1)
        self.assertFalse(projection["executor_resolved"])
        self.assertFalse(projection["archive_eligible"])
        self.assertIn("EXECUTOR_AMBIGUOUS", projection["archive_reason_codes"])

    def test_query_is_deterministic_observational_and_includes_checkpoint_evidence(self):
        status = {"schema": "stegverse.heartbeat-worker-status/v0.3", "source_registry_generation": 9, "heartbeat_epoch": 5, "tasks": [
            {"task_id": "B", "goal_id": "G2", "state": "BLOCKED", "archive_eligible": False, "archive_reason_codes": ["BLOCKED_UNCLAIMED"], "worker_id": None, "claim_id": None, "fencing_token": None, "last_checkpoint_ref": "cp-b", "next_authorized_action": "wait", "evidence_refs": ["e2"]},
            {"task_id": "A", "goal_id": "G1", "state": "COMPLETED", "archive_eligible": True, "archive_reason_codes": [], "worker_id": None, "claim_id": None, "fencing_token": 1, "last_checkpoint_ref": "cp-a", "next_authorized_action": "none", "evidence_refs": ["e1"]}
        ]}
        result = query(status, states={"BLOCKED"})
        self.assertTrue(result["observational_only"])
        self.assertFalse(result["execution_authority"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["tasks"][0]["task_id"], "B")
        self.assertEqual(result["tasks"][0]["last_checkpoint_ref"], "cp-b")
        self.assertEqual(result["tasks"][0]["evidence_refs"], ["e2"])

    def test_completed_root_without_unresolved_descendants_converges(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            root_task = {"task_id": "ROOT", "goal_id": "ROOT", "state": "COMPLETED", "handoff_ref": "handoffs/ROOT.json", "claim_id": None, "worker_id": None, "evidence_refs": ["master-records:final"]}
            write(root / "handoffs/ROOT.json", handoff("ROOT"))
            result = evaluate_convergence({"generation": 1, "tasks": [root_task]}, root)
            goal = result["goals"][0]
            self.assertTrue(goal["converged"])
            self.assertEqual(goal["reason_codes"], [])

    def test_unresolved_descendant_prevents_convergence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            root_h = handoff("ROOT")
            child_h = handoff("CHILD", parent_task_id="ROOT")
            write(root / "handoffs/ROOT.json", root_h)
            write(root / "handoffs/CHILD.json", child_h)
            tasks = [
                {"task_id": "ROOT", "goal_id": "ROOT", "state": "COMPLETED", "handoff_ref": "handoffs/ROOT.json", "claim_id": None, "worker_id": None, "evidence_refs": ["master-records:final"]},
                {"task_id": "CHILD", "goal_id": "CHILD", "state": "BLOCKED", "handoff_ref": "handoffs/CHILD.json", "claim_id": None, "worker_id": None, "evidence_refs": []},
            ]
            result = evaluate_convergence({"generation": 2, "tasks": tasks}, root)
            goal = next(item for item in result["goals"] if item["root_task_id"] == "ROOT")
            self.assertFalse(goal["converged"])
            self.assertIn("UNRESOLVED_DESCENDANTS", goal["reason_codes"])
            self.assertIn("CUSTODY_OR_RECONSTRUCTION_INCOMPLETE", goal["reason_codes"])


if __name__ == "__main__":
    unittest.main()
