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
            "subsignals": {
                "worker_coordination": {
                    "state": "ACTIVE",
                    "active_leases": [],
                    "worker_registry_ref": "control/worker-registry.json",
                }
            },
        }
        (control / "heartbeat-state.json").write_text(json.dumps(legacy, indent=2) + "\n", encoding="utf-8")
        registry = {
            "schema": "stegverse.heartbeat-worker-registry/v0.1",
            "generation": 18,
            "workers": [],
            "tasks": [],
        }
        (control / "worker-registry.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        (control / "heartbeat-subsignals.json").write_text(
            json.dumps({
                "schema": "stegverse.heartbeat-subsignals/v1",
                "generation": 23,
                "subsignals": {
                    "organization_federation": {
                        "kind": "organization_readiness_federation",
                        "state": "ACTIVE_PARTIAL_COVERAGE",
                    },
                    "legacy_transport": {
                        "kind": "transport_lease",
                        "lease_id": "LEGACY-TRANSPORT",
                    },
                },
            }, indent=2) + "\n",
            encoding="utf-8",
        )
        return root

    def _g18_registry(self) -> dict:
        return {
            "generation": 18,
            "tasks": [
                {
                    "task_id": "SHWP-DURABLE-RUNTIME-ACTIVATION",
                    "goal_id": "SHWP-DURABLE-RUNTIME-ACTIVATION",
                    "state": "BLOCKED",
                    "worker_id": "sovereign-runtime-activation-worker",
                    "worker_instance_id": "sovereign-runtime-activation-worker-HB15-G18",
                    "claim_id": "SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18",
                    "heartbeat_timing": {
                        "current_transition": "SOVEREIGN_RUNTIME_SOLUTION_REQUIRED",
                        "expiry_epoch": 4111,
                        "expiry_basis": "TASK_CLASS_COST_BASIS",
                        "fencing_token": 18,
                    },
                }
            ],
        }

    def test_first_write_freezes_legacy_hb29_and_activates_hb30_separated_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(Path(tmp))
            legacy_path = root / "control" / "heartbeat-state.json"
            legacy_before = legacy_path.read_bytes()
            runtime = HeartbeatRuntime(root)
            result = runtime.cycle(write=True)

            self.assertEqual(result["epoch"], 30)
            self.assertEqual(result["runtime_schema"], "stegverse.heartbeat-carrier-runtime-state/v1")
            self.assertEqual(result["legacy_hb29_cutover"], "ACTIVATED")
            self.assertTrue(result["legacy_hb29_was_first_cutover"])
            self.assertEqual(legacy_path.read_bytes(), legacy_before)

            carrier_state = json.loads((root / "control" / "heartbeat-carrier-runtime-state.json").read_text())
            self.assertEqual(carrier_state["epoch"], 30)
            self.assertEqual(carrier_state["activation_state"], "ACTIVE")
            self.assertTrue(carrier_state["legacy_cutover"]["closed"])
            self.assertEqual(carrier_state["legacy_cutover"]["legacy_epoch"], 29)

            carrier = json.loads((root / "control" / "heartbeat-carrier-observation.json").read_text())
            carrier_text = json.dumps(carrier, sort_keys=True)
            self.assertEqual(carrier["schema"], "stegverse.heartbeat-carrier-observation/v1")
            self.assertEqual(carrier["carrier"]["reference_frame"], "heartbeat_epoch:30")
            self.assertNotIn("claim_id", carrier_text)
            self.assertNotIn("fencing_token", carrier_text)
            self.assertNotIn("active_leases", carrier_text)
            self.assertFalse(carrier["authority"]["heartbeat_grants_execution_authority"])
            self.assertEqual(carrier["authority"]["credential_authority"], "TV/TVC")

            persisted_control = json.loads((root / "control" / "worker-control-plane-coordination.json").read_text())
            self.assertEqual(persisted_control["schema"], "stegverse.worker-control-plane-coordination/v1")
            self.assertEqual(persisted_control["observed_reference"]["reference_frame"], "heartbeat_epoch:30")
            self.assertEqual(persisted_control["worker_coordination"]["active_leases"], [])

            projected_control = runtime._control_plane_coordination(carrier_state, self._g18_registry())
            lease = projected_control["worker_coordination"]["active_leases"][0]
            self.assertEqual(lease["claim_id"], "SHWP-SHWP-DURABLE-RUNTIME-ACTIVATION-G18")
            self.assertEqual(lease["fencing_token"], 18)
            self.assertFalse(lease["heartbeat_grants_authority"])
            self.assertNotIn("claim_id", carrier_text)

            receipt = json.loads((root / "receipts" / "heartbeat-schema-cutover" / "HB29.json").read_text())
            self.assertEqual(receipt["state"], "CLOSED_MIGRATED")
            self.assertEqual(receipt["legacy_epoch"], 29)
            self.assertEqual(receipt["first_new_epoch"], 30)
            self.assertFalse(receipt["legacy_state_mutated"])
            self.assertEqual(receipt["legacy_state_sha256"], hashlib.sha256(legacy_before).hexdigest())
            self.assertEqual(receipt["credential_authority"], "TV/TVC")
            self.assertFalse(receipt["non_tv_tvc_secret_or_token_used"])

    def test_second_cycle_advances_new_carrier_without_rewriting_hb29_receipt(self) -> None:
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

    def test_dry_run_previews_hb30_without_creating_cutover_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(Path(tmp))
            legacy_path = root / "control" / "heartbeat-state.json"
            legacy_before = legacy_path.read_bytes()
            result = HeartbeatRuntime(root).cycle(write=False)
            self.assertEqual(result["epoch"], 30)
            self.assertEqual(result["legacy_hb29_cutover"], "PREVIEW_ONLY")
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
