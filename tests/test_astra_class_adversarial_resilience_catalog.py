from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_astra_catalog",
    ROOT / "scripts/validate_astra_class_adversarial_resilience_catalog.py",
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class AstraResilienceCatalogTests(unittest.TestCase):
    def test_catalog_covers_required_attack_classes_without_authority(self) -> None:
        payload = json.loads((ROOT / "control/astra-class-adversarial-resilience-test-catalog.json").read_text(encoding="utf-8"))
        result = mod.validate(payload)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertEqual(result["test_count"], 6)
        self.assertEqual(set(result["entities"]), {"StegVerse-001", "StegVerse-002", "SV-011"})
        self.assertEqual(set(result["classes"]), mod.REQUIRED_CLASSES)

    def test_authority_escalation_case_proves_denied_consequence(self) -> None:
        payload = json.loads((ROOT / "control/astra-class-adversarial-resilience-test-catalog.json").read_text(encoding="utf-8"))
        case = next(row for row in payload["tests"] if row["class"] == "AUTHORITY_ESCALATION")
        self.assertIn("credential_mint_denied", case["required_assertions"])
        self.assertIn("transition_admission_denied", case["required_assertions"])
        self.assertIn("consequence_reachable_false", case["required_assertions"])
        self.assertFalse(payload["capability_confers_authority"])
        self.assertEqual(payload["credential_authority"], "TV/TVC")


if __name__ == "__main__":
    unittest.main()
