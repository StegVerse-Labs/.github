from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK_ID="SHWP-STEGFIN-SOVEREIGN-TRADING-001"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"
spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)

class StegFinSovereignTradingCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/stegfin-sovereign-trading-001.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/SHWP-STEGFIN-SOVEREIGN-TRADING-001.json").read_text(encoding="utf-8"))

    def test_vector_recomputes_from_single_exact_blocker(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]),self.record["vector"])
        self.assertEqual(self.record["vector"],"50000000101000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"],1)
        self.assertEqual(self.task["admissible_existence"]["blockers"],self.handoff["admissible_existence"]["blockers"])

    def test_same_execution_proof_remains_missing(self):
        self.assertEqual(self.task["admissible_existence"]["blockers"],["SAME_EXECUTION_INTERNAL_SETTLEMENT_RECONSTRUCTION_E2_NOT_YET_OBSERVED"])
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])
        self.assertFalse(self.record["exact_metrics"]["evidence_complete"])
        self.assertFalse(self.record["exact_metrics"]["activated"])
        self.assertFalse(self.record["exact_metrics"]["propagated"])

    def test_internal_lane_does_not_gain_external_financial_authority(self):
        self.assertFalse(self.handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(self.handoff["authority"]["github_token_required"])
        self.assertFalse(self.handoff["authority"]["wallet_signing_authority"])
        self.assertFalse(self.handoff["authority"]["broadcast_authority"])
        self.assertIn("no_external_custody",self.handoff["goal"]["authority_ceiling"])
        self.assertIn("no_external_network_execution",self.handoff["goal"]["authority_ceiling"])
        self.assertIn("no_scale_up",self.handoff["goal"]["authority_ceiling"])
        self.assertEqual(self.record["authority_effect"],"NONE")

    def test_bindings_and_thread_state(self):
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)
        self.assertFalse(self.record["exact_metrics"]["thread_required"])

if __name__=="__main__": unittest.main()
