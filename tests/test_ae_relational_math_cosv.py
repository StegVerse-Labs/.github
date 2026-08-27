from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK_ID="AE-RELATIONAL-MATH-WORKER-001"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"
spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)
class AERelationalMathCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/ae-relational-math-worker-001.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/AE-RELATIONAL-MATH-WORKER-001.json").read_text(encoding="utf-8"))
    def test_vector_recomputes(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]),self.record["vector"])
        self.assertEqual(self.record["vector"],"50000000101000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"],len(self.task["admissible_existence"]["blockers"]))
    def test_machine_owned_single_terminal_state_blocker(self):
        self.assertEqual(self.handoff["state"],"HANDOFF_READY_MACHINE_OWNED")
        self.assertFalse(self.handoff["task"]["manual_execution_allowed"])
        self.assertEqual(self.task["admissible_existence"]["blockers"],["AE_AUTO_0011_TERMINAL_VALIDATED_STATE_NOT_YET_OBSERVED"])
    def test_no_activation_or_propagation_promotion(self):
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])
        self.assertFalse(self.record["exact_metrics"]["evidence_complete"])
        self.assertFalse(self.record["exact_metrics"]["activated"])
        self.assertFalse(self.record["exact_metrics"]["propagated"])
        self.assertFalse(self.handoff["authority"]["publication_authority"])
        self.assertFalse(self.handoff["authority"]["release_authority"])
    def test_bindings_authority_neutral(self):
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.task["machine_readable_state"]["cosv"]["authority_effect"],"NONE")
if __name__=="__main__": unittest.main()
