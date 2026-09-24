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
            "receipt": {
                "transition_id": "WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW",
                "transition_sequence": 1,
                "subject_or_correlation_id": "TASK-1",
                "prior_state_ref_or_hash": None,
                "transition_evidence": {"functional_memory": memory},
            },
        }
        task = {"task_id": "TASK-1", "functional_memory": {"receipt_sha256": "b" * 64}}
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


    def test_unreconstructable_predecessor_cannot_emit_successor_functional_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            bound = bind_assignment_review(
                root=self.root(tmp),
                task={"task_id": "TASK-1"},
                packet=self.packet("ADMIT"),
                prior_memory=None,
                prior_memory_valid=False,
                prior_memory_reason="state_transition_receipt_not_found",
            )
        task = {
            "task_id": "TASK-1",
            "functional_memory": {
                "schema": SCHEMA,
                "state": "RECORDED",
                "sequence": 1,
                "receipt_sha256": "c" * 64,
            },
        }
        with patch(
            "heartbeat_runtime.worker_assignment_functional_memory.submit_state_receipt"
        ) as submit:
            memory = record_non_allow_functional_memory(
                task=task,
                trigger={"packet_id": "P2", "source": "INDEPENDENT_TASK_CONTROL"},
                packet=bound,
            )
        self.assertEqual(memory["state"], "BOUNDARY")
        self.assertEqual(memory["reason"], "FUNCTIONAL_MEMORY_PREDECESSOR_NOT_RECONSTRUCTED")
        self.assertNotIn("sequence", memory)
        submit.assert_not_called()

    def test_missing_pointer_recovers_latest_ordered_functional_memory_from_master_records(self):
        memory1 = {
            "schema": SCHEMA,
            "sequence": 1,
            "task_id": "TASK-1",
            "admissibility_resolution": "DENY",
        }
        memory2 = {
            "schema": SCHEMA,
            "sequence": 2,
            "task_id": "TASK-1",
            "admissibility_resolution": "DEFER",
        }
        hash1 = "d" * 64
        hash2 = "e" * 64
        records = [
            {
                "state": "PASS",
                "receipt_sha256": hash1,
                "reconstructed_receipt_sha256": hash1,
                "required_evidence_validation_status": "PASS",
                "master_record_ref": "master-record:1",
                "receipt": {
                    "transition_id": "WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW",
                    "transition_sequence": 1,
                    "subject_or_correlation_id": "TASK-1",
                    "prior_state_ref_or_hash": None,
                    "transition_evidence": {"functional_memory": memory1},
                },
            },
            {
                "state": "PASS",
                "receipt_sha256": hash2,
                "reconstructed_receipt_sha256": hash2,
                "required_evidence_validation_status": "PASS",
                "master_record_ref": "master-record:2",
                "receipt": {
                    "transition_id": "WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW",
                    "transition_sequence": 2,
                    "subject_or_correlation_id": "TASK-1",
                    "prior_state_ref_or_hash": f"sha256:{hash1}",
                    "transition_evidence": {"functional_memory": memory2},
                },
            },
        ]
        task = {"task_id": "TASK-1"}
        with patch(
            "heartbeat_runtime.worker_assignment_functional_memory.query_state_receipts",
            return_value={"state": "PASS", "records": records},
        ):
            rebuilt, valid, reason = reconstruct_prior_functional_memory(task)
        self.assertTrue(valid)
        self.assertIsNone(reason)
        self.assertEqual(rebuilt, memory2)
        self.assertEqual(task["functional_memory"]["sequence"], 2)
        self.assertEqual(task["functional_memory"]["receipt_sha256"], hash2)
        self.assertTrue(task["functional_memory"]["pointer_recovered_from_master_records"])

    def test_pointer_recovery_fails_closed_on_predecessor_chain_gap(self):
        memory2 = {
            "schema": SCHEMA,
            "sequence": 2,
            "task_id": "TASK-1",
            "admissibility_resolution": "DENY",
        }
        hash2 = "f" * 64
        task = {"task_id": "TASK-1"}
        with patch(
            "heartbeat_runtime.worker_assignment_functional_memory.query_state_receipts",
            return_value={
                "state": "PASS",
                "records": [{
                    "state": "PASS",
                    "receipt_sha256": hash2,
                    "reconstructed_receipt_sha256": hash2,
                    "required_evidence_validation_status": "PASS",
                    "master_record_ref": "master-record:2",
                    "receipt": {
                        "transition_id": "WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW",
                        "transition_sequence": 2,
                        "subject_or_correlation_id": "TASK-1",
                        "prior_state_ref_or_hash": None,
                        "transition_evidence": {"functional_memory": memory2},
                    },
                }],
            },
        ):
            rebuilt, valid, reason = reconstruct_prior_functional_memory(task)
        self.assertIsNone(rebuilt)
        self.assertFalse(valid)
        self.assertEqual(reason, "FUNCTIONAL_MEMORY_SEQUENCE_GAP_OR_REORDER")
        self.assertNotIn("functional_memory", task)


    def test_successor_functional_memory_reconstructs_predecessor_at_emit_boundary(self):
        previous_hash = "9" * 64
        previous = {
            "schema": SCHEMA,
            "state": "RECORDED",
            "sequence": 1,
            "receipt_sha256": previous_hash,
        }
        with tempfile.TemporaryDirectory() as tmp:
            bound = bind_assignment_review(
                root=self.root(tmp),
                task={"task_id": "TASK-1"},
                packet=self.packet("BLOCK"),
                prior_memory={
                    "schema": SCHEMA,
                    "sequence": 1,
                    "task_id": "TASK-1",
                    "admissibility_resolution": "DENY",
                },
                prior_memory_valid=True,
                prior_memory_reason=None,
            )
        predecessor_evidence = {
            "evidence_id": "predecessor-master-records-closure:WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW",
            "evidence_type": "PREDECESSOR_MASTER_RECORDS_CLOSURE",
            "origin_transition_id": "WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW",
            "encoding": "canonical-json",
            "sha256": "8" * 64,
            "content": {
                "transition_id": "WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW",
                "state": "RECORDED",
                "reconstruction_status": "PASS",
                "required_evidence_validation_status": "PASS",
                "receipt_sha256": previous_hash,
                "reconstructed_receipt_sha256": previous_hash,
            },
        }
        returned = {
            "state": "RECORDED",
            "reconstruction_status": "PASS",
            "required_evidence_validation_status": "PASS",
            "receipt_sha256": "7" * 64,
            "reconstructed_receipt_sha256": "7" * 64,
            "master_record_ref": "master-record:successor",
        }
        with patch(
            "heartbeat_runtime.worker_assignment_functional_memory.require_predecessor_master_records_closure",
            return_value=(f"sha256:{previous_hash}", [predecessor_evidence]),
        ) as require_predecessor, patch(
            "heartbeat_runtime.worker_assignment_functional_memory.submit_state_receipt",
            return_value=returned,
        ) as submit:
            memory = record_non_allow_functional_memory(
                task={"task_id": "TASK-1", "functional_memory": previous},
                trigger={"packet_id": "P3", "source": "INDEPENDENT_TASK_CONTROL"},
                packet=bound,
            )

        self.assertEqual(memory["state"], "RECORDED")
        require_predecessor.assert_called_once_with(
            previous_hash,
            successor_transition_id="WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW",
        )
        receipt = submit.call_args.args[0]
        self.assertEqual(receipt["prior_state_ref_or_hash"], f"sha256:{previous_hash}")
        self.assertEqual(
            [item["evidence_type"] for item in receipt["required_evidence_manifest"]],
            ["PREDECESSOR_MASTER_RECORDS_CLOSURE", "WORKERCOORDINATOR_NON_ALLOW_ASSIGNMENT_FUNCTIONAL_MEMORY"],
        )

    def test_emit_boundary_reconstruction_failure_blocks_successor_submission(self):
        previous_hash = "6" * 64
        previous = {
            "schema": SCHEMA,
            "state": "RECORDED",
            "sequence": 1,
            "receipt_sha256": previous_hash,
        }
        with tempfile.TemporaryDirectory() as tmp:
            bound = bind_assignment_review(
                root=self.root(tmp),
                task={"task_id": "TASK-1"},
                packet=self.packet("BLOCK"),
                prior_memory={
                    "schema": SCHEMA,
                    "sequence": 1,
                    "task_id": "TASK-1",
                    "admissibility_resolution": "DENY",
                },
                prior_memory_valid=True,
                prior_memory_reason=None,
            )
        with patch(
            "heartbeat_runtime.worker_assignment_functional_memory.require_predecessor_master_records_closure",
            side_effect=RuntimeError("CANONICAL_MASTER_RECORDS_RECONSTRUCTION_HASH_MISMATCH"),
        ), patch(
            "heartbeat_runtime.worker_assignment_functional_memory.submit_state_receipt",
        ) as submit:
            memory = record_non_allow_functional_memory(
                task={"task_id": "TASK-1", "functional_memory": previous},
                trigger={"packet_id": "P4", "source": "INDEPENDENT_TASK_CONTROL"},
                packet=bound,
            )
        self.assertEqual(memory["state"], "BOUNDARY")
        self.assertEqual(memory["reason"], "CANONICAL_MASTER_RECORDS_RECONSTRUCTION_HASH_MISMATCH")
        submit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
