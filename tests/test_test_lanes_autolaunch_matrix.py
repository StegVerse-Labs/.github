import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("matrix_eval", ROOT / "scripts" / "evaluate_test_lanes_autolaunch_matrix.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)
MATRIX = json.loads((ROOT / "control" / "test-lanes-autolaunch-matrix.v1.json").read_text())


def ready_snapshot():
    return {
        "schema": "stegverse.test-lanes-autolaunch-snapshot/v1",
        "matrix_id": "STEGVERSE-TEST-LANES-AUTOLAUNCH-001",
        "runtime": {
            "carrier_epoch": 30,
            "worker_observed_current_carrier": True,
            "state_reconstruction_pass": True,
        },
        "sovereign": {
            "same_execution_activation": True,
            "primary_endpoint_ready": True,
            "model_verified": True,
            "credential_requirement": "NONE",
            "third_party_inference_required": False,
        },
        "tvc": {
            "route_admitted": True,
            "credential_authority": "TV/TVC",
            "non_tv_tvc_secret_or_token_detected": False,
        },
        "providers": {
            "openai": "READY_FOR_TVC_EXECUTION",
            "anthropic": "READY_FOR_TVC_EXECUTION",
            "deepseek": "READY_FOR_TVC_EXECUTION",
            "kimi": "READY_FOR_TVC_EXECUTION",
        },
        "test": {
            "manifest_valid": True,
            "task_blob_exact": True,
            "plan_state": "READY",
            "primary_provider": "stegverse_local",
            "ready_lane_count": 9,
            "ready_execution_group_count": 5,
        },
        "validation": {"source_validation_observed": True},
        "evidence": {"sink_ready": True},
        "claims": {"conflicting_active_claim": False},
    }


class MatrixTests(unittest.TestCase):
    def test_ready_matrix_only_requests_fresh_claim(self):
        result = MODULE.evaluate(MATRIX, ready_snapshot())
        self.assertEqual(result["state"], "ALLOW_EXECUTION_CLAIM")
        self.assertTrue(result["fresh_execution_claim_required"])
        self.assertFalse(result["execution_authority_granted"])
        self.assertFalse(result["heartbeat_grants_execution_authority"])
        self.assertEqual(result["blocking_predicates"], [])
        self.assertEqual(result["prohibitive_failures"], [])

    def test_missing_hb30_blocks_without_false_failure(self):
        snapshot = ready_snapshot()
        snapshot["runtime"]["carrier_epoch"] = 29
        result = MODULE.evaluate(MATRIX, snapshot)
        self.assertEqual(result["state"], "BLOCKED")
        self.assertIn("carrier_hb30_plus", result["blocking_predicates"])
        self.assertFalse(result["execution_authority_granted"])

    def test_non_tv_tvc_secret_violation_fails_closed(self):
        snapshot = ready_snapshot()
        snapshot["tvc"]["non_tv_tvc_secret_or_token_detected"] = True
        result = MODULE.evaluate(MATRIX, snapshot)
        self.assertEqual(result["state"], "FAIL_CLOSED")
        self.assertIn("no_non_tv_tvc_secret", result["prohibitive_failures"])

    def test_third_party_primary_promotion_fails_closed(self):
        snapshot = ready_snapshot()
        snapshot["test"]["primary_provider"] = "openai"
        result = MODULE.evaluate(MATRIX, snapshot)
        self.assertEqual(result["state"], "FAIL_CLOSED")
        self.assertIn("primary_provider_stegverse", result["prohibitive_failures"])

    def test_eight_of_nine_lanes_blocks_canonical_run(self):
        snapshot = ready_snapshot()
        snapshot["test"]["ready_lane_count"] = 8
        result = MODULE.evaluate(MATRIX, snapshot)
        self.assertEqual(result["state"], "BLOCKED")
        self.assertIn("all_nine_logical_lanes_ready", result["blocking_predicates"])

    def test_duplicate_claim_fails_closed(self):
        snapshot = ready_snapshot()
        snapshot["claims"]["conflicting_active_claim"] = True
        result = MODULE.evaluate(MATRIX, snapshot)
        self.assertEqual(result["state"], "FAIL_CLOSED")
        self.assertIn("no_duplicate_execution_claim", result["prohibitive_failures"])


if __name__ == "__main__":
    unittest.main()
