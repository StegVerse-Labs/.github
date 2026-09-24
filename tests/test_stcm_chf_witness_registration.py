"""Source-registration contract only; not an authenticated task check-in or physical witness."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "STCM-CHF-THERMODYNAMIC-WITNESS-COMPARISON-001"
VECTOR = "10111010112000"

class TestStcmChfWitnessRegistration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "data/canonical-task-registry.json").read_text())
        cls.shard = json.loads((ROOT / "data/canonical-task-records" / (TASK_ID + ".json")).read_text())
        cls.index = json.loads((ROOT / "control/task-vector-index.json").read_text())
        cls.vector = json.loads((ROOT / "control/task-vectors" / (TASK_ID + ".json")).read_text())

    def test_unique_canonical_registration(self):
        rows = [t for t in self.registry["tasks"] if t["task_id"] == TASK_ID]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], self.shard)
        self.assertGreaterEqual(self.registry["generation"], 211)

    def test_cosv_exact_pointer_and_width(self):
        rows = [r for r in self.index["tasks"] if r["task_id"] == TASK_ID]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["vector"], VECTOR)
        self.assertEqual(self.shard["cosv_task_vector"], VECTOR)
        self.assertEqual(self.vector["vector"], VECTOR)
        self.assertEqual(self.vector["profile"], "task.v1")
        self.assertEqual(len(VECTOR), 14)

    def test_independent_native_ownership(self):
        paths = set(self.shard["source_refs"])
        self.assertIn("Admissible-Existence/STCM/STCM_MIRROR_HANDOFF.md", paths)
        self.assertIn("Admissible-Existence/CHF/docs/CHF_MIRROR_HANDOFF.md", paths)
        deps = {d["dependency_id"]: d for d in self.shard["dependencies"]}
        self.assertEqual(deps["STCM_NATIVE_SEMANTICS"]["state"], "NOT_CLAIMED")
        self.assertEqual(deps["CHF_NATIVE_SEMANTICS"]["state"], "NOT_CLAIMED")

    def test_registration_has_no_execution_authority(self):
        self.assertEqual(self.shard["checkout_state"], "UNCLAIMED")
        self.assertIsNone(self.shard["worker_claim"]["claim_ref"])
        self.assertIsNone(self.shard["worker_claim"]["fence_ref"])
        self.assertFalse(self.shard["completion"]["validated"])
        self.assertFalse(self.shard["authority_model"]["task_registry_mints_execution_authority"])
        self.assertFalse(self.shard["authority_model"]["synthetic_fixtures_prove_physical_measurement"])

    def test_target_scope_and_handoff(self):
        self.assertEqual(self.shard["targets"]["repositories"], ["Admissible-Existence/.github"])
        self.assertEqual(set(self.shard["targets"]["components"]), {
            "inert-common-specimen-schema", "independent-witness-comparison-fixtures",
            "negative-control-comparison-validator",
        })
        handoff = ROOT / "docs/STCM_CHF_THERMODYNAMIC_WITNESS_REGISTRATION_MIRROR_HANDOFF.md"
        self.assertTrue(handoff.is_file())
        self.assertIn(TASK_ID, handoff.read_text())
        self.assertIn(TASK_ID, (ROOT / "README.md").read_text())

if __name__ == "__main__":
    unittest.main()
