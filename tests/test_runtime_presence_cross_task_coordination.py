from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RuntimePresenceCrossTaskCoordinationTests(unittest.TestCase):
    def test_corrective_preflight_passed_before_subject_binding_mutation(self):
        receipt = json.loads((ROOT / "receipts/preflight/RUNTIME-PRESENCE-SUBJECT-BINDING-CORRECTION-001.json").read_text())
        self.assertEqual(receipt["state"], "PASS")
        self.assertEqual(receipt["verdict"], "PASS")
        self.assertTrue(receipt["readme_impact_required"])
        self.assertTrue(receipt["readme_impact"]["material_function_change"])
        self.assertTrue(receipt["readme_impact"]["readme_updated_in_change_set"])
        self.assertEqual(receipt["readme_impact"]["readme_path"], "README.md")
        self.assertTrue(receipt["collision_review"]["semantic_conflict_observed"])

    def test_overbroad_runtime_presence_fragment_is_not_canonical(self):
        self.assertFalse((ROOT / "control/cross-task-coordination.d/runtime-presence-predicates.json").exists())

    def test_existing_candidate_remains_deferred_until_authentic_subject_identity(self):
        candidate = json.loads(
            (ROOT / "control/cross-task-coordination-candidates/resident-process-alive-supervised.json").read_text()
        )
        self.assertEqual(candidate["state"], "DEFERRED_SUBJECT_BINDING_REQUIRED")
        self.assertEqual(candidate["authority_effect"], "NONE_COORDINATION_STAGING_ONLY")
        self.assertEqual(candidate["semantic_predicate_id"], "resident_process_alive_supervised")
        required = set(candidate["required_subject_binding_before_admission"])
        self.assertIn("runtime_root identity", required)
        self.assertIn("resident.node_id when available from authentic runtime evidence", required)
        self.assertIn("canonical worker runtime identity", required)
        self.assertEqual(candidate["canonical_evidence_ref"], "receipts/sovereign-host/runtime-presence.latest.json")
        self.assertIn("Do not create another runtime-presence projector", candidate["safe_next_action"])

    def test_readme_documents_deferred_subject_binding_and_evidence_limits(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("### Cross-task runtime-presence evidence", readme)
        self.assertIn("shared cross-task reuse is currently deferred", readme)
        self.assertIn("runtime_root", readme)
        self.assertIn("resident.node_id", readme)
        self.assertIn("does **not** prove that a specific request was consumed", readme)
        self.assertIn("HeartBeat remains non-authorizing", readme)


if __name__ == "__main__":
    unittest.main()
