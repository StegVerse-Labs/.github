from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_quantum_resilience_contract",
    ROOT / "scripts" / "validate_quantum_resilience_contract.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class QuantumResilienceContractTests(unittest.TestCase):
    def test_contract_and_census_fail_closed_on_unknowns(self) -> None:
        result = mod.validate()
        self.assertEqual(result["status"], "PASS_QUANTUM_RESILIENCE_SOURCE_CONTRACT")
        self.assertEqual(result["goal_id"], "QUANTUM-RESILIENCE-001")
        self.assertEqual(result["known_classical_only_count"], 3)
        self.assertEqual(result["hybrid_migration_required_count"], 2)
        self.assertEqual(result["known_quantum_exposure_count"], 5)
        self.assertEqual(result["pqc_validated_surface_count"], 0)
        self.assertGreaterEqual(len(result["unresolved_critical"]), 1)
        self.assertEqual(result["credential_authority"], "TV/TVC")
        self.assertFalse(result["runtime_claim"])
        self.assertFalse(result["deployment_claim"])
        self.assertEqual(result["authority_effect"], "NONE_VALIDATION_ONLY")


if __name__ == "__main__":
    unittest.main()
