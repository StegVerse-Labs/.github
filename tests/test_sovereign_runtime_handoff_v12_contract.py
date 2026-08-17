from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoffs" / "SHWP-DURABLE-RUNTIME-ACTIVATION.json"


class SovereignRuntimeHandoffV12ContractTests(unittest.TestCase):
    def setUp(self):
        self.handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))

    def test_canonical_runtime_is_separated_v12(self):
        execution = self.handoff["execution"]
        self.assertEqual(execution["canonical_carrier_runtime"], "heartbeat_runtime.engine_v12.HeartbeatRuntime")
        self.assertEqual(execution["worker_runtime"], "heartbeat_runtime.worker_runtime.WorkerCoordinator")
        self.assertFalse(execution["legacy_combined_runtime_is_production_target"])
        self.assertIn("heartbeat_runtime/engine_v12.py", self.handoff["task"]["source_refs"])
        self.assertNotIn("heartbeat_runtime/engine_v11.py", self.handoff["task"]["source_refs"])

    def test_legacy_hb29_is_immutable_cutover_source_not_live_progress_file(self):
        cutover = self.handoff["v12_cutover_contract"]
        execution = self.handoff["execution"]
        action = self.handoff["completion"]["next_authorized_action"]
        self.assertEqual(cutover["legacy_source"], "control/heartbeat-state.json")
        self.assertEqual(cutover["legacy_epoch"], 29)
        self.assertTrue(cutover["legacy_source_must_remain_immutable"])
        self.assertEqual(cutover["first_persistent_carrier_epoch"], 30)
        self.assertEqual(cutover["carrier_state"], "control/heartbeat-carrier-runtime-state.json")
        self.assertFalse(execution["legacy_state_mutable_after_cutover"])
        self.assertEqual(execution["legacy_state_epoch"], 29)
        self.assertIn("advance_heartbeat_transition.py", action)
        self.assertIn("legacy HB29", action)
        self.assertIn("HB30 or a later valid successor", action)

    def test_state_transition_continuity_replaces_resident_service_as_completion_prerequisite(self):
        continuity = self.handoff["state_transition_continuity"]
        expected = {
            "legacy_hb29_unchanged",
            "carrier_epoch_at_least_30",
            "carrier_generation_non_regressing",
            "worker_runtime_checkpoint_observed_at_or_after_carrier_epoch",
            "worker_control_plane_observed",
            "no_duplicate_claim_or_fence",
            "state_reconstruction_pass",
        }
        self.assertEqual(set(continuity["terminal_predicates"]), expected)
        self.assertFalse(continuity["another_physical_machine_required"])
        self.assertFalse(continuity["always_on_external_host_required"])
        self.assertFalse(continuity["wall_clock_continuous_process_required"])
        self.assertTrue(continuity["resident_native_supervision_optional"])
        self.assertEqual(continuity["transition_producer"], "scripts/advance_heartbeat_transition.py")
        resident = set(self.handoff["continuity"]["resident_supervision_optional_predicates"])
        self.assertIn("continuous_runtime_live", resident)
        self.assertIn("controlled_restart_observed", resident)

    def test_repairs_and_authority_boundaries_are_durable(self):
        repairs = self.handoff["released_repairs"]
        self.assertEqual(repairs["g18_adapter_liveness"]["pull_request"], 203)
        self.assertEqual(repairs["ephemeral_separated_runtime"]["pull_request"], 204)
        authority = self.handoff["authority"]
        self.assertEqual(authority["credential_authority"], "TV/TVC")
        self.assertEqual(authority["github_token_production_authority"], "NONE")
        self.assertFalse(authority["non_tv_tvc_secret_or_token_allowed"])
        self.assertFalse(self.handoff["completion"]["live_activation_claimed"])


if __name__ == "__main__":
    unittest.main()
