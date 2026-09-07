#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "canonical-work-anthropic-intr-transport-288.json"
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
DISPATCHER = ROOT / "scripts" / "dispatch_resident_execution_requests.py"


class AnthropicCanonicalWorkResidentRequestTests(unittest.TestCase):
    def task(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        matches = [row for row in registry.get("tasks", []) if row.get("task_id") == "LLMA-ANTHROPIC-INTR-TRANSPORT-288"]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def test_task_is_registered_without_execution_authority(self):
        task = self.task()
        self.assertEqual(task["coordination_state"], "PROPOSED")
        self.assertIn("INGRESS_ADMITTED", task["allowed_next_transitions"])
        self.assertIsNone(task["worker_claim"]["claim_ref"])
        self.assertIsNone(task["worker_claim"]["fence_ref"])
        self.assertFalse(task["completion"]["claimed"])
        self.assertFalse(task["completion"]["validated"])

    def test_runtime_requirements_reuse_existing_sovereign_worker(self):
        task = self.task()
        req = task["runtime_requirements"]
        self.assertEqual(req["capabilities"], ["bounded_process_execution"])
        self.assertEqual(req["environment"], "SOVEREIGN_RESIDENT")
        self.assertEqual(req["direction"], "INTERNAL")
        self.assertTrue(req["mutation_required"])
        self.assertFalse(req["deployment_required"])
        self.assertFalse(req["current_observation_required"])
        self.assertIsNone(task["runtime_resolution"])

    def test_real_blocker_is_current_worker_observation_not_missing_profile(self):
        task = self.task()
        blocker_ids = {row["blocker_id"] for row in task["blockers"]}
        self.assertIn("BLOCK-ANTHROPIC-CURRENT-TASK-EXECUTING-WORKERCOORDINATOR", blocker_ids)
        serialized = json.dumps(task, sort_keys=True)
        self.assertNotIn("RUNTIME_PROFILE_MISSING", serialized)
        self.assertIn("CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION", serialized)

    def test_request_is_non_authorizing_and_single_device_compatible(self):
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["request_id"], "RESIDENT-EXEC-CANONICAL-WORK-ANTHROPIC-INTR-TRANSPORT-288")
        self.assertEqual(request["task_id"], "LLMA-ANTHROPIC-INTR-TRANSPORT-288")
        self.assertEqual(request["mode"], "CANONICAL_WORK_EVENT_BOOTSTRAP")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(request["github_token_runtime_authority"], "NONE")
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["oscillator_grants_execution_authority"])
        self.assertFalse(request["second_machine_required"])
        self.assertFalse(request["network_source_fetch_allowed"])

    def test_existing_consumer_and_dispatcher_are_reused(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        dispatcher = DISPATCHER.read_text(encoding="utf-8")
        self.assertIn("ANTHROPIC_SPEC", consumer)
        self.assertIn("canonical-work-anthropic-intr-transport-288.json", consumer)
        self.assertIn("LLMA-ANTHROPIC-INTR-TRANSPORT-288", consumer)
        self.assertIn("canonical_work_coordination", dispatcher)
        self.assertIn("consume-canonical-work-coordination-bootstrap.py", dispatcher)
        self.assertNotIn("anthropic_provider_scheduler", dispatcher)


if __name__ == "__main__":
    unittest.main()
