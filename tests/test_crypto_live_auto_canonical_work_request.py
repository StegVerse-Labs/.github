#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "canonical-work-crypto-live-auto-001.json"
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
COORDINATION = ROOT / "control" / "cross-task-coordination.d" / "crypto-live-auto-001-canonical-work-ingress.json"
PREFLIGHT = ROOT / "receipts" / "preflight" / "CRYPTO-LIVE-AUTO-CANONICAL-WORK-001.json"
README = ROOT / "README.md"


class CryptoLiveAutoCanonicalWorkRequestTests(unittest.TestCase):
    def test_task_registered_as_proposed_without_worker_claim(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(registry.get("generation"), 17)
        matches = [row for row in registry.get("tasks", []) if row.get("task_id") == "CRYPTO-LIVE-AUTO-001"]
        self.assertEqual(len(matches), 1)
        task = matches[0]
        self.assertEqual(task.get("coordination_state"), "PROPOSED")
        self.assertEqual(task.get("allowed_next_transitions"), ["INGRESS_ADMITTED"])
        self.assertIsNone(task.get("worker_claim", {}).get("claim_ref"))
        self.assertIsNone(task.get("worker_claim", {}).get("fence_ref"))
        self.assertFalse(task.get("authority_model", {}).get("task_registry_mints_execution_authority"))
        self.assertFalse(task.get("authority_model", {}).get("source_state_proves_execution"))

    def test_request_is_exact_and_non_authorizing(self):
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["request_id"], "RESIDENT-EXEC-CANONICAL-WORK-CRYPTO-LIVE-AUTO-001")
        self.assertEqual(request["task_id"], "CRYPTO-LIVE-AUTO-001")
        self.assertEqual(request["state"], "REQUESTED")
        self.assertEqual(request["mode"], "CANONICAL_WORK_EVENT_BOOTSTRAP")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(request["github_token_runtime_authority"], "NONE")
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["heartbeat_grants_execution_authority"])
        self.assertFalse(request["oscillator_grants_execution_authority"])
        self.assertFalse(request["second_machine_required"])
        self.assertFalse(request["network_source_fetch_allowed"])

    def test_existing_consumer_visits_crypto_request(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        self.assertIn("CRYPTO_LIVE_AUTO_SPEC", consumer)
        self.assertIn("canonical-work-crypto-live-auto-001.json", consumer)
        self.assertIn("canonical-work-crypto-live-auto-request-consumption.latest.json", consumer)
        self.assertIn('"task_id": "CRYPTO-LIVE-AUTO-001"', consumer)
        self.assertIn("later_request_attempts_blocked_by_earlier_failure", consumer)

    def test_subject_bound_coordination_does_not_infer_consumption(self):
        fragment = json.loads(COORDINATION.read_text(encoding="utf-8"))
        predicates = {row["semantic_predicate_id"]: row for row in fragment["predicates"]}
        staged = predicates["canonical_work_request_staged"]
        consumed = predicates["resident_request_consumed"]
        expected_binding = {
            "task_id": "CRYPTO-LIVE-AUTO-001",
            "request_id": "RESIDENT-EXEC-CANONICAL-WORK-CRYPTO-LIVE-AUTO-001",
        }
        self.assertEqual(staged["subject_binding"], expected_binding)
        self.assertEqual(staged["state"], "SATISFIED")
        self.assertEqual(consumed["subject_binding"], expected_binding)
        self.assertEqual(consumed["state"], "UNKNOWN")

    def test_preflight_records_non_material_readme_determination(self):
        preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
        self.assertEqual(preflight["result"], "ADMIT_COORDINATION")
        self.assertFalse(preflight["readme_impact"]["required"])
        self.assertFalse(preflight["readme_impact"]["material_function_change"])
        readme = README.read_text(encoding="utf-8")
        self.assertIn("Canonical Work task ingress", readme)
        self.assertIn("multiple explicit task request specifications", readme)


if __name__ == "__main__":
    unittest.main()
