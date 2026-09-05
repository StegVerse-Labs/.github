from __future__ import annotations
import importlib.util, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("transition_readiness",ROOT/"scripts/evaluate_runtime_profile_map_transition_readiness.py")
mod=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(mod)

class TransitionReadinessTests(unittest.TestCase):
    def task(self):
        return {"task_id":"T1","correlation_id":"C1","coordination_state":"PROPOSED","dependencies":[],"blockers":[]}
    def ready(self):
        return {"task_id":"T1","disposition":"ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW"}
    def worker(self): return {"tasks":[]}

    def test_consistent_ready_routes_to_worker_review_without_authority(self):
        result=mod.evaluate(self.task(),self.ready(),{"task_id":"T1","correlation_id":"C1","state":"CONSISTENT"},self.worker())
        self.assertEqual(result["disposition"],"ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW")
        self.assertFalse(result["execution_authority_granted"])
        self.assertFalse(result["interlock_intr_admission_granted"])
        self.assertFalse(result["claim_or_fence_minted"])

    def test_conflict_blocks_transition_review(self):
        result=mod.evaluate(self.task(),self.ready(),{"task_id":"T1","correlation_id":"C1","state":"CONFLICT"},self.worker())
        self.assertEqual(result["disposition"],"BLOCK_FOR_RECONCILIATION_CONFLICT")

    def test_existing_claim_requires_reuse_wait_or_transfer(self):
        worker={"tasks":[{"task_id":"T1","claim_id":"CLAIM-1","heartbeat_timing":{"fencing_token":7}}]}
        result=mod.evaluate(self.task(),self.ready(),{"task_id":"T1","correlation_id":"C1","state":"CONSISTENT"},worker)
        self.assertEqual(result["disposition"],"EXISTING_WORKERCOORDINATOR_OWNERSHIP_REUSE_WAIT_OR_TRANSFER")
        self.assertEqual(result["workercoordinator_fence_projection"],7)

if __name__=="__main__": unittest.main()
