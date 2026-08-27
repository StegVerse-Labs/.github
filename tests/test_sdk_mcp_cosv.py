from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TASK_ID="SDK-MCP-CANONICAL-VALIDATION-009"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"
spec=importlib.util.spec_from_file_location("cosv", ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)

class SDKMCPCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/sdk-mcp-canonical-validation-009.json").read_text(encoding="utf-8"))
        self.task=next(x for x in fragment["tasks"] if x["task_id"]==TASK_ID)
        self.handoff=json.loads((ROOT/"handoffs/SDK-MCP-CANONICAL-VALIDATION-009.json").read_text(encoding="utf-8"))

    def test_vector_recomputes(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]), self.record["vector"])
        self.assertEqual(self.record["vector"], "50000000101000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"], len(self.task["admissible_existence"]["blockers"]))

    def test_machine_owned_no_manual_claim(self):
        self.assertEqual(self.handoff["state"], "HANDOFF_READY_MACHINE_OWNED")
        self.assertFalse(self.handoff["task"]["manual_execution_allowed"])
        self.assertEqual(self.record["exact_metrics"]["lifecycle"], "MACHINE_OWNED")
        self.assertFalse(self.record["exact_metrics"]["thread_required"])

    def test_no_activation_promotion(self):
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])
        self.assertFalse(self.record["exact_metrics"]["evidence_complete"])
        self.assertFalse(self.record["exact_metrics"]["activated"])
        self.assertFalse(self.record["exact_metrics"]["propagated"])

    def test_bindings_match(self):
        self.assertEqual(self.task["source_state_vector_ref"], VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"], VECTOR_REF)
        self.assertEqual(self.task["machine_readable_state"]["cosv"]["authority_effect"], "NONE")

if __name__=="__main__": unittest.main()
