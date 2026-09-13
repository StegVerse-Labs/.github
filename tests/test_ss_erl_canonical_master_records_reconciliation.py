import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001"
TASK = ROOT / "data" / "canonical-task-records" / f"{TASK_ID}.json"
BINDING = ROOT / "data" / "goal-task-component-bindings" / f"{TASK_ID}.master-records.json"
HANDOFF = ROOT / "docs" / "SS_ERL_MASTER_RECORDS_COMPONENT_BINDING_MIRROR_HANDOFF.md"


class ERLCanonicalMasterRecordsReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task = json.loads(TASK.read_text())
        cls.binding = json.loads(BINDING.read_text())
        cls.handoff = HANDOFF.read_text()

    def test_task_identity_and_binding_projection_are_preserved(self):
        self.assertEqual(self.task["task_id"], TASK_ID)
        self.assertEqual(self.task["cosv_task_vector"], "40000100100000")
        self.assertEqual(
            self.task["component_model_projection"]["master_records_component_binding"],
            f"data/goal-task-component-bindings/{TASK_ID}.master-records.json",
        )
        self.assertIn("master-records/orchestration", self.task["targets"]["repositories"])
        self.assertIn(
            f"data/goal-task-component-bindings/{TASK_ID}.master-records.json",
            self.task["handoff_projection_refs"],
        )

    def test_master_records_dependency_is_source_available_but_runtime_pending(self):
        dependency = next(
            item for item in self.task["dependencies"]
            if item["dependency_id"] == "DEP-ERL-MASTER-RECORDS-INTR-CUSTODY"
        )
        self.assertEqual(
            dependency["state"],
            "AVAILABLE_SOURCE_ONLY_RUNTIME_EVIDENCE_PENDING",
        )
        self.assertEqual(
            dependency["ref"],
            "master-records/orchestration#94@560863ff192f4437911a8d748984d06566c120c7",
        )
        self.assertFalse(self.task["completion"]["claimed"])
        self.assertFalse(self.task["completion"]["validated"])
        self.assertFalse(self.task["completion"]["activation_proof_complete"])
        self.assertFalse(self.binding["validation"]["runtime_evidence_for_this_goal_proven"])
        self.assertFalse(self.binding["provider_operation_reexecution_authorized"])

    def test_authority_boundaries_and_handoff_status_are_fail_closed(self):
        authority = self.task["authority_model"]
        self.assertEqual(authority["github_runtime_authority"], "NONE")
        self.assertEqual(authority["device_user_verification_authority"], "NONE")
        self.assertFalse(authority["provider_operation_reexecution_authorized"])
        self.assertTrue(authority["kv_skap_remains_sole_user_verification_authority"])
        self.assertTrue(authority["master_records_remains_custody_reconstruction_authority"])
        self.assertIn("SOURCE BINDING MERGED AND VALIDATED", self.handoff)
        self.assertIn("MASTER_RECORDS_CUSTODY_RECONSTRUCTION_OBSERVED` remains false", self.handoff)


if __name__ == "__main__":
    unittest.main()
