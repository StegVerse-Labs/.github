"""Source-only checks for the open-source strategy census; no rights or release authority."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "ECOSYSTEM-OPEN-SOURCE-STRATEGY-001"


class TestOpenSourceStrategyInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads((ROOT / "data/open-source-repository-licensing-inventory.json").read_text())
        cls.registry = json.loads((ROOT / "data/canonical-task-registry.json").read_text())
        cls.shard = json.loads((ROOT / "data/canonical-task-records" / (TASK_ID + ".json")).read_text())

    def test_full_metadata_census(self):
        c = self.inventory["counts"]
        self.assertEqual(c["repositories"], 119)
        self.assertEqual(c["public"] + c["private"] + c["internal"], 119)
        self.assertEqual(c["license_metadata_checked"], 119)
        self.assertEqual(c["metadata_unchecked"], 0)
        self.assertEqual(c["detected_licenses"] + c["other_unrecognized_license"] + c["no_license_detected"], 119)

    def test_public_inventory_contains_only_public_rows(self):
        rows = self.inventory["repositories"]
        self.assertEqual(len(rows), 46)
        self.assertTrue(all(x["visibility"] == "public" for x in rows))
        self.assertEqual(self.inventory["nonpublic_aggregate"]["metadata_checked"], 73)

    def test_canonical_task_matches_shard_without_release_claim(self):
        rows = [t for t in self.registry["tasks"] if t["task_id"] == TASK_ID]
        self.assertEqual(rows, [self.shard])
        self.assertEqual(self.shard["cosv_task_vector"], "20010010100000")
        self.assertEqual(self.shard["inventory"]["ownership_verified"], 0)
        self.assertEqual(self.shard["source_progress"]["publication"], "NOT_AUTHORIZED")

    def test_review_artifacts_present(self):
        for name in [
            "docs/OPEN_SOURCE_FIRST_WAVE_RIGHTS_AUDIT.md",
            "docs/STEGVERSE_STAGED_OPEN_SOURCE_RELEASE_POLICY_DRAFT.md",
            "docs/ECOSYSTEM_OPEN_SOURCE_STRATEGY_MIRROR_HANDOFF.md",
        ]:
            self.assertTrue((ROOT / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
