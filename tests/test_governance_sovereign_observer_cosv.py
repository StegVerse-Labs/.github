from __future__ import annotations
import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TASK_ID="GOVERNANCE-SOVEREIGN-TASK-OBSERVER-001"
VECTOR_REF=f"control/task-vectors/{TASK_ID}.json"

spec=importlib.util.spec_from_file_location("cosv",ROOT/"scripts"/"cosv.py")
assert spec and spec.loader
cosv=importlib.util.module_from_spec(spec); spec.loader.exec_module(cosv)

class GovernanceSovereignObserverCOSVTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ROOT/VECTOR_REF).read_text(encoding="utf-8"))
        fragment=json.loads((ROOT/"control/worker-registry.d/governance-sovereign-task-observer-001.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/GOVERNANCE-SOVEREIGN-TASK-OBSERVER-001.json").read_text(encoding="utf-8"))
        self.coverage=json.loads((ROOT/"control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))

    def test_vector_recomputes_with_four_blockers_and_thread_requirement(self):
        self.assertTrue(cosv.validate_record(self.record))
        self.assertEqual(cosv.encode_task(self.record["exact_metrics"]),self.record["vector"])
        self.assertEqual(self.record["vector"],"50000000114000")
        self.assertEqual(self.record["exact_metrics"]["blocker_count"],4)
        self.assertTrue(self.record["exact_metrics"]["thread_required"])
        self.assertEqual(self.task["admissible_existence"]["blockers"],self.handoff["admissible_existence"]["blockers"])

    def test_machine_owned_observer_does_not_gain_authority(self):
        self.assertEqual(self.handoff["state"],"HANDOFF_READY_MACHINE_OWNED")
        self.assertFalse(self.handoff["task"]["manual_execution_allowed"])
        self.assertFalse(self.handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(self.handoff["authority"]["github_token_required"])
        self.assertFalse(self.handoff["authority"]["repository_writeback_authority"])
        self.assertFalse(self.handoff["authority"]["governance_decision_authority"])
        self.assertFalse(self.handoff["authority"]["cge_decision_authority"])
        self.assertFalse(self.handoff["authority"]["runtime_authority"])
        self.assertFalse(self.handoff["authority"]["release_authority"])

    def test_live_dependencies_remain_unobserved(self):
        self.assertIsNone(self.task["admissible_existence"]["activation_proof_ref"])
        self.assertFalse(self.record["exact_metrics"]["evidence_complete"])
        self.assertFalse(self.record["exact_metrics"]["activated"])
        self.assertFalse(self.record["exact_metrics"]["propagated"])
        self.assertFalse(self.handoff["execution"]["hosted_execution_allowed"])
        self.assertFalse(self.handoff["execution"]["remote_checkout_allowed"])

    def test_thread_requirement_is_explicit_in_coverage(self):
        rows={x["task_id"]:x for x in self.coverage.get("thread_required_vectors",[])}
        self.assertIn(TASK_ID,rows)
        self.assertTrue(rows[TASK_ID]["thread_required"])
        self.assertEqual(self.task["source_state_vector_ref"],VECTOR_REF)
        self.assertEqual(self.handoff["source_state_vector_ref"],VECTOR_REF)

if __name__=="__main__": unittest.main()
