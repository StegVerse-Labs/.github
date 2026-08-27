from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK_ID="HEARTBEAT-OSCILLATOR-RESIDENT-START-012"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"
spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)
class HeartbeatResidentStartCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/heartbeat-oscillator-resident-start-012.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/HEARTBEAT-OSCILLATOR-RESIDENT-START-012.json").read_text(encoding="utf-8"))
    def test_vector_recomputes(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]),self.record["vector"])
        self.assertEqual(self.record["vector"],"50000000100000")
    def test_no_registered_blocker_and_no_start_promotion(self):
        self.assertIsNone(self.task["block_ref"])
        self.assertEqual(self.record["exact_metrics"]["blocker_count"],0)
        self.assertEqual(self.handoff["completion"]["live_activation_state"],"START_NOT_YET_OBSERVED")
        self.assertFalse(self.record["exact_metrics"]["evidence_complete"])
        self.assertFalse(self.record["exact_metrics"]["activated"])
        self.assertFalse(self.record["exact_metrics"]["propagated"])
    def test_carrier_start_has_no_worker_or_third_party_prerequisite(self):
        admission=self.task["admission"]
        self.assertFalse(admission["carrier_trigger_required"])
        self.assertFalse(admission["workercoordinator_required_for_carrier_start"])
        self.assertTrue(admission["direct_resident_installer_remains_authorized"])
        self.assertFalse(self.handoff["activation"]["network_fetch_required"])
        self.assertFalse(self.handoff["activation"]["third_party_runtime_required"])
        self.assertFalse(self.handoff["authority"]["heartbeat_grants_execution_authority"])
    def test_bindings_are_authority_neutral(self):
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.task["machine_readable_state"]["cosv"]["authority_effect"],"NONE")
if __name__=="__main__": unittest.main()
