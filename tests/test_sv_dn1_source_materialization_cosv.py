from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK_ID="SV-DN1-SOURCE-MATERIALIZATION-001"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"
spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)
class SVDN1SourceMaterializationCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/sv-dn1-source-materialization-001.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/SV-DN1-SOURCE-MATERIALIZATION-001.json").read_text(encoding="utf-8"))
    def test_vector_recomputes(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]),self.record["vector"])
        self.assertEqual(self.record["vector"],"50000000101000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"],len(self.task["admissible_existence"]["blockers"]))
    def test_single_materialization_receipt_blocker(self):
        self.assertEqual(self.task["admissible_existence"]["blockers"],["SOVEREIGN_SOURCE_MATERIALIZATION_RECEIPT_NOT_YET_OBSERVED"])
        self.assertEqual(self.handoff["state"],"HANDOFF_READY_MACHINE_OWNED")
        self.assertFalse(self.handoff["task"]["manual_execution_allowed"])
    def test_no_authority_or_activation_promotion(self):
        m=self.record["exact_metrics"]
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])
        self.assertFalse(m["evidence_complete"]); self.assertFalse(m["activated"]); self.assertFalse(m["propagated"])
        self.assertFalse(self.handoff["execution"]["remote_checkout_allowed"])
        self.assertFalse(self.handoff["authority"]["github_token_required"])
        self.assertFalse(self.handoff["authority"]["provider_credential_authority"])
        self.assertFalse(self.handoff["authority"]["observation_authority"])
        self.assertFalse(self.handoff["authority"]["sdk_admission_authority"])
        self.assertFalse(self.handoff["authority"]["publication_authority"])
    def test_bindings_authority_neutral(self):
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.task["machine_readable_state"]["cosv"]["authority_effect"],"NONE")
if __name__=="__main__": unittest.main()
