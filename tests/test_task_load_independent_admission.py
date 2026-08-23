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

    def test_heartbeat_live_proof_is_dependency_blocked_but_independent_after_release(self) -> None:
        task = self.assert_independent(
            "control/worker-registry.d/heartbeat-independent-oscillator-live-009.json",
            "HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009",
            expected_state="BLOCKED_DEPENDENCY",
            expected_claim_state="WAITING_FOR_RESIDENT_START_DEPENDENCY",
        )
        self.assertEqual(task["dependencies"], ["HEARTBEAT-OSCILLATOR-RESIDENT-START-012"])
        self.assertEqual(task["block_ref"], "HEARTBEAT-OSCILLATOR-RESIDENT-START-012")
        self.assertIn("carrier-activation.latest.json", task["admission"]["dependency_release_condition"])
        self.assertIn("verified=true", task["admission"]["dependency_release_condition"])

    def test_cosv_packet_automation_is_independently_claimable(self) -> None:
        self.assert_independent(
            "control/worker-registry.d/cosv-live-packet-automation-006.json",
            "COSV-LIVE-PACKET-AUTOMATION-006",
        )

    def test_resident_heartbeat_start_is_independently_claimable_without_becoming_a_startup_dependency(self) -> None:
        rel = "control/worker-registry.d/heartbeat-oscillator-resident-start-012.json"
        self.assert_independent(rel, "HEARTBEAT-OSCILLATOR-RESIDENT-START-012")
        fragment = self.load(rel)
        admission = fragment["tasks"][0]["admission"]
        self.assertTrue(admission["direct_resident_installer_remains_authorized"])
        self.assertFalse(admission["workercoordinator_required_for_carrier_start"])
        self.assertFalse(fragment["worker_runtime_dependency_for_carrier_start"])
        self.assertFalse(fragment["network_fetch_required"])
        self.assertFalse(fragment["third_party_process_host_required"])
        self.assertFalse(fragment["third_party_scheduler_required"])
        self.assertFalse(fragment["third_party_deployment_required"])


if __name__ == "__main__":
    unittest.main()
