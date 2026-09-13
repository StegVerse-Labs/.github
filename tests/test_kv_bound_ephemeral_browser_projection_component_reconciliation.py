from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001"
COSV = "50000010100000"


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def load_module(rel: str, name: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class KVReusableComponentModelTests(unittest.TestCase):
    def test_decomposition_result_recomputes_exactly(self):
        source = load_json(f"data/reusable-task-componentization-inputs/{TASK_ID}.json")
        recorded = load_json(f"data/reusable-task-componentization-evaluations/{TASK_ID}.json")
        actual = load_module("scripts/evaluate_reusable_task_componentization.py", "component_eval").evaluate(source)
        self.assertEqual(actual, recorded)
        self.assertEqual(actual["score"], 30)
        self.assertTrue(actual["must_stop_scope_growth"])

    def test_transport_profile_selects_only_required_transport_components(self):
        profile = load_json(f"data/goal-task-transport-profiles/{TASK_ID}.json")
        self.assertEqual(profile["task_id"], TASK_ID)
        self.assertEqual(profile["cosv_task_vector"], COSV)
        self.assertEqual(profile["selected_components"], ["RTC-MANIFEST-001", "RTC-ROUNDTRIP-003", "RTC-EVIDENCE-CUSTODY-004", "RTC-INTERLOCK-INTR-TRANSPORT-008", "RTC-FARSIDE-FINAL-009"])

    def test_component_profile_adds_reuse_without_new_goal(self):
        profile = load_json(f"data/goal-task-component-profiles/{TASK_ID}.json")
        self.assertFalse(profile["new_goal_task_required"])
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
        self.assertFalse(contract["invariants"]["user_interaction_required_after_established_node_connectivity"])

    def base_payload(self):
        return {
            "node_context": {"connectivity_state": "ESTABLISHED", "node_id": "node-1"},
            "ecosystem_state": {"task_id": TASK_ID, "coordination_state": "ACTIVE", "worker_claim_ref": "TASK-2026-0011:G7", "fence_ref": "FENCE7"},
            "current_requirements": {
                "task_id": TASK_ID,
                "required_coordination_state": "ACTIVE",
                "required_worker_claim_ref": "TASK-2026-0011:G7",
                "required_fence_ref": "FENCE7",
                "required_predicates": ["A", "B"],
                "historically_reusable_predicates": ["A", "B"],
                "must_be_current_for_this_execution": [],
                "accepted_verification_modes": ["REPLAY", "RECONSTRUCTION"],
                "accepted_evidence_classes": ["TEST"],
                "require_exact_node_route_match": True,
            },
            "indexed_events": [{"event_ref": "event-1", "evidence_class": "TEST", "verification_modes": {"REPLAY": "PASS"}, "node_id": "node-1", "observed_predicates": ["A", "B"]}],
            "current_observations": {"observed_predicates": []},
        }

    def test_reuse_evaluator_accepts_verified_same_route_event(self):
        result = load_module("scripts/evaluate_indexed_event_reuse.py", "reuse_eval").evaluate(self.base_payload())
        self.assertEqual(result["state"], "REUSE_ACCEPTED")
        self.assertEqual(result["covered_from_historical_evidence"], ["A", "B"])
        self.assertFalse(result["user_interaction_required"])

    def test_current_only_predicate_never_inherits_historical_coverage(self):
        payload = self.base_payload()
        payload["current_requirements"]["required_predicates"] = ["A", "B", "C"]
        payload["current_requirements"]["must_be_current_for_this_execution"] = ["B", "C"]
        payload["current_observations"] = {"observed_predicates": ["C"]}
        result = load_module("scripts/evaluate_indexed_event_reuse.py", "reuse_eval_current").evaluate(payload)
        self.assertEqual(result["state"], "DELTA_REQUIRED")
        self.assertEqual(result["missing_delta"], ["B"])
        self.assertEqual(result["covered_from_historical_evidence"], ["A"])

    def test_route_mismatch_rejects_historical_event_without_user_step(self):
        payload = self.base_payload()
        payload["node_context"]["node_id"] = "node-2"
        result = load_module("scripts/evaluate_indexed_event_reuse.py", "reuse_eval_route").evaluate(payload)
        self.assertEqual(result["state"], "DELTA_REQUIRED")
        self.assertEqual(result["missing_delta"], ["A", "B"])
        self.assertIn("EXACT_NODE_ROUTE_MISMATCH", result["rejected_events"][0]["failures"])
        self.assertFalse(result["user_interaction_required"])

    def test_ecosystem_claim_drift_fails_closed(self):
        payload = self.base_payload()
        payload["ecosystem_state"]["worker_claim_ref"] = "TASK-2026-0011:G8"
        result = load_module("scripts/evaluate_indexed_event_reuse.py", "reuse_eval_drift").evaluate(payload)
        self.assertEqual(result["state"], "FAIL_CLOSED")
        self.assertIn("CURRENT_ECOSYSTEM_WORKER_CLAIM_MISMATCH", result["failures"])

    def test_automatic_builder_uses_replay_and_reconstruction_without_user_input(self):
        runtime = Path(tempfile.mkdtemp())
        payload = load_module("scripts/build_kv_evidence_reuse_input.py", "reuse_builder").build_payload(ROOT, runtime)
        self.assertTrue(payload["input_derived_automatically"])
        self.assertFalse(payload["user_interaction_required"])
        by_class = {row["evidence_class"]: row for row in payload["indexed_events"]}
        self.assertEqual(by_class["CANONICAL_ALLOCATOR_REPLAY"]["verification_modes"]["REPLAY"], "PASS")
        self.assertEqual(by_class["WORKERCOORDINATOR_RUNTIME_RECONSTRUCTION"]["verification_modes"]["RECONSTRUCTION"], "PASS")

    def test_current_route_does_not_require_site_projection(self):
        mod = load_module("scripts/build_kv_evidence_reuse_input.py", "reuse_route_no_site_projection")
        node = "SV-NODE-" + "a" * 24
        discovery = SimpleNamespace(
            LOCAL_BASES=("http://127.0.0.1:8000",),
            _probe=lambda _base: ("REACHABLE", b"discovery", {"target_node_ref": node}),
        )
        wrapper = {
            "state": "EVIDENCE_AVAILABLE",
            "evidence": {
                "execution_surface": "CURRENT_USER_IPHONE",
                "node_origin": "STEGBROWSER_RESIDENT",
                "site_projection_observed": False,
                "node_receipt_1_sha256": "NONE",
            },
            "_projected": {
                "node_ref": node,
                "source_device_hb_reference": "heartbeat_epoch:100",
                "current_observed_hb_reference": "heartbeat_epoch:101",
                "observation_ref": "runtime://retained-node/example",
            },
        }
        readback = SimpleNamespace(_probe=lambda _base, _node: ("REACHABLE", b"receipt", wrapper))
        with patch.object(mod, "_module", side_effect=[discovery, readback]):
            result = mod.current_retained_iphone_route(ROOT)
        self.assertEqual(result["connectivity_state"], "ESTABLISHED")
        self.assertEqual(result["retained_node_ref"], node)
        self.assertFalse(result["site_projection_observed"])
        self.assertIsNone(result["node_receipt_1_sha256"])

    def test_current_route_rejects_projected_node_mismatch(self):
        mod = load_module("scripts/build_kv_evidence_reuse_input.py", "reuse_route_mismatch")
        node = "SV-NODE-" + "a" * 24
        discovery = SimpleNamespace(
            LOCAL_BASES=("http://127.0.0.1:8000",),
            _probe=lambda _base: ("REACHABLE", b"discovery", {"target_node_ref": node}),
        )
        wrapper = {
            "state": "EVIDENCE_AVAILABLE",
            "evidence": {"execution_surface": "CURRENT_USER_IPHONE", "node_origin": "STEGBROWSER_RESIDENT"},
            "_projected": {"node_ref": "SV-NODE-" + "b" * 24},
        }
        readback = SimpleNamespace(_probe=lambda _base, _node: ("REACHABLE", b"receipt", wrapper))
        with patch.object(mod, "_module", side_effect=[discovery, readback]):
            result = mod.current_retained_iphone_route(ROOT)
        self.assertEqual(result["connectivity_state"], "UNRESOLVED")

    def test_task_record_stays_active_without_runtime_upgrade(self):
        record = load_json(f"data/canonical-task-records/{TASK_ID}.json")
        self.assertEqual(record["coordination_state"], "ACTIVE")
        self.assertFalse(record["completion"]["claimed"])
        self.assertFalse(record["completion"]["validated"])
        self.assertEqual(record["authority_model"]["device_user_verification_authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
