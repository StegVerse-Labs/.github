from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001"
COSV = "50000010100000"


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def load_evaluator():
    path = ROOT / "scripts/evaluate_reusable_task_componentization.py"
    spec = importlib.util.spec_from_file_location("reusable_component_eval", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class KVReusableComponentModelTests(unittest.TestCase):
    def test_decomposition_result_recomputes_exactly(self):
        source = load_json(f"data/reusable-task-componentization-inputs/{TASK_ID}.json")
        recorded = load_json(f"data/reusable-task-componentization-evaluations/{TASK_ID}.json")
        actual = load_evaluator().evaluate(source)
        self.assertEqual(actual, recorded)
        self.assertEqual(actual["score"], 30)
        self.assertTrue(actual["must_stop_scope_growth"])

    def test_transport_profile_selects_only_required_components(self):
        profile = load_json(f"data/goal-task-transport-profiles/{TASK_ID}.json")
        self.assertEqual(profile["task_id"], TASK_ID)
        self.assertEqual(profile["cosv_task_vector"], COSV)
        self.assertEqual(
            profile["selected_components"],
            ["RTC-MANIFEST-001", "RTC-ROUNDTRIP-003", "RTC-EVIDENCE-CUSTODY-004", "RTC-INTERLOCK-INTR-TRANSPORT-008", "RTC-FARSIDE-FINAL-009"],
        )
        req = profile["transport_requirements"]
        self.assertFalse(req["governed_processing"])
        self.assertFalse(req["publisher_projection"])
        self.assertFalse(req["sdk_return_assembly"])
        self.assertFalse(req["stegverse_final_egress_transition"])
        self.assertTrue(req["far_side_final_transition"])

    def test_component_profile_preserves_goal_identity(self):
        profile = load_json(f"data/goal-task-component-profiles/{TASK_ID}.json")
        self.assertEqual(profile["task_id"], TASK_ID)
        self.assertEqual(profile["cosv_task_vector"], COSV)
        self.assertTrue(profile["goal_identity_preserved"])
        self.assertFalse(profile["new_goal_task_required"])
        self.assertFalse(profile["new_reusable_component_required"])
        self.assertFalse(profile["componentization_mints_authority"])
        self.assertIn("TESTFLIGHT_CURRENT_IPHONE_RUNTIME_OBSERVED", profile["goal_predicates"])
        self.assertIn("MASTER_RECORDS_CUSTODY_RECONSTRUCTION_OBSERVED", profile["goal_predicates"])

    def test_task_record_binds_component_model_without_runtime_upgrade(self):
        record = load_json(f"data/canonical-task-records/{TASK_ID}.json")
        self.assertEqual(record["task_id"], TASK_ID)
        self.assertEqual(record["cosv_task_vector"], COSV)
        self.assertEqual(record["coordination_state"], "ACTIVE")
        projection = record["component_model_projection"]
        self.assertEqual(projection["decomposition_score"], 30)
        self.assertTrue(projection["goal_identity_preserved"])
        self.assertTrue(projection["cosv_identity_preserved"])
        self.assertFalse(projection["componentization_mints_authority"])
        self.assertFalse(projection["runtime_predicates_completed_by_source_reuse"])
        self.assertFalse(record["completion"]["claimed"])
        self.assertFalse(record["completion"]["validated"])
        self.assertFalse(record["completion"]["activation_proof_complete"])
        self.assertIn("MASTER_RECORDS_CUSTODY_RECONSTRUCTION_OBSERVED", record["expected_evidence_predicates"])
        self.assertEqual(record["authority_model"]["device_user_verification_authority"], "NONE")
        self.assertTrue(record["authority_model"]["kv_skap_sole_user_verification_authority"])

    def test_runtime_handoff_remains_runtime_truth(self):
        handoff = (ROOT / "docs/KV_BOUND_EPHEMERAL_BROWSER_PROJECTION_MIRROR_HANDOFF.md").read_text(encoding="utf-8")
        component_handoff = (ROOT / "docs/KV_BOUND_EPHEMERAL_BROWSER_PROJECTION_COMPONENT_MODEL_MIRROR_HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("TESTFLIGHT_CURRENT_IPHONE_RUNTIME_OBSERVED", handoff)
        self.assertIn("This handoff remains runtime truth", handoff)
        self.assertIn("No genuinely new reusable component is required", component_handoff)
        self.assertIn("user-verification authority `NONE`", component_handoff)


if __name__ == "__main__":
    unittest.main()
