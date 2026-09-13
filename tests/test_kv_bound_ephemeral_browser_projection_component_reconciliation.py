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


def load_reuse_evaluator():
    path = ROOT / "scripts/evaluate_indexed_event_reuse.py"
    spec = importlib.util.spec_from_file_location("indexed_evidence_reuse", path)
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

    def test_transport_profile_selects_only_required_transport_components(self):
        profile = load_json(f"data/goal-task-transport-profiles/{TASK_ID}.json")
        self.assertEqual(profile["task_id"], TASK_ID)
        self.assertEqual(profile["cosv_task_vector"], COSV)
        self.assertEqual(
            profile["selected_components"],
            ["RTC-MANIFEST-001", "RTC-ROUNDTRIP-003", "RTC-EVIDENCE-CUSTODY-004", "RTC-INTERLOCK-INTR-TRANSPORT-008", "RTC-FARSIDE-FINAL-009"],
        )

    def test_component_profile_adds_reuse_without_new_goal(self):
        profile = load_json(f"data/goal-task-component-profiles/{TASK_ID}.json")
        self.assertEqual(profile["task_id"], TASK_ID)
        self.assertEqual(profile["cosv_task_vector"], COSV)
        self.assertTrue(profile["goal_identity_preserved"])
        self.assertFalse(profile["new_goal_task_required"])
        self.assertTrue(profile["new_reusable_component_required"])
        self.assertFalse(profile["componentization_mints_authority"])
        self.assertIn("RTC-EVIDENCE-CURRENT-SELECTOR-010", profile["selected_components"])
        self.assertIn("RTC-EVIDENCE-REPLAY-REUSE-011", profile["selected_components"])
        self.assertIn("TESTFLIGHT_SIGNING_PROVIDER_RELEASE_INSTALL_OBSERVED", profile["goal_predicates"])
        self.assertNotIn("TESTFLIGHT_CURRENT_IPHONE_RUNTIME_OBSERVED", profile["goal_predicates"])
        self.assertFalse(profile["historical_runtime_reuse"]["user_reverification_after_established_node_connectivity"])

    def test_reuse_contract_is_non_authorizing(self):
        contract = load_json("data/reusable-indexed-evidence-reuse-component-contract.json")
        self.assertEqual(contract["component_id"], "RTC-EVIDENCE-REPLAY-REUSE-011")
        self.assertEqual(contract["authority_effect"], "NONE_VALIDATION_ONLY")
        self.assertFalse(contract["invariants"]["historical_evidence_mints_authority"])
        self.assertTrue(contract["invariants"]["established_node_connectivity_is_transport_only"])
        self.assertFalse(contract["invariants"]["user_interaction_required_after_established_node_connectivity"])

    def test_reuse_evaluator_reuses_complete_reconstructed_event(self):
        result = load_reuse_evaluator().evaluate({
            "node_context": {"connectivity_state": "ESTABLISHED"},
            "current_requirements": {"required_predicates": ["A", "B"]},
            "indexed_event": {"replay_state": "PASS", "reconstruction_state": "PASS", "observed_predicates": ["A", "B"]},
        })
        self.assertEqual(result["state"], "REUSE_ACCEPTED")
        self.assertTrue(result["reused_event"])
        self.assertFalse(result["user_interaction_required"])

    def test_reuse_evaluator_returns_only_missing_delta(self):
        result = load_reuse_evaluator().evaluate({
            "node_context": {"connectivity_state": "ESTABLISHED"},
            "current_requirements": {"required_predicates": ["A", "B", "C"]},
            "indexed_event": {"replay_state": "PASS", "reconstruction_state": "PASS", "observed_predicates": ["A", "C"]},
        })
        self.assertEqual(result["state"], "DELTA_REQUIRED")
        self.assertEqual(result["missing_delta"], ["B"])

    def test_reuse_evaluator_fails_closed_on_bad_replay(self):
        result = load_reuse_evaluator().evaluate({
            "node_context": {"connectivity_state": "ESTABLISHED"},
            "current_requirements": {"required_predicates": []},
            "indexed_event": {"replay_state": "FAIL", "reconstruction_state": "PASS", "observed_predicates": []},
        })
        self.assertEqual(result["state"], "FAIL_CLOSED")
        self.assertIn("INDEXED_EVENT_REPLAY_NOT_PASS", result["failures"])

    def test_task_record_stays_active_without_runtime_upgrade(self):
        record = load_json(f"data/canonical-task-records/{TASK_ID}.json")
        self.assertEqual(record["task_id"], TASK_ID)
        self.assertEqual(record["coordination_state"], "ACTIVE")
        self.assertFalse(record["completion"]["claimed"])
        self.assertFalse(record["completion"]["validated"])
        self.assertEqual(record["authority_model"]["device_user_verification_authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
