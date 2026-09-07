#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "canonical-work-erl-ai-economic-transparency-review-001.json"
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
CROSS_TASK = ROOT / "control" / "cross-task-coordination.d" / "erl-ai-economic-transparency-review-001-canonical-work-ingress.json"
HANDOFF = ROOT / "handoffs" / "SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001.json"
PREFLIGHT = ROOT / "receipts" / "preflight" / "ERL-CANONICAL-WORK-INGRESS-001.json"

TASK_ID = "SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001"
REQUEST_ID = "RESIDENT-EXEC-CANONICAL-WORK-ERL-AI-ECON-TRANSPARENCY-REVIEW-001"


class ErlCanonicalWorkIngressTests(unittest.TestCase):
    def test_registry_requires_ingress_before_completion(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        matches = [row for row in registry.get("tasks", []) if row.get("task_id") == TASK_ID]
        self.assertEqual(len(matches), 1)
        task = matches[0]
        self.assertEqual(task.get("coordination_state"), "PROPOSED")
        self.assertIn("INGRESS_ADMITTED", task.get("allowed_next_transitions", []))
        self.assertFalse(task.get("completion", {}).get("claimed"))
        self.assertIsNone(task.get("worker_claim", {}).get("claim_ref"))
        self.assertIsNone(task.get("worker_claim", {}).get("fence_ref"))

    def test_request_is_exact_and_non_authorizing(self):
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["request_id"], REQUEST_ID)
        self.assertEqual(request["task_id"], TASK_ID)
        self.assertEqual(request["state"], "REQUESTED")
        self.assertEqual(request["mode"], "CANONICAL_WORK_EVENT_BOOTSTRAP")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(request["github_token_runtime_authority"], "NONE")
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["oscillator_grants_execution_authority"])
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["second_machine_required"])
        self.assertFalse(request["network_source_fetch_allowed"])

    def test_shared_consumer_visits_erl_without_new_dispatch_plane(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        self.assertIn("ERL_REVIEW_SPEC", consumer)
        self.assertIn('"task_id": "SHWP-ERL-AI-ECON-TRANSPARENCY-REVIEW-001"', consumer)
        self.assertIn("canonical-work-erl-ai-economic-transparency-review-001.json", consumer)
        self.assertIn("REQUEST_SPECS", consumer)
        self.assertIn("later_request_attempts_blocked_by_earlier_failure", consumer)

    def test_cross_task_predicates_fail_closed_at_authentic_ingress(self):
        coordination = json.loads(CROSS_TASK.read_text(encoding="utf-8"))
        predicates = {row["semantic_predicate_id"]: row for row in coordination["predicates"]}
        staged = predicates["canonical_work_request_staged"]
        observed = predicates["resident_request_consumed"]
        self.assertEqual(staged["state"], "SATISFIED")
        self.assertEqual(observed["state"], "UNKNOWN")
        self.assertEqual(observed["required_field_values"]["state"], "COMPLETED")
        self.assertEqual(observed["required_field_values"]["task_id"], TASK_ID)
        self.assertEqual(coordination["authority_effect"], "NONE_COORDINATION_ONLY")

    def test_handoff_orders_ingress_before_workercoordinator_execution(self):
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        self.assertEqual(handoff["activation"]["canonical_work_ingress_request_ref"], str(REQUEST.relative_to(ROOT)))
        self.assertIn("First allow the existing Canonical Work resident consumer", handoff["completion"]["next_authorized_action"])
        self.assertIn("fresh fence", handoff["completion"]["next_authorized_action"])
        self.assertIn("CANONICAL_WORK_INGRESS_RECEIPT_PENDING", handoff["admissible_existence"]["blockers"])
        self.assertFalse(handoff["authority"]["carrier_trigger_required"])
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])

    def test_preflight_contains_readme_completeness_determination(self):
        preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
        impact = preflight["readme_impact"]
        self.assertTrue(impact["required"])
        self.assertFalse(impact["material_function_change"])
        self.assertFalse(impact["readme_updated_in_change_set"])
        self.assertTrue(impact["no_readme_update_reason"])
        self.assertTrue(impact["evidence_refs"])
        self.assertEqual(preflight["disposition"], "ADMIT_COORDINATION")
        self.assertFalse(preflight["new_workercoordinator_required"])
        self.assertFalse(preflight["new_intr_ingress_required"])


if __name__ == "__main__":
    unittest.main()
