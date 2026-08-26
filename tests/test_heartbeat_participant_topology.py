import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HeartbeatParticipantTopologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.body = json.loads((ROOT / "control" / "heartbeat-participant-topology.json").read_text(encoding="utf-8"))

    def test_canonical_heartbeat_contract(self):
        hb = self.body["heartbeat"]
        self.assertEqual(hb["anchor_epoch"], 32)
        self.assertEqual(hb["anchor_heartbeat_id"], "HB-0000000W")
        self.assertEqual(hb["display_format"], "HB-XXXXXXXX")
        self.assertEqual(hb["encoding"], "FIXED_WIDTH_BASE36")
        self.assertEqual(hb["period_ms"], 10)
        self.assertEqual(hb["rate_hz"], 100)
        self.assertEqual(hb["progression_dependency"], "OSCILLATOR_ONLY")
        self.assertFalse(hb["observation_is_causal"])
        self.assertEqual(hb["authority_effect"], "NONE")

    def test_known_denominators_are_fully_registered(self):
        self.assertEqual(len(self.body["organizations"]), 14)
        self.assertEqual(len(self.body["critical_repositories"]), 11)
        self.assertEqual(len(self.body["connected_drive_resources"]), 4)
        coverage = self.body["coverage"]
        self.assertEqual(coverage["organizations_registered"], 14)
        self.assertEqual(coverage["critical_repositories_registered"], 11)
        self.assertEqual(coverage["connected_drive_resources_registered"], 4)
        self.assertEqual(coverage["unrepresented_known_participants"], 0)

    def test_awareness_is_reciprocal_but_non_authorizing(self):
        contract = self.body["reciprocal_awareness_contract"]
        self.assertTrue(contract["heartbeat_knows_participants"])
        self.assertTrue(contract["participants_know_heartbeat"])
        self.assertTrue(contract["participant_presence_is_topology_metadata_only"])
        for key, value in contract.items():
            if key.startswith("heartbeat_grants_"):
                self.assertFalse(value, key)
        self.assertFalse(self.body["drive_progression_authority"])
        self.assertFalse(self.body["repository_progression_authority"])
        self.assertFalse(self.body["organization_progression_authority"])

    def test_drive_resource_ids_are_unique_and_explicit(self):
        ids = [row["id"] for row in self.body["connected_drive_resources"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("14JzFbQelopGDkOEvQOz8vjHb1VNVW6to", ids)
        self.assertIn("1coBvj8JsumtC3TfVlowXTscqAPBqdq6opuF7MXthMos", ids)


if __name__ == "__main__":
    unittest.main()
