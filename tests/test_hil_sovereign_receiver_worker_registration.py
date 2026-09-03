from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from workers.hil_sovereign_receiver_worker import (
    DEFAULT_PORT,
    receiver_port,
    state_root,
    worker_response,
)

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "SHWP-HIL-SOVEREIGN-RECEIVER-001"


class HILSovereignReceiverWorkerRegistrationTests(unittest.TestCase):
    def test_registry_fragment_binds_exact_worker_adapter_and_independent_admission(self) -> None:
        registry = json.loads(
            (ROOT / "control/worker-registry.d/hil-sovereign-receiver-001.json").read_text(encoding="utf-8")
        )
        task = registry["tasks"][0]
        self.assertEqual(registry["schema"], "stegverse.worker-registry-fragment/v0.1")
        self.assertEqual(task["task_id"], TASK_ID)
        self.assertEqual(task["state"], "HANDOFF_READY")
        self.assertEqual(task["executor_binding"], "AUTHORIZED")
        self.assertEqual(task["cost_basis_ref"], "cost-basis/worker-runtime/hil-sovereign-receiver.json")
        admission = task["admission"]
        self.assertEqual(admission["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertEqual(admission["claim_state"], "AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM")
        self.assertTrue(admission["heartbeat_reference_only"])
        self.assertFalse(admission["heartbeat_grants_execution_authority"])
        self.assertFalse(admission["carrier_trigger_required"])
        self.assertTrue(admission["fresh_fence_required"])
        self.assertEqual(registry["workers"][0]["worker_id"], "hil-sovereign-receiver-worker")
        self.assertEqual(registry["workers"][0]["adapter_ref"], "process:hil-sovereign-receiver-v1")
        self.assertFalse(registry["github_token_required"])

    def test_cost_basis_is_bounded_and_zero_external_cost(self) -> None:
        value = json.loads(
            (ROOT / "cost-basis/worker-runtime/hil-sovereign-receiver.json").read_text(encoding="utf-8")
        )
        self.assertEqual(value["schema"], "stegverse.worker-runtime-cost-basis/v0.1")
        self.assertEqual(value["task_class"], "hil_sovereign_receiver_activation")
        self.assertGreaterEqual(value["hb_estimate"]["expiry_candidate_beats"], 1)
        self.assertNotEqual(value["hb_estimate"]["confidence"], "NONE")
        self.assertEqual(value["cost_estimate"]["external_cost_usd"], 0)
        self.assertEqual(value["cost_estimate"]["operator_seconds"], 0)

    def test_process_adapter_is_enabled_and_credential_minimal(self) -> None:
        adapters = json.loads(
            (ROOT / "control/process-worker-adapters.d/hil-sovereign-receiver-001.json").read_text(encoding="utf-8")
        )
        adapter = adapters["adapters"][0]
        self.assertTrue(adapter["enabled"])
        self.assertEqual(adapter["adapter_ref"], "process:hil-sovereign-receiver-v1")
        self.assertEqual(adapter["command"], ["python", "workers/hil_sovereign_receiver_worker.py"])
        self.assertNotIn("GITHUB_TOKEN", adapter["env_allowlist"])
        self.assertNotIn("GH_TOKEN", adapter["env_allowlist"])
        self.assertIn("STEGVERSE_LLM_ADAPTER_ROOT", adapter["env_allowlist"])
        self.assertIn("STEGVERSE_HIL_STATE_ROOT", adapter["env_allowlist"])

    def test_executable_handoff_preserves_authority_boundaries(self) -> None:
        handoff = json.loads(
            (ROOT / "handoffs/SHWP-HIL-SOVEREIGN-RECEIVER-001.json").read_text(encoding="utf-8")
        )
        self.assertEqual(handoff["schema"], "stegverse.executable-handoff/v0.1")
        self.assertEqual(handoff["state"], "INCOMPLETE_REQUIRES_CONTINUED_BUILD")
        authority = handoff["authority"]
        self.assertEqual(authority["credential_authority"], "TV/TVC")
        self.assertFalse(authority["github_token_required"])
        self.assertFalse(authority["participant_machine_required"])
        self.assertFalse(authority["developer_machine_required"])
        self.assertTrue(authority["current_user_iphone_required"])
        self.assertFalse(authority["hb30_browser_capsule_required"])
        self.assertFalse(authority["third_party_runtime_required"])
        self.assertFalse(authority["execution_authority"])
        self.assertFalse(authority["publication_authority"])
        self.assertFalse(authority["master_records_authority"])
        self.assertTrue(authority["same_device_execution_required"])
        self.assertFalse(authority["requires_other_machine"])
        self.assertFalse(authority["other_machine_may_be_required"])
        self.assertTrue(authority["active_established_device_required"])
        self.assertEqual(handoff["activation"]["esrl_shared_gateway_runtime"]["state"], "INCOMPLETE_OTHER_MACHINE_REQUIRED")
        self.assertTrue(handoff["activation"]["esrl_shared_gateway_runtime"]["other_machine_dependency"])
        self.assertFalse(handoff["activation"]["esrl_shared_gateway_runtime"]["public_gateway_same_device_observed"])
        execution = handoff["execution"]
        self.assertIn("sovereign_hil_receiver_activation", execution["required_capabilities"])
        self.assertEqual(execution["allowed_paths"], ["receipts/hil-sovereign-receiver/**"])
        self.assertEqual(execution["external_cost_ceiling_usd"], 0)

    def test_worker_defaults_to_durable_stegverse_state_and_bounded_port(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            expected = Path(td) / "hil-state"
            with patch.dict("os.environ", {"STEGVERSE_HIL_STATE_ROOT": str(expected), "STEGVERSE_HIL_RECEIVER_PORT": "8877"}, clear=False):
                self.assertEqual(state_root(), expected.resolve())
                self.assertEqual(receiver_port(), 8877)
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(receiver_port(), DEFAULT_PORT)
            self.assertIn(".stegverse/hil/sovereign-receiver", state_root().as_posix())

    def test_worker_response_keeps_activation_open_after_local_ready(self) -> None:
        response = worker_response(
            state="ACTIVE",
            transition="HIL_RECEIVER_LOCAL_READY_PUBLIC_RENDEZVOUS_REQUIRED",
            sequence=4,
            epoch=42,
            next_transition="HIL_PUBLIC_HTTPS_RENDEZVOUS",
        )
        self.assertEqual(response["schema"], "stegverse.worker-response/v0.1")
        self.assertEqual(response["state"], "ACTIVE")
        self.assertEqual(response["expected_next_earliest_epoch"], 43)
        self.assertEqual(response["expected_next_latest_epoch"], 46)
        self.assertIn("receipts/hil-sovereign-receiver/", response["checkpoint_ref"])


if __name__ == "__main__":
    unittest.main()
