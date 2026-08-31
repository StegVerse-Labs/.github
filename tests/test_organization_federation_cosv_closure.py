from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cosv", ROOT / "scripts" / "cosv.py")
assert spec and spec.loader
cosv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosv)

class OrganizationFederationCOSVClosureTests(unittest.TestCase):
    def test_all_organization_tasks_are_vectorized_with_policy_correct_domains(self):
        registry = json.loads((ROOT / "control/organization-task-registry.json").read_text())
        index = json.loads((ROOT / "control/task-vector-index.json").read_text())
        indexed = {x["task_id"]: x for x in index["tasks"]}
        self.assertEqual(len(registry["tasks"]), 14)
        for task in registry["tasks"]:
            record = json.loads((ROOT / f"control/task-vectors/{task['task_id']}.json").read_text())
            blocked = task["state"] == "BLOCKED"
            expected = "60000000101000" if blocked else "50000000100000"
            self.assertTrue(cosv.validate_record(record), task["task_id"])
            self.assertEqual(cosv.encode_task(record["exact_metrics"]), expected, task["task_id"])
            self.assertEqual(record["vector"], expected, task["task_id"])
            self.assertEqual(record["exact_metrics"]["blocker_count"], 1 if blocked else 0)
            self.assertEqual(record["exact_metrics"]["lifecycle"], "BLOCKED" if blocked else "MACHINE_OWNED")
            self.assertFalse(record["exact_metrics"]["evidence_complete"])
            self.assertFalse(record["exact_metrics"]["activated"])
            self.assertFalse(record["exact_metrics"]["propagated"])
            self.assertEqual(record["authority_effect"], "NONE")
            self.assertEqual(task["source_state_vector_ref"], f"control/task-vectors/{task['task_id']}.json")
            self.assertEqual(task["machine_readable_state"]["cosv"]["vector"], expected)
            self.assertEqual(indexed[task["task_id"]]["vector"], expected)

    def test_workaround_required_is_not_false_blocked(self):
        registry = json.loads((ROOT / "control/organization-task-registry.json").read_text())
        task = next(x for x in registry["tasks"] if x["task_id"] == "ORG-FED-AACT-E-001")
        record = json.loads((ROOT / "control/task-vectors/ORG-FED-AACT-E-001.json").read_text())
        self.assertEqual(task["state"], "WORKAROUND_REQUIRED")
        self.assertEqual(record["exact_metrics"]["lifecycle"], "MACHINE_OWNED")
        self.assertEqual(record["exact_metrics"]["blocker_count"], 0)

    def test_active_task_projection_is_closed_without_activation_claim(self):
        coverage = json.loads((ROOT / "control/cosv-global-registry-coverage.json").read_text())
        self.assertEqual(coverage["worker_registry_summary"]["active_unvectorized_unique_task_ids"], 0)
        self.assertEqual(coverage["organization_registry_summary"]["active_unvectorized_task_ids"], 0)
        self.assertEqual(coverage["total_active_unvectorized_unique_task_ids"], 0)
        self.assertEqual(coverage["active_worker_task_ids_missing_canonical_cosv"], [])
        self.assertEqual(coverage["active_organization_task_ids_missing_canonical_cosv"], [])
        closure = coverage["active_task_vector_coverage_closure"]
        self.assertEqual(closure["total_active_tasks_vectorized"], 78)
        self.assertTrue(closure["source_projection_complete"])
        self.assertFalse(closure["runtime_activation_claimed"])
        self.assertEqual(closure["authority_effect"], "NONE")

if __name__ == "__main__":
    unittest.main()
