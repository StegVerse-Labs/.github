#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical-task-registry.json"
REQUEST = ROOT / "control" / "resident-execution-request.d" / "canonical-work-quantum-resilience-001.json"
BOOTSTRAP = ROOT / "scripts" / "run_canonical_work_event_bootstrap.py"
WRAPPER = ROOT / "scripts" / "install_and_run_canonical_work_event_bootstrap.py"
CONSUMER = ROOT / "control" / "resident-execution-request.d" / "consume-canonical-work-coordination-bootstrap.py"
README = ROOT / "README.md"
RUNTIME_HANDOFF = ROOT / "docs" / "CANONICAL_WORK_COORDINATION_RUNTIME_MIRROR_HANDOFF.md"
QUANTUM_HANDOFF = ROOT / "docs" / "QUANTUM_RESILIENCE_MIRROR_HANDOFF.md"


class CanonicalWorkRegisteredTaskIngressTests(unittest.TestCase):
    def test_quantum_task_is_registered_and_ingress_eligible(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        matches = [row for row in registry.get("tasks", []) if row.get("task_id") == "QUANTUM-RESILIENCE-001"]
        self.assertEqual(len(matches), 1)
        task = matches[0]
        self.assertEqual(task.get("coordination_state"), "PROPOSED")
        self.assertIn("INGRESS_ADMITTED", task.get("allowed_next_transitions", []))
        self.assertIsNone(task.get("worker_claim", {}).get("claim_ref"))
        self.assertIsNone(task.get("worker_claim", {}).get("fence_ref"))

    def test_quantum_request_is_non_authorizing(self):
        request = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(request["task_id"], "QUANTUM-RESILIENCE-001")
        self.assertEqual(request["state"], "REQUESTED")
        self.assertEqual(request["mode"], "CANONICAL_WORK_EVENT_BOOTSTRAP")
        self.assertEqual(request["credential_authority"], "TV/TVC")
        self.assertEqual(request["github_token_runtime_authority"], "NONE")
        self.assertFalse(request["request_granted_authority"])
        self.assertFalse(request["second_machine_required"])
        self.assertFalse(request["network_source_fetch_allowed"])

    def test_bootstrap_validates_registry_task_instead_of_hard_coding_one_identity(self):
        bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        wrapper = WRAPPER.read_text(encoding="utf-8")
        self.assertIn("def validate_target_task", bootstrap)
        self.assertIn("canonical_task_identity_must_resolve_exactly_once", bootstrap)
        self.assertIn("canonical_task_not_proposed_for_ingress", bootstrap)
        self.assertNotIn("bootstrap_is_bounded_to_canonical_work_coordination_task", bootstrap)
        self.assertIn('"--task-id"', wrapper)

    def test_existing_resident_consumer_visits_quantum_spec_without_new_dispatch_plane(self):
        consumer = CONSUMER.read_text(encoding="utf-8")
        self.assertIn("QUANTUM_SPEC", consumer)
        self.assertIn("REQUEST_SPECS = (DEFAULT_SPEC, QUANTUM_SPEC)", consumer)
        self.assertIn('"task_id": "QUANTUM-RESILIENCE-001"', consumer)
        self.assertIn("later_request_attempts_blocked_by_earlier_failure", consumer)

    def test_readme_and_handoffs_document_material_runtime_semantics(self):
        readme = README.read_text(encoding="utf-8")
        runtime_handoff = RUNTIME_HANDOFF.read_text(encoding="utf-8")
        quantum_handoff = QUANTUM_HANDOFF.read_text(encoding="utf-8")
        self.assertIn("Canonical Work task ingress", readme)
        self.assertIn("registered canonical task", runtime_handoff)
        self.assertIn("canonical-work-quantum-resilience-001.json", quantum_handoff)


if __name__ == "__main__":
    unittest.main()
