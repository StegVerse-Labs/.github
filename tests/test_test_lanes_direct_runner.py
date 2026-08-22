from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "run_test_lanes_direct.py"
SPEC = importlib.util.spec_from_file_location("run_test_lanes_direct", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class DirectTestLanesRunnerTests(unittest.TestCase):
    def test_direct_runner_has_no_heartbeat_or_g18_runtime_dependency(self) -> None:
        text = PATH.read_text(encoding="utf-8")
        prohibited = (
            "heartbeat-carrier-runtime-state.json",
            "worker-runtime-state.json",
            "SHWP-DURABLE-RUNTIME-ACTIVATION-G18",
            "heartbeat-transition-continuity",
            "sovereign_same_execution_activation",
        )
        for marker in prohibited:
            self.assertNotIn(marker, text)
        self.assertIn('"heartbeat_required": False', text)
        self.assertIn('"g18_required": False', text)
        self.assertIn('"worker_coordinator_required": False', text)

    def test_direct_runner_uses_canonical_bounded_primary_launcher(self) -> None:
        text = PATH.read_text(encoding="utf-8")
        self.assertIn('"tools/run_sovereign_model.py"', text)
        self.assertIn('"http://127.0.0.1:11435"', text)
        self.assertIn('"BOUNDED_CANONICAL_TEST_PROCESS"', text)
        self.assertIn("stop_process(primary_process)", text)

    def test_direct_runner_bootstraps_existing_tvc_services_without_reading_secret_values(self) -> None:
        text = PATH.read_text(encoding="utf-8")
        self.assertIn('"stegwallet.container_vault_agent"', text)
        self.assertIn('"scripts/run_vault_broker.py"', text)
        self.assertIn('"--provider-secret-file"', text)
        self.assertIn('"BOUNDED_EXISTING_TVC_SERVICES"', text)
        self.assertNotIn("read_text(encoding=\"utf-8\") for provider", text)
        self.assertNotIn("read_bytes()", text)

    def test_missing_provider_registration_is_explicit_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "runtime-secrets").mkdir()
            with self.assertRaisesRegex(RuntimeError, "TVC_PROVIDER_CREDENTIAL_REGISTRATION_REQUIRED"):
                MODULE.provider_secret_paths(root)

    def test_provider_secret_metadata_must_be_restrictive(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            secret_dir = root / "runtime-secrets"
            secret_dir.mkdir()
            for provider, name in MODULE.PROVIDER_SECRET_FILES.items():
                path = secret_dir / name
                path.write_text("placeholder", encoding="utf-8")
                os.chmod(path, 0o400)
            paths = MODULE.provider_secret_paths(root)
            self.assertEqual(set(paths), set(MODULE.PROVIDERS))
            os.chmod(paths["openai"], 0o440)
            with self.assertRaisesRegex(RuntimeError, "TVC_PROVIDER_SECRET_PERMISSIONS_TOO_BROAD:openai"):
                MODULE.provider_secret_paths(root)

    def test_terminal_pass_requires_helper_success_comparison_pass_and_nine_evidence_records(self) -> None:
        good = {"comparison_state": "PASS", "lane_evidence_count": 9}
        self.assertTrue(MODULE.execution_passed(True, good))
        self.assertFalse(MODULE.execution_passed(False, good))
        self.assertFalse(MODULE.execution_passed(True, {"comparison_state": "BLOCKED", "lane_evidence_count": 9}))
        self.assertFalse(MODULE.execution_passed(True, {"comparison_state": "PASS", "lane_evidence_count": 8}))
        self.assertFalse(MODULE.execution_passed(True, None))

    def test_canonical_model_selection_requires_all_four_external_models(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "models.json"
            path.write_text(json.dumps({
                "schema": "stegverse.test-lanes-model-selection/v1",
                "test_id": "SV-COST-NINE-LANE-v1",
                "models": {
                    "openai": "gpt-5.6-sol",
                    "anthropic": "claude-opus-5",
                    "deepseek": "deepseek-v4-pro",
                    "kimi": "kimi-k3",
                },
            }), encoding="utf-8")
            selected = MODULE.validate_model_selection(path)
            self.assertEqual(selected["openai"], "gpt-5.6-sol")
            self.assertEqual(selected["anthropic"], "claude-opus-5")
            self.assertEqual(selected["deepseek"], "deepseek-v4-pro")
            self.assertEqual(selected["kimi"], "kimi-k3")

    def test_canonical_plan_requires_nine_ready_lanes_and_five_groups(self) -> None:
        providers = [
            "openai", "openai", "anthropic", "anthropic", "stegverse_local",
            "deepseek", "deepseek", "kimi", "kimi",
        ]
        plan = {
            "state": "READY",
            "primary_provider": "stegverse_local",
            "lanes": [
                {"lane_id": f"lane-{i}", "provider": provider, "state": "READY_LOCAL_PRIMARY" if provider == "stegverse_local" else "READY_FOR_TVC_EXECUTION"}
                for i, provider in enumerate(providers)
            ],
            "execution_groups": [{"execution_group_id": f"g-{i}"} for i in range(5)],
        }
        MODULE.assert_full_nine_ready(plan)
        plan["lanes"][0]["state"] = "SKIPPED_OPTIONAL_CREDENTIAL_UNBOUND"
        with self.assertRaises(RuntimeError):
            MODULE.assert_full_nine_ready(plan)


if __name__ == "__main__":
    unittest.main()
