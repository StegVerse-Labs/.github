from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from workers.stegfin_live_entry_inventory_worker import child_env, verified_inventory_envelope

ROOT = Path(__file__).resolve().parents[1]


def envelope() -> dict:
    return {
        "inventory": {
            "schema": "stegwallet.base_asset_lounge_snapshot.v1",
            "chain_id": "0x2105",
            "inventory_state_hash": "sha256:inventory",
            "boundary_state_hash": "sha256:boundary",
            "assets": [{"symbol": "ETH"}, {"symbol": "USDC"}, {"symbol": "WETH"}],
        },
        "observation_receipt": {
            "schema": "stegwallet.live_inventory_observation_receipt.v1",
            "state": "INVENTORY_N_OBSERVED",
            "complete_current_asset_inventory": True,
            "provider_capability_required": False,
            "github_token_required": False,
            "github_runtime_required": False,
            "wallet_contacted": False,
            "signed": False,
            "broadcast": False,
            "trade_authority_granted": False,
            "authority_effect": "NONE_OBSERVATION_ONLY",
            "inventory_state_hash": "sha256:inventory",
            "boundary_state_hash": "sha256:boundary",
        },
    }


class StegFinLiveEntryInventoryWorkerTests(unittest.TestCase):
    def test_inventory_envelope_requires_complete_non_authorizing_observation(self) -> None:
        value = envelope()
        self.assertTrue(verified_inventory_envelope(value))
        value["observation_receipt"]["trade_authority_granted"] = True
        self.assertFalse(verified_inventory_envelope(value))

    def test_inventory_envelope_rejects_state_hash_drift(self) -> None:
        value = envelope()
        value["observation_receipt"]["inventory_state_hash"] = "sha256:other"
        self.assertFalse(verified_inventory_envelope(value))

    def test_child_environment_contains_no_github_provider_or_wallet_credentials(self) -> None:
        forbidden = {
            "GITHUB_TOKEN": "forbidden",
            "GH_TOKEN": "forbidden",
            "ZEROEX_API_KEY": "forbidden",
            "WALLET_PRIVATE_KEY": "forbidden",
            "AWS_SECRET_ACCESS_KEY": "forbidden",
        }
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, forbidden, clear=False):
            root = Path(td)
            env = child_env(root)
        self.assertEqual(set(env), {"PATH", "PYTHONPATH", "LANG", "LC_ALL"})
        self.assertEqual(env["PYTHONPATH"], str(root))
        for name in forbidden:
            self.assertNotIn(name, env)

    def test_v2_append_only_executor_is_the_task_specific_repair(self) -> None:
        fragment = json.loads((ROOT / "control/worker-registry.d/stegfin-live-entry-003-executor-v2.json").read_text())
        self.assertEqual(fragment["tasks"], [])
        worker = fragment["workers"][0]
        self.assertEqual(worker["worker_id"], "stegfin-live-entry-inventory-worker-v2")
        self.assertIn("stegfin_live_entry_inventory_observation", worker["capabilities"])
        self.assertFalse(fragment["historical_worker_mutated"])
        self.assertFalse(fragment["github_token_required"])

    def test_v2_is_the_only_worker_eligible_for_live_entry_required_capabilities(self) -> None:
        handoff = json.loads((ROOT / "handoffs/STEGFIN-LIVE-ENTRY-003.json").read_text())
        required = set(handoff["execution"]["required_capabilities"])
        registry = json.loads((ROOT / "control/worker-registry.json").read_text())
        fragment = json.loads((ROOT / "control/worker-registry.d/stegfin-live-entry-003-executor-v2.json").read_text())
        workers = list(registry["workers"]) + list(fragment["workers"])
        profiles = json.loads((ROOT / "control/worker-capability-profiles.json").read_text())
        profile_map = {row["profile_id"]: row for row in profiles["profiles"]}
        eligible = []
        for worker in workers:
            if worker.get("status") != "AVAILABLE":
                continue
            worker_caps = set(worker.get("capabilities") or [])
            profile_ref = worker.get("capability_profile_ref") or ""
            profile_id = profile_ref.split("#", 1)[-1]
            profile = profile_map.get(profile_id)
            if not profile:
                continue
            if not required.issubset(worker_caps):
                continue
            if not required.issubset(set(profile.get("allowed_capabilities") or [])):
                continue
            eligible.append(worker["worker_id"])
        self.assertEqual(eligible, ["stegfin-live-entry-inventory-worker-v2"])


if __name__ == "__main__":
    unittest.main()
