import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)

class COSVTests(unittest.TestCase):
    def test_session_vector(self):
        v=cosv.encode_task({"lifecycle":"MERGED_INTO_CANONICAL_WORKSTREAM","archive_ready":True,"unassigned_work":0,"chat_owned_implementation":0,"chat_owned_validation":0,"chat_owned_integration":0,"chat_owned_observation":0,"chat_owned_credentials":0,"canonical_owner_installed":True,"thread_required":False,"blocker_count":0,"evidence_complete":True,"activated":False,"propagated":None})
        self.assertEqual(v,"91000000100102")
    def test_quantity_saturation(self): self.assertEqual(cosv.qty(14),9)
    def test_factor_completion_is_distinct(self):
        self.assertEqual(cosv.factor(99),8); self.assertEqual(cosv.factor(100),9)
    def test_task_validation_rejects_bad_ternary(self):
        self.assertFalse(cosv.validate_vector("task.v1","99000000100102"))
    def test_transition_same(self):
        v="91000000100102"; self.assertEqual(cosv.transition("task.v1",v,v),"0"*14)
    def test_aggregate_rollup(self):
        children=[
          {"vector":"59999999900000","weight":9,"exact_metrics":{"developed":100,"validation":100,"integration":100,"propagation":100,"activation":100,"readiness":100,"ownership":100,"evidence":100}},
          {"vector":"58888888810002","weight":1,"exact_metrics":{"developed":95,"validation":95,"integration":95,"propagation":95,"activation":95,"readiness":95,"ownership":95,"evidence":95,"critical_blockers":1}}
        ]
        r=cosv.aggregate(children)
        self.assertEqual(len(r["vector"]),14)
        self.assertEqual(r["exact_metrics"]["critical_blockers"],1)
    def test_record_requires_evidence(self):
        r={"identity":"x","profile":"task.v1","level":"task","vector":"91000000100102","evidence_refs":[],"observed_at":"now","exact_metrics":{}}
        self.assertFalse(cosv.validate_record(r))

if __name__=="__main__": unittest.main()
