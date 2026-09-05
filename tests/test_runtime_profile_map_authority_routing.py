from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location(
        "route_runtime_profile_map_governance_review",
        ROOT / "scripts/route_runtime_profile_map_governance_review.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


mod = load_module()


class AuthorityRoutingTests(unittest.TestCase):
    def test_routes_without_invoking_authority(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review = root / "review.json"
            review.write_text(json.dumps({
                "schema": "stegverse.runtime-profile-map-governance-review/v1",
                "task_id": "TASK-1",
                "correlation_id": "CORR-1",
                "transition_readiness_disposition": "ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW",
                "next_governance_review": "WORKERCOORDINATOR_ADMISSION_REVIEW",
                "review_authority_class": "WORKERCOORDINATOR",
                "review_required_before_transition": True,
                "task_state_changed": False,
                "claim_or_fence_minted": False,
                "execution_authority_granted": False,
                "interlock_intr_admission_granted": False,
                "heartbeat_or_oscillator_advanced": False,
            }) + "\n", encoding="utf-8")
            result = mod.route(review, root)
            self.assertEqual(result["state"], "ROUTED_FOR_CURRENT_AUTHORITY_REVIEW")
            self.assertEqual(result["review_authority_class"], "WORKERCOORDINATOR")
            self.assertFalse(result["authority_invoked"])
            self.assertFalse(result["claim_or_fence_minted"])
            self.assertFalse(result["execution_authority_granted"])
            self.assertTrue(Path(result["envelope_ref"]).is_file())

    def test_unsupported_authority_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review = root / "review.json"
            review.write_text(json.dumps({
                "schema": "stegverse.runtime-profile-map-governance-review/v1",
                "task_id": "TASK-1",
                "correlation_id": "CORR-1",
                "review_authority_class": "UNKNOWN_AUTHORITY",
                "review_required_before_transition": True,
                "task_state_changed": False,
                "claim_or_fence_minted": False,
                "execution_authority_granted": False,
                "interlock_intr_admission_granted": False,
                "heartbeat_or_oscillator_advanced": False,
            }) + "\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                mod.route(review, root)


if __name__ == "__main__":
    unittest.main()
