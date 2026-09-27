import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("component010_checkout_audit", ROOT / "scripts" / "audit_component010_checkout.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Component010CheckoutAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "data/canonical-task-registry.json").read_text())
        cls.shard = json.loads((ROOT / "data/canonical-task-records" / (MODULE.TASK_ID + ".json")).read_text())

    def test_current_source_checkout_requires_real_claim(self):
        result = MODULE.audit(self.registry, self.shard)
        self.assertEqual(result["source_projection_disposition"], "FAIL_CLOSED_STALE_CHECKOUT_EVIDENCE")
        self.assertFalse(result["claim_authentically_verified"])
        self.assertFalse(result["runtime_transition_observed"])
        self.assertFalse(result["canonical_registry_mutated"])

    def test_pointer_is_not_authentic_runtime_proof(self):
        registry = copy.deepcopy(self.registry)
        shard = copy.deepcopy(self.shard)
        for row in registry["tasks"]:
            if row.get("task_id") == MODULE.TASK_ID:
                row["worker_claim"] = {"receipt_ref": "private://unverified", "fence": "unverified"}
        shard["worker_claim"] = {"receipt_ref": "private://unverified", "fence": "unverified"}
        result = MODULE.audit(registry, shard)
        self.assertEqual(result["source_projection_disposition"], "REQUIRES_AUTHENTIC_CLAIM_READBACK")
        self.assertFalse(result["claim_authentically_verified"])

    def test_unclaimed_is_not_a_completed_task(self):
        registry = copy.deepcopy(self.registry)
        shard = copy.deepcopy(self.shard)
        for row in registry["tasks"]:
            if row.get("task_id") == MODULE.TASK_ID:
                row["checkout_state"] = "UNCLAIMED"
        shard["checkout_state"] = "UNCLAIMED"
        result = MODULE.audit(registry, shard)
        self.assertEqual(result["source_projection_disposition"], "NO_ACTIVE_CHECKOUT")
        self.assertFalse(result["runtime_transition_observed"])

    def test_aggregate_shard_disagreement_fails_closed(self):
        shard = copy.deepcopy(self.shard)
        shard["checkout_state"] = "UNCLAIMED"
        with self.assertRaisesRegex(ValueError, "SHARD_AGGREGATE_MISMATCH"):
            MODULE.audit(self.registry, shard)


if __name__ == "__main__":
    unittest.main()
