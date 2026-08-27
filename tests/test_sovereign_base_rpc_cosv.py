from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TASK_ID="SHWP-SOVEREIGN-BASE-RPC-ACTIVATION-001"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"
spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)
class SovereignBaseRPCCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/sovereign-base-rpc-activation-001.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/SHWP-SOVEREIGN-BASE-RPC-ACTIVATION-001.json").read_text(encoding="utf-8"))
        self.orgtask=json.loads((ROOT/"tasks/TASK-2026-0005.json").read_text(encoding="utf-8"))
    def test_vector_recomputes(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]),self.record["vector"])
        self.assertEqual(self.record["vector"],"50000000101000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"],len(self.task["admissible_existence"]["blockers"]))
    def test_single_live_endpoint_blocker_is_preserved(self):
        self.assertEqual(self.task["admissible_existence"]["blockers"],["REAL_SYNCHRONIZED_STEGVERSE_BASE_ENDPOINT_NOT_YET_OBSERVED"])
        self.assertEqual(self.orgtask["machine_observable_blocker"],"REAL_SYNCHRONIZED_STEGVERSE_BASE_ENDPOINT_NOT_YET_OBSERVED")
        self.assertFalse(self.handoff["constraint"]["human_action_required"])
    def test_reference_validation_is_not_activation(self):
        m=self.record["exact_metrics"]
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])
        self.assertFalse(m["evidence_complete"]); self.assertFalse(m["activated"]); self.assertFalse(m["propagated"])
        self.assertEqual(self.orgtask["activation_state"],"BLOCKED_MACHINE_OWNED_REAL_ENDPOINT_PENDING")
        self.assertEqual(self.handoff["authority"]["trade_authority"],"NONE")
        self.assertEqual(self.handoff["authority"]["wallet_authority"],"NONE")
    def test_bindings_are_authority_neutral(self):
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.task["machine_readable_state"]["cosv"]["authority_effect"],"NONE")
if __name__=="__main__": unittest.main()
