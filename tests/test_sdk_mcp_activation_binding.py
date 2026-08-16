from __future__ import annotations

import json
import unittest
from pathlib import Path

from heartbeat_runtime.engine_v2 import HeartbeatRuntime

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoffs" / "SDK-MCP-CANONICAL-VALIDATION-009.json"
FRAGMENT = ROOT / "control" / "worker-registry.d" / "sdk-mcp-canonical-validation-009.json"


class SDKMCPActivationBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        cls.fragment = json.loads(FRAGMENT.read_text(encoding="utf-8"))

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


if __name__ == "__main__":
    unittest.main()
