from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_quantum_tls_confidentiality_census",
    ROOT / "scripts" / "validate_quantum_tls_confidentiality_census.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class QuantumTlsConfidentialityCensusTests(unittest.TestCase):
    def test_partial_tls_census_preserves_unknowns_and_authority_boundary(self) -> None:
        result = mod.validate()
        self.assertEqual(result["status"], "PASS_QUANTUM_TLS_CONFIDENTIALITY_CENSUS")
        self.assertEqual(result["goal_id"], "QUANTUM-RESILIENCE-001")
        self.assertEqual(result["surface_count"], 2)
        self.assertFalse(result["quantum_safe_claim"])
        self.assertFalse(result["pqc_deployment_claim"])
        self.assertEqual(result["authority_effect"], "NONE_CENSUS_ONLY")


if __name__ == "__main__":
    unittest.main()
