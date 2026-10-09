from __future__ import annotations

from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

from heartbeat_runtime.worker_assignment_functional_memory import (
    SCHEMA,
    bind_assignment_review,
    record_non_allow_functional_memory,
    reconstruct_prior_functional_memory,
)
from workers.canonical_state_transition_custody import build_state_receipt, sha256_uri, submit_state_receipt
from tests.organization_ledger_standin import publish_tampering


class WorkerAssignmentFunctionalMemoryTests(unittest.TestCase):
    def setUp(self):
        # Ledger roots are supplied, never derived from the host.
        ledger = tempfile.TemporaryDirectory()
        self.addCleanup(ledger.cleanup)
        env = patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": ledger.name})
        env.start()
        self.addCleanup(env.stop)

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

    def record(self, sequence: int, prior: str | None, *, task_id: str = "TASK-1",
               transition_id: str = "WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW") -> dict:
        """Real producer: one functional-memory state receipt appended to the tmp Organization ledger."""
        memory = {"schema": SCHEMA, "sequence": sequence, "task_id": task_id,
                  "admissibility_resolution": "DENY" if sequence % 2 else "DEFER"}
        pack_sha = sha256_uri(memory).split(":", 1)[1]
        result = submit_state_receipt(build_state_receipt(
            transition_id=transition_id,
            transition_sequence=sequence,
            subject_or_correlation_id=task_id,
            transition_outcome="DENY",
            prior_state_ref_or_hash=None if prior is None else f"sha256:{prior}",
            resulting_state_ref_or_hash=f"sha256:{pack_sha}",
            governance_decision_ref_where_applicable=None,
            transition_evidence={"functional_memory": memory},
            required_evidence_manifest=[{
                "evidence_id": f"fm:{task_id}:{sequence}",
                "evidence_type": "WORKERCOORDINATOR_NON_ALLOW_ASSIGNMENT_FUNCTIONAL_MEMORY",
                "origin_transition_id": transition_id,
                "encoding": "canonical-json",
                "sha256": pack_sha,
                "content": memory,
            }],
        ))
        self.assertEqual(result["state"], "RECORDED")
        return {"memory": memory, "receipt_sha256": result["receipt_sha256"],
                "organization_receipt_sha256": result["organization_receipt"]["receipt_sha256"]}

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
        # Real producer: appends to the tmp Organization ledger root.
        with patch(
            "heartbeat_runtime.worker_assignment_functional_memory.submit_state_receipt",
            side_effect=submit_state_receipt,
        ) as submit:
            memory = record_non_allow_functional_memory(
                task={"task_id": "TASK-1"},
                trigger={"packet_id": "P1", "source": "INDEPENDENT_TASK_CONTROL"},
                packet=bound,
            )
        self.assertEqual(memory["schema"], SCHEMA)
        self.assertEqual(memory["state"], "RECORDED")
        self.assertEqual(memory["admissibility_resolution"], "DENY")
        receipt = submit.call_args.args[0]
        self.assertEqual(memory["receipt_sha256"], sha256_uri(receipt).split(":", 1)[1])
        self.assertEqual(receipt["transition_outcome"], "DENY")
        self.assertFalse(receipt["transition_evidence"]["worker_materialized"])
        self.assertEqual(receipt["transition_evidence"]["functional_memory"]["task_registry_generation"], 84)

    def test_prior_memory_is_resolved_from_verified_organization_receipt_before_reuse(self):
        first = self.record(1, None)
        task = {"task_id": "TASK-1", "functional_memory": {
            "receipt_sha256": first["receipt_sha256"],
            "organization_receipt_sha256": first["organization_receipt_sha256"],
            "sequence": 1,
        }}
        with patch("workers.canonical_state_transition_custody.reconstruct_state_receipt") as master_records:
            rebuilt, valid, reason = reconstruct_prior_functional_memory(task)
        self.assertTrue(valid)
        self.assertIsNone(reason)
        self.assertEqual(rebuilt, first["memory"])
        master_records.assert_not_called()

    def test_prior_memory_without_organization_receipt_fails_closed(self):
        first = self.record(1, None)
        task = {"task_id": "TASK-1", "functional_memory": {"receipt_sha256": first["receipt_sha256"]}}
        rebuilt, valid, reason = reconstruct_prior_functional_memory(task)
        self.assertIsNone(rebuilt)
        self.assertFalse(valid)
        self.assertEqual(reason, "ORGANIZATION_RECEIPT_REFUSED:FAIL_CLOSED:ORGANIZATION_RECEIPT_SHA256_ABSENT")

    def test_prior_memory_receipt_bound_to_another_state_receipt_is_denied(self):
        first = self.record(1, None)
        second = self.record(2, first["receipt_sha256"])
        task = {"task_id": "TASK-1", "functional_memory": {
            "receipt_sha256": first["receipt_sha256"],
            "organization_receipt_sha256": second["organization_receipt_sha256"],
        }}
        rebuilt, valid, reason = reconstruct_prior_functional_memory(task)
        self.assertIsNone(rebuilt)
        self.assertFalse(valid)
        self.assertEqual(reason, "ORGANIZATION_RECEIPT_REFUSED:DENY:ORGANIZATION_RECEIPT_NOT_BOUND_TO_STATE_RECEIPT")

    def test_prior_memory_with_missing_retained_source_receipt_fails_closed(self):
        first = self.record(1, None)
        ledger = Path(os.environ["STEGVERSE_ORG_LEDGER_ROOT"])
        (ledger / "source-receipts" / (first["receipt_sha256"] + ".json")).unlink()
        publish_tampering(ledger)  # a loss is real only at the declared locus
        task = {"task_id": "TASK-1", "functional_memory": {
            "receipt_sha256": first["receipt_sha256"],
            "organization_receipt_sha256": first["organization_receipt_sha256"],
        }}
        rebuilt, valid, reason = reconstruct_prior_functional_memory(task)
        self.assertFalse(valid)
        self.assertEqual(reason, "ORGANIZATION_RECEIPT_REFUSED:FAIL_CLOSED:ORGANIZATION_SOURCE_RECEIPT_READBACK_MISSING")

    def test_prior_memory_without_ledger_root_reads_the_declared_locus(self):
        first = self.record(1, None)
        task = {"task_id": "TASK-1", "functional_memory": {
            "receipt_sha256": first["receipt_sha256"],
            "organization_receipt_sha256": first["organization_receipt_sha256"],
        }}
        # OL-1b: with no cache supplied, the prior memory is reconstructed from
        # the locus the Organization manifest declares, never a host path.
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("STEGVERSE_ORG_LEDGER_ROOT")
            rebuilt, valid, reason = reconstruct_prior_functional_memory(task)
        self.assertTrue(valid, reason)
        self.assertIsNotNone(rebuilt)

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

    def test_missing_pointer_recovers_latest_ordered_functional_memory_from_organization_ledger(self):
        first = self.record(1, None)
        self.record(1, None, task_id="TASK-OTHER")
        second = self.record(2, first["receipt_sha256"])
        task = {"task_id": "TASK-1"}
        with patch("workers.canonical_state_transition_custody.query_state_receipts") as master_records:
            rebuilt, valid, reason = reconstruct_prior_functional_memory(task)
        self.assertTrue(valid)
        self.assertIsNone(reason)
        self.assertEqual(rebuilt, second["memory"])
        self.assertEqual(task["functional_memory"]["sequence"], 2)
        self.assertEqual(task["functional_memory"]["receipt_sha256"], second["receipt_sha256"])
        self.assertEqual(task["functional_memory"]["organization_receipt_sha256"], second["organization_receipt_sha256"])
        self.assertTrue(task["functional_memory"]["pointer_recovered_from_organization_ledger"])
        master_records.assert_not_called()

    def test_missing_pointer_with_empty_organization_ledger_has_no_prior_memory(self):
        task = {"task_id": "TASK-1"}
        rebuilt, valid, reason = reconstruct_prior_functional_memory(task)
        self.assertEqual((rebuilt, valid, reason), (None, True, None))
        self.assertNotIn("functional_memory", task)

    def test_pointer_recovery_fails_closed_on_predecessor_chain_gap(self):
        self.record(2, None)
        task = {"task_id": "TASK-1"}
        rebuilt, valid, reason = reconstruct_prior_functional_memory(task)
        self.assertIsNone(rebuilt)
        self.assertFalse(valid)
        self.assertEqual(reason, "FUNCTIONAL_MEMORY_SEQUENCE_GAP_OR_REORDER")
        self.assertNotIn("functional_memory", task)

    def test_pointer_recovery_fails_closed_on_broken_predecessor_link(self):
        first = self.record(1, None)
        self.record(2, "a" * 64)
        self.assertIsNotNone(first)
        task = {"task_id": "TASK-1"}
        rebuilt, valid, reason = reconstruct_prior_functional_memory(task)
        self.assertFalse(valid)
        self.assertEqual(reason, "FUNCTIONAL_MEMORY_PREDECESSOR_CHAIN_INVALID")
        self.assertNotIn("functional_memory", task)

    def test_recorded_pointer_carries_verified_organization_receipt_and_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            bound = bind_assignment_review(
                root=self.root(tmp), task={"task_id": "TASK-1"}, packet=self.packet("BLOCK"),
                prior_memory=None, prior_memory_valid=True, prior_memory_reason=None,
            )
        pointer = record_non_allow_functional_memory(
            task={"task_id": "TASK-1"},
            trigger={"packet_id": "P5", "source": "INDEPENDENT_TASK_CONTROL"},
            packet=bound,
        )
        self.assertEqual(pointer["state"], "RECORDED")
        self.assertRegex(pointer["organization_receipt_sha256"], r"^sha256:[0-9a-f]{64}$")
        rebuilt, valid, reason = reconstruct_prior_functional_memory({"task_id": "TASK-1", "functional_memory": pointer})
        self.assertTrue(valid, reason)
        self.assertEqual(rebuilt["sequence"], 1)
        self.assertEqual(rebuilt["admissibility_resolution"], "DENY")

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
            "evidence_id": "predecessor-master-records-organization-record:WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW",
            "evidence_type": "PREDECESSOR_MASTER_RECORDS_ORGANIZATION_RECORD",
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
        predecessor_evidence["sha256"] = sha256_uri(predecessor_evidence["content"]).split(":", 1)[1]
        with patch(
            "heartbeat_runtime.worker_assignment_functional_memory.require_predecessor_master_records_organization_record",
            return_value=(f"sha256:{previous_hash}", [predecessor_evidence]),
        ) as require_predecessor, patch(
            "heartbeat_runtime.worker_assignment_functional_memory.submit_state_receipt",
            side_effect=submit_state_receipt,
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
            ["PREDECESSOR_MASTER_RECORDS_ORGANIZATION_RECORD", "WORKERCOORDINATOR_NON_ALLOW_ASSIGNMENT_FUNCTIONAL_MEMORY"],
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
            "heartbeat_runtime.worker_assignment_functional_memory.require_predecessor_master_records_organization_record",
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
