from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "stegfin_live_entry_inventory_worker.py"


def load_worker():
    spec = importlib.util.spec_from_file_location("stegfin_live_entry_inventory_worker", WORKER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StegFinLocalSourceDiscoveryTests(unittest.TestCase):
    def test_explicit_local_source_root_is_reused_without_network_or_credentials(self) -> None:
        module = load_worker()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "stegfin-governance"
            for relative in (
                "scripts/observe_live_base_inventory.py",
                "stegwallet/live_pretrade.py",
                "registries/base_0x_v2_candidate_2026_07.json",
                "docs/STEGFIN_MIRROR_HANDOFF.md",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture\n", encoding="utf-8")
            prior = os.environ.get("STEGVERSE_STEGFIN_SOURCE_ROOT")
            os.environ["STEGVERSE_STEGFIN_SOURCE_ROOT"] = str(root)
            try:
                self.assertEqual(module.find_stegfin_root(), root.resolve())
            finally:
                if prior is None:
                    os.environ.pop("STEGVERSE_STEGFIN_SOURCE_ROOT", None)
                else:
                    os.environ["STEGVERSE_STEGFIN_SOURCE_ROOT"] = prior

    def test_process_adapter_exposes_only_nonsecret_source_locator(self) -> None:
        adapters = json.loads((ROOT / "control" / "process-worker-adapters.json").read_text())
        adapter = next(
            row for row in adapters["adapters"]
            if row["adapter_ref"] == "process:stegfin-live-entry-inventory-v1"
        )
        allowlist = set(adapter["env_allowlist"])
        self.assertIn("STEGVERSE_STEGFIN_SOURCE_ROOT", allowlist)
        self.assertNotIn("GITHUB_TOKEN", allowlist)
        self.assertNotIn("GH_TOKEN", allowlist)
        self.assertNotIn("ZEROEX_API_KEY", allowlist)
        self.assertNotIn("WALLET_PRIVATE_KEY", allowlist)


if __name__ == "__main__":
    unittest.main()
