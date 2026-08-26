from __future__ import annotations

import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from workers import stegos_relay_node_kv_continuity_worker as worker


def invocation():
    handoff = json.loads(
        (Path(__file__).resolve().parents[1] / "handoffs/SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001.json").read_text()
    )
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 32,
        "task": {
            "task_id": worker.TASK_ID,
            "claim_id": "claim-23",
            "heartbeat_timing": {"fencing_token": 23},
        },
        "handoff": handoff,
    }


class RelayNodeKVContinuityWorkerTests(unittest.TestCase):
    def test_registration_preserves_authority_boundaries(self):
        root = Path(__file__).resolve().parents[1]
        registry = json.loads((root / "control/worker-registry.d/stegos-relay-node-kv-continuity-001.json").read_text())
        adapter = json.loads((root / "control/process-worker-adapters.d/stegos-relay-node-kv-continuity-001.json").read_text())
        handoff = json.loads((root / "handoffs/SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001.json").read_text())
        task = registry["tasks"][0]
        self.assertEqual(task["state"], "HANDOFF_READY")
        self.assertFalse(task["admission"]["heartbeat_grants_execution_authority"])
        self.assertEqual(task["admission"]["parent_terminal_transition_required"], "SOVEREIGN_RELAY_LEASE_OPEN")
        self.assertEqual(registry["credential_authority"], "TV/TVC")
        self.assertFalse(registry["github_token_required"])
        row = adapter["adapters"][0]
        self.assertEqual(row["adapter_ref"], "process:stegos-relay-node-kv-continuity-v1")
        self.assertEqual(row["env_allowlist"], ["STEGVERSE_STEGOS_ROOT", "STEGVERSE_RELAY_RUNTIME_BASE"])
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertFalse(handoff["execution"]["parent_activation_request"]["production_capacity_deficit_claimed"])

    def test_missing_parent_receipt_remains_active_without_runtime_action(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(worker, "ROOT", root),                  mock.patch.object(worker, "PARENT_RECEIPT", root / "receipts/stegos-sovereign-relay/parent.json"),                  mock.patch.object(worker, "RECEIPT", root / "receipts/stegos-sovereign-relay/continuity.json"),                  mock.patch.object(sys, "stdin", io.StringIO(json.dumps(invocation()))),                  mock.patch.object(sys, "stdout", io.StringIO()):
                self.assertEqual(worker.main(), 0)
                result = json.loads(worker.RECEIPT.read_text())
                self.assertEqual(result["state"], "ACTIVE")
                self.assertEqual(result["transition_id"], "PARENT_RELAY_LEASE_OPEN_REQUIRED")
                self.assertFalse(result["blocker"]["human_action_required"])
                self.assertFalse(result["blocker"]["physical_additional_machine_required"])

    def test_success_requires_real_release_shape_and_distinct_recreation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            parent_receipt = root / "receipts/stegos-sovereign-relay/parent.json"
            output_receipt = root / "receipts/stegos-sovereign-relay/continuity.json"
            parent_receipt.parent.mkdir(parents=True)
            first_evidence = {
                "schema": "stegos.sovereign_network_runtime_materialization.v1",
                "evidence_id": "first-evidence",
                "lease_id": "first-lease",
                "generation": 1,
                "node_kv_state_root": "kv://stegos-sovereign-relay/controlled-activation-root-1",
            }
            parent_receipt.write_text(json.dumps({
                "state": "COMPLETED",
                "transition_id": "SOVEREIGN_RELAY_LEASE_OPEN",
                "materialization_evidence": first_evidence,
                "runtime": {"runtime_root": str(root / "runtime-first")},
            }))

            fake_continuity = types.ModuleType("stegos.relay_node_kv_continuity")
            fake_continuity.build_teardown_observation = lambda **kwargs: {
                "schema": "stegos.sovereign_relay_teardown_observation.v1",
                "teardown_id": "teardown-1",
            }
            fake_continuity.prove_node_kv_recreation_continuity = lambda **kwargs: {
                "schema": "stegos.sovereign_relay_node_kv_continuity.v1",
                "continuity_id": "continuity-1",
                "state_root_continuity_verified": True,
            }
            fake_continuity.validate_node_kv_continuity_evidence = lambda evidence: None

            fake_adapter_mod = types.ModuleType("stegos.sovereign_ephemeral_node_adapter")
            class FakeAdapter:
                def __init__(self, **kwargs):
                    pass
                def release(self, runtime):
                    return {
                        "runtime_root": runtime["runtime_root"],
                        "relay_terminated": True,
                        "carrier_terminated": True,
                        "worker_terminated": True,
                        "credential_authority": "TV/TVC",
                        "authority_effect": "NONE",
                    }
            fake_adapter_mod.SovereignEphemeralNodeAdapter = FakeAdapter

            requests = []
            def fake_materialize(**kwargs):
                requests.append(kwargs["request"])
                return {
                    "evidence": {
                        "schema": "stegos.sovereign_network_runtime_materialization.v1",
                        "evidence_id": "second-evidence",
                        "lease_id": "second-lease",
                        "generation": 2,
                        "node_kv_state_root": first_evidence["node_kv_state_root"],
                    },
                    "runtime": {"runtime_root": str(root / "runtime-second")},
                    "rendezvous": {"rendezvous_id": "rv-2"},
                }

            stegos_root = root / "StegOS"
            stegos_root.mkdir()
            with mock.patch.object(worker, "ROOT", root),                  mock.patch.object(worker, "PARENT_RECEIPT", parent_receipt),                  mock.patch.object(worker, "RECEIPT", output_receipt),                  mock.patch.object(worker, "find_stegos_root", return_value=stegos_root),                  mock.patch.object(worker, "materialize_relay", side_effect=fake_materialize),                  mock.patch.dict(sys.modules, {
                     "stegos.relay_node_kv_continuity": fake_continuity,
                     "stegos.sovereign_ephemeral_node_adapter": fake_adapter_mod,
                 }),                  mock.patch.object(sys, "stdin", io.StringIO(json.dumps(invocation()))),                  mock.patch.object(sys, "stdout", io.StringIO()):
                self.assertEqual(worker.main(), 0)

            result = json.loads(output_receipt.read_text())
            self.assertEqual(result["state"], "COMPLETED")
            self.assertEqual(result["transition_id"], "RELAY_NODE_KV_CONTINUITY_VERIFIED")
            self.assertTrue(result["continuity_evidence"]["state_root_continuity_verified"])
            self.assertEqual(requests[0]["generation"], 2)
            self.assertFalse(requests[0]["production_capacity_deficit_claimed"])
            self.assertFalse(requests[0]["route_admitted"])
            self.assertFalse(requests[0]["outbound_egress_authorized"])


if __name__ == "__main__":
    unittest.main()
