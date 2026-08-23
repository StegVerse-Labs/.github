from __future__ import annotations

import json
import unittest
from pathlib import Path

from heartbeat_runtime.worker_runtime import WorkerCoordinator

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009"


class IndependentHeartbeatLiveProofRegistrationTests(unittest.TestCase):
    def load(self, rel: str) -> dict:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))

    def test_terminal_registry_handoff_adapter_and_cost_basis_remain_bound_as_provenance(self) -> None:
        registry_fragment = self.load("control/worker-registry.d/heartbeat-independent-oscillator-live-009.json")
        adapter_fragment = self.load("control/process-worker-adapters.d/heartbeat-independent-oscillator-live-009.json")
        handoff = self.load("handoffs/HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009.json")
        cost = self.load("cost-basis/worker-runtime/heartbeat-independent-oscillator-live-proof.json")

        self.assertEqual(registry_fragment["schema"], "stegverse.worker-registry-fragment/v0.1")
        self.assertEqual(registry_fragment["authority_effect"], "NONE_REGISTRATION_ONLY")
        self.assertTrue(registry_fragment["terminal_registration_only"])
        self.assertFalse(registry_fragment["reacquisition_allowed"])
        self.assertEqual(adapter_fragment["schema"], "stegverse.process-worker-adapter-fragment/v0.1")
        self.assertEqual(handoff["schema"], "stegverse.executable-handoff/v0.1")
        self.assertEqual(handoff["state"], "COMPLETED")
        self.assertEqual(cost["schema"], "stegverse.worker-runtime-cost-basis/v0.1")

        task = registry_fragment["tasks"][0]
        adapter = adapter_fragment["adapters"][0]
        self.assertEqual(task["task_id"], TASK_ID)
        self.assertEqual(task["state"], "COMPLETED")
        self.assertTrue(task["archive_eligible"])
        self.assertEqual(task["terminal_transition_id"], "INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED")
        self.assertEqual(task["dependencies"], [])
        self.assertIsNone(task["block_ref"])
        self.assertIsNone(task["claim_id"])
        self.assertIsNone(task["worker_id"])
        self.assertEqual(registry_fragment["workers"], [])
        self.assertEqual(task["cost_basis_ref"], "cost-basis/worker-runtime/heartbeat-independent-oscillator-live-proof.json")
        self.assertEqual(adapter["adapter_ref"], "process:heartbeat-independent-oscillator-live-proof-v1")
        self.assertEqual(adapter["env_allowlist"], [])
        self.assertEqual(adapter["command"], ["python", "workers/independent_heartbeat_live_proof_worker.py"])
        self.assertEqual(cost["task_class"], "independent_heartbeat_live_proof")
        self.assertEqual(handoff["completion"]["transition_id"], "INDEPENDENT_HEARTBEAT_LIVE_PROOF_VERIFIED")
        self.assertFalse(handoff["completion"]["resident_sampler_required_for_progression"])

    def test_worker_coordinator_retains_finite_historical_budget_without_reacquisition(self) -> None:
        fragment = self.load("control/worker-registry.d/heartbeat-independent-oscillator-live-009.json")
        task = fragment["tasks"][0]
        runtime = WorkerCoordinator(ROOT, adapters={})
        budget, basis = runtime._expiry_budget(task)
        self.assertEqual(basis, "TASK_CLASS_COST_BASIS")
        self.assertEqual(budget, 4)
        self.assertLessEqual(budget, int(self.load("handoffs/HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009.json")["execution"]["runtime_window_beats"]))
        self.assertEqual(task["state"], "COMPLETED")
        self.assertFalse(fragment["reacquisition_allowed"])

    def test_registration_grants_no_credential_or_heartbeat_authority(self) -> None:
        fragment = self.load("control/worker-registry.d/heartbeat-independent-oscillator-live-009.json")
        handoff = self.load("handoffs/HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009.json")
        self.assertEqual(fragment["credential_authority"], "TV/TVC")
        self.assertFalse(fragment["github_token_required"])
        self.assertFalse(fragment["non_tv_tvc_secret_or_token_required"])
        self.assertFalse(fragment["third_party_runtime_required"])
        self.assertFalse(fragment["continuous_process_required"])
        self.assertFalse(fragment["resident_sampler_required_for_progression"])
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertEqual(handoff["authority"]["credential_authority"], "TV/TVC")
        self.assertEqual(handoff["authority"]["credential_requirement"], "NONE")
        self.assertEqual(handoff["authority"]["third_party_runtime_role"], "FALLBACK_ONLY")
        self.assertTrue(handoff["authority"]["stegverse_primary"])


if __name__ == "__main__":
    unittest.main()
