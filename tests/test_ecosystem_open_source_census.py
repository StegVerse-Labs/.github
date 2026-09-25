"""Source-only invariants for the organization-scoped open-source census."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOAL = "ECOSYSTEM-OPEN-SOURCE-STRATEGY-001"

class TestEcosystemOpenSourceCensus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eco = json.loads((ROOT / "data/ecosystem-open-source-organization-census-20260925.json").read_text())
        cls.labs = json.loads((ROOT / "data/open-source-repository-licensing-inventory.json").read_text())
        cls.reg = json.loads((ROOT / "data/canonical-task-registry.json").read_text())
        cls.shard = json.loads((ROOT / "data/canonical-task-records" / (GOAL + ".json")).read_text())
    
    def test_organization_counts(self):
        rows = self.eco["organizations"]
        self.assertEqual(len(rows), 14)
        self.assertEqual(sum(r["visible_repositories"] for r in rows), 252)
        for field in ["public_count", "private_count", "internal_count"]:
            self.assertEqual(sum(r[field] for r in rows), self.eco["counts"][field.split("_")[0]])
        for row in rows:
            self.assertEqual(row["visible_repositories"], row["public_count"]+row["private_count"]+row["internal_count"])
    
    def test_labs_scope_unchanged(self):
        self.assertEqual(self.labs["counts"]["repositories"], 119)
        self.assertEqual(self.labs["counts"]["license_metadata_checked"], 119)
        labs = next(r for r in self.eco["organizations"] if r["organization"] == "StegVerse-Labs")
        self.assertEqual(labs["visible_repositories"], 119)
        self.assertEqual(labs["license_metadata_coverage"], "119/119")
    
    def test_one_additional_organization_audited(self):
        org = next(r for r in self.eco["organizations"] if r["organization"] == "StegVerse-org")
        self.assertEqual(org["license_metadata_coverage"], "18/18")
        self.assertEqual(sum(r["license_metadata_coverage"] == "NOT_AUDITED" for r in self.eco["organizations"]), 12)
        self.assertFalse(self.eco["historical_universe_audit_complete"])
    
    def test_registry_source_only(self):
        self.assertEqual([x for x in self.reg["tasks"] if x["task_id"] == GOAL], [self.shard])
        self.assertEqual(self.shard["cosv_task_vector"], "20010010100000")
        self.assertFalse(self.shard["ecosystem_inventory"]["release_authorized"])
        self.assertEqual(self.shard["coordination_state"], "ACTIVE")

if __name__ == "__main__":
    unittest.main()
