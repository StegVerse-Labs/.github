from __future__ import annotations

import json
import unittest
from pathlib import Path

from heartbeat_runtime import HeartbeatRuntime
from scripts.run_heartbeat_runtime import load_adapters

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoffs" / "SDK-MCP-CANONICAL-VALIDATION-009.json"
FRAGMENT = ROOT / "control" / "worker-registry.d" / "sdk-mcp-canonical-validation-009.json"
PROFILES = ROOT / "control" / "worker-capability-profiles.json"


class SDKMCPActivationBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        cls.fragment = json.loads(FRAGMENT.read_text(encoding="utf-8"))
        cls.profiles = json.loads(PROFILES.read_text(encoding="utf-8"))

    def test_handoff_uses_existing_machine_authorization_binding(self):
        activation = self.handoff["activation"]
        self.assertEqual("AUTHORIZED", activation["executor_binding"])
        self.assertEqual(
            "StegVerse-org/StegVerse-SDK:tasks/SDK-MCP-CANONICAL-VALIDATION-009.json",
            activation["authorization_ref"],
        )
        self.assertEqual("fenced_atomic_checkout", activation["checkout_policy"])
        self.assertFalse(self.handoff["authority"]["heartbeat_grants_execution_authority"])

    def test_runtime_recognizes_binding_without_heartbeat_authority(self):
        runtime = HeartbeatRuntime(ROOT)
        self.assertTrue(runtime._execution_authorized(self.handoff))
        authority = self.handoff["authority"]
        self.assertEqual("TV/TVC", authority["credential_authority"])
        self.assertEqual("NONE", authority["github_token_runtime_authority"])
        self.assertFalse(authority["non_tv_tvc_secret_or_token_allowed"])
        self.assertFalse(authority["execution_authority_created"])

    def test_registry_policy_matches_handoff_policy(self):
        task = self.fragment["tasks"][0]
        self.assertEqual("SDK-MCP-CANONICAL-VALIDATION-009", task["task_id"])
        self.assertEqual("AUTHORIZED", task["executor_binding"])
        self.assertEqual(
            self.handoff["authority"]["policy_version"],
            task["authorized_policy_version"],
        )
        self.assertFalse(self.fragment["github_token_required"])
        self.assertEqual("TV/TVC", self.fragment["credential_authority"])
        self.assertFalse(self.fragment["non_tv_tvc_secret_or_token_allowed"])

    def test_registry_has_finite_expiry_basis_bounded_by_runtime_window(self):
        task = self.fragment["tasks"][0]
        self.assertEqual(
            "cost-basis/worker-runtime/sdk-mcp-canonical-validation.json",
            task["cost_basis_ref"],
        )
        cost = json.loads((ROOT / task["cost_basis_ref"]).read_text(encoding="utf-8"))
        self.assertEqual("stegverse.worker-runtime-cost-basis/v0.1", cost["schema"])
        self.assertEqual("sdk_mcp_canonical_validation", cost["task_class"])
        self.assertEqual(64, cost["hb_estimate"]["expiry_candidate_beats"])
        self.assertEqual(64, self.handoff["execution"]["runtime_window_beats"])
        self.assertEqual(0, cost["cost_estimate"]["external_cost_usd"])

    def test_sovereign_profile_admits_exact_validation_capabilities_without_authority(self):
        worker = self.fragment["workers"][0]
        profile_id = worker["capability_profile_ref"].split("#", 1)[1]
        profile = next(p for p in self.profiles["profiles"] if p["profile_id"] == profile_id)
        required = set(self.handoff["execution"]["required_capabilities"])
        self.assertTrue(required.issubset(set(worker["capabilities"])))
        self.assertTrue(required.issubset(set(profile["allowed_capabilities"])))
        self.assertEqual("repository_worker", profile["executor_type"])
        self.assertFalse(profile["availability_grants_authority"])
        self.assertFalse(profile["capability_match_grants_authority"])
        self.assertIn("canonical_artifact_validation", profile["allowed_capabilities"])
        self.assertIn("master_records_replay_reconstruction_validation", profile["allowed_capabilities"])

    def test_canonical_runtime_resolves_exactly_one_mcp_worker_after_fragment_admission(self):
        runtime = HeartbeatRuntime(ROOT, adapters=load_adapters(ROOT))
        registry = json.loads((ROOT / "control" / "worker-registry.json").read_text(encoding="utf-8"))
        runtime._apply_registry_fragments(registry)
        task = next(
            item for item in registry["tasks"]
            if item.get("task_id") == "SDK-MCP-CANONICAL-VALIDATION-009"
        )
        worker = runtime._worker_for(task, registry)
        self.assertIsNotNone(worker)
        self.assertEqual("sdk-mcp-canonical-validation-worker", worker["worker_id"])
        self.assertEqual("AVAILABLE", worker["status"])
        self.assertEqual("process:sdk-mcp-canonical-validation-v1", worker["adapter_ref"])


if __name__ == "__main__":
    unittest.main()
