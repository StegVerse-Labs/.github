import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("autolaunch_worker", ROOT / "workers" / "test_lanes_autolaunch_worker.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class AutolaunchWorkerTests(unittest.TestCase):
    def test_provider_and_github_secrets_are_detected(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "not-a-real-key"}, clear=True):
            self.assertTrue(MODULE.secret_env_detected())
        with patch.dict(os.environ, {"GITHUB_TOKEN": "not-a-real-token"}, clear=True):
            self.assertTrue(MODULE.secret_env_detected())
        with patch.dict(os.environ, {"STEGVERSE_TVC_ROOT": "/tmp/tvc"}, clear=True):
            self.assertFalse(MODULE.secret_env_detected())

    def test_hosted_environment_is_not_runtime_eligible(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True):
            self.assertTrue(MODULE.hosted_environment())
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(MODULE.hosted_environment())

    def test_model_selection_is_nonsecret_and_exact_four_provider_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "selection.json"
            path.write_text(json.dumps({
                "schema": "stegverse.test-lanes-model-selection/v1",
                "test_id": "SV-COST-NINE-LANE-v1",
                "models": {
                    "openai": "gpt-test",
                    "anthropic": "claude-test",
                    "deepseek": "deepseek-test",
                    "kimi": "kimi-test"
                }
            }))
            with patch.dict(os.environ, {"STEGVERSE_TEST_LANES_MODEL_SELECTION": str(path)}, clear=True):
                models, selected_path = MODULE.model_selection()
            self.assertEqual(set(models), {"openai", "anthropic", "deepseek", "kimi"})
            self.assertEqual(selected_path, path)

    def test_incomplete_model_selection_does_not_satisfy_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "selection.json"
            path.write_text(json.dumps({
                "schema": "stegverse.test-lanes-model-selection/v1",
                "test_id": "SV-COST-NINE-LANE-v1",
                "models": {"openai": "gpt-test"}
            }))
            with patch.dict(os.environ, {"STEGVERSE_TEST_LANES_MODEL_SELECTION": str(path), "HOME": directory}, clear=True):
                models, selected_path = MODULE.model_selection()
            self.assertEqual(models, {})
            self.assertIsNone(selected_path)

    def test_stale_lower_fence_claim_is_superseded_not_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt_root = Path(directory)
            active = receipt_root / "active-claim.json"
            active.write_text(json.dumps({
                "schema": "stegverse.test-lanes-run-claim/v1",
                "state": "ACTIVE",
                "test_run_claim_id": "old:claim",
                "fencing_token": 20
            }))
            with patch.object(MODULE, "RECEIPT_ROOT", receipt_root), patch.object(MODULE, "ACTIVE_CLAIM", active):
                conflict, prior = MODULE.active_claim_conflict(21)
            self.assertFalse(conflict)
            self.assertEqual(prior["state"], "SUPERSEDED")
            self.assertFalse(active.exists())

    def test_current_or_newer_active_claim_blocks_duplicate_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            active = Path(directory) / "active-claim.json"
            active.write_text(json.dumps({"state": "ACTIVE", "test_run_claim_id": "live", "fencing_token": 22}))
            with patch.object(MODULE, "ACTIVE_CLAIM", active):
                conflict, prior = MODULE.active_claim_conflict(22)
            self.assertTrue(conflict)
            self.assertEqual(prior["state"], "ACTIVE")


if __name__ == "__main__":
    unittest.main()
