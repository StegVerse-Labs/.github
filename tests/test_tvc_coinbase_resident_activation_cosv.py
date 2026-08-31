from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TASK_ID="TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"

spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)

class TVCCoinbaseResidentActivationCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/tvc-coinbase-intr-resident-activation-001.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/TVC-COINBASE-INTR-RESIDENT-ACTIVATION-001.json").read_text(encoding="utf-8"))

    def test_vector_recomputes_without_stale_g18_blocker(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]),self.record["vector"])
        self.assertEqual(self.record["vector"],"50000000103000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"],3)
        self.assertEqual(self.task["admissible_existence"]["blockers"],self.handoff["admissible_existence"]["blockers"])

    def test_machine_owned_runtime_has_no_provider_or_site_authority(self):
        self.assertEqual(self.task["state"],"HANDOFF_READY")
        self.assertFalse(self.handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertEqual(self.handoff["authority"]["provider_operation_authority"],"NONE")
        self.assertEqual(self.handoff["authority"]["site_repository_mutation_authority"],"NONE")
        self.assertFalse(self.handoff["authority"]["physical_additional_machine_required"])
        self.assertFalse(self.handoff["authority"]["third_party_runtime_required"])
        self.assertEqual(self.handoff["authority"]["credential_authority"],"TV/TVC")

    def test_runtime_and_owner_ingress_are_not_promoted(self):
        m=self.record["exact_metrics"]
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])
        self.assertFalse(m["evidence_complete"])
        self.assertFalse(m["activated"])
        self.assertFalse(m["propagated"])
        self.assertFalse(self.handoff["completion"]["runtime_activation_claimed"])
        self.assertIn("Do not wait for G18 cleanup",self.handoff["completion"]["next_authorized_action"])
        self.assertEqual(self.record["authority_effect"],"NONE")

    def test_bindings_are_canonical_and_thread_not_required(self):
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)
        self.assertFalse(self.record["exact_metrics"]["thread_required"])
        self.assertTrue(self.task["admission"]["parent_claim_reuse_prohibited"])

    def test_g18_terminalization_is_not_an_admission_dependency(self):
        self.assertEqual(self.task["admission"]["required_terminal_dependencies"],[])
        self.assertIn("management/SHWP_RUNTIME_ACTIVATION_BLOCKER.json",self.task["admission"]["authority_source"])
        self.assertNotIn("SOVEREIGN_RUNTIME_NOT_YET_LIVE_PROVEN",self.task["admissible_existence"]["blockers"])
        self.assertNotIn("SHWP-DURABLE-RUNTIME-ACTIVATION:COMPLETED",self.handoff["task"]["dependencies"])
        self.assertIn("HB31-RELEASE-COMPLETE:SATISFIED",self.handoff["task"]["dependencies"])

if __name__=="__main__": unittest.main()
