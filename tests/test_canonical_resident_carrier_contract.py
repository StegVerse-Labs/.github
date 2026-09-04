from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/validate_canonical_resident_carrier_contract.py"
SPEC = importlib.util.spec_from_file_location("canonical_resident_carrier_validator", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class CanonicalResidentCarrierContractTests(unittest.TestCase):
    def test_contract_and_dispatcher_are_consistent(self) -> None:
        result = MODULE.validate(ROOT)
        self.assertEqual(result["state"], "PASS")
        self.assertEqual(result["consumer_count"], 3)
        self.assertEqual(result["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")
        self.assertEqual(result["worker_runtime"], "WorkerCoordinator")
        self.assertEqual(result["credential_authority"], "TV/TVC")
        self.assertEqual(result["github_token_runtime_authority"], "NONE")


if __name__ == "__main__":
    unittest.main()
