import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workers import stegos_sovereign_relay_bridge as bridge
from workers import stegos_sovereign_relay_materialization_worker as worker


def _make_stegos_root(root: Path) -> Path:
    for rel in bridge.REQUIRED_STEGOS_SURFACES:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture\n", encoding="utf-8")
    return root


class StegOSSovereignRelayMaterializationTests(unittest.TestCase):
    def test_find_stegos_root_prefers_explicit_complete_surface(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            control = root / "control"
            control.mkdir()
            stegos = _make_stegos_root(root / "source" / "StegOS")
            found = bridge.find_stegos_root(control, {"STEGVERSE_STEGOS_ROOT": str(stegos)})
            self.assertEqual(found, stegos.resolve())

    def test_find_stegos_root_rejects_incomplete_surface(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            control = root / "control"
            control.mkdir()
            partial = root / "StegOS"
            partial.mkdir()
            self.assertIsNone(bridge.find_stegos_root(control, {"STEGVERSE_STEGOS_ROOT": str(partial)}))

    def test_process_adapter_and_registry_fragments_preserve_authority_boundaries(self):
        root = Path(__file__).resolve().parents[1]
        adapter = json.loads((root / "control/process-worker-adapters.d/stegos-sovereign-relay-materialization-001.json").read_text())
        registry = json.loads((root / "control/worker-registry.d/stegos-sovereign-relay-materialization-001.json").read_text())
        row = adapter["adapters"][0]
        self.assertEqual(row["adapter_ref"], "process:stegos-sovereign-relay-materialization-v1")
        self.assertEqual(row["env_allowlist"], ["STEGVERSE_STEGOS_ROOT", "STEGVERSE_RELAY_RUNTIME_BASE"])
        task = registry["tasks"][0]
        self.assertEqual(task["state"], "HANDOFF_READY")
        self.assertEqual(task["admission"]["authority_domain"], "INDEPENDENT_TASK_CONTROL")
        self.assertFalse(task["admission"]["heartbeat_grants_execution_authority"])
        self.assertTrue(task["admission"]["fresh_fence_required"])
        self.assertEqual(registry["credential_authority"], "TV/TVC")
        self.assertFalse(registry["github_token_required"])

    def test_executable_handoff_request_is_non_authorizing_controlled_activation(self):
        root = Path(__file__).resolve().parents[1]
        handoff = json.loads((root / "handoffs/SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001.json").read_text())
        req = handoff["execution"]["relay_activation_request"]
        self.assertEqual(handoff["state"], "HANDOFF_READY")
        self.assertFalse(handoff["authority"]["heartbeat_grants_execution_authority"])
        self.assertEqual(req["admission_state"], "ADMITTED")
        self.assertEqual(req["evidence_class"], "CONTROLLED_SOVEREIGN_RUNTIME_ACTIVATION")
        self.assertFalse(req["production_capacity_deficit_claimed"])
        self.assertEqual(req["credential_authority"], "TV/TVC")
        self.assertFalse(req["route_admitted"])
        self.assertFalse(req["outbound_egress_authorized"])

    def test_worker_completes_only_on_full_lease_open_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fake_root = root / "repo"
            fake_root.mkdir()
            stegos = _make_stegos_root(root / "StegOS")
            receipt = fake_root / "receipts/stegos-sovereign-relay/SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001.json"
            materialized = {
                "evidence": {
                    "lease_state": "LEASE_OPEN",
                    "runtime_instantiated": True,
                    "local_identity_verified": True,
                    "bounded_rendezvous_open": True,
                    "public_identity_verified": True,
                    "route_admitted": False,
                    "outbound_egress_executed": False,
                    "credential_authority": "TV/TVC",
                    "credential_material_present": False,
                    "canonical_transition_committed": False,
                },
                "runtime": {"runtime_id": "runtime-1"},
                "rendezvous": {"rendezvous_id": "rv-1"},
            }
            handoff = {
                "execution": {
                    "required_capabilities": ["runtime_observation", "bounded_process_execution", "sovereign_relay_materialization"],
                    "allowed_paths": ["receipts/stegos-sovereign-relay/**"],
                    "relay_activation_request": {"schema": "stegverse.sovereign-relay-materialization-request/v1"},
                }
            }
            invocation = {
                "schema": "stegverse.worker-invocation/v0.1",
                "heartbeat_epoch": 32,
                "task": {"task_id": worker.TASK_ID, "claim_id": "claim-22", "heartbeat_timing": {"fencing_token": 22}},
                "handoff": handoff,
            }
            with mock.patch.object(worker, "ROOT", fake_root), mock.patch.object(worker, "RECEIPT", receipt), mock.patch.object(worker, "find_stegos_root", return_value=stegos), mock.patch.object(worker, "runtime_base", return_value=root / "runtime"), mock.patch.object(worker, "materialize_relay", return_value=materialized), mock.patch("sys.stdin", io.StringIO(json.dumps(invocation))), mock.patch("sys.stdout", io.StringIO()):
                self.assertEqual(worker.main(), 0)
            result = json.loads(receipt.read_text())
            self.assertEqual(result["state"], "COMPLETED")
            self.assertEqual(result["transition_id"], "SOVEREIGN_RELAY_LEASE_OPEN")
            self.assertTrue(result["relay_lease_open"])
            self.assertFalse(result["route_admitted"])
            self.assertFalse(result["outbound_egress_executed"])

    def test_worker_stays_active_when_stegos_source_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fake_root = root / "repo"
            fake_root.mkdir()
            receipt = fake_root / "receipts/stegos-sovereign-relay/SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001.json"
            invocation = {
                "schema": "stegverse.worker-invocation/v0.1",
                "heartbeat_epoch": 32,
                "task": {"task_id": worker.TASK_ID, "claim_id": "claim-22", "heartbeat_timing": {"fencing_token": 22}},
                "handoff": {"execution": {"required_capabilities": ["runtime_observation", "bounded_process_execution", "sovereign_relay_materialization"], "allowed_paths": ["receipts/stegos-sovereign-relay/**"]}},
            }
            with mock.patch.object(worker, "ROOT", fake_root), mock.patch.object(worker, "RECEIPT", receipt), mock.patch.object(worker, "find_stegos_root", return_value=None), mock.patch("sys.stdin", io.StringIO(json.dumps(invocation))), mock.patch("sys.stdout", io.StringIO()):
                self.assertEqual(worker.main(), 0)
            result = json.loads(receipt.read_text())
            self.assertEqual(result["state"], "ACTIVE")
            self.assertEqual(result["transition_id"], "STEGOS_RELAY_SOURCE_MATERIALIZATION_REQUIRED")
            self.assertFalse(result["blocker"]["physical_additional_machine_required"])
            self.assertFalse(result["blocker"]["human_action_required"])


if __name__ == "__main__":
    unittest.main()
