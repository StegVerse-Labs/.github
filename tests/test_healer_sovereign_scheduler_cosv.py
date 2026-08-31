from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK_ID="SHWP-HEALER-SOVEREIGN-SCHEDULER-001"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"
spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)
class HealerSovereignSchedulerCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/healer-sovereign-scheduler-001.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json").read_text(encoding="utf-8"))
    def test_vector_recomputes(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]),self.record["vector"])
        self.assertEqual(self.record["vector"],"50000000100000")
    def test_retired_g18_is_not_a_machine_dependency_blocker(self):
        dep=self.handoff["completion"]["dependency_state"]
        self.assertEqual(dep["state"],"RELEASE_COMPLETE_NOT_A_DOWNSTREAM_GATE")
        self.assertIsNone(dep["blocker"])
        self.assertFalse(dep["g18_terminalization_required"])
        self.assertEqual(self.record["exact_metrics"]["blocker_count"],0)
        self.assertFalse(dep["current_iphone_hb30_action_required"])
        self.assertFalse(dep["third_party_primary_runtime_required"])
    def test_no_live_activation_or_propagation_promotion(self):
        tls=self.handoff["completion"]["coinbase_gateway_tls_source"]
        self.assertFalse(tls["production_public_route_observed"])
        self.assertFalse(tls["local_tls_runtime_receipt_observed"])
        self.assertFalse(self.record["exact_metrics"]["evidence_complete"])
        self.assertFalse(self.record["exact_metrics"]["activated"])
        self.assertFalse(self.record["exact_metrics"]["propagated"])
    def test_bindings_are_authority_neutral(self):
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.task["machine_readable_state"]["cosv"]["authority_effect"],"NONE")
if __name__=="__main__": unittest.main()
