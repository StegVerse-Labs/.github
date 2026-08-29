from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK_ID="SHWP-ARA-GRAPH-RUNTIME-086"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"
spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)
class ARAGraphRuntimeCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/ara-graph-runtime-086.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/SHWP-ARA-GRAPH-RUNTIME-086.json").read_text(encoding="utf-8"))
    def test_vector_recomputes(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]),self.record["vector"])
        self.assertEqual(self.record["vector"],"50000000101000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"],len(self.task["admissible_existence"]["blockers"]))
    def test_single_provider_operation_receipt_blocker(self):
        self.assertEqual(self.task["admissible_existence"]["blockers"],["LIVE_ARA_GRAPH_PROVIDER_OPERATION_RECEIPT_NOT_YET_OBSERVED"])
        self.assertFalse(self.handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(self.handoff["activation"]["heartbeat_dependency"])
        self.assertFalse(self.handoff["activation"]["carrier_trigger_required"])
    def test_no_runtime_or_provider_promotion(self):
        m=self.record["exact_metrics"]
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])
        self.assertFalse(m["evidence_complete"]); self.assertFalse(m["activated"]); self.assertFalse(m["propagated"])
        self.assertEqual(self.handoff["authority"]["credential_authority"],"TV/TVC")
        self.assertFalse(self.handoff["authority"]["github_token_required"])
    def test_bindings_authority_neutral(self):
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.task["machine_readable_state"]["cosv"]["authority_effect"],"NONE")
if __name__=="__main__": unittest.main()
