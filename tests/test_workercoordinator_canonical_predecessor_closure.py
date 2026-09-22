from __future__ import annotations

import unittest
from unittest.mock import patch

from heartbeat_runtime.worker_runtime_legacy import WorkerCoordinator


def closed(digest: str) -> dict:
    return {
        "state": "RECORDED",
        "reconstruction_status": "PASS",
        "required_evidence_validation_status": "PASS",
        "receipt_sha256": digest,
        "reconstructed_receipt_sha256": digest,
        "required_evidence_count": 2,
        "master_record_ref": "master-record:claim",
    }


class WorkerCoordinatorCanonicalPredecessorTests(unittest.TestCase):
    def coordinator(self) -> WorkerCoordinator:
        return object.__new__(WorkerCoordinator)

    def test_claim_fence_consumes_reconstructed_functional_memory_closure(self) -> None:
        predecessor = {
            "evidence_id": "predecessor-master-records-closure:WORKERCOORDINATOR_CLAIM_FENCE_BOUND",
            "evidence_type": "PREDECESSOR_MASTER_RECORDS_CLOSURE",
            "origin_transition_id": "WORKERCOORDINATOR_CLAIM_FENCE_BOUND",
            "encoding": "canonical-json",
            "sha256": "1" * 64,
            "content": {
                "transition_id": "WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW",
                "state": "RECORDED",
                "reconstruction_status": "PASS",
                "required_evidence_validation_status": "PASS",
                "receipt_sha256": "a" * 64,
                "reconstructed_receipt_sha256": "a" * 64,
            },
        }
        record = {
            "functional_memory_context": {
                "prior_functional_memory_receipt_sha256": "a" * 64,
            }
        }
        with patch(
            "heartbeat_runtime.worker_runtime_legacy.require_predecessor_master_records_closure",
            return_value=("sha256:" + "a" * 64, [predecessor]),
        ) as require_predecessor, patch(
            "heartbeat_runtime.worker_runtime_legacy.submit_state_receipt",
            return_value=closed("b" * 64),
        ) as submit:
            result = self.coordinator()._custody_assignment_transition(
                task={"task_id": "TASK-1", "last_checkpoint_ref": "noncanonical-checkpoint"},
                trigger={"packet_id": "P1", "source": "INDEPENDENT_TASK_CONTROL"},
                record=record,
                claim_id="CLAIM-1",
                fencing_token=7,
                worker_instance_id="WORKER-1",
            )

        require_predecessor.assert_called_once_with(
            "a" * 64,
            successor_transition_id="WORKERCOORDINATOR_CLAIM_FENCE_BOUND",
        )
        receipt = submit.call_args.args[0]
        self.assertEqual(receipt["prior_state_ref_or_hash"], "sha256:" + "a" * 64)
        self.assertNotEqual(receipt["prior_state_ref_or_hash"], "noncanonical-checkpoint")
        self.assertEqual(
            [row["evidence_type"] for row in receipt["required_evidence_manifest"]],
            ["PREDECESSOR_MASTER_RECORDS_CLOSURE", "WORKERCOORDINATOR_CLAIM_FENCE_ASSIGNMENT"],
        )
        self.assertEqual(result["state"], "RECORDED")
        self.assertEqual(result["receipt_sha256"], "b" * 64)

    def test_claim_fence_without_predecessor_does_not_invent_one(self) -> None:
        with patch(
            "heartbeat_runtime.worker_runtime_legacy.require_predecessor_master_records_closure",
            return_value=(None, []),
        ) as require_predecessor, patch(
            "heartbeat_runtime.worker_runtime_legacy.submit_state_receipt",
            return_value=closed("c" * 64),
        ) as submit:
            self.coordinator()._custody_assignment_transition(
                task={"task_id": "TASK-2", "last_checkpoint_ref": "legacy-domain-checkpoint"},
                trigger={"packet_id": "P2", "source": "INDEPENDENT_TASK_CONTROL"},
                record={},
                claim_id="CLAIM-2",
                fencing_token=8,
                worker_instance_id="WORKER-2",
            )
        require_predecessor.assert_called_once_with(
            None,
            successor_transition_id="WORKERCOORDINATOR_CLAIM_FENCE_BOUND",
        )
        receipt = submit.call_args.args[0]
        self.assertIsNone(receipt["prior_state_ref_or_hash"])
        self.assertEqual(
            [row["evidence_type"] for row in receipt["required_evidence_manifest"]],
            ["WORKERCOORDINATOR_CLAIM_FENCE_ASSIGNMENT"],
        )


if __name__ == "__main__":
    unittest.main()
