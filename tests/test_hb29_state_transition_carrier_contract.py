from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "advance_heartbeat_transition.py"
CONTRACT = ROOT / "management" / "SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json"
BLOCKER = ROOT / "management" / "SHWP_RUNTIME_ACTIVATION_BLOCKER.json"
HANDOFF = ROOT / "handoffs" / "SHWP-DURABLE-RUNTIME-ACTIVATION.json"
BOOTSTRAP = ROOT / "scripts" / "bootstrap_sovereign_runtime.py"

spec = importlib.util.spec_from_file_location("advance_heartbeat_transition", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class HB29StateTransitionCarrierContractTests(unittest.TestCase):
    def test_contract_does_not_require_another_machine_or_always_on_host(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["continuity_model"], "STATE_TRANSITION_CONTINUITY")
        self.assertEqual(contract["legacy_epoch"], 29)
        self.assertEqual(contract["first_successor_epoch"], 30)
        self.assertFalse(contract["another_physical_machine_required"])
        self.assertFalse(contract["always_on_external_host_required"])
        self.assertFalse(contract["wall_clock_continuous_process_required"])
        self.assertEqual(contract["credential_boundary"]["credential_authority"], "TV/TVC")
        self.assertEqual(contract["credential_boundary"]["github_token_runtime_authority"], "NONE")
        self.assertFalse(contract["credential_boundary"]["non_tv_tvc_secret_or_token_allowed"])

    def test_current_blocker_preserves_iphone_state_transition_policy(self):
        blocker = json.loads(BLOCKER.read_text(encoding="utf-8"))
        self.assertEqual(blocker["sole_permitted_user_physical_carrier"], "CURRENT_USER_IPHONE")
        self.assertFalse(blocker["additional_physical_machine_allowed_or_required"])
        self.assertFalse(blocker["corrected_invariants"]["wall_clock_continuous_process_is_required_for_continuity"])
        self.assertTrue(blocker["corrected_invariants"]["heartbeat_continuity_is_state_transition_continuity"])

    def test_handoff_cannot_make_continuous_external_host_a_release_prerequisite(self):
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        continuity = handoff.get("state_transition_continuity") or {}
        self.assertEqual(continuity.get("contract_ref"), "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json")
        self.assertFalse(continuity.get("always_on_external_host_required"))
        self.assertFalse(continuity.get("wall_clock_continuous_process_required"))
        self.assertEqual(continuity.get("transition_producer"), "scripts/advance_heartbeat_transition.py")

    def test_bootstrap_eligibility_uses_v12_separated_sources(self):
        text = BOOTSTRAP.read_text(encoding="utf-8")
        required_block = text.split("REQUIRED_SOURCE_FILES = (", 1)[1].split(")\nREQUIRED_PREDICATES", 1)[0]
        self.assertIn('Path("heartbeat_runtime/engine_v12.py")', required_block)
        self.assertIn('Path("heartbeat_runtime/worker_runtime.py")', required_block)
        self.assertIn('Path("scripts/run_worker_runtime.py")', required_block)
        self.assertNotIn('Path("heartbeat_runtime/engine_v11.py")', required_block)

    def test_transition_producer_advances_without_forwarding_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "management").mkdir(parents=True)
            (root / "control").mkdir(parents=True)
            (root / "scripts").mkdir(parents=True)
            (root / "heartbeat_runtime").mkdir(parents=True)
            (root / "receipts" / "heartbeat-schema-cutover").mkdir(parents=True)

            (root / "management" / "SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json").write_text(
                json.dumps({
                    "continuity_model": "STATE_TRANSITION_CONTINUITY",
                    "legacy_epoch": 29,
                    "first_successor_epoch": 30,
                    "always_on_external_host_required": False,
                }),
                encoding="utf-8",
            )
            legacy = {"schema": "stegverse.org-heartbeat-state/v1", "epoch": 29, "generation": 29}
            (root / "control" / "heartbeat-state.json").write_text(json.dumps(legacy), encoding="utf-8")
            (root / "scripts" / "run_heartbeat_runtime.py").write_text("# test stub\n", encoding="utf-8")
            (root / "heartbeat_runtime" / "engine_v12.py").write_text("# test stub\n", encoding="utf-8")

            captured_env = {}

            def fake_run(command, **kwargs):
                captured_env.update(kwargs.get("env") or {})
                carrier = {
                    "schema": "stegverse.heartbeat-carrier-runtime-state/v1",
                    "epoch": 30,
                    "generation": 30,
                }
                control_plane = {
                    "schema": "stegverse.worker-control-plane-coordination/v1",
                    "worker_coordination": {
                        "active_leases": [
                            {
                                "claim_id": "G18",
                                "fencing_token": 18,
                                "worker_instance_id": "worker-G18",
                            }
                        ]
                    },
                }
                (root / "control" / "heartbeat-carrier-runtime-state.json").write_text(json.dumps(carrier), encoding="utf-8")
                (root / "control" / "worker-control-plane-coordination.json").write_text(json.dumps(control_plane), encoding="utf-8")
                (root / "receipts" / "heartbeat-schema-cutover" / "HB29.json").write_text("{}", encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            receipt_path = root / "receipts" / "heartbeat-transition-continuity" / "latest.json"
            with patch.object(module.subprocess, "run", side_effect=fake_run):
                result = module.advance(
                    root,
                    receipt_path,
                    env={
                        "HOME": str(root),
                        "PATH": "/usr/bin",
                        "GITHUB_TOKEN": "forbidden",
                        "TVC_TOKEN": "also-not-forwarded",
                    },
                )

            self.assertEqual(result["state"], "CARRIER_TRANSITION_COMPLETE")
            self.assertEqual(result["carrier_epoch_before"], 29)
            self.assertEqual(result["carrier_epoch_after"], 30)
            self.assertTrue(result["predicates"]["legacy_hb29_unchanged"])
            self.assertNotIn("GITHUB_TOKEN", captured_env)
            self.assertNotIn("TVC_TOKEN", captured_env)
            self.assertEqual(result["credential_authority"], "TV/TVC")
            self.assertEqual(result["github_token_runtime_authority"], "NONE")

    def test_hosted_environment_fails_closed_without_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt_path = root / "receipt.json"
            result = module.advance(root, receipt_path, env={"GITHUB_ACTIONS": "true"})
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "HOSTED_ENVIRONMENT_CANNOT_PRODUCE_SOVEREIGN_TRANSITION")
            self.assertTrue(result["hosted_environment_rejected"])


if __name__ == "__main__":
    unittest.main()
