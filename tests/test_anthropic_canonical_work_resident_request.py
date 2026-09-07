#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "canonical-work-anthropic-intr-transport-288.json"
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
COORDINATION = ROOT / "control" / "cross-task-coordination.d" / "anthropic-intr-transport-288-canonical-work-ingress.json"
PREFLIGHT = ROOT / "data" / "preflight" / "llma-anthropic-intr-transport-288-post-merge-reconcile.json"

TASK_ID = "LLMA-ANTHROPIC-INTR-TRANSPORT-288"
REQUEST_ID = "RESIDENT-EXEC-CANONICAL-WORK-ANTHROPIC-INTR-TRANSPORT-288"
MERGE_SHA = "cde350e41d16a9932932b96d77c0dbd37b950284"


class AnthropicCanonicalWorkResidentRequestTests(unittest.TestCase):
    def task(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        matches = [row for row in registry.get("tasks", []) if row.get("task_id") == TASK_ID]
        self.assertEqual(len(matches), 1)
        return registry, matches[0]

    def test_task_is_registered_without_execution_authority(self):
        registry, task = self.task()
        self.assertGreaterEqual(registry.get("generation", 0), 17)
        self.assertEqual(task["coordination_state"], "PROPOSED")
        self.assertIn("INGRESS_ADMITTED", task["allowed_next_transitions"])
        self.assertIsNone(task["worker_claim"]["claim_ref"])
        self.assertIsNone(task["worker_claim"]["fence_ref"])
        self.assertFalse(task["completion"]["claimed"])
        self.assertFalse(task["completion"]["validated"])

    def test_source_merge_is_resolved_but_runtime_dependencies_are_not(self):
        _, task = self.task()
        deps = {row["dependency_id"]: row for row in task["dependencies"]}
        self.assertEqual(deps["DEP-ANTHROPIC-ADAPTER-SOURCE-MERGED"]["state"], "RESOLVED")
        self.assertIn(MERGE_SHA, deps["DEP-ANTHROPIC-ADAPTER-SOURCE-MERGED"]["ref"])
        for dep_id in (
            "DEP-ANTHROPIC-CANONICAL-WORK-INGRESS",
            "DEP-ANTHROPIC-CURRENT-TASK-EXECUTING-WORKERCOORDINATOR",
            "DEP-ANTHROPIC-MASTER-RECORDS-PROVIDER-USAGE",
        ):
            self.assertEqual(deps[dep_id]["state"], "UNRESOLVED")

    def test_runtime_requirements_reuse_existing_worker_profile_contract(self):
        _, task = self.task()
        req = task["runtime_requirements"]
        self.assertEqual(req["capabilities"], ["bounded_process_execution"])
        self.assertEqual(req["environment"], "SOVEREIGN_RESIDENT")
        self.assertEqual(req["direction"], "INTERNAL")
        self.assertTrue(req["mutation_required"])
        self.assertFalse(req["deployment_required"])
        self.assertFalse(req["current_observation_required"])
        self.assertIsNone(task["runtime_resolution"])

    def test_request_is_exact_and_non_authorizing(self):
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["request_id"], REQUEST_ID)
        self.assertEqual(request["task_id"], TASK_ID)
        self.assertEqual(request["state"], "REQUESTED")
        self.assertEqual(request["mode"], "CANONICAL_WORK_EVENT_BOOTSTRAP")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(request["github_token_runtime_authority"], "NONE")
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["oscillator_grants_execution_authority"])
        self.assertFalse(request["second_machine_required"])
        self.assertFalse(request["network_source_fetch_allowed"])

    def test_existing_consumer_is_extended_without_replacing_newer_specs(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        for required in ("ERL_REVIEW_SPEC", "CRYPTO_LIVE_AUTO_SPEC", "ANTHROPIC_SPEC"):
            self.assertIn(required, consumer)
        self.assertIn("canonical-work-anthropic-intr-transport-288.json", consumer)
        self.assertIn(TASK_ID, consumer)
        self.assertIn("later_request_attempts_blocked_by_earlier_failure", consumer)

    def test_cross_task_projection_separates_source_staging_from_runtime_truth(self):
        fragment = json.loads(COORDINATION.read_text(encoding="utf-8"))
        predicates = {row["semantic_predicate_id"]: row for row in fragment["predicates"]}
        self.assertEqual(predicates["canonical_work_request_staged"]["state"], "SATISFIED")
        self.assertEqual(predicates["resident_request_consumed"]["state"], "UNKNOWN")
        self.assertEqual(
            predicates["resident_request_consumed"]["expected_output_ref"],
            "receipts/sovereign-host/canonical-work-anthropic-intr-transport-288-request-consumption.latest.json",
        )
        self.assertEqual(fragment["authority_effect"], "NONE_COORDINATION_ONLY")

    def test_preflight_records_supported_no_readme_update_determination(self):
        preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
        self.assertEqual(preflight["state"], "PASS")
        self.assertFalse(preflight["readme_completeness"]["material_function_change"])
        self.assertEqual(preflight["readme_completeness"]["impact"], "NO_UPDATE_REQUIRED")
        self.assertFalse(preflight["readme_completeness"]["readme_updated_in_change_set"])
        self.assertTrue(preflight["readme_completeness"]["evidence_refs"])


if __name__ == "__main__":
    unittest.main()
