import copy
import unittest

from scripts import reconcile_hil_esrl_acceptance as mod


class ReconcileHilEsrlAcceptanceTests(unittest.TestCase):
    def intake(self):
        return {
            "schema": mod.INTAKE_SCHEMA,
            "state": "ACCEPTED",
            "task_id": mod.TASK_ID,
            "lease_id": "HIL-BROWSER-ESRL-0123456789abcdef01234567",
            "source_artifact_sha256": "sha256:" + "a" * 64,
            "lease_state": "LEASE_OPEN",
            "esrl_lease_open_observed": True,
            "post_restart_exact_byte_proof_observed": False,
            "tvc_lifecycle_receipt_observed": False,
            "broader_hil_lifecycle_complete": False,
        }

    def task_vector(self):
        return {
            "identity": f"StegVerse-Labs/.github:task:{mod.TASK_ID}",
            "profile": "task.v1",
            "vector": mod.CURRENT_VECTOR,
            "exact_metrics": {
                "blocker_count": 3,
                "evidence_complete": False,
                "activated": False,
                "propagated": False,
            },
        }

    def registry(self):
        return {
            "tasks": [{
                "task_id": mod.TASK_ID,
                "state": "HANDOFF_READY",
                "archive_eligible": False,
                "archive_reason_codes": [mod.ESRL_BLOCKER, *mod.REMAINING_BLOCKERS],
            }]
        }

    def test_exact_accepted_esrl_proposes_only_one_blocker_removal(self):
        result = mod.build_proposal(
            intake=self.intake(), task_vector=self.task_vector(), worker_registry=self.registry()
        )
        self.assertEqual(result["state"], "READY_FOR_CANONICAL_RECONCILIATION")
        self.assertEqual(result["previous_vector"], "50000000103000")
        self.assertEqual(result["proposed_vector"], "50000000102000")
        self.assertEqual(result["removed_blocker"], mod.ESRL_BLOCKER)
        self.assertEqual(result["remaining_blockers"], mod.REMAINING_BLOCKERS)
        self.assertEqual(result["proposed_blocker_count"], 2)
        self.assertEqual(result["next_runtime_stage"], "HIL_RECEIVER_READY_AND_CUSTODY")
        self.assertFalse(result["mutation_performed"])
        self.assertFalse(result["activated"])
        self.assertFalse(result["propagated"])

    def test_rejects_unaccepted_esrl(self):
        value = self.intake()
        value["state"] = "FAIL_CLOSED"
        with self.assertRaisesRegex(mod.ReconciliationError, "intake_not_accepted"):
            mod.build_proposal(intake=value, task_vector=self.task_vector(), worker_registry=self.registry())

    def test_rejects_preexisting_downstream_promotion(self):
        value = self.intake()
        value["post_restart_exact_byte_proof_observed"] = True
        with self.assertRaisesRegex(mod.ReconciliationError, "unexpected_post_restart_promotion"):
            mod.build_proposal(intake=value, task_vector=self.task_vector(), worker_registry=self.registry())

    def test_rejects_wrong_current_vector(self):
        vector = self.task_vector()
        vector["vector"] = mod.NEXT_VECTOR
        with self.assertRaisesRegex(mod.ReconciliationError, "task_vector_not_expected_pre_esrl_state"):
            mod.build_proposal(intake=self.intake(), task_vector=vector, worker_registry=self.registry())

    def test_rejects_blocker_set_drift(self):
        registry = copy.deepcopy(self.registry())
        registry["tasks"][0]["archive_reason_codes"].reverse()
        with self.assertRaisesRegex(mod.ReconciliationError, "worker_registry_blocker_set_invalid"):
            mod.build_proposal(intake=self.intake(), task_vector=self.task_vector(), worker_registry=registry)


if __name__ == "__main__":
    unittest.main()
