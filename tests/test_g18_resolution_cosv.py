from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK_ID="RESOLVE-G18-RESIDENT-REQUEST-CONSUMPTION-001"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"
spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)
class G18ResolutionCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/g18-resident-request-consumption-resolution-001.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/RESOLVE-G18-RESIDENT-REQUEST-CONSUMPTION-001.json").read_text(encoding="utf-8"))
    def test_vector_recomputes(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]),self.record["vector"])
        self.assertEqual(self.record["vector"],"50000000101000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"],len(self.task["admissible_existence"]["blockers"]))
    def test_single_resolution_blocker(self):
        self.assertEqual(self.task["admissible_existence"]["blockers"],["G18_RESIDENT_REQUEST_CONSUMPTION_NOT_YET_OBSERVED"])
        self.assertTrue(self.handoff["authority"]["fresh_fence_required"])
        self.assertFalse(self.handoff["authority"]["new_g18_claim_allowed"])
        self.assertFalse(self.task["admission"]["parent_claim_reuse_prohibited"] is False)
    def test_no_runtime_or_authority_promotion(self):
        m=self.record["exact_metrics"]
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])
        self.assertFalse(m["evidence_complete"]); self.assertFalse(m["activated"]); self.assertFalse(m["propagated"])
        self.assertFalse(self.handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(self.handoff["authority"]["third_party_runtime_required"])
        self.assertFalse(self.handoff["authority"]["physical_additional_machine_required"])
        self.assertFalse(self.handoff["completion"]["runtime_activation_claimed"])
        self.assertFalse(self.handoff["completion"]["g18_terminalization_claimed"])
    def test_dispatcher_source_does_not_satisfy_consumption(self):
        self.assertTrue((ROOT/"scripts/dispatch_resident_execution_requests.py").is_file())
        self.assertTrue((ROOT/"scripts/bootstrap_sovereign_runtime.py").is_file())
        self.assertEqual(self.task["admissible_existence"]["blockers"],["G18_RESIDENT_REQUEST_CONSUMPTION_NOT_YET_OBSERVED"])
        self.assertFalse(self.record["exact_metrics"]["evidence_complete"])
        self.assertFalse(self.record["exact_metrics"]["activated"])

    def test_bindings_authority_neutral(self):
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.task["machine_readable_state"]["cosv"]["authority_effect"],"NONE")
if __name__=="__main__": unittest.main()
