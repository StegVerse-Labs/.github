"""Source-only canonical registration and COSV proof for existing StegOS AI participants.

Does not attest authenticated AI session origin, WorkerCoordinator claim, InTr
ALLOW, real provider execution, or Master Records reconstruction.
"""
from __future__ import annotations
import json
import unittest
from pathlib import Path

from scripts.cosv import encode_task, validate_record
from scripts.validate_task_registration_substrate_resolution import validate_resolution

ROOT=Path(__file__).resolve().parents[1]
FIRST="STEGOS-LOCAL-AI-ENTITY-CHATGPT-001"
SECOND="STEGOS-LOCAL-AI-ENTITY-CLAUDE-CODE-001"
PARENT="ECOSYSTEM-ECONOMIC-WHITEPAPER-GATED-ROADMAP-001"

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

class RegisteredLocalAIParticipants(unittest.TestCase):
    def test_first_then_second_source_registration_and_dependency(self):
        registry=load("data/canonical-task-registry.json")
        rows=registry["tasks"]
        first_rows=[(i,r) for i,r in enumerate(rows) if r["task_id"]==FIRST]
        second_rows=[(i,r) for i,r in enumerate(rows) if r["task_id"]==SECOND]
        self.assertEqual(len(first_rows),1)
        self.assertEqual(len(second_rows),1)
        self.assertLess(first_rows[0][0],second_rows[0][0])
        first=first_rows[0][1]
        second=second_rows[0][1]
        self.assertEqual(first["parent_task_id"],PARENT)
        self.assertEqual(second["parent_task_id"],FIRST)
        self.assertEqual(first["root_correlation_id"],PARENT)
        self.assertEqual(second["root_correlation_id"],PARENT)
        self.assertTrue(any(d["ref"]==FIRST and d["state"]=="UNRESOLVED" for d in second["dependencies"]))
        self.assertEqual(first["registration"]["benchmark_id"],"S1_CHATGPT")
        self.assertEqual(second["registration"]["benchmark_id"],"S1_CLAUDE")
        for row in (first,second):
            shard=load("data/canonical-task-records/"+row["task_id"]+".json")
            self.assertEqual(row,shard)
            self.assertEqual(row["coordination_state"],"PROPOSED")
            self.assertEqual(row["checkout_state"],"UNCLAIMED")
            self.assertIsNone(row["worker_claim"]["claim_ref"])
            self.assertIsNone(row["worker_claim"]["fence_ref"])
            self.assertFalse(row["completion"]["claimed"])
            self.assertFalse(row["completion"]["validated"])
            self.assertFalse(row["registration"]["source_registration_grants_execution_authority"])
            self.assertEqual(row["registration"]["benchmark_status"],"NOT_VERIFIED")
            self.assertEqual(row["registration"]["ecc_status"],"DEFERRED_UNTIL_AUTHENTIC_EXECUTION")
            validate_resolution(row)

    def test_vectors_derived_from_actual_source_counts_and_index_consistent(self):
        index=load("control/task-vector-index.json")
        self.assertEqual(len({r["task_id"] for r in index["tasks"]}),len(index["tasks"]))
        for task_id,expected_count in ((FIRST,2),(SECOND,3)):
            shard=load("data/canonical-task-records/"+task_id+".json")
            v=load("control/task-vectors/"+task_id+".json")
            fragment=load("control/task-vector-index.d/"+task_id+".json")
            index_rows=[r for r in index["tasks"] if r["task_id"]==task_id]
            self.assertEqual(len(index_rows),1)
            self.assertTrue(validate_record(v))
            self.assertEqual(v["exact_metrics"]["blocker_count"],len(shard["blockers"]))
            self.assertEqual(v["exact_metrics"]["blocker_count"],expected_count)
            self.assertEqual(v["vector"],encode_task(v["exact_metrics"]))
            self.assertEqual(shard["cosv_task_vector"],v["vector"])
            self.assertEqual(index_rows[0],fragment)
            self.assertEqual(fragment["vector"],v["vector"])
            self.assertEqual(fragment["source_state_vector_ref"],"control/task-vectors/"+task_id+".json")
            self.assertFalse(v["exact_metrics"]["evidence_complete"])
            self.assertFalse(v["exact_metrics"]["activated"])
            self.assertFalse(v["exact_metrics"]["propagated"])
            self.assertEqual(v["authority_effect"],"NONE")

if __name__=="__main__":
    unittest.main()
