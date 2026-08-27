from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class EcosystemChatInferenceBindingTests(unittest.TestCase):
    def test_independent_parent_is_non_authorizing_and_fresh_fenced(self) -> None:
        handoff=json.loads((ROOT/"handoffs"/"SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json").read_text())
        auth=json.loads((ROOT/"authorizations"/"SHWP-ECOSYSTEM-CHAT-INFERENCE-001-independent-parent.json").read_text())
        source=(ROOT/"scripts"/"run_independent_ecosystem_chat_parent.py").read_text()
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(handoff["authority"]["github_actions_activation_role"])
        self.assertFalse(handoff["activation"]["heartbeat_required_for_admission"])
        self.assertFalse(handoff["activation"]["heartbeat_reference_is_causal"])
        self.assertGreater(handoff["activation"]["minimum_fencing_token_exclusive"],22-1)
        self.assertEqual(auth["minimum_fencing_token_exclusive"],handoff["activation"]["minimum_fencing_token_exclusive"])
        self.assertFalse(auth["heartbeat_grants_execution_authority"])
        self.assertFalse(auth["recovery_reacquisition_allowed"])
        self.assertNotIn("ProcessWorkerAdapter",source)
        self.assertIn("clean_exec_env",source)

if __name__=="__main__":
    unittest.main()
