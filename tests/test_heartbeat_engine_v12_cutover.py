from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from heartbeat_runtime.engine_v12 import HeartbeatRuntime


class HeartbeatEngineV12CutoverTests(unittest.TestCase):
    def _root(self, base: Path) -> Path:
        root = base / "repo"
        control = root / "control"
        control.mkdir(parents=True)
        legacy = {
            "schema": "stegverse.org-heartbeat-state/v1",
            "epoch": 29,
            "generation": 29,
            "last_cycle_at": "2026-08-10T20:51:11Z",
            "subsignals": {"worker_coordination": {"state": "ACTIVE"}},
        }
        (control / "heartbeat-state.json").write_text(json.dumps(legacy, indent=2) + "\n", encoding="utf-8")
        registry = {
            "schema": "stegverse.heartbeat-worker-registry/v0.1",
            "generation": 18,
            "workers": [],
            "tasks": [
                {
                    "task_id": "READY-A",
                    "goal_id": "READY-A",
                    "state": "HANDOFF_READY",
                    "handoff_ref": "handoffs/ready-a.json",
                    "executor_binding": "AUTHORIZED",
                    "worker_id": None,
                    "worker_instance_id": None,
                    "claim_id": None,
                    "lease": None,
                    "heartbeat_timing": None,
                    "assignment_timer": None,
                    "cost_basis_ref": "cost-basis/ready-a.json",
                    "external_entity_job_ref": None,
                    "last_checkpoint_ref": None,
                    "block_ref": None,
                    "archive_eligible": False,
                    "archive_reason_codes": [],
                    "evidence_refs": [],
                },
                {
                    "task_id": "ACTIVE-A",
                    "goal_id": "ACTIVE-A",
                    "state": "ACTIVE",
                    "handoff_ref": "handoffs/active-a.json",
                    "executor_binding": "BOUND",
                    "worker_id": "worker-a",
                    "worker_instance_id": "worker-a-HB7-G18",
                    "claim_id": "SHWP-ACTIVE-A-G18",
                    "lease": None,
                    "heartbeat_timing": {
                        "start_epoch": 7,
                        "last_response_epoch": 29,
                        "last_transition_epoch": 29,
                        "current_transition": "RUNNING",
                        "transition_sequence": 4,
                        "expected_next_transition": None,
                        "expected_next_earliest_epoch": None,
                        "expected_next_latest_epoch": None,
                        "max_missing_response_beats": 3,
                        "expiry_epoch": 71,
                        "expiry_basis": "TASK_CLASS_COST_BASIS",
                        "fencing_token": 18,
                    },
                    "assignment_timer": None,
                    "cost_basis_ref": "cost-basis/active-a.json",
                    "external_entity_job_ref": None,
                    "last_checkpoint_ref": None,
                    "block_ref": None,
                    "archive_eligible": False,
                    "archive_reason_codes": [],
                    "evidence_refs": [],
                },
            ],
        }
        (control / "worker-registry.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        (control / "heartbeat-subsignals.json").write_text(
            json.dumps({
                "schema": "stegverse.heartbeat-subsignals/v1",
                "generation": 23,
                "subsignals": {
                    "organization_federation": {"kind": "organization_readiness_federation", "state": "ACTIVE_PARTIAL_COVERAGE"},
                    "legacy_transport": {"kind": "transport_lease", "lease_id": "LEGACY-TRANSPORT"},
                },
            }, indent=2) + "\n",
            encoding="utf-8",
        )
        return root

    def test_first_write_freezes_hb29_and_emits_hb30_separated_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(Path(tmp))
            legacy_path = root / "control" / "heartbeat-state.json"
            legacy_before = legacy_path.read_bytes()
            result = HeartbeatRuntime(root).cycle(write=True)

            self.assertEqual(result["epoch"], 30)
            self.assertEqual(result["runtime_schema"], "stegverse.heartbeat-carrier-runtime-state/v1")
            self.assertEqual(result["legacy_hb29_cutover"], "ACTIVATED")
            self.assertTrue(result["legacy_hb29_was_first_cutover"])
            self.assertEqual(legacy_path.read_bytes(), legacy_before)
            self.assertEqual(result["claims_issued"], 0)
            self.assertEqual(result["workers_invoked"], 0)
            self.assertEqual(result["tasks_activated"], 0)
            self.assertEqual(result["leases_expired"], 0)
            self.assertIn("coherent_signal_space", result)
            self.assertFalse(result["coherent_signal_space"].get("completeness_claim", False))
            self.assertEqual(len(result["assignment_trigger_packets"]), 1)
            trigger = result["assignment_trigger_packets"][0]
            self.assertEqual(trigger["task_id"], "READY-A")
            self.assertEqual(trigger["carrier_epoch"], 30)
            self.assertEqual(trigger["authority_effect"], "NONE")
            self.assertFalse(trigger["execution_authority"])
            self.assertEqual(trigger["terminal_destination"], "MASTER_RECORDS")

            carrier = json.loads((root / "control" / "heartbeat-carrier-runtime-state.json").read_text())
            self.assertEqual(carrier["epoch"], 30)
            self.assertEqual(carrier["activation_state"], "ACTIVE")
            self.assertTrue(carrier["legacy_cutover"]["closed"])
            self.assertEqual(carrier["legacy_cutover"]["legacy_epoch"], 29)

            observation = json.loads((root / "control" / "heartbeat-carrier-observation.json").read_text())
            observation_text = json.dumps(observation, sort_keys=True)
            self.assertEqual(observation["schema"], "stegverse.heartbeat-carrier-observation/v1")
            self.assertEqual(observation["carrier"]["reference_frame"], "heartbeat_epoch:30")
            self.assertNotIn("claim_id", observation_text)
            self.assertNotIn("fencing_token", observation_text)
            self.assertNotIn("active_leases", observation_text)
            self.assertIn("coherent_signal_space_candidate_presence", observation_text)
            self.assertFalse(observation["authority"]["heartbeat_grants_execution_authority"])
            self.assertEqual(observation["authority"]["credential_authority"], "TV/TVC")

            control_plane = json.loads((root / "control" / "worker-control-plane-coordination.json").read_text())
            self.assertEqual(control_plane["schema"], "stegverse.worker-control-plane-coordination/v1")
            self.assertEqual(control_plane["observed_reference"]["reference_frame"], "heartbeat_epoch:30")
            lease = control_plane["worker_coordination"]["active_leases"][0]
            self.assertEqual(lease["claim_id"], "SHWP-ACTIVE-A-G18")
            self.assertEqual(lease["fencing_token"], 18)
            self.assertFalse(lease["heartbeat_grants_authority"])

            receipt = json.loads((root / "receipts" / "heartbeat-schema-cutover" / "HB29.json").read_text())
            self.assertEqual(receipt["state"], "CLOSED_MIGRATED")
            self.assertEqual(receipt["legacy_epoch"], 29)
            self.assertEqual(receipt["first_new_epoch"], 30)
            self.assertFalse(receipt["legacy_state_mutated"])
            self.assertEqual(receipt["legacy_state_sha256"], hashlib.sha256(legacy_before).hexdigest())
            self.assertEqual(receipt["credential_authority"], "TV/TVC")
            self.assertFalse(receipt["non_tv_tvc_secret_or_token_used"])

    def test_second_cycle_advances_carrier_without_rewriting_hb29_or_cutover_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(Path(tmp))
            legacy_path = root / "control" / "heartbeat-state.json"
            legacy_before = legacy_path.read_bytes()
            runtime = HeartbeatRuntime(root)
            runtime.cycle(write=True)
            receipt_path = root / "receipts" / "heartbeat-schema-cutover" / "HB29.json"
            receipt_before = receipt_path.read_bytes()
            second = runtime.cycle(write=True)
            self.assertEqual(second["epoch"], 31)
            self.assertFalse(second["legacy_hb29_was_first_cutover"])
            self.assertEqual(legacy_path.read_bytes(), legacy_before)
            self.assertEqual(receipt_path.read_bytes(), receipt_before)
            carrier = json.loads((root / "control" / "heartbeat-carrier-runtime-state.json").read_text())
            self.assertEqual(carrier["epoch"], 31)
            self.assertEqual(carrier["reference_frame"], "heartbeat_epoch:31")

    def test_existing_carrier_without_cutover_receipt_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(Path(tmp))
            runtime = HeartbeatRuntime(root)
            runtime.cycle(write=True)
            receipt_path = root / "receipts" / "heartbeat-schema-cutover" / "HB29.json"
            receipt_path.unlink()
            with self.assertRaisesRegex(RuntimeError, "without the immutable HB29 cutover receipt"):
                runtime.cycle(write=True)

    def test_dry_run_previews_hb30_without_creating_cutover_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(Path(tmp))
            legacy_path = root / "control" / "heartbeat-state.json"
            legacy_before = legacy_path.read_bytes()
            result = HeartbeatRuntime(root).cycle(write=False)
            self.assertEqual(result["epoch"], 30)
            self.assertEqual(result["legacy_hb29_cutover"], "PREVIEW_ONLY")
            self.assertIn("coherent_signal_space", result)
            self.assertEqual(legacy_path.read_bytes(), legacy_before)
            self.assertFalse((root / "control" / "heartbeat-carrier-runtime-state.json").exists())
            self.assertFalse((root / "receipts" / "heartbeat-schema-cutover" / "HB29.json").exists())

    def test_wrong_legacy_epoch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(Path(tmp))
            path = root / "control" / "heartbeat-state.json"
            value = json.loads(path.read_text())
            value["epoch"] = 28
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "requires legacy epoch 29"):
                HeartbeatRuntime(root).cycle(write=True)


if __name__ == "__main__":
    unittest.main()
