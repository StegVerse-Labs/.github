from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_quantum_wallet_signature_census",
    ROOT / "scripts" / "validate_quantum_wallet_signature_census.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class QuantumWalletSignatureCensusTests(unittest.TestCase):
    def test_user_only_authority_and_unknown_signer_algorithm_are_preserved(self) -> None:
        result = mod.validate()
        self.assertEqual(result["status"], "PASS_QUANTUM_WALLET_SIGNATURE_CENSUS")
        self.assertEqual(result["surface_count"], 2)
        self.assertEqual(result["wallet_signing_authority"], "USER_ONLY")
        self.assertEqual(result["wallet_broadcast_authority"], "USER_ONLY")
        self.assertFalse(result["quantum_safe_claim"])
        self.assertFalse(result["pqc_deployment_claim"])
        self.assertEqual(result["authority_effect"], "NONE_CENSUS_ONLY")


if __name__ == "__main__":
    unittest.main()
