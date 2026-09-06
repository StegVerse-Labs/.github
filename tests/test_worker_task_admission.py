from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from heartbeat_runtime import WorkerCoordinator
from heartbeat_runtime.admitted_worker_runtime import WorkerCoordinator as AdmittedWorkerCoordinator
from heartbeat_runtime.worker_task_admission import review_worker_task_admission


class WorkerTaskAdmissionTests(unittest.TestCase):
    def base(self):
        task = {
            "task_id": "TASK-1",
            "goal_id": "GOAL-1",
            "state": "HANDOFF_READY",
            "worker_id": None,
            "worker_instance_id": None,
            "claim_id": None,
            "heartbeat_timing": None,
            "archive_eligible": False,
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "handoff_ref": "handoffs/TASK-1.json",
        }
        handoff = {
            "task": {"task_id": "TASK-1"},
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
        }
        registry = {"schema": "stegverse.heartbeat-worker-registry/v0.1", "generation": 4, "tasks": [task], "workers": []}
        return task, handoff, registry

    def review(self, **overrides):
        task, handoff, registry = self.base()
        task.update(overrides.pop("task", {}))
        handoff.update(overrides.pop("handoff", {}))
        with tempfile.TemporaryDirectory() as tmp:
            return review_worker_task_admission(
                root=Path(tmp), task=task, handoff=handoff, registry=registry,
                carrier_epoch=32, trigger_source="INDEPENDENT_TASK_CONTROL",
                execution_authorized=overrides.pop("execution_authorized", True),
                dependencies_complete=overrides.pop("dependencies_complete", True),
                worker_resolved=overrides.pop("worker_resolved", True),
                semantic_state_current=overrides.pop("semantic_state_current", True),
            )

    def test_package_exports_admitted_coordinator(self):
        self.assertIs(WorkerCoordinator, AdmittedWorkerCoordinator)

    def test_valid_packet_admits_without_granting_authority(self):
        packet = self.review()
        self.assertEqual(packet["review"]["verdict"], "ADMIT")
        self.assertEqual(packet["heartbeat_id"], "HB-0000000W")
        self.assertFalse(packet["authority"]["review_grants_execution_authority"])
        self.assertFalse(packet["authority"]["claim_authority"])
        self.assertFalse(packet["authority"]["fence_authority"])
        self.assertFalse(packet["authority"]["lease_authority"])
        self.assertEqual(len(packet["digests"]["task_sha256"]), 64)
        self.assertEqual(len(packet["packet_sha256"]), 64)
        self.assertTrue(packet["review"]["predicates"]["readme_impact_complete"])
        self.assertFalse(packet["readme_impact"]["required"])

    def test_dependency_failure_blocks(self):
        packet = self.review(dependencies_complete=False)
        self.assertEqual(packet["review"]["verdict"], "BLOCK")
        self.assertIn("dependencies_complete", packet["review"]["reasons"])

    def test_execution_authority_failure_blocks(self):
        packet = self.review(execution_authorized=False)
        self.assertEqual(packet["review"]["verdict"], "BLOCK")
        self.assertIn("execution_authorized", packet["review"]["reasons"])

    def test_existing_claim_or_worker_blocks(self):
        packet = self.review(task={"claim_id": "OLD", "worker_id": "worker-x"})
        self.assertEqual(packet["review"]["verdict"], "BLOCK")
        self.assertIn("no_existing_assignment", packet["review"]["reasons"])

    def test_stale_source_state_requires_update(self):
        packet = self.review(semantic_state_current=False)
        self.assertEqual(packet["review"]["verdict"], "UPDATE")
        self.assertIn("SOURCE_STATE_STALE", packet["review"]["reasons"])

    def test_handoff_identity_mismatch_requires_update(self):
        packet = self.review(handoff={"task": {"task_id": "OTHER"}})
        self.assertEqual(packet["review"]["verdict"], "UPDATE")
        self.assertIn("HANDOFF_TASK_IDENTITY_STALE", packet["review"]["reasons"])

    def test_terminal_task_retires(self):
        packet = self.review(task={"state": "COMPLETED"})
        self.assertEqual(packet["review"]["verdict"], "RETIRE")

    def test_non_tvc_credential_blocks(self):
        packet = self.review(task={"credential_authority": "OTHER"})
        self.assertEqual(packet["review"]["verdict"], "BLOCK")
        self.assertIn("credential_authority_tvc_only", packet["review"]["reasons"])

    def test_github_token_authority_blocks(self):
        packet = self.review(task={"github_token_runtime_authority": "TOKEN"})
        self.assertEqual(packet["review"]["verdict"], "BLOCK")
        self.assertIn("github_token_runtime_authority_none", packet["review"]["reasons"])

    def test_readme_required_but_undeclared_blocks(self):
        packet = self.review(task={"readme_impact_required": True})
        self.assertEqual(packet["review"]["verdict"], "BLOCK")
        self.assertIn("readme_impact_complete", packet["review"]["reasons"])
        self.assertEqual(packet["readme_impact"]["disposition"], "README_IMPACT_UNDECLARED")

    def test_material_function_change_requires_readme_update(self):
        packet = self.review(task={
            "readme_impact_required": True,
            "readme_impact": {
                "material_function_change": True,
                "readme_path": "README.md",
                "readme_updated_in_change_set": False,
                "evidence_refs": ["diff:heartbeat_runtime/worker_task_admission.py"],
            },
        })
        self.assertEqual(packet["review"]["verdict"], "BLOCK")
        self.assertIn("readme_impact_complete", packet["review"]["reasons"])
        self.assertEqual(packet["readme_impact"]["disposition"], "MATERIAL_FUNCTION_CHANGE_REQUIRES_README_UPDATE")

    def test_material_function_change_with_readme_update_admits(self):
        packet = self.review(task={
            "readme_impact_required": True,
            "readme_impact": {
                "material_function_change": True,
                "readme_path": "README.md",
                "readme_updated_in_change_set": True,
                "evidence_refs": ["README.md#functional-change-readme-invariant", "diff:heartbeat_runtime/worker_task_admission.py"],
            },
        })
        self.assertEqual(packet["review"]["verdict"], "ADMIT")
        self.assertTrue(packet["review"]["predicates"]["readme_impact_complete"])
        self.assertEqual(packet["readme_impact"]["disposition"], "README_UPDATED_FOR_MATERIAL_FUNCTION_CHANGE")

    def test_nonmaterial_determination_requires_reason_and_evidence(self):
        packet = self.review(task={
            "readme_impact_required": True,
            "readme_impact": {
                "material_function_change": False,
                "no_readme_update_reason": "Test-only refactor with no behavior change.",
                "evidence_refs": ["tests/test_worker_task_admission.py"],
            },
        })
        self.assertEqual(packet["review"]["verdict"], "ADMIT")
        self.assertEqual(packet["readme_impact"]["disposition"], "NONMATERIAL_CHANGE_EVIDENCE_SUPPORTED")

    def test_nonmaterial_determination_without_evidence_blocks(self):
        packet = self.review(task={
            "readme_impact_required": True,
            "readme_impact": {
                "material_function_change": False,
                "no_readme_update_reason": "No behavior change.",
                "evidence_refs": [],
            },
        })
        self.assertEqual(packet["review"]["verdict"], "BLOCK")
        self.assertIn("readme_impact_complete", packet["review"]["reasons"])

    def test_declared_cosv_vector_is_embedded_in_admission_packet(self):
        packet = self.review(task={
            "source_state_vector_ref": "tasks/TASK-1.json#machine_readable_state.cosv",
            "machine_readable_state": {
                "cosv": {
                    "profile": "task.v1",
                    "notation": "L R U I V G O C M T B E A P",
                    "width": 14,
                    "vector": "10000000100001",
                    "vector_state": "EMITTED",
                    "authority_effect": "NONE",
                }
            },
        })
        self.assertEqual(packet["review"]["verdict"], "ADMIT")
        self.assertTrue(packet["review"]["predicates"]["source_state_vector_valid"])
        self.assertEqual(packet["operational_state_vector"]["vector"], "10000000100001")
        self.assertEqual(packet["operational_state_vector"]["notation"], "L R U I V G O C M T B E A P")

    def test_declared_missing_cosv_blocks(self):
        packet = self.review(task={
            "source_state_vector_ref": "tasks/TASK-1.json#machine_readable_state.cosv",
        })
        self.assertEqual(packet["review"]["verdict"], "BLOCK")
        self.assertIn("source_state_vector_valid", packet["review"]["reasons"])

    def test_malformed_cosv_domain_blocks(self):
        packet = self.review(task={
            "source_state_vector_ref": "tasks/TASK-1.json#machine_readable_state.cosv",
            "machine_readable_state": {
                "cosv": {
                    "profile": "task.v1",
                    "notation": "L R U I V G O C M T B E A P",
                    "width": 14,
                    "vector": "19999999999999",
                    "vector_state": "EMITTED",
                    "authority_effect": "NONE",
                }
            },
        })
        self.assertEqual(packet["review"]["verdict"], "BLOCK")
        self.assertIn("source_state_vector_valid", packet["review"]["reasons"])

if __name__ == "__main__":
    unittest.main()
