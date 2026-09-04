from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/validate_astra_class_adversarial_resilience_contract.py"
SPEC = importlib.util.spec_from_file_location("astra_class_resilience_validator", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AstraClassAdversarialResilienceContractTests(unittest.TestCase):
    def test_contract_preserves_authority_boundaries_and_entity_roles(self) -> None:
        result = MODULE.validate(ROOT)
        self.assertEqual(result["state"], "PASS")
        self.assertEqual(result["goal_id"], "ASTRA-CLASS-RESILIENCE-001")
        self.assertEqual(result["entity_count"], 3)
        self.assertEqual(result["credential_authority"], "TV/TVC")
        self.assertEqual(result["worker_runtime"], "WorkerCoordinator")
        self.assertFalse(result["runtime_claim"])
        self.assertEqual(result["authority_effect"], "NONE_VALIDATION_ONLY")


if __name__ == "__main__":
    unittest.main()
