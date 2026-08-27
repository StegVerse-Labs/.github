from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK_ID="STEGFIN-EARLY-ADOPTER-VALIDATION-WORKER-001"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"
spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)
class StegFinEarlyAdopterValidationCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/stegfin-early-adopter-contribution-validation-001.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/STEGFIN-EARLY-ADOPTER-VALIDATION-WORKER-001.json").read_text(encoding="utf-8"))
    def test_vector_recomputes(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]),self.record["vector"])
        self.assertEqual(self.record["vector"],"50000000101000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"],len(self.task["admissible_existence"]["blockers"]))
    def test_machine_owned_private_source_boundary(self):
        self.assertEqual(self.task["state"],"HANDOFF_READY")
        self.assertEqual(self.task["worker_id"],"stegfin-early-adopter-contribution-validation-worker")
        self.assertEqual(self.handoff["constraint"]["condition"],"AUTHORIZED_LOCAL_PRIVATE_SOURCE_PATH_NOT_YET_OBSERVED")
        self.assertFalse(self.handoff["constraint"]["human_action_required"])
    def test_no_activation_or_financial_authority_promotion(self):
        m=self.record["exact_metrics"]
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])
        self.assertFalse(m["evidence_complete"]); self.assertFalse(m["activated"]); self.assertFalse(m["propagated"])
        self.assertEqual(self.handoff["authority"]["trade_authority"],"NONE")
        self.assertEqual(self.handoff["authority"]["wallet_authority"],"NONE")
    def test_bindings_authority_neutral(self):
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.task["machine_readable_state"]["cosv"]["authority_effect"],"NONE")
if __name__=="__main__": unittest.main()
