from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "data/goal-task-component-bindings/SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001.master-records.json"


class ERLMasterRecordsBindingTests(unittest.TestCase):
    def test_binding_preserves_reusable_authority_and_runtime_evidence_boundary(self):
        value = json.loads(BINDING.read_text(encoding="utf-8"))
        self.assertEqual(value["task_id"], "SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001")
        self.assertEqual(value["cosv_task_vector"], "40000100100000")
        self.assertEqual(value["component_id"], "RTC-EVIDENCE-CUSTODY-004")
        self.assertEqual(value["canonical_owner"], "Master Records")
        self.assertEqual(value["implementation_repository"], "master-records/orchestration")
        self.assertEqual(value["implementation_merge_commit"], "560863ff192f4437911a8d748984d06566c120c7")
        self.assertEqual(value["authority_effect"], "NONE_CUSTODY_AND_RECONSTRUCTION_ONLY")
        self.assertFalse(value["provider_operation_reexecution_authorized"])
        self.assertEqual(value["device_user_verification_authority"], "NONE")
        self.assertEqual(value["user_verification_authority"], "KV/SKAP Vault")
        self.assertFalse(value["validation"]["runtime_evidence_for_this_goal_proven"])
        self.assertIn("AUTHENTIC_THREE_HOP_RECEIPT_CHAIN_OBSERVED", value["preconditions"])
        self.assertIn("TERMINAL_EXACT_BYTES_READBACK_VERIFIED", value["preconditions"])


if __name__ == "__main__":
    unittest.main()
