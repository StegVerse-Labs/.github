from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TaskLoadIndependentAdmissionTests(unittest.TestCase):
    def load(self, rel: str) -> dict:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))

    def assert_independent(
        self,
        rel: str,
        task_id: str,
        *,
        expected_state: str = "HANDOFF_READY",
        expected_claim_state: str = "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM",
    ) -> dict:
        fragment = self.load(rel)
        task = next(item for item in fragment["tasks"] if item["task_id"] == task_id)
        admission = task["admission"]
        self.assertEqual(task["state"], expected_state)
        self.assertIsNone(task["claim_id"])
        self.assertEqual(admission["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertEqual(admission["claim_state"], expected_claim_state)
        self.assertTrue(admission["fresh_fence_required"])
        self.assertGreaterEqual(admission["minimum_fencing_token_exclusive"], 21)
        self.assertFalse(admission["heartbeat_grants_execution_authority"])
        self.assertFalse(admission["carrier_trigger_required"])
        self.assertFalse(fragment["github_token_required"])
        self.assertEqual(fragment["credential_authority"], "TV/TVC")
        self.assertFalse(fragment["non_tv_tvc_secret_or_token_required"])
        self.assertFalse(fragment["third_party_runtime_required"])
        return task

    def test_heartbeat_live_proof_is_terminal_and_not_reacquirable(self) -> None:
        fragment = self.load("control/worker-registry.d/heartbeat-independent-oscillator-live-009.json")
        task = fragment["tasks"][0]
        self.assertEqual(task["task_id"], "HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009")
        self.assertEqual(task["state"], "COMPLETED")
        self.assertTrue(task["archive_eligible"])
        self.assertEqual(task["dependencies"], [])
        self.assertIsNone(task["block_ref"])
        self.assertIsNone(task["claim_id"])
        self.assertIsNone(task["worker_id"])
        self.assertEqual(task["terminal_transition_id"], "INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED")
        self.assertTrue(fragment["terminal_registration_only"])
        self.assertFalse(fragment["reacquisition_allowed"])
        self.assertEqual(fragment["authority_effect"], "NONE_REGISTRATION_ONLY")
        self.assertFalse(fragment["continuous_process_required"])
        self.assertFalse(fragment["resident_sampler_required_for_progression"])

    def test_cosv_packet_automation_is_independently_claimable(self) -> None:
        self.assert_independent(
            "control/worker-registry.d/cosv-live-packet-automation-006.json",
            "COSV-LIVE-PACKET-AUTOMATION-006",
        )

    def test_optional_resident_sampler_is_independently_claimable_but_not_heartbeat_authority(self) -> None:
        rel = "control/worker-registry.d/heartbeat-oscillator-resident-start-012.json"
        task = self.assert_independent(
            rel,
            "HEARTBEAT-OSCILLATOR-RESIDENT-START-012",
            expected_claim_state="AUTHORIZED_FOR_OPTIONAL_RESIDENT_SAMPLER_CLAIM",
        )
        fragment = self.load(rel)
        admission = task["admission"]
        self.assertEqual(task["role"], "OPTIONAL_RESIDENT_SAMPLER_AND_PERSISTENCE")
        self.assertFalse(task["heartbeat_existence_dependency"])
        self.assertFalse(task["heartbeat_progression_dependency"])
        self.assertTrue(admission["direct_resident_installer_remains_authorized"])
        self.assertFalse(admission["workercoordinator_required_for_carrier_start"])
        self.assertFalse(admission["live_009_depends_on_this_task"])
        self.assertFalse(fragment["continuous_process_required_for_heartbeat"])
        self.assertFalse(fragment["resident_sampler_required_for_progression"])
        self.assertFalse(fragment["network_fetch_required"])


if __name__ == "__main__":
    unittest.main()
