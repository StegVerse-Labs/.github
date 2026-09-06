from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RuntimePresenceCrossTaskCoordinationTests(unittest.TestCase):
    def test_preflight_passed_before_coordination_mutation(self):
        receipt = json.loads((ROOT / "receipts/preflight/CROSS-TASK-RUNTIME-PRESENCE-PREDICATE-001.json").read_text())
        self.assertEqual(receipt["state"], "PASS")
        self.assertEqual(receipt["verdict"], "PASS")
        self.assertTrue(receipt["readme_impact_required"])
        self.assertTrue(receipt["readme_impact"]["material_function_change"])
        self.assertTrue(receipt["readme_impact"]["readme_updated_in_change_set"])
        self.assertEqual(receipt["readme_impact"]["readme_path"], "README.md")
        self.assertFalse(receipt["collision_review"]["mutation_scope_collision_observed"])
        self.assertFalse(receipt["reuse_resolution"]["duplicate_runtime_implementation_required"])

    def test_runtime_presence_predicate_is_subject_bound_and_non_authorizing(self):
        fragment = json.loads((ROOT / "control/cross-task-coordination.d/runtime-presence-predicates.json").read_text())
        self.assertEqual(fragment["authority_effect"], "NONE_COORDINATION_ONLY")
        self.assertEqual(len(fragment["predicates"]), 1)
        predicate = fragment["predicates"][0]
        self.assertEqual(predicate["semantic_predicate_id"], "resident_worker_runtime_present")
        self.assertEqual(predicate["subject_binding"]["runtime_profile_id"], "canonical-resident-substrate-v1")
        self.assertEqual(predicate["subject_binding"]["worker_runtime"], "heartbeat_runtime.worker_runtime.WorkerCoordinator")
        self.assertEqual(predicate["authoritative_producer"], "heartbeat_runtime/runtime_presence_projection.py")
        self.assertEqual(predicate["required_schema"], "stegverse.hb-runtime-presence-resident-observability/v1")
        self.assertEqual(predicate["expected_output_ref"], "receipts/sovereign-host/runtime-presence.latest.json")
        self.assertEqual(predicate["max_age_seconds"], 60)
        self.assertEqual(predicate["state"], "UNKNOWN")

    def test_bound_consumers_reuse_existing_presence_producer(self):
        fragment = json.loads((ROOT / "control/cross-task-coordination.d/runtime-presence-predicates.json").read_text())
        predicate = fragment["predicates"][0]
        self.assertEqual(set(predicate["consumers"]), {
            "SHWP-SV002-ORG-RUNTIME-ACTIVATION-001",
            "SHWP-SV002-PUBLIC-OBSERVATION-RUNTIME-001",
            "SHWP-SV011-PHASE5-SOURCE-MATERIALIZATION-001",
            "SHWP-SV011-PHASE5-BOUNDARY-001",
        })
        gap = fragment["gaps"][0]
        self.assertIn("Do not create another heartbeat", gap["action_without_collision"])
        self.assertIn("WorkerCoordinator", gap["action_without_collision"])

    def test_readme_documents_presence_vs_execution_distinction(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("### Cross-task runtime-presence evidence", readme)
        self.assertIn("does **not** prove that a specific request was consumed", readme)
        self.assertIn("HeartBeat remains non-authorizing", readme)


if __name__ == "__main__":
    unittest.main()
