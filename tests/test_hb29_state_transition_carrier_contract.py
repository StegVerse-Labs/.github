from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

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
    def test_contract_is_independent_oscillator_continuity_without_host_authority(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["continuity_model"], "INDEPENDENT_OSCILLATOR_CONTINUITY")
        self.assertEqual(contract["legacy_epoch"], 29)
        oscillator = contract["oscillator"]
        self.assertEqual(oscillator["mechanism"], "INDEPENDENT_PHASE_OSCILLATOR")
        self.assertEqual(oscillator["phase_travel_time_ms"], 10)
        self.assertEqual(oscillator["reference_frequency_hz"], 100)
        self.assertEqual(oscillator["progression_dependency"], "OSCILLATOR_ONLY")
        self.assertFalse(oscillator["worker_or_task_gating"])
        self.assertFalse(oscillator["observation_is_causal"])
        fallback = contract["third_party_fallback_policy"]
        self.assertFalse(fallback["required_dependency"])
        self.assertEqual(fallback["role"], "FALLBACK_ONLY")
        self.assertEqual(contract["credential_boundary"]["credential_authority"], "TV/TVC")
        self.assertEqual(contract["credential_boundary"]["github_token_runtime_authority"], "NONE")
        self.assertFalse(contract["credential_boundary"]["non_tv_tvc_secret_or_token_allowed"])

    def test_current_blocker_preserves_iphone_state_transition_policy(self):
        blocker = json.loads(BLOCKER.read_text(encoding="utf-8"))
        self.assertEqual(blocker["sole_permitted_user_physical_carrier"], "CURRENT_USER_IPHONE")
        self.assertFalse(blocker["additional_physical_machine_allowed_or_required"])
        self.assertFalse(blocker["corrected_invariants"]["wall_clock_continuous_process_is_required_for_continuity"])
        self.assertTrue(blocker["corrected_invariants"]["heartbeat_continuity_is_state_transition_continuity"])

    def test_handoff_binds_oscillator_continuity_without_external_host_prerequisite(self):
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        continuity = handoff["state_transition_continuity"]
        execution = handoff["execution"]
        self.assertEqual(continuity["contract_ref"], "management/SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json")
        self.assertEqual(continuity["continuity_model"], "INDEPENDENT_OSCILLATOR_CONTINUITY")
        self.assertEqual(continuity["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")
        self.assertFalse(continuity["worker_or_task_gating_of_heartbeat"])
        self.assertFalse(continuity["always_on_external_host_required"])
        self.assertFalse(continuity["another_physical_machine_required"])
        self.assertEqual(execution["carrier_runtime_entrypoint"], "scripts/run_heartbeat_runtime.py")
        self.assertEqual(execution["worker_runtime_entrypoint"], "scripts/run_worker_runtime.py")

    def test_bootstrap_eligibility_uses_separated_sources(self):
        text = BOOTSTRAP.read_text(encoding="utf-8")
        required_block = text.split("REQUIRED_SOURCE_FILES = (", 1)[1].split(")\nREQUIRED_PREDICATES", 1)[0]
        self.assertIn('Path("heartbeat_runtime/engine_v12.py")', required_block)
        self.assertIn('Path("heartbeat_runtime/worker_runtime.py")', required_block)
        self.assertIn('Path("scripts/run_worker_runtime.py")', required_block)
        self.assertNotIn('Path("heartbeat_runtime/engine_v11.py")', required_block)

    def test_compatibility_command_is_sampling_not_invocation_driven_advancement(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("INDEPENDENT_OSCILLATOR_CONTINUITY", source)
        self.assertIn('"progression_dependency": "OSCILLATOR_ONLY"', source)
        self.assertIn('"observation_is_causal": False', source)
        self.assertIn("HeartbeatRuntime(root).cycle(write=True)", source)
        self.assertNotIn("subprocess.run", source)
        self.assertNotIn("GITHUB_TOKEN", source)
        self.assertNotIn("TVC_TOKEN", source)

    def test_hosted_environment_fails_closed_without_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt_path = root / "receipt.json"
            result = module.sample(root, receipt_path, env={"GITHUB_ACTIONS": "true"})
            self.assertEqual(result["state"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "THIRD_PARTY_HOST_IS_NOT_PRIMARY_SOVEREIGN_CARRIER_EVIDENCE")
            self.assertEqual(result["progression_dependency"], "OSCILLATOR_ONLY")
            self.assertFalse(result["observation_is_causal"])
            self.assertFalse((root / "control" / "heartbeat-carrier-runtime-state.json").exists())


if __name__ == "__main__":
    unittest.main()
