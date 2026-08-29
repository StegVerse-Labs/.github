from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TASK_ID="SHWP-COHERENT-SIGNAL-FORMAL-CANDIDATE-001"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"

spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)

class CoherentSignalFormalCandidateCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/coherent-signal-formal-candidate-001.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/SHWP-COHERENT-SIGNAL-FORMAL-CANDIDATE-001.json").read_text(encoding="utf-8"))

    def test_vector_recomputes(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]),self.record["vector"])
        self.assertEqual(self.record["vector"],"50000000101000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"],len(self.task["admissible_existence"]["blockers"]))

    def test_single_candidate_emission_blocker_and_worker_ownership(self):
        self.assertEqual(self.task["admissible_existence"]["blockers"],["FORMAL_MATHEMATICAL_CANDIDATE_NOT_YET_EMITTED"])
        self.assertEqual(self.handoff["state"],"HANDOFF_READY")
        self.assertFalse(self.handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(self.handoff["authority"]["github_token_required"])
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)

    def test_candidate_does_not_promote_formal_or_runtime_authority(self):
        m=self.record["exact_metrics"]
        self.assertFalse(m["evidence_complete"])
        self.assertFalse(m["activated"])
        self.assertFalse(m["propagated"])
        self.assertIn("no_formalism_authority",self.handoff["goal"]["authority_ceiling"])
        self.assertIn("no_execution_authority",self.handoff["goal"]["authority_ceiling"])
        self.assertIn("Operator-family hypothesis is promoted to theorem without evidence",self.handoff["goal"]["failure_predicates"])
        self.assertIn("Frequency/phase coordinates are declared complete without evidence",self.handoff["goal"]["failure_predicates"])
        self.assertEqual(self.record["authority_effect"],"NONE")

if __name__=="__main__": unittest.main()
