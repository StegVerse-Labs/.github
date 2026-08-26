from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestLanesAutolaunchBindingTests(unittest.TestCase):
    def test_native_binding_contract(self) -> None:
        task = json.loads((ROOT / "control" / "worker-registry.d" / "test-lanes-autolaunch.json").read_text())
        adapter = json.loads((ROOT / "control" / "process-worker-adapters.d" / "test-lanes-autolaunch.json").read_text())
        auth = json.loads((ROOT / "authorizations" / "STEGVERSE-TEST-LANES-AUTOLAUNCH-001.json").read_text())
        handoff = json.loads((ROOT / "handoffs" / "STEGVERSE-TEST-LANES-AUTOLAUNCH-001.json").read_text())
        cost = json.loads((ROOT / "cost-basis" / "worker-runtime" / "test-lanes-autolaunch.json").read_text())

        self.assertEqual(task["schema"], "stegverse.worker-registry-fragment/v0.1")
        row = task["tasks"][0]
        self.assertEqual(row["task_id"], "STEGVERSE-TEST-LANES-AUTOLAUNCH-001")
        self.assertEqual(row["state"], "HANDOFF_READY")
        self.assertEqual(row["executor_binding"], "AUTHORIZED")
        self.assertEqual(row["handoff_ref"], "handoffs/STEGVERSE-TEST-LANES-AUTOLAUNCH-001.json")
        self.assertEqual(row["cost_basis_ref"], "cost-basis/worker-runtime/test-lanes-autolaunch.json")

        self.assertEqual(adapter["schema"], "stegverse.process-worker-adapter-fragment/v0.1")
        binding = adapter["adapters"][0]
        self.assertEqual(binding["adapter_ref"], "process:test-lanes-autolaunch-v1")
        self.assertEqual(binding["command"], ["python", "workers/test_lanes_autolaunch_entrypoint.py"])
        for name in (
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "DEEPSEEK_API_KEY",
            "MOONSHOT_API_KEY",
            "GITHUB_TOKEN",
            "GH_TOKEN",
        ):
            self.assertNotIn(name, binding["env_allowlist"])

        self.assertEqual(auth["credential_authority"], "TV/TVC")
        self.assertFalse(auth["heartbeat_grants_execution_authority"])
        self.assertEqual(auth["primary_provider"], "stegverse_local")
        self.assertFalse(auth["provider_secret_transport_allowed"])

        self.assertEqual(handoff["schema"], "stegverse.executable-handoff/v0.1")
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertEqual(handoff["authority"]["credential_authority"], "TV/TVC")
        self.assertEqual(handoff["execution"]["runtime_window_beats"], 128)

        self.assertEqual(cost["schema"], "stegverse.worker-runtime-cost-basis/v0.1")
        self.assertEqual(cost["hb_estimate"]["expiry_candidate_beats"], 128)


if __name__ == "__main__":
    unittest.main()
