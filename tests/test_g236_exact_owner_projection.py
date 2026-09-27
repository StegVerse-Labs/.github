"""Exact g236 observed-owner source projection, non-authorizing regression."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER_IDS = [
  "ERL-SPURLOCK-CPD-ENTRY-001",
  "FEDERAL-HEALTH-PII-EXCEEDANCE-HARDENING-001",
  "GP10-COMMERCIAL-RESPONSE-VALIDATION-001",
  "MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001",
  "MIR-TVC-PROVIDER-ROUNDTRIP-001",
  "PAYMENT-PROVIDER-AUTHENTIC-INGRESS-001",
  "SS-KV-SKAP-SOCIAL-RELEASE-001",
  "STEG-BROWSER-CURRENT-IPHONE-A1-A4-EXECUTION-001",
  "STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001",
  "STEG-BROWSER-RESIDENT-RECEIPT-TRANSPORT-001",
  "STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001",
  "STEGOS-AI-PREEXECUTION-RUNTIME-PROOF-001",
  "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001",
  "STEGOS-NODE-MANIFOLD-001",
  "STEGVERSE-TASK-REGISTRY-HEALTH-MONITOR-001",
  "TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001",
  "TVC-IOS-OPAQUE-RECIPIENT-CAPABILITY-001",
  "TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001",
  "TVC-RECIPIENT-ADMISSION-SIGNING-CUSTODY-001"
]

class ExactOwnerProjectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "data/canonical-task-registry.json").read_text())
        cls.rows = cls.registry["tasks"]
        cls.by_id = {t["task_id"]: t for t in cls.rows}
        cls.index = json.loads((ROOT / "control/task-vector-index.json").read_text())
        cls.indexed = {r["task_id"]: r.get("vector") for r in cls.index["tasks"]}

    def test_current_projection_contains_exactly_one_of_each_original_owner(self):
        self.assertEqual(len(self.rows), len(self.by_id))
        for task_id in OWNER_IDS:
            with self.subTest(task_id=task_id):
                self.assertIn(task_id, self.by_id)
                shard = json.loads((ROOT / "data/canonical-task-records" / (task_id + ".json")).read_text())
                self.assertEqual(self.by_id[task_id], shard)
                self.assertEqual((shard["coordination_state"], shard["checkout_state"]), ("ACTIVE", "CHECKED_OUT"))
                vector = shard.get("cosv_task_vector")
                if vector and task_id in self.indexed:
                    self.assertEqual(vector, self.indexed[task_id])

    def test_ai_source_cycle_exact_native_completed_shard(self):
        task_id = "AI-GOVERNANCE-OPPORTUNITY-ENGINE-001"
        shard = json.loads((ROOT / "data/canonical-task-records" / (task_id + ".json")).read_text())
        self.assertEqual(self.by_id[task_id], shard)
        self.assertEqual((shard["coordination_state"], shard["checkout_state"]), ("RETIRED", "COMPLETED"))
        self.assertTrue(shard["completion"]["claimed"] and shard["completion"]["validated"])
        self.assertEqual(shard["completion"]["reconciliation_ref"], "StegVerse-Labs/StegBusiness-Ops@0f22edcf245ca4ef94921afebb3c173e0b037b4a")
        self.assertFalse(shard["authority_model"]["outreach_authority"])
        self.assertEqual(shard["goal_prompt_count"], "20/20")

    def test_no_projection_mints_cosv_or_runtime_authority(self):
        self.assertTrue(self.registry["generation"] >= 238)
        for task_id in OWNER_IDS:
            shard = self.by_id[task_id]
            self.assertEqual(shard.get("authority_model", {}).get("task_registry_mints_execution_authority", False), False)
            self.assertNotIn("PROJECTION_ASSIGNED", shard.get("cosv_task_vector") or "")

if __name__ == "__main__":
    unittest.main()
