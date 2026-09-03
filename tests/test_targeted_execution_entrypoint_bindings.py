from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GENERIC = {
    "handoffs/COSV-LIVE-PACKET-AUTOMATION-006.json": "COSV-LIVE-PACKET-AUTOMATION-006",
    "handoffs/SHWP-HIL-SOVEREIGN-RECEIVER-001.json": "SHWP-HIL-SOVEREIGN-RECEIVER-001",
    "handoffs/SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001.json": "SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001",
    "handoffs/SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001.json": "SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001",
    "handoffs/SHWP-TV-TVC-RESIDENT-PROOF-001.json": "SHWP-TV-TVC-RESIDENT-PROOF-001",
}


class TargetedExecutionEntrypointBindingTests(unittest.TestCase):
    def load(self, rel: str) -> dict:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))

    def test_generic_independent_tasks_bind_exact_one_shot_entrypoint(self):
        for rel, task_id in GENERIC.items():
            with self.subTest(rel=rel):
                handoff = self.load(rel)
                activation = handoff["activation"]
                target = activation["targeted_execution"]
                self.assertEqual(activation["authority_domain"], "INDEPENDENT_TASK_CONTROL")
                self.assertEqual(activation["carrier"], "heartbeat_reference_only")
                self.assertFalse(activation["carrier_trigger_required"])
                self.assertEqual(target["mode"], "TARGETED_INDEPENDENT_TASK_CONTROL_ONE_SHOT")
                self.assertEqual(
                    target["argv"],
                    ["python", "scripts/run_worker_runtime.py", "--task-id", task_id],
                )
                self.assertTrue(target["requires_existing_separated_carrier_reference"])
                self.assertFalse(target["g18_bootstrap_allowed"])
                self.assertFalse(target["compatibility_carrier_packet_consumption"])
                self.assertFalse(target["unrelated_worker_execution"])
                self.assertFalse(target["broad_orphan_reconciliation"])
                self.assertFalse(target["heartbeat_grants_execution_authority"])
                self.assertEqual(target["credential_authority"], "TV/TVC")
                self.assertEqual(target["github_token_runtime_authority"], "NONE")

    def test_hil_current_solution_is_same_device_runtime_execution(self):
        handoff = self.load("handoffs/SHWP-HIL-SOVEREIGN-RECEIVER-001.json")
        self.assertEqual(handoff["state"], "SAME_DEVICE_SOURCE_INTEGRATION_VALIDATION_PENDING")
        self.assertEqual(
            handoff["block"]["dependency"],
            "authentic same-device HIL runtime execution and retained receipts",
        )
        self.assertEqual(
            handoff["block"]["observer"],
            "authentic same-device runtime receipts retained by the established device",
        )
        self.assertEqual(
            handoff["block"]["solution_command"],
            "python scripts/run_worker_runtime.py --task-id SHWP-HIL-SOVEREIGN-RECEIVER-001",
        )
        self.assertEqual(
            handoff["activation"]["targeted_execution"]["argv"],
            ["python", "scripts/run_worker_runtime.py", "--task-id", "SHWP-HIL-SOVEREIGN-RECEIVER-001"],
        )
        self.assertTrue(handoff["activation"]["targeted_execution"]["same_device_execution_required"])
        self.assertFalse(handoff["activation"]["targeted_execution"]["other_machine_allowed"])
        self.assertFalse(handoff["activation"]["esrl_shared_gateway_runtime"]["public_gateway_required_for_lease_open"])
        self.assertTrue(handoff["activation"]["esrl_shared_gateway_runtime"]["local_ready_sufficient_for_targeted_execution"])
        self.assertFalse(handoff["activation"]["esrl_shared_gateway_runtime"]["other_machine_dependency"])
        self.assertTrue(handoff["activation"]["esrl_shared_gateway_runtime"]["public_observation_is_downstream_optional"])
        self.assertNotIn("each admitted heartbeat", handoff["activation"]["recheck_trigger"])

    def test_ecosystem_chat_keeps_dedicated_historical_parent_executor(self):
        handoff = self.load("handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json")
        target = handoff["activation"]["targeted_execution"]
        self.assertEqual(target["mode"], "DEDICATED_INDEPENDENT_PARENT_ONE_SHOT")
        self.assertEqual(
            target["argv"],
            ["python", "scripts/run_independent_ecosystem_chat_parent.py"],
        )
        self.assertFalse(target["generic_worker_runtime_task_id_mode_allowed"])
        self.assertEqual(target["fresh_fence_minimum_exclusive"], 22)
        self.assertFalse(target["g20_authority_reuse_allowed"])
        self.assertFalse(target["g22_recovery_authority_reuse_allowed"])
        self.assertEqual(target["credential_authority"], "TV/TVC")
        self.assertEqual(target["github_token_runtime_authority"], "NONE")


    def test_portable_refresh_then_execute_bindings_require_no_systemd_or_second_machine(self):
        for rel, task_id in GENERIC.items():
            with self.subTest(rel=rel):
                handoff = self.load(rel)
                portable = handoff["activation"]["portable_refresh_then_execute"]
                self.assertEqual(portable["mode"], "PORTABLE_REFRESH_THEN_TARGETED_ONE_SHOT")
                self.assertEqual(
                    portable["argv"],
                    ["python", "scripts/refresh_and_execute_resident_task.py", "--task-id", task_id],
                )
                self.assertFalse(portable["systemd_required"])
                self.assertFalse(portable["second_machine_required"])
                self.assertFalse(portable["network_source_fetch_allowed"])
                self.assertTrue(portable["runtime_state_preserved"])
                self.assertFalse(portable["source_refresh_is_runtime_execution"])
                self.assertFalse(portable["heartbeat_grants_execution_authority"])
                self.assertEqual(portable["github_token_runtime_authority"], "NONE")
                self.assertEqual(portable["credential_authority"], "TV/TVC")

    def test_ecosystem_chat_portable_refresh_keeps_dedicated_parent_mode(self):
        handoff = self.load("handoffs/SHWP-ECOSYSTEM-CHAT-INFERENCE-001.json")
        portable = handoff["activation"]["portable_refresh_then_execute"]
        self.assertEqual(portable["mode"], "PORTABLE_REFRESH_THEN_DEDICATED_PARENT_ONE_SHOT")
        self.assertEqual(
            portable["argv"],
            ["python", "scripts/refresh_and_execute_resident_task.py", "--ecosystem-chat-parent"],
        )
        self.assertFalse(portable["systemd_required"])
        self.assertFalse(portable["second_machine_required"])
        self.assertFalse(portable["network_source_fetch_allowed"])
        self.assertFalse(portable["source_refresh_is_runtime_execution"])
        self.assertEqual(portable["credential_authority"], "TV/TVC")


if __name__ == "__main__":
    unittest.main()
