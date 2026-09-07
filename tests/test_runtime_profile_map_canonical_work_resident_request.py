#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "canonical-work-runtime-profile-map-001.json"
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
README = ROOT / "README.md"


class RuntimeProfileMapCanonicalWorkResidentRequestTests(unittest.TestCase):
    def test_runtime_profile_map_task_is_registered_and_ingress_eligible(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        matches = [row for row in registry.get("tasks", []) if row.get("task_id") == "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001"]
        self.assertEqual(len(matches), 1)
        task = matches[0]
        self.assertEqual(task.get("coordination_state"), "PROPOSED")
        self.assertIn("INGRESS_ADMITTED", task.get("allowed_next_transitions", []))
        self.assertIsNone(task.get("worker_claim", {}).get("claim_ref"))
        self.assertIsNone(task.get("worker_claim", {}).get("fence_ref"))

    def test_runtime_profile_map_request_is_non_authorizing(self):
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["request_id"], "RESIDENT-EXEC-CANONICAL-WORK-RUNTIME-PROFILE-MAP-001")
        self.assertEqual(request["task_id"], "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001")
        self.assertEqual(request["state"], "REQUESTED")
        self.assertEqual(request["mode"], "CANONICAL_WORK_EVENT_BOOTSTRAP")
        self.assertEqual(request["entrypoint"], "scripts/install_and_run_canonical_work_event_bootstrap.py")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(request["github_token_runtime_authority"], "NONE")
        self.assertFalse(request["github_token_required"])
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["oscillator_grants_execution_authority"])
        self.assertFalse(request["second_machine_required"])
        self.assertFalse(request["network_source_fetch_allowed"])

    def test_existing_consumer_visits_runtime_profile_map_without_new_dispatch_plane(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        self.assertIn("RUNTIME_PROFILE_MAP_SPEC", consumer)
        self.assertIn("ERL_REVIEW_SPEC", consumer)
        self.assertIn("CRYPTO_LIVE_AUTO_SPEC", consumer)
        self.assertIn('"task_id": "STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001"', consumer)
        self.assertIn('"--task-id"', consumer)
        self.assertIn("later_request_attempts_blocked_by_earlier_failure", consumer)

    def test_readme_already_documents_generic_registered_task_semantics(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn("Canonical Work task ingress", readme)
        self.assertIn("tasks that already exist in the canonical Task Registry", readme)
        self.assertIn("multiple explicit task request specifications", readme)
        self.assertIn("does not create task identity", readme)


if __name__ == "__main__":
    unittest.main()
