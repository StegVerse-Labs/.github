from __future__ import annotations

import json
import unittest
from pathlib import Path

from heartbeat_runtime.worker_runtime import WorkerCoordinator

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009"
RESIDENT_START_ID = "HEARTBEAT-OSCILLATOR-RESIDENT-START-012"


class IndependentHeartbeatLiveProofRegistrationTests(unittest.TestCase):
    def load(self, rel: str) -> dict:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))

    def test_registry_handoff_adapter_and_cost_basis_are_bound(self) -> None:
        registry_fragment = self.load("control/worker-registry.d/heartbeat-independent-oscillator-live-009.json")
        adapter_fragment = self.load("control/process-worker-adapters.d/heartbeat-independent-oscillator-live-009.json")
        handoff = self.load("handoffs/HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009.json")
        cost = self.load("cost-basis/worker-runtime/heartbeat-independent-oscillator-live-proof.json")

        self.assertEqual(registry_fragment["schema"], "stegverse.worker-registry-fragment/v0.1")
        self.assertEqual(adapter_fragment["schema"], "stegverse.process-worker-adapter-fragment/v0.1")
        self.assertEqual(handoff["schema"], "stegverse.executable-handoff/v0.1")
        self.assertEqual(cost["schema"], "stegverse.worker-runtime-cost-basis/v0.1")

        task = registry_fragment["tasks"][0]
        worker = registry_fragment["workers"][0]
        adapter = adapter_fragment["adapters"][0]
        admission = task["admission"]

        self.assertEqual(task["task_id"], TASK_ID)
        self.assertEqual(task["state"], "BLOCKED_DEPENDENCY")
        self.assertEqual(task["dependencies"], [RESIDENT_START_ID])
        self.assertEqual(task["block_ref"], RESIDENT_START_ID)
        self.assertIsNone(task["claim_id"])
        self.assertEqual(admission["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertEqual(admission["claim_state"], "WAITING_FOR_RESIDENT_START_DEPENDENCY")
        self.assertFalse(admission["heartbeat_grants_execution_authority"])
        self.assertFalse(admission["carrier_trigger_required"])
        self.assertTrue(admission["fresh_fence_required"])
        self.assertEqual(
            admission["dependency_release_condition"],
            "receipts/sovereign-host/carrier-activation.latest.json exists and scripts/verify_sovereign_heartbeat_carrier_activation.py returns verified=true",
        )
        self.assertEqual(task["cost_basis_ref"], "cost-basis/worker-runtime/heartbeat-independent-oscillator-live-proof.json")
        self.assertEqual(worker["adapter_ref"], adapter["adapter_ref"])
        self.assertEqual(worker["authority_source"], adapter["authority_ref"])
        self.assertEqual(set(worker["capabilities"]), set(adapter["capabilities"]))
        self.assertTrue(set(handoff["execution"]["required_capabilities"]).issubset(set(worker["capabilities"])))
        self.assertEqual(adapter["env_allowlist"], [])
        self.assertEqual(adapter["command"], ["python", "workers/independent_heartbeat_live_proof_worker.py"])
        self.assertEqual(cost["task_class"], "independent_heartbeat_live_proof")
        self.assertGreater(cost["hb_estimate"]["expiry_candidate_beats"], 0)
        self.assertNotEqual(cost["hb_estimate"]["confidence"], "NONE")

    def test_worker_coordinator_derives_finite_budget(self) -> None:
        fragment = self.load("control/worker-registry.d/heartbeat-independent-oscillator-live-009.json")
        task = fragment["tasks"][0]
        runtime = WorkerCoordinator(ROOT, adapters={})
        budget, basis = runtime._expiry_budget(task)
        self.assertEqual(basis, "TASK_CLASS_COST_BASIS")
        self.assertEqual(budget, 4)
        self.assertLessEqual(budget, int(self.load("handoffs/HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009.json")["execution"]["runtime_window_beats"]))

    def test_registration_grants_no_credential_or_heartbeat_authority(self) -> None:
        fragment = self.load("control/worker-registry.d/heartbeat-independent-oscillator-live-009.json")
        handoff = self.load("handoffs/HEARTBEAT-INDEPENDENT-OSCILLATOR-LIVE-009.json")
        self.assertEqual(fragment["credential_authority"], "TV/TVC")
        self.assertFalse(fragment["github_token_required"])
        self.assertFalse(fragment["non_tv_tvc_secret_or_token_required"])
        self.assertFalse(fragment["third_party_runtime_required"])
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertEqual(handoff["authority"]["credential_authority"], "TV/TVC")
        self.assertEqual(handoff["authority"]["credential_requirement"], "NONE")
        self.assertEqual(handoff["authority"]["third_party_runtime_role"], "FALLBACK_ONLY")
        self.assertTrue(handoff["authority"]["stegverse_primary"])


if __name__ == "__main__":
    unittest.main()
