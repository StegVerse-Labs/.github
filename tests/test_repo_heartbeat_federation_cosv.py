from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TASK_ID="SHWP-REPO-HEARTBEAT-FEDERATION-001"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"
spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)

class RepoHeartbeatFederationCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/repo-heartbeat-federation-001.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/SHWP-REPO-HEARTBEAT-FEDERATION-001.json").read_text(encoding="utf-8"))

    def test_vector_recomputes(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]), self.record["vector"])
        self.assertEqual(self.record["vector"], "50000000100000")

    def test_incomplete_coverage_is_not_task_blocker(self):
        self.assertIsNone(self.task["block_ref"])
        self.assertIsNone(self.handoff["block"])
        self.assertEqual(self.record["exact_metrics"]["blocker_count"], 0)

    def test_no_live_coverage_promotion(self):
        m=self.record["exact_metrics"]
        self.assertFalse(m["evidence_complete"])
        self.assertFalse(m["activated"])
        self.assertFalse(m["propagated"])
        self.assertEqual(self.task["state"], "HANDOFF_READY")

    def test_binding_authority_neutral(self):
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.task["machine_readable_state"]["cosv"]["authority_effect"],"NONE")

if __name__=="__main__": unittest.main()
