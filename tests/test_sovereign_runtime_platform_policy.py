from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "control" / "sovereign-runtime-platform-policy.json"
ACTIVATION_WORKER = ROOT / "workers" / "sovereign_runtime_activation_worker.py"
RESOLUTION_WORKER = ROOT / "workers" / "sovereign_node_repository_resolution_worker.py"
BOOTSTRAP = ROOT / "scripts" / "bootstrap_sovereign_runtime.py"
VERIFIER = ROOT / "scripts" / "verify_sovereign_runtime_activation.py"


class SovereignRuntimePlatformPolicyTests(unittest.TestCase):
    def test_policy_requires_stegverse_only_and_prohibits_render(self) -> None:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertEqual(policy["execution_domain"], "DEPLOYMENT_LOCAL_SOVEREIGN_HOST_ONLY")
        self.assertEqual(policy["physical_host_cardinality_default"], 1)
        self.assertFalse(policy["additional_physical_host_required"])
        self.assertTrue(policy["physical_peer_requirement_prohibited"])
        self.assertFalse(policy["render_allowed"])
        self.assertFalse(policy["third_party_process_host_allowed"])
        self.assertFalse(policy["third_party_scheduler_allowed"])
        self.assertEqual(
            policy["fallback_policy"],
            "FAIL_CLOSED_OR_USE_SAME_HOST_LOGICAL_ISOLATION; NEVER SUBSTITUTE_THIRD_PARTY_RUNTIME_OR_MACHINE",
        )
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
        verifier = VERIFIER.read_text(encoding="utf-8")

        for source in (activation, resolution, bootstrap, verifier):
            self.assertIn("RENDER", source)
            self.assertIn("GITHUB_ACTIONS", source)

        self.assertIn("THIRD_PARTY_HOST_IS_NOT_SOVEREIGN_RUNTIME_EVIDENCE", activation)
        self.assertIn("hosted_environment", resolution)
        self.assertIn("hosted", bootstrap.lower())
        self.assertIn("hosted", verifier.lower())

    def test_policy_allows_only_stegverse_carrier_classes(self) -> None:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        carriers = policy["allowed_carrier_classes"]
        self.assertGreaterEqual(len(carriers), 2)
        self.assertTrue(all("StegVerse" in carrier for carrier in carriers))
        self.assertTrue(policy["activation_evidence_must_be_host_local"])
        self.assertIn("deployment's own sovereign physical host", policy["machine_observable_release_condition"])
        self.assertIn("isolated same-host StegVerse logical nodes", policy["machine_observable_release_condition"])
        self.assertFalse(policy["third_party_machine_required"])


if __name__ == "__main__":
    unittest.main()
