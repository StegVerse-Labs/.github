from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from heartbeat_runtime.worker_assignment_functional_memory import (
    SCHEMA,
    bind_assignment_review,
    record_non_allow_functional_memory,
    reconstruct_prior_functional_memory,
)


class WorkerAssignmentFunctionalMemoryTests(unittest.TestCase):
    def packet(self, verdict: str = "BLOCK") -> dict:
        return {
            "schema": "stegverse.worker-task-admission-packet/v1",
            "task_id": "TASK-1",
            "goal_id": "GOAL-1",
            "heartbeat_id": "HB-0000000W",
            "carrier_epoch": 32,
            "trigger_source": "INDEPENDENT_TASK_CONTROL",
            "review": {
                "verdict": verdict,
                "reasons": ["dependencies_complete"] if verdict != "ADMIT" else ["ALL_PREINITIATION_PREDICATES_PASS"],
                "predicates": {"dependencies_complete": verdict == "ADMIT"},
            },
            "operational_state_vector": {
                "profile": "task.v1",
                "notation": "L R U I V G O C M T B E A P",
                "vector": "10000000100001",
                "vector_state": "EMITTED",
                "authority_effect": "NONE",
            },
            "packet_sha256": "prebind",
        }

    def root(self, tmp: str) -> Path:
        root = Path(tmp)
        registry = root / "data" / "canonical-task-registry.json"
        registry.parent.mkdir(parents=True)
        registry.write_text(
            '{"schema":"stegverse.canonical-task-registry/v1","generation":84,"tasks":[{"task_id":"TASK-1"}]}',
            encoding="utf-8",
        )
        return root

    def test_non_allow_review_binds_registry_generation_cosv_and_matrix_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            bound = bind_assignment_review(
                root=self.root(tmp),
                task={"task_id": "TASK-1"},
                packet=self.packet("BLOCK"),
                prior_memory=None,
                prior_memory_valid=True,
                prior_memory_reason=None,
            )
        transition = bound["assignment_transition"]
        self.assertEqual(transition["task_registry_generation"], 84)
        self.assertEqual(transition["generation_bound_cosv_id"], "RG84:10000000100001")
        self.assertEqual(transition["admissibility_resolution"], "DENY")
        self.assertFalse(transition["worker_materialization_permitted"])
        self.assertTrue(transition["non_allow_requires_master_records"])
        self.assertNotEqual(bound["packet_sha256"], "prebind")

    def test_update_maps_to_defer_and_allow_maps_only_from_admit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.root(tmp)
            deferred = bind_assignment_review(
                root=root,
                task={"task_id": "TASK-1"},
                packet=self.packet("UPDATE"),
                prior_memory=None,
                prior_memory_valid=True,
                prior_memory_reason=None,
            )
            allowed = bind_assignment_review(
                root=root,
                task={"task_id": "TASK-1"},
                packet=self.packet("ADMIT"),
                prior_memory=None,
                prior_memory_valid=True,
                prior_memory_reason=None,
            )
        self.assertEqual(deferred["assignment_transition"]["admissibility_resolution"], "DEFER")
        self.assertEqual(allowed["assignment_transition"]["admissibility_resolution"], "ALLOW")
        self.assertTrue(allowed["assignment_transition"]["worker_materialization_permitted"])

    def test_non_allow_is_recorded_as_master_records_functional_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            bound = bind_assignment_review(
                root=self.root(tmp),
                task={"task_id": "TASK-1"},
                packet=self.packet("BLOCK"),
                prior_memory=None,
                prior_memory_valid=True,
                prior_memory_reason=None,
            )
        returned = {
            "state": "RECORDED",
            "reconstruction_status": "PASS",
            "required_evidence_validation_status": "PASS",
            "receipt_sha256": "a" * 64,
            "reconstructed_receipt_sha256": "a" * 64,
            "master_record_ref": "master-record:test",
        }
        with patch(
            "heartbeat_runtime.worker_assignment_functional_memory.submit_state_receipt",
            return_value=returned,
        ) as submit:
            memory = record_non_allow_functional_memory(
                task={"task_id": "TASK-1"},
                trigger={"packet_id": "P1", "source": "INDEPENDENT_TASK_CONTROL"},
                packet=bound,
            )
        self.assertEqual(memory["schema"], SCHEMA)
        self.assertEqual(memory["state"], "RECORDED")
        self.assertEqual(memory["admissibility_resolution"], "DENY")
        self.assertEqual(memory["receipt_sha256"], "a" * 64)
        receipt = submit.call_args.args[0]
        self.assertEqual(receipt["transition_outcome"], "DENY")
        self.assertFalse(receipt["transition_evidence"]["worker_materialized"])
        self.assertEqual(receipt["transition_evidence"]["functional_memory"]["task_registry_generation"], 84)

    def test_prior_memory_is_reconstructed_from_master_records_before_reuse(self):
        memory = {
            "schema": SCHEMA,
            "sequence": 1,
            "task_id": "TASK-1",
            "admissibility_resolution": "DEFER",
        }
        reconstruction = {
            "state": "PASS",
            "receipt_sha256": "b" * 64,
            "reconstructed_receipt_sha256": "b" * 64,
            "required_evidence_validation_status": "PASS",
            "receipt": {"transition_evidence": {"functional_memory": memory}},
        }
        task = {"functional_memory": {"receipt_sha256": "b" * 64}}
        with patch(
            "heartbeat_runtime.worker_assignment_functional_memory.reconstruct_state_receipt",
            return_value=reconstruction,
        ):
            rebuilt, valid, reason = reconstruct_prior_functional_memory(task)
        self.assertTrue(valid)
        self.assertIsNone(reason)
        self.assertEqual(rebuilt, memory)

    def test_unreconstructable_prior_memory_forces_non_allow_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            bound = bind_assignment_review(
                root=self.root(tmp),
                task={"task_id": "TASK-1"},
                packet=self.packet("ADMIT"),
                prior_memory=None,
                prior_memory_valid=False,
                prior_memory_reason="missing",
            )
        self.assertEqual(bound["review"]["verdict"], "BLOCK")
        self.assertIn("FUNCTIONAL_MEMORY_RECONSTRUCTION_FAILED", bound["review"]["reasons"])
        self.assertEqual(bound["assignment_transition"]["admissibility_resolution"], "DENY")


if __name__ == "__main__":
    unittest.main()
