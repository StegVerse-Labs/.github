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
        self.assertIn("control/heartbeat-state.json", action)
        self.assertIn("remaining at HB29", action)
        self.assertIn("HB30 or later", action)

    def test_worker_coordinator_and_all_nine_predicates_are_required(self):
        continuity = self.handoff["continuity"]
        expected = {
            "runtime_materialized",
            "native_service_active",
            "continuous_runtime_live",
            "heartbeat_epoch_advanced",
            "worker_coordination_checkpoint_observed",
            "controlled_restart_observed",
            "epoch_and_generation_non_regressing",
            "no_duplicate_claim_or_fence",
            "state_reconstruction_pass",
        }
        self.assertEqual(set(continuity["required_predicates"]), expected)
        terminal = " ".join(self.handoff["completion"]["terminal_when"])
        self.assertIn("WorkerCoordinator", terminal)
        self.assertIn("control/heartbeat-carrier-runtime-state.json", terminal)

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
