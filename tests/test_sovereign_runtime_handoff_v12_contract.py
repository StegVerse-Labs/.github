from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoffs" / "SHWP-DURABLE-RUNTIME-ACTIVATION.json"
OSCILLATOR_HANDOFF = ROOT / "docs" / "HEARTBEAT_OSCILLATOR_PRODUCER_MIRROR_HANDOFF.md"
CONTRACT = ROOT / "management" / "SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json"


class SovereignRuntimeHandoffContractTests(unittest.TestCase):
    def setUp(self):
        self.handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_canonical_runtime_is_separated_and_oscillator_contract_is_v13(self):
        execution = self.handoff["execution"]
        self.assertEqual(execution["canonical_carrier_runtime"], "heartbeat_runtime.engine_v13.HeartbeatRuntime")
        self.assertEqual(execution["worker_runtime"], "heartbeat_runtime.worker_runtime.WorkerCoordinator")
        self.assertEqual(execution["carrier_runtime_entrypoint"], "scripts/run_heartbeat_runtime.py")
        self.assertEqual(execution["worker_runtime_entrypoint"], "scripts/run_worker_runtime.py")
        self.assertEqual(
            execution["bounded_progression_sequence"],
            [
                "python scripts/bootstrap_sovereign_runtime.py --source-root . --skip-post-bootstrap-stegfin",
                "python scripts/verify_sovereign_runtime_activation.py",
            ],
        )
        self.assertEqual(self.contract["canonical_runtime"], "heartbeat_runtime.engine_v13.HeartbeatRuntime")
        self.assertEqual(self.contract["oscillator_producer"], "heartbeat_runtime/oscillator_producer.py")
        scoped = OSCILLATOR_HANDOFF.read_text(encoding="utf-8")
        self.assertIn("heartbeat_runtime/oscillator_producer.py", scoped)
        self.assertIn("public runner production mode: oscillator phase deadline driven", scoped)
        self.assertIn("progression dependency: OSCILLATOR_ONLY", scoped)
        self.assertIn("carrier event prerequisite: false", scoped)

    def test_legacy_hb29_is_immutable_while_oscillator_produces_successors(self):
        execution = self.handoff["execution"]
        continuity = self.handoff["state_transition_continuity"]
        self.assertFalse(execution["legacy_state_mutable_after_cutover"])
        self.assertEqual(execution["legacy_state_epoch"], 29)
        self.assertEqual(execution["legacy_state_ref"], "control/heartbeat-state.json")
        self.assertEqual(continuity["continuity_model"], "INDEPENDENT_OSCILLATOR_CONTINUITY")
        self.assertEqual(continuity["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")
        self.assertFalse(continuity["worker_or_task_gating_of_heartbeat"])
        self.assertFalse(continuity["another_physical_machine_required"])
        self.assertFalse(continuity["always_on_external_host_required"])

    def test_worker_evidence_is_goal_evidence_not_heartbeat_clock(self):
        continuity = self.handoff["state_transition_continuity"]
        self.assertFalse(continuity["task_capable_worker_cycle_required_for_g18_goal_release"])
        self.assertFalse(continuity["g18_terminalization_required_for_orphan_recovery"])
        self.assertFalse(continuity["worker_or_task_gating_of_heartbeat"])
        parallel = {row["task_id"]: row for row in self.handoff["parallel_continuations"]}
        recovery = parallel["RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28"]
        self.assertEqual(recovery["state"], "HANDOFF_READY")
        self.assertFalse(recovery["g18_terminalization_required"])
        self.assertGreater(recovery["minimum_fencing_token_exclusive"], 19)

    def test_repairs_and_authority_boundaries_are_durable(self):
        repairs = self.handoff["released_repairs"]
        self.assertEqual(repairs["g18_adapter_liveness"]["pull_request"], 203)
        self.assertEqual(repairs["ephemeral_separated_runtime"]["pull_request"], 204)
        authority = self.handoff["authority"]
        self.assertEqual(authority["credential_authority"], "TV/TVC")
        self.assertEqual(authority["github_token_production_authority"], "NONE")
        self.assertFalse(authority["non_tv_tvc_secret_or_token_allowed"])
        completion = self.handoff["completion"]
        self.assertTrue(completion["success_predicates_satisfied"])
        self.assertEqual(completion["heartbeat_protocol_activation_state"], "TERMINAL_ACTIVE_PROTOCOL_VERIFIED")
        self.assertFalse(completion["heartbeat_dependency"])
        self.assertEqual(completion["live_runtime_activation_state"], "NOT_REQUIRED_FOR_HEARTBEAT_RELEASE_OR_DOWNSTREAM_ADMISSION")
        self.assertIsNone(completion["blocker_reason"])
        self.assertFalse(authority["g18_terminalization_may_gate_downstream"])
        self.assertTrue(completion["resident_request_resolution_task_registered"])
        self.assertEqual(completion["resident_request_resolution_task_id"], "RESOLVE-G18-RESIDENT-REQUEST-CONSUMPTION-001")
        self.assertFalse(completion["resident_request_resolution_runtime_observed"])


if __name__ == "__main__":
    unittest.main()
