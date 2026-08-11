from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from workers.stegfin_sovereign_trading_worker import env

ROOT = Path(__file__).resolve().parents[1]


class StegFinSovereignTradingWorkerTests(unittest.TestCase):
    def test_worker_child_environment_strips_github_provider_wallet_and_cloud_credentials(self) -> None:
        forbidden = {
            "GITHUB_TOKEN": "forbidden",
            "GH_TOKEN": "forbidden",
            "ZEROEX_API_KEY": "forbidden",
            "WALLET_PRIVATE_KEY": "forbidden",
            "AWS_SECRET_ACCESS_KEY": "forbidden",
            "CLOUDFLARE_API_TOKEN": "forbidden",
        }
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, forbidden, clear=False):
            root = Path(td)
            child = env(root)
        self.assertEqual(set(child), {"PATH", "PYTHONPATH", "LANG", "LC_ALL"})
        self.assertEqual(child["PYTHONPATH"], str(root))
        for name in forbidden:
            self.assertNotIn(name, child)

    def test_registry_fragment_uniquely_binds_internal_activation_worker(self) -> None:
        fragment = json.loads((ROOT / "control/worker-registry.d/stegfin-sovereign-trading-001.json").read_text())
        task = fragment["tasks"][0]
        worker = fragment["workers"][0]
        capability = "stegfin_sovereign_internal_trading_activation"
        self.assertEqual(task["task_id"], "SHWP-STEGFIN-SOVEREIGN-TRADING-001")
        self.assertEqual(worker["worker_id"], "stegfin-sovereign-trading-worker")
        self.assertIn(capability, worker["capabilities"])
        self.assertFalse(fragment["github_token_required"])
        self.assertEqual(fragment["provider_capability_authority"], "TV_TVC_UNCHANGED")
        self.assertFalse(fragment["wallet_signing_authority"])
        self.assertFalse(fragment["transaction_broadcast_authority"])

    def test_handoff_has_zero_external_financial_authority(self) -> None:
        handoff = json.loads((ROOT / "handoffs/SHWP-STEGFIN-SOVEREIGN-TRADING-001.json").read_text())
        caps = set(handoff["execution"]["required_capabilities"])
        self.assertIn("stegfin_sovereign_internal_trading_activation", caps)
        self.assertEqual(handoff["execution"]["external_cost_ceiling_usd"], 0)
        self.assertIn("TV/TVC credential authority unaffected", handoff["authority"]["authority_source"])
        ceiling = set(handoff["goal"]["authority_ceiling"])
        self.assertIn("no_wallet_signing", ceiling)
        self.assertIn("no_transaction_broadcast", ceiling)
        self.assertIn("no_external_custody", ceiling)
        self.assertIn("no_scale_up", ceiling)
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])

    def test_profile_admits_bounded_internal_activation_without_expanding_authority(self) -> None:
        profiles = json.loads((ROOT / "control/worker-capability-profiles.json").read_text())
        profile = next(row for row in profiles["profiles"] if row["profile_id"] == "sovereign-runtime-worker-v1")
        allowed = set(profile["allowed_capabilities"])
        self.assertIn("bounded_process_execution", allowed)
        self.assertIn("stegfin_sovereign_internal_trading_activation", allowed)
        self.assertFalse(profile["availability_grants_authority"])
        self.assertFalse(profile["capability_match_grants_authority"])


if __name__ == "__main__":
    unittest.main()
