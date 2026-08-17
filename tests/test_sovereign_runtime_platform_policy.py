from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "control" / "sovereign-runtime-platform-policy.json"
ACTIVATION_WORKER = ROOT / "workers" / "sovereign_runtime_activation_worker.py"
RESOLUTION_WORKER = ROOT / "workers" / "sovereign_node_repository_resolution_worker.py"
BOOTSTRAP = ROOT / "scripts" / "bootstrap_sovereign_runtime.py"
TRANSITION = ROOT / "scripts" / "advance_heartbeat_transition.py"
VERIFIER = ROOT / "scripts" / "verify_sovereign_runtime_activation.py"


class SovereignRuntimePlatformPolicyTests(unittest.TestCase):
    def test_policy_requires_stegverse_only_and_prohibits_render(self) -> None:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertEqual(policy["physical_host_cardinality_default"], 1)
        self.assertFalse(policy["additional_physical_host_required"])
        self.assertTrue(policy["physical_peer_requirement_prohibited"])
        self.assertFalse(policy["render_allowed"])
        self.assertFalse(policy["third_party_process_host_allowed"])
        self.assertFalse(policy["third_party_scheduler_allowed"])
        self.assertIn("Render", policy["prohibited_required_dependencies"])
        self.assertIn("GitHub Actions", policy["prohibited_required_dependencies"])
        self.assertEqual(policy["credential_authority"], "TV/TVC")
        self.assertFalse(policy["non_tv_tvc_secret_or_token_allowed"])
        self.assertEqual(policy["github_token_runtime_authority"], "NONE")
        self.assertFalse(policy["hosted_validation_is_activation"])

    def test_runtime_sources_fail_closed_on_render_and_hosted_surfaces(self) -> None:
        activation = ACTIVATION_WORKER.read_text(encoding="utf-8")
        resolution = RESOLUTION_WORKER.read_text(encoding="utf-8")
        bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        transition = TRANSITION.read_text(encoding="utf-8")
        verifier = VERIFIER.read_text(encoding="utf-8")

        for source in (activation, resolution, bootstrap, transition, verifier):
            self.assertIn("RENDER", source)
            self.assertIn("GITHUB_ACTIONS", source)

        self.assertIn("THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_TRANSITION_EVIDENCE", activation)
        self.assertIn("HOSTED_ENVIRONMENT_CANNOT_PRODUCE_SOVEREIGN_TRANSITION", transition)
        self.assertIn("hosted_environment", resolution)
        self.assertIn("hosted", bootstrap.lower())
        self.assertIn("hosted", verifier.lower())

    def test_state_transition_contract_forbids_host_substitution(self) -> None:
        contract = json.loads((ROOT / "management" / "SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json").read_text(encoding="utf-8"))
        self.assertFalse(contract["another_physical_machine_required"])
        self.assertFalse(contract["always_on_external_host_required"])
        self.assertFalse(contract["wall_clock_continuous_process_required"])
        self.assertEqual(contract["sole_permitted_user_physical_carrier"], "CURRENT_USER_IPHONE")
        prohibited = " ".join(contract["prohibited_substitutions"])
        self.assertIn("Render", prohibited)
        self.assertIn("GitHub Actions", prohibited)
        self.assertEqual(contract["credential_boundary"]["credential_authority"], "TV/TVC")


if __name__ == "__main__":
    unittest.main()
