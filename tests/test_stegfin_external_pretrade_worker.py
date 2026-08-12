from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKER_PATH = ROOT / "workers" / "stegfin_external_pretrade_worker.py"
HANDOFF = ROOT / "handoffs" / "STEGFIN-LIVE-PRETRADE-005.json"
REGISTRY = ROOT / "control" / "worker-registry.d" / "stegfin-live-pretrade-005.json"
ADAPTER = ROOT / "control" / "process-worker-adapters.d" / "stegfin-live-pretrade-005.json"


spec = importlib.util.spec_from_file_location("stegfin_external_pretrade_worker", WORKER_PATH)
assert spec and spec.loader
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class StegFinExternalPretradeWorkerTests(unittest.TestCase):
    def test_registry_and_adapter_bind_unique_capability(self) -> None:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        adapter = json.loads(ADAPTER.read_text(encoding="utf-8"))
        task = registry["tasks"][0]
        registered_worker = registry["workers"][0]
        adapter_entry = adapter["adapters"][0]
        self.assertEqual(task["task_id"], "STEGFIN-LIVE-PRETRADE-005")
        self.assertEqual(registered_worker["adapter_ref"], "process:stegfin-live-pretrade-v1")
        self.assertIn("stegfin_external_pretrade_preparation", registered_worker["capabilities"])
        self.assertEqual(adapter_entry["adapter_ref"], registered_worker["adapter_ref"])
        self.assertIn("stegfin_external_pretrade_preparation", adapter_entry["capabilities"])

    def test_adapter_allowlist_contains_no_credential_variables(self) -> None:
        adapter = json.loads(ADAPTER.read_text(encoding="utf-8"))["adapters"][0]
        allow = set(adapter.get("env_allowlist") or [])
        forbidden = {
            "GITHUB_TOKEN", "GH_TOKEN", "ZEROEX_API_KEY", "OPENAI_API_KEY",
            "PRIVATE_KEY", "WALLET_PRIVATE_KEY", "SEED_PHRASE", "MNEMONIC",
            "CLOUDFLARE_API_TOKEN", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
        }
        self.assertTrue(allow.isdisjoint(forbidden))
        self.assertEqual(
            allow,
            {"STEGVERSE_STEGFIN_SOURCE_ROOT", "STEGVERSE_TV_SOURCE_ROOT", "STEGVERSE_TVC_SOURCE_ROOT", "HOME", "XDG_STATE_HOME", "LOCALAPPDATA"},
        )

    def test_handoff_stops_at_user_wallet_boundary(self) -> None:
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        authority = handoff["authority"]
        self.assertEqual(authority["credential_authority"], "TV/TVC")
        self.assertEqual(authority["provider_capability_authority"], "TV_TVC_VAULT_ONLY")
        self.assertEqual(authority["wallet_signing_authority"], "USER_ONLY")
        self.assertEqual(authority["broadcast_authority"], "USER_ONLY")
        self.assertEqual(authority["github_token_production_authority"], "NONE")
        self.assertEqual(handoff["goal"]["successor_policy"], "HUMAN_AUTHORITY_REQUIRED_AT_WALLET_BOUNDARY")

    def test_provider_capability_permission_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "provider_0x"
            path.write_text("not-read-by-test", encoding="utf-8")
            os.chmod(path, 0o600)
            self.assertTrue(worker.protected_provider_capability(path))
            os.chmod(path, 0o640)
            self.assertFalse(worker.protected_provider_capability(path))

    def test_worker_source_uses_canonical_tvc_and_vault_surfaces(self) -> None:
        source = WORKER_PATH.read_text(encoding="utf-8")
        for marker in (
            "tvc_stegwallet_trading_gate_cli.py",
            "tvc_resolve_provider_capability.py",
            "tvc_issue_stegwallet_quote_lease.py",
            "build_sovereign_validation_trade_request.py",
            "build_tv_tvc_registry_approval.py",
            "build_sovereign_live_pretrade_e1.py",
            "run_tv_tvc_sovereign_pretrade.py",
            "USER_APPROVAL_REQUIRED",
            "USER_SWAP_SIGNATURE_REQUIRED",
            '"credential_authority": "TV/TVC"',
            '"github_token_required": False',
        ):
            self.assertIn(marker, source)
        for forbidden in (
            "GITHUB_TOKEN", "GH_TOKEN", "ZEROEX_API_KEY", "WALLET_PRIVATE_KEY",
            "SEED_PHRASE", "MNEMONIC", "OPENAI_API_KEY",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
