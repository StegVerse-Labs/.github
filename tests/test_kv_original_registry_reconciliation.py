"""Non-authorizing regression for restoration of the EXISTING KV Goal identity."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
TASK="KV-CONNECTION-REVALIDATION-WORKER-001"

class KVExistingGoalRegistryTests(unittest.TestCase):
    def test_exact_single_original_goal_and_shard(self):
        registry=json.loads((ROOT/"data/canonical-task-registry.json").read_text())
        rows=[x for x in registry["tasks"] if x["task_id"]==TASK]
        self.assertEqual(len(rows),1)
        row=rows[0]
        shard=json.loads((ROOT/"data/canonical-task-records"/f"{TASK}.json").read_text())
        self.assertEqual(row,shard)
        self.assertEqual(row["root_correlation_id"],TASK)
        self.assertEqual(row["cosv_task_vector"],"50000000102000")
        self.assertEqual(row["coordination_state"],"PROPOSED")
        self.assertTrue(row["registration"]["existing_goal_not_new_goal"])
        self.assertTrue(row["registration"]["source_pr_only"])

    def test_original_owner_and_no_authority_promotion(self):
        row=json.loads((ROOT/"data/canonical-task-records"/f"{TASK}.json").read_text())
        handoff=json.loads((ROOT/"handoffs"/f"{TASK}.json").read_text())
        vector=json.loads((ROOT/"control/task-vectors"/f"{TASK}.json").read_text())
        self.assertEqual(handoff["task"]["task_id"],TASK)
        self.assertEqual(vector["vector"],row["cosv_task_vector"])
        self.assertIn("continuity-vault-kit#119",handoff["task"]["canonical_owner_ref"])
        self.assertTrue(row["worker_claim"]["projection_only"])
        self.assertFalse(row["completion"]["claimed"])
        self.assertFalse(row["completion"]["provider_connect_verified"])
        self.assertFalse(row["completion"]["kv2_materialized"])
        self.assertEqual(row["authority_model"]["healer_role"],"OPTIONAL_CARRIER_NOT_KV_COMPLETION")
        self.assertTrue(row["registration"]["post_merge_authentic_gate_required"])

if __name__=="__main__":
    unittest.main()
