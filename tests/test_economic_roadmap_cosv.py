from __future__ import annotations
import json
import unittest
from pathlib import Path
from scripts.cosv import encode_task,validate_record
ROOT=Path(__file__).resolve().parents[1]
TASK_ID="ECOSYSTEM-ECONOMIC-WHITEPAPER-GATED-ROADMAP-001"
def load(p):return json.loads((ROOT/p).read_text(encoding="utf-8"))
class EconomicRoadmapCosvTests(unittest.TestCase):
    def test_canonical_task_and_observational_vector_agree(self):
        registry=load("data/canonical-task-registry.json")
        matches=[x for x in registry["tasks"] if x["task_id"]==TASK_ID]
        self.assertEqual(len(matches),1)
        task=matches[0]
        self.assertEqual(task["coordination_state"],"PROPOSED")
        self.assertIsNone(task["worker_claim"]["claim_ref"])
        self.assertIsNone(task["worker_claim"]["fence_ref"])
        self.assertFalse(task["completion"]["validated"])
        record=load("control/task-vectors/"+TASK_ID+".json")
        self.assertTrue(validate_record(record))
        self.assertEqual(record["exact_metrics"]["symbol_order"],"LRUIVGOCMTBEAP")
        self.assertEqual(record["exact_metrics"]["blocker_count"],len(task["blockers"]))
        self.assertEqual(len(task["blockers"]),4)
        self.assertEqual(next(x for x in task["dependencies"] if x["dependency_id"]=="CANONICAL_COSV_EMISSION")["state"],"RESOLVED")
        self.assertNotIn("COSV_NOT_EMITTED",[x["blocker_id"] for x in task["blockers"]])
        self.assertEqual(record["vector"],encode_task(record["exact_metrics"]))
        self.assertEqual(record["vector"],"10100000104000")
        self.assertFalse(record["exact_metrics"]["evidence_complete"])
        self.assertFalse(record["exact_metrics"]["activated"])
        self.assertFalse(record["exact_metrics"]["propagated"])
        self.assertEqual(record["authority_effect"],"NONE")
    def test_aggregate_and_fragment_index_are_consistent(self):
        idx=load("control/task-vector-index.json")
        rows=[x for x in idx["tasks"] if x["task_id"]==TASK_ID]
        self.assertEqual(len(rows),1)
        shard=load("control/task-vector-index.d/"+TASK_ID+".json")
        for key in ("source_state_vector_ref","vector","vector_state","authority_effect"):
            self.assertEqual(rows[0][key],shard[key])
        self.assertEqual(idx["coverage"]["indexed_vectorized_tasks"],len(idx["tasks"]))
        self.assertEqual(idx["coverage"]["local_cosv_record_tasks"]+idx["coverage"]["external_owner_projection_tasks"],len(idx["tasks"]))
        self.assertEqual(shard["registry_ref"],"data/canonical-task-records/"+TASK_ID+".json")
if __name__=="__main__":unittest.main()
