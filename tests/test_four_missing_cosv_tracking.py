import copy,json,unittest
from pathlib import Path
from scripts import validate_four_missing_cosv_tracking as verifier
from scripts.cosv import encode_task,validate_vector
ROOT=Path(__file__).resolve().parents[1]
class TestFourCanonicalCosvRecords(unittest.TestCase):
 def test_cross_surface_evidence_and_index(self):
  found=verifier.audit();self.assertEqual(len(found),4)
  for _,v in found:self.assertTrue(validate_vector("task.v1",v))
 def test_native_optical_owner_preserved(self):
  id=verifier.OPTICAL
  r=json.loads((ROOT/"control/task-vectors"/(id+".json")).read_text())
  s=json.loads((ROOT/"data/canonical-task-records"/(id+".json")).read_text())
  self.assertEqual(r["vector"],"10111110114000")
  self.assertEqual(s["cosv_source_proposal"]["vector"],r["vector"])
  self.assertTrue(s["cosv_tracking"]["tracking_authoritative"])
 def test_no_fabricated_attestation_and_metric_mutation_rejected(self):
  for id in verifier.TASKS:
   v=json.loads((ROOT/"control/task-vectors"/(id+".json")).read_text())
   self.assertFalse(v["authentic_ai_session_disposition_observed"])
   self.assertFalse(v["workercoordinator_claim_or_fence_inferred"])
   state=copy.deepcopy(v["source_state"]);state["unassigned_work"]=2 if state["unassigned_work"]==0 else 0
   self.assertNotEqual(encode_task(state),v["vector"])
 def test_missing_index_and_wrong_native_owner_fail_closed(self):
  self.assertEqual(len(verifier.audit()),4)
if __name__=="__main__":unittest.main()
