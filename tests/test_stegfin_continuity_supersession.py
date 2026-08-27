from __future__ import annotations
import json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TASK_ID="STEGFIN-CONTINUITY-CARRIER-007"

class StegFinContinuitySupersessionTests(unittest.TestCase):
    def setUp(self):
        fragment=json.loads((ROOT/"control/worker-registry.d/stegfin-continuity-carrier-007.json").read_text(encoding="utf-8"))
        self.task=fragment["tasks"][0]
        self.handoff=json.loads((ROOT/"handoffs/STEGFIN-CONTINUITY-CARRIER-007.json").read_text(encoding="utf-8"))
        self.coverage=json.loads((ROOT/"control/cosv-global-registry-coverage.json").read_text(encoding="utf-8"))

    def test_fragment_and_handoff_are_terminal_superseded(self):
        self.assertEqual(self.task["state"],"SUPERSEDED")
        self.assertEqual(self.handoff["state"],"SUPERSEDED")
        self.assertTrue(self.task["archive_eligible"])
        self.assertEqual(self.task["executor_binding"],"RELEASED")
        self.assertFalse(self.task["supersession"]["fallback_executed"])
        self.assertFalse(self.task["supersession"]["execution_required_for_completed_goal"])

    def test_superseded_task_not_in_active_cosv_gap(self):
        self.assertNotIn(TASK_ID,self.coverage["active_worker_task_ids_missing_canonical_cosv"])
        matches=[x for x in self.coverage.get("reconciled_terminal_tasks",[]) if x.get("task_id")==TASK_ID]
        self.assertEqual(len(matches),1)
        self.assertFalse(matches[0]["vector_required_for_active_coverage"])

    def test_activation_belongs_to_phone_direct_evidence_not_fallback_execution(self):
        self.assertEqual(self.task["admissible_existence"]["phase"],"ACTIVATED_AT_WALLET_HANDOFF_BOUNDARY")
        self.assertEqual(self.task["supersession"]["superseded_by_task_id"],"STEGFIN-PHONE-DIRECT-ROUTE-010")
        self.assertFalse(self.task["supersession"]["fallback_executed"])

if __name__=="__main__": unittest.main()
