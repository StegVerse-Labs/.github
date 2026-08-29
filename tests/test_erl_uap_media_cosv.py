from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK_ID="SHWP-ERL-UAP-MEDIA-001"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"
spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)

class ERLUAPMediaCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/erl-uap-media-001.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/SHWP-ERL-UAP-MEDIA-001.json").read_text(encoding="utf-8"))

    def test_vector_recomputes_from_single_blocker(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]),self.record["vector"])
        self.assertEqual(self.record["vector"],"50000000101000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"],1)
        self.assertEqual(self.task["admissible_existence"]["blockers"],self.handoff["admissible_existence"]["blockers"])

    def test_public_source_worker_is_credential_free_and_non_authorizing(self):
        self.assertEqual(self.task["admissible_existence"]["blockers"],["LOCAL_ERL_SOURCE_AND_PUBLIC_ENDPOINT_OBSERVATION_PENDING"])
        self.assertFalse(self.handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(self.handoff["authority"]["github_token_required"])
        self.assertEqual(self.handoff["authority"]["credential_requirement"],"NONE")
        self.assertFalse(self.handoff["authority"]["research_promotion_authority"])
        self.assertFalse(self.handoff["authority"]["publication_authority"])
        self.assertFalse(self.handoff["authority"]["wallet_signing_authority"])
        self.assertFalse(self.handoff["authority"]["broadcast_authority"])

    def test_empirical_research_is_not_promoted_by_vector(self):
        m=self.record["exact_metrics"]
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])
        self.assertFalse(m["evidence_complete"])
        self.assertFalse(m["activated"])
        self.assertFalse(m["propagated"])
        self.assertIn("no_research_promotion",self.handoff["goal"]["authority_ceiling"])
        self.assertIn("no_publication",self.handoff["goal"]["authority_ceiling"])
        self.assertFalse(self.record["exact_metrics"]["thread_required"])

    def test_bindings_are_canonical(self):
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.record["authority_effect"],"NONE")

if __name__=="__main__": unittest.main()
