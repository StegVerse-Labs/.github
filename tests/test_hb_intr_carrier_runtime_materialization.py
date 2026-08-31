from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CARRIER = "heartbeat_runtime/intr_derived_carrier.py"


class HBInTrCarrierRuntimeMaterializationTests(unittest.TestCase):
    def test_bootstrap_requires_canonical_carrier_source(self):
        source = (ROOT / "scripts/bootstrap_sovereign_runtime.py").read_text(encoding="utf-8")
        self.assertIn('Path("heartbeat_runtime/intr_derived_carrier.py")', source)

    def test_installer_requires_materialized_carrier_module(self):
        source = (ROOT / "scripts/install_sovereign_heartbeat_service.py").read_text(encoding="utf-8")
        self.assertIn('target_root / "heartbeat_runtime" / "intr_derived_carrier.py"', source)

    def test_refresh_rejects_source_missing_carrier_module(self):
        source = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
        self.assertIn('source / "heartbeat_runtime/intr_derived_carrier.py"', source)


if __name__ == "__main__":
    unittest.main()
