"""Negative controls for StegHealth candidate import authorization."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/reconcile_email_failure_incidents.py"
spec = importlib.util.spec_from_file_location("email_failure_reconciler", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CurrentFailureGuardTests(unittest.TestCase):
    def test_unreconciled_candidate_does_not_mutate_registry(self):
        registry = {"generation": 1, "tasks": []}
        vectors = {"tasks": []}
        candidate = {"schema": "stegverse.canonical-task-record/v1",
                     "task_id": "STEGHEALTH-FAILURE-REMEDIATION-FIXTURE"}
        owner = {"task_creation_owner": module.STEGHEALTH_OWNER,
                 "canonical_task_candidates": [candidate], "task_handoffs": []}
        with self.assertRaisesRegex(RuntimeError, "CURRENT_GITHUB_FAILURE_UNRESOLVED_AND_OWNER_VERIFIED"):
            module.import_steghealth_candidates(registry, vectors, Path("/unused"), owner)
        self.assertEqual(registry, {"generation": 1, "tasks": []})
        self.assertEqual(vectors, {"tasks": []})

    def test_successful_rerun_is_not_an_unresolved_failure(self):
        registry = {"generation": 1, "tasks": []}
        vectors = {"tasks": []}
        candidate = {"schema": "stegverse.canonical-task-record/v1",
                     "task_id": "STEGHEALTH-FAILURE-REMEDIATION-FIXTURE",
                     "current_failure_reconciliation": {
                         "state": "RESOLVED", "github_current_state_verified": True,
                         "owner": module.STEGHEALTH_OWNER,
                         "evidence_refs": ["github://fixture/rerun"]}}
        owner = {"task_creation_owner": module.STEGHEALTH_OWNER,
                 "canonical_task_candidates": [candidate], "task_handoffs": []}
        with self.assertRaisesRegex(RuntimeError, "CURRENT_GITHUB_FAILURE_UNRESOLVED_AND_OWNER_VERIFIED"):
            module.import_steghealth_candidates(registry, vectors, Path("/unused"), owner)
        self.assertEqual(registry["tasks"], [])


if __name__ == "__main__":
    unittest.main()
