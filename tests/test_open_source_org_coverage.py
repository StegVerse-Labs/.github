"""Bounded source-only organization audit census and task-shard parity."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK="ECOSYSTEM-OPEN-SOURCE-STRATEGY-001"
class TestOrganizationSourceCoverage(unittest.TestCase):
    def test_merged_coverage_and_rights_boundary(self):
        c=json.loads((ROOT/"data/ecosystem-open-source-organization-census-20260925.json").read_text())
        r=json.loads((ROOT/"data/canonical-task-registry.json").read_text())
        s=json.loads((ROOT/"data/canonical-task-records"/(TASK+".json")).read_text())
        self.assertEqual(c["counts"]["metadata_audited_repositories"],168)
        self.assertEqual(c["counts"]["metadata_audited_organizations"],6)
        self.assertEqual(c["counts"]["other_organizations_visibility_only"],8)
        self.assertEqual(c["counts"]["repository_entries"],252)
        self.assertEqual(sum(o["visible_repositories"] for o in c["organizations"] if o["license_metadata_coverage"]!="NOT_AUDITED"),168)
        self.assertEqual(r["tasks"][[t["task_id"] for t in r["tasks"]].index(TASK)],s)
        self.assertEqual(s["ecosystem_inventory"]["metadata_checked_entries"],168)
        self.assertEqual(s["coordination_state"],"ACTIVE")
        self.assertFalse(s["completion"]["validated"])
        self.assertFalse(s["ecosystem_inventory"]["release_authorized"])
        for o in c["organizations"]:
            self.assertFalse("repositories" in o, "central census must not expose source-owner repo names")
if __name__=="__main__":unittest.main()
